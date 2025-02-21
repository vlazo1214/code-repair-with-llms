import re
from typing import List, Tuple, Optional, Any
from transformers import AutoTokenizer
from huggingface_hub import InferenceClient
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FaultLocalization:
    def __init__(self, model: Any, file_contents: str) -> None:
        logger.info("Initializing FaultLocalization")
        try:
            self.model = model
            self.file_contents = file_contents
            self.max_context = self.model.max_context - 250
            self.max_response = self.model.max_response - 250
            logger.debug(f"Max context size: {self.max_context}, Max response size: {self.max_response}")
            
            self.chunks: List[Tuple[int, str]] = self._chunk_code()
            self.fault_localization: Optional[str] = None
            logger.info("FaultLocalization initialized successfully")
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}", exc_info=True)
            raise
    
    def _chunk_code(self) -> List[Tuple[int, str]]:
        logger.info("Starting code chunking process")
        try:
            tokens = self.model.tokenizer.encode(self.file_contents, add_special_tokens=False)
            chunk_size = self.max_response
            chunks: List[Tuple[int, str]] = []
            
            logger.debug(f"Total tokens: {len(tokens)}, Chunk size: {chunk_size}")
            
            for i in range(0, len(tokens), chunk_size):
                chunk_tokens = tokens[i:i + chunk_size]
                chunk_text = self.model.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
                chunks.append((i // chunk_size, chunk_text))
                logger.debug(f"Created chunk {i // chunk_size} with {len(chunk_tokens)} tokens")
            
            logger.info(f"Code chunking completed. Total chunks: {len(chunks)}")
            return chunks
        except Exception as e:
            logger.error(f"Error during code chunking: {str(e)}", exc_info=True)
            raise
    
    def get_prompt(self, code: str) -> str:
        logger.debug("Generating prompt for code analysis")
        prompt = f"""
        Analyze the following code file to identify any vulnerabilities or faults. For each identified issue, provide 
        the analysis using the following structured format:

        ### High-Level Overview:
        - Provide a clear, explicit summary of what the file is doing, including its purpose and functionality.

        ### Detected Faults:
        For each fault or vulnerability, use this consistent structure:

        #### Fault 1:
        - **Fault Detected**: [Brief description of the issue]
        - **Cause**: [Explain what part of the code is causing the issue and why]
        - **Impact**: [Outline the potential consequences of this fault on the program's functionality or security]
        - **Solution**: [Provide a detailed suggestion or fix to resolve the issue but do not include a code block just an explanation]

        Repeat the above format (Fault 2, Fault 3, etc.) for additional issues if applicable. If no faults are detected, 
        explicitly state that the code appears to be fault-free.

        ### Output Requirements:
        - Use bullet points and section headers for clarity.
        - Ensure all explanations are concise, actionable, and easy to understand.

        Here is the code: 
        {code}
        """
        logger.debug("Prompt generated successfully")
        return prompt
    
    def clean_response(self, response: str) -> str:
        logger.debug("Cleaning and formatting response")
        cleaned_prompt = f"""
        Refine the following fault analysis to adhere to the structured format:

        ### High-Level Overview:
        - Ensure the summary accurately reflects the file's purpose and functionality.

        ### Detected Faults:
        For each identified fault, follow this structure:

        #### Fault 1:
        - **Fault Detected**: Ensure the description is precise and clear.
        - **Cause**: Provide a detailed yet concise explanation of the root cause.
        - **Impact**: Clarify the potential risks or consequences of the issue.
        - **Solution**: Ensure the solution is actionable and easy to implement.

        Repeat for additional faults (Fault 2, Fault 3, etc.), maintaining clarity and consistency. If no faults are detected, 
        explicitly state that the code appears to be fault-free.

        ### Output Requirements:
        - Improve readability and structure.
        - Enhance clarity and comprehensiveness.
        - Maintain consistency in formatting and terminology.

        Here is the analysis:
        {response}
        """
        logger.debug("Response cleaning completed")
        return cleaned_prompt
    
    def calculate_fault_localization(self) -> None:
        logger.info("Starting fault localization calculation")
        try:
            accumulated_responses: List[str] = []
            
            for index, chunk in self.chunks:
                logger.info(f"Processing chunk {index}")
                prompt = self.get_prompt(chunk)
                logger.debug(f"Generated prompt for chunk {index}")
                
                response = self.model.generate_response(prompt)
                logger.debug(f"Received response for chunk {index}")
                accumulated_responses.append(response)
            
            full_analysis = "\n".join(accumulated_responses)
            logger.debug("Combined all responses")
            
            if len(accumulated_responses) > 1:
                logger.info("Multiple responses detected, cleaning and consolidating")
                cleaned_analysis = self.model.generate_response(self.clean_response(full_analysis))
                self.fault_localization = cleaned_analysis
            else:
                logger.info("Single response detected, using as is")
                self.fault_localization = full_analysis
                
            logger.info("Fault localization calculation completed successfully")
        except Exception as e:
            logger.error(f"Error during fault localization calculation: {str(e)}", exc_info=True)
            raise
