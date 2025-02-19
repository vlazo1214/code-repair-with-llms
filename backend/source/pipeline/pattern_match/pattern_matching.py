import re
from typing import List, Any

class PatternMatch:
    def __init__(self, model: Any, rag: Any, fault_plan: str) -> None:
        self.model = model
        self.rag = rag
        self.fault_plan = fault_plan
        self.patterns: List[str] = []

    def get_prompt(self, fault: str, context: str) -> str:
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
        return self.patterns
    
    def extract_faults(self, input_string: str) -> List[str]:
        # Regular expression to match "#### Fault X:"
        fault_pattern = r"(#### Fault \d+:.*?)(?=#### Fault \d+:|$)"  
        matches = re.findall(fault_pattern, input_string, re.DOTALL)  

        # Extract the full fault text from each match
        faults: List[str] = [match.strip() for match in matches]  
        return faults  

    def return_code_block(self, text: str) -> str:
        # regex pattern to match text between triple backticks
        pattern = r"```(?:[a-zA-Z]*)?\r?\n([\s\S]*?)```"

        # find first match and return only the code content
        match = re.search(pattern, text)
        return match.group(1) if match else ""

    # based on prompt and number of faults, execute for each fault
    def execute_pattern_matching(self) -> None:
        # get faults
        faults: List[str] = self.extract_faults(self.fault_plan)
        
        pre_patterns: List[str] = []

        for fault in faults:
            retrieved_context = self.rag.retrieve_context(fault)
            context = "\n".join(entry["code"] for entry in retrieved_context)
            prompt = self.get_prompt(fault, context)
            response = self.model.generate_response(prompt)

            pre_patterns.append(response)

        for pats in pre_patterns:
            self.patterns.append(self.return_code_block(pats))