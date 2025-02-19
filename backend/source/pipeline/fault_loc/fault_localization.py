import re
from typing import List, Tuple, Optional, Any
from transformers import AutoTokenizer
from huggingface_hub import InferenceClient
import os

class FaultLocalization:
    def __init__(self, model: Any, file_contents: str) -> None:
        self.model = model  # Model object
        self.file_contents = file_contents
        self.max_context = self.model.max_context - 250
        self.max_response = self.model.max_response - 250
        self.chunks: List[Tuple[int, str]] = self._chunk_code()
        self.fault_localization: Optional[str] = None
    
    def _chunk_code(self) -> List[Tuple[int, str]]:
        tokens = self.model.tokenizer.encode(self.file_contents, add_special_tokens=False)
        chunk_size = self.max_response
        chunks: List[Tuple[int, str]] = []
        
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.model.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunks.append((i // chunk_size, chunk_text))
        
        return chunks
    
    def get_prompt(self, code: str) -> str:
        return f"""
Analyze the following code file to identify any vulnerabilities or faults. For each identified issue, provide 
the analysis using the following structured format:

### High-Level Overview:
- Provide a clear, explicit summary of what the file is doing, including its purpose and functionality.

### Detected Faults:
For each fault or vulnerability, use this consistent structure:

#### Fault 1:
- **Fault Detected**: [Brief description of the issue]
- **Cause**: [Explain what part of the code is causing the issue and why]
- **Impact**: [Outline the potential consequences of this fault on the program’s functionality or security]
- **Solution**: [Provide a detailed suggestion or fix to resolve the issue]

Repeat the above format (Fault 2, Fault 3, etc.) for additional issues if applicable. If no faults are detected, 
explicitly state that the code appears to be fault-free.

### Output Requirements:
- Use bullet points and section headers for clarity.
- Ensure all explanations are concise, actionable, and easy to understand.

Here is the code: 
{code}
        """
    
    def clean_response(self, response: str) -> str:
        return f"""
Refine the following fault analysis to adhere to the structured format:

### High-Level Overview:
- Ensure the summary accurately reflects the file’s purpose and functionality.

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
    
    def calculate_fault_localization(self) -> None:
        accumulated_responses: List[str] = []
        
        for index, chunk in self.chunks:
            response = self.model.generate_response(self.get_prompt(chunk))
            accumulated_responses.append(response)
        
        full_analysis = "\n".join(accumulated_responses)
        if len(accumulated_responses) > 1:
            cleaned_analysis = self.model.generate_response(self.clean_response(full_analysis))
            self.fault_localization = cleaned_analysis
        else:
            self.fault_localization = full_analysis
