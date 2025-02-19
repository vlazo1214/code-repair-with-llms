import unittest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from backend.source.pipeline.fault_loc.fault_localization import FaultLocalization


class TestFaultLocalization(unittest.TestCase):
    def setUp(self) -> None:
        # Create a mock model
        self.mock_model = Mock()
        self.mock_model.max_context = 1000
        self.mock_model.max_response = 750
        self.mock_model.tokenizer = Mock()
        self.mock_model.generate_response = Mock()

        # Sample code content
        self.sample_code = "def test_function():\n    pass"
        
        # Make the mock tokenizer return a list of tokens
        self.mock_model.tokenizer.encode.return_value = [1, 2, 3, 4, 5]  # Example list of tokens
        
        # Initialize FaultLocalization with mock model
        self.fault_loc = FaultLocalization(self.mock_model, self.sample_code)

    def test_initialization(self) -> None:
        """Test proper initialization of FaultLocalization"""
        self.assertEqual(self.fault_loc.model, self.mock_model)
        self.assertEqual(self.fault_loc.file_contents, self.sample_code)
        self.assertEqual(self.fault_loc.max_response, 500)  # 750 - 250
        self.assertIsNone(self.fault_loc.fault_localization)
        self.assertIsInstance(self.fault_loc.chunks, list)

    def test_chunk_code(self) -> None:
        """Test code chunking functionality"""
        # Mock tokenizer encode and decode
        self.mock_model.tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        self.mock_model.tokenizer.decode.return_value = "test code chunk"
        
        chunks = self.fault_loc._chunk_code()
        
        # Verify encode was called correctly
        self.mock_model.tokenizer.encode.assert_any_call(
            self.sample_code, add_special_tokens=False
        )
        
        # Verify chunks structure
        self.assertIsInstance(chunks, list)
        for chunk in chunks:
            self.assertIsInstance(chunk, tuple)
            self.assertEqual(len(chunk), 2)
            self.assertIsInstance(chunk[0], int)
            self.assertIsInstance(chunk[1], str)

    def test_get_prompt(self) -> None:
        """Test prompt generation"""
        test_code = "print('hello')"
        prompt = self.fault_loc.get_prompt(test_code)
        
        # Verify prompt structure
        self.assertIsInstance(prompt, str)
        self.assertIn("High-Level Overview", prompt)
        self.assertIn("Detected Faults", prompt)
        self.assertIn("Output Requirements", prompt)
        self.assertIn(test_code, prompt)

    def test_clean_response(self) -> None:
        """Test response cleaning functionality"""
        test_response = "Some analysis text"
        cleaned = self.fault_loc.clean_response(test_response)
        
        # Verify cleaned response structure
        self.assertIsInstance(cleaned, str)
        self.assertIn("High-Level Overview", cleaned)
        self.assertIn("Detected Faults", cleaned)
        self.assertIn("Output Requirements", cleaned)
        self.assertIn(test_response, cleaned)

    def test_calculate_fault_localization_single_chunk(self) -> None:
        """Test fault localization calculation with single chunk"""
        # Setup mock response
        self.mock_model.generate_response.return_value = "Analysis result"
        self.fault_loc.chunks = [(0, "test code")]
        
        self.fault_loc.calculate_fault_localization()
        
        # Verify model called correctly
        self.mock_model.generate_response.assert_called_once()
        self.assertEqual(self.fault_loc.fault_localization, "Analysis result")

    def test_calculate_fault_localization_multiple_chunks(self) -> None:
        """Test fault localization calculation with multiple chunks"""
        # Setup mock responses
        self.mock_model.generate_response.side_effect = [
            "Analysis 1",
            "Analysis 2",
            "Combined analysis"
        ]
        self.fault_loc.chunks = [(0, "chunk1"), (1, "chunk2")]
        
        self.fault_loc.calculate_fault_localization()
        
        # Verify model called correct number of times
        self.assertEqual(self.mock_model.generate_response.call_count, 3)
        self.assertEqual(self.fault_loc.fault_localization, "Combined analysis")

    def test_empty_code(self) -> None:
        """Test handling of empty code"""
        fault_loc = FaultLocalization(self.mock_model, "")
        self.mock_model.tokenizer.encode.return_value = []
        chunks = fault_loc._chunk_code()
        self.assertEqual(chunks, [])

    def test_large_code_chunking(self) -> None:
        """Test chunking of large code files"""
        # Mock a large token sequence
        large_tokens = list(range(2000))  # Create 2000 tokens
        self.mock_model.tokenizer.encode.return_value = large_tokens
        self.mock_model.tokenizer.decode.return_value = "chunk"
        
        fault_loc = FaultLocalization(self.mock_model, "large code")
        chunks = fault_loc._chunk_code()
        
        # Verify chunks are created correctly
        self.assertTrue(len(chunks) > 1)
        self.assertEqual(chunks[0][0], 0)  # First chunk index
        self.assertEqual(chunks[1][0], 1)  # Second chunk index

    def test_model_response_error_handling(self) -> None:
        """Test handling of model response errors"""
        self.mock_model.generate_response.side_effect = Exception("Model error")
        self.fault_loc.chunks = [(0, "test code")]
        
        with self.assertRaises(Exception):
            self.fault_loc.calculate_fault_localization()

    def test_tokenizer_error_handling(self) -> None:
        """Test handling of tokenizer errors"""
        self.mock_model.tokenizer.encode.side_effect = Exception("Tokenizer error")
        
        with self.assertRaises(Exception):
            self.fault_loc._chunk_code()


if __name__ == '__main__':
    unittest.main()
