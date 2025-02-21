import re
import logging
from typing import List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatternMatch:
    def __init__(self, model: Any, rag: Any, fault_plan: str) -> None:
        logger.info("Initializing PatternMatch")
        self.model = model
        self.rag = rag
        self.fault_plan = fault_plan
        self.patterns: List[str] = []

    def get_prompt(self, fault: str, context: str) -> str:
        logger.debug("Generating prompt with fault and context")
        return f"""
        You are an expert software engineer. Given the following fault and context, generate an improved code implementation.
        
        **Fault Details (Do NOT include in response):**
        {fault}

        **Context Information (Do NOT include in response):**
        {context}

        Now, generate the solution based on the above fault and context, but only return the structured implementation.
        The solution should just be the small code change and not the entire file. Be sure to follow this guideline.

        ### High-Level Explanation:
        /// Concise and short explanation goes here

        ### Implementation Plan:
        #### Code Changes:
        ```[language]
        // Provide the detailed code implementation here
        ```
        
        Ensure the output follows this format exactly and does not include any references to the provided fault or context.
        """

    def get_matches(self) -> List[str]:
        logger.debug("Returning patterns list")
        return self.patterns
    
    def extract_faults(self, input_string: str) -> List[str]:
        logger.debug("Extracting faults from input string")
        # Regular expression to match "#### Fault X:"
        fault_pattern = r"(#### Fault \d+:.*?)(?=#### Fault \d+:|$)"  
        matches = re.findall(fault_pattern, input_string, re.DOTALL)  

        # Extract the full fault text from each match
        faults: List[str] = [match.strip() for match in matches]
        logger.info(f"Found {len(faults)} faults in input")
        return faults  

    def return_code_block(self, text: str) -> str:
        logger.debug("Extracting code block from text")
        # regex pattern to match text between triple backticks
        pattern = r"```(?:[a-zA-Z]*)?\r?\n([\s\S]*?)```"

        # find first match and return only the code content
        match = re.search(pattern, text)
        if match:
            logger.debug("Successfully extracted code block")
            return match.group(1)
        else:
            logger.warning("No code block found in text")
            return ""

    # based on prompt and number of faults, execute for each fault
    def execute_pattern_matching(self) -> None:
        logger.info("Starting pattern matching execution")
        # get faults
        faults: List[str] = self.extract_faults(self.fault_plan)
        
        pre_patterns: List[str] = []

        for i, fault in enumerate(faults, 1):
            logger.info(f"Processing fault {i}/{len(faults)}")
            retrieved_context = self.rag.retrieve_context(fault)
            context = "\n".join(entry["code"] for entry in retrieved_context)
            logger.debug(f"Retrieved context for fault {i}")
            
            prompt = self.get_prompt(fault, context)
            logger.debug(f"Generated prompt for fault {i}")
            
            response = self.model.generate_response(prompt)
            logger.debug(f"Received response for fault {i}")

            pre_patterns.append(response)

        logger.info(f"Processing {len(pre_patterns)} patterns")
        for i, pats in enumerate(pre_patterns, 1):
            logger.debug(f"Extracting code block from pattern {i}")
            self.patterns.append(self.return_code_block(pats))
        
        logger.info("Pattern matching execution completed")
