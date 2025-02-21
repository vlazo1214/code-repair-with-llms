import unittest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from backend.source.pipeline.pattern_match.pattern_matching import PatternMatch

class TestPatternMatch(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.mock_model = Mock()
        self.mock_rag = Mock()
        self.fault_plan = """
        #### Fault 1:
        Description of fault 1
        #### Fault 2:
        Description of fault 2
        """
        self.pattern_match = PatternMatch(self.mock_model, self.mock_rag, self.fault_plan)

    def test_initialization(self) -> None:
        """Test proper initialization of PatternMatch."""
        self.assertEqual(self.pattern_match.model, self.mock_model)
        self.assertEqual(self.pattern_match.rag, self.mock_rag)
        self.assertEqual(self.pattern_match.fault_plan, self.fault_plan)
        self.assertEqual(self.pattern_match.patterns, [])

    def test_get_prompt(self) -> None:
        """Test prompt generation."""
        fault = "Test fault"
        context = "Test context"
        prompt = self.pattern_match.get_prompt(fault, context)

        # Verify prompt structure
        self.assertIsInstance(prompt, str)
        self.assertIn(fault, prompt)
        self.assertIn(context, prompt)
        self.assertIn("High-Level Explanation", prompt)
        self.assertIn("Implementation Plan", prompt)
        self.assertIn("Code Changes", prompt)

    def test_get_matches(self) -> None:
        """Test getting matches."""
        test_patterns = ["pattern1", "pattern2"]
        self.pattern_match.patterns = test_patterns
        matches = self.pattern_match.get_matches()
        self.assertEqual(matches, test_patterns)

    def test_extract_faults_multiple(self) -> None:
        """Test extracting multiple faults."""
        fault_text = """
        #### Fault 1:
        First fault description
        #### Fault 2:
        Second fault description
        """
        faults = self.pattern_match.extract_faults(fault_text)
        
        self.assertEqual(len(faults), 2)
        self.assertIn("#### Fault 1:", faults[0])
        self.assertIn("#### Fault 2:", faults[1])

    def test_extract_faults_single(self) -> None:
        """Test extracting single fault."""
        fault_text = "#### Fault 1:\nSingle fault description"
        faults = self.pattern_match.extract_faults(fault_text)
        
        self.assertEqual(len(faults), 1)
        self.assertIn("#### Fault 1:", faults[0])

    def test_extract_faults_empty(self) -> None:
        """Test extracting faults from empty string."""
        faults = self.pattern_match.extract_faults("")
        self.assertEqual(faults, [])

    def test_return_code_block_with_language(self) -> None:
        """Test extracting code block with language specification."""
        text = """
        Some text
        ```python
        def test():
            pass
        ```
        More text
        """
        code = self.pattern_match.return_code_block(text)
        self.assertEqual(code.strip(), "def test():\n            pass")

    def test_return_code_block_without_language(self) -> None:
        """Test extracting code block without language specification."""
        text = """
        Some text
        ```
        code block
        ```
        """
        code = self.pattern_match.return_code_block(text)
        self.assertEqual(code.strip(), "code block")

    def test_return_code_block_empty(self) -> None:
        """Test handling of text without code block."""
        code = self.pattern_match.return_code_block("No code block here")
        self.assertEqual(code, "")

    def test_execute_pattern_matching(self) -> None:
        """Test complete pattern matching execution."""
        # Setup mock responses
        mock_context = [
            {"code": "test code 1"},
            {"code": "test code 2"}
        ]
        
        self.mock_rag.retrieve_context.return_value = mock_context
        
        self.mock_model.generate_response.return_value = """
        Some text
        ```python
        def test():
            pass
        ```
        """

        # Execute pattern matching
        self.pattern_match.execute_pattern_matching()

        # Verify RAG was called for each fault
        expected_rag_calls = len(self.pattern_match.extract_faults(self.fault_plan))
        self.assertEqual(self.mock_rag.retrieve_context.call_count, expected_rag_calls)

        # Verify model was called for each fault
        self.assertEqual(self.mock_model.generate_response.call_count, expected_rag_calls)

        # Verify patterns were extracted
        self.assertTrue(len(self.pattern_match.patterns) > 0)
        for pattern in self.pattern_match.patterns:
            self.assertIsInstance(pattern, str)

    def test_execute_pattern_matching_no_faults(self) -> None:
        """Test pattern matching execution with no faults."""
        self.pattern_match.fault_plan = ""
        self.pattern_match.execute_pattern_matching()
        
        # Verify no calls were made
        self.mock_rag.retrieve_context.assert_not_called()
        self.mock_model.generate_response.assert_not_called()
        self.assertEqual(self.pattern_match.patterns, [])  # Compare to an empty list

    def test_execute_pattern_matching_error_handling(self) -> None:
        """Test error handling in pattern matching execution."""
        # Setup mock to raise exception
        self.mock_rag.retrieve_context.side_effect = Exception("Test error")
        
        # Execute with fault plan that should trigger the error
        self.pattern_match.fault_plan = "#### Fault 1:\nTest fault"
        
        # Verify exception is raised
        with self.assertRaises(Exception):
            self.pattern_match.execute_pattern_matching()

if __name__ == '__main__':
    unittest.main()
