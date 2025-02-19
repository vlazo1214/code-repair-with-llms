import os
import re
from typing import List, Any, Optional

class PatchGeneration:
    def __init__(self, model: Any, file_contents: str, patterns: List[str], language) -> None:
        self.model = model
        self.patterns = patterns
        self.file_contents = file_contents
        self.patch_candidates_dir = "patch_candidates"
        self.language = language
    
    def get_prompt(self, pattern: str, current_code: str = "") -> str:
        if current_code:
            return f"""Apply the given pattern fix to the current code while preserving previous fixes.  
            FOLLOW THE OUTPUT GUIDELINES COMPLETELY AND ALWAYS. ENSURE THAT THE CODE BLOCK IS FORMATTED AS SPECIFIED AND ALWAYS COMPLETED.

            Instructions:  
            - Integrate only the necessary modifications from the pattern into the current code.  
            - Maintain the structure and formatting of the original file.  
            - Return the full, updated file with all fixes applied.  
            - Do not add explanations, comments, or extra formatting.  

            Inputs:  
            - Current code state:  
            {current_code}  

            - Pattern to address:  
            {pattern} 

            Output:
            - The full, updated file with the vulnerability fixed.

            Format:
            ```{self.language}
            // Provide the detailed code implementation here
            ```
            """
        else:
            return f"""
            Apply the provided pattern fix to the given file contents and return the entire updated file with the fixes applied.
            FOLLOW THE OUTPUT GUIDELINES COMPLETELY AND ALWAYS. ENSURE THAT THE CODE BLOCK IS FORMATTED AS SPECIFIED AND ALWAYS COMPLETED.

            Instructions:
            - Integrate only the relevant code modifications from the pattern fix into the file contents.
            - Maintain the structure and formatting of the original file.
            - Return the full, corrected file—do not output only the changes.
            - Do not add explanations, comments, or any extra formatting.

            Inputs:
            - file_contents: {self.file_contents}
            - pattern_fix: {pattern}

            Output:
            - The full, updated file with the vulnerability fixed.

            Format:
            ```{self.language}
            // Provide the detailed code implementation here
            ```
            """
        
    def return_code_block(self, text: str) -> str:
        # regex pattern to match text between triple backticks
        pattern = r"```(?:[a-zA-Z]*)?\r?\n([\s\S]*?)```"

        # find first match and return only the code content
        match = re.search(pattern, text)
        return match.group(1) if match else ""

    def create_patch_files(self) -> None:
        # Ensure the output directory exists
        os.makedirs(self.patch_candidates_dir, exist_ok=True)

        # Create or get the base patch file
        base_file_name = os.path.join(self.patch_candidates_dir, f"iterative_patch.{self.language}")
        current_code = ""

        # Read existing content if file exists
        if os.path.exists(base_file_name):
            try:
                with open(base_file_name, "r", encoding='utf-8') as existing_file:
                    current_code = existing_file.read()
            except Exception as e:
                print(f"Warning: Could not read existing file: {str(e)}")
                current_code = ""

        # Iterate through the patterns and update the patch file
        for idx, pattern in enumerate(self.patterns):
            try:
                # Include current code state in the prompt
                prompt = self.get_prompt(pattern, current_code)
                response = self.model.generate_response(prompt)

                # Update the current code with the new response
                current_code = self.return_code_block(response)

                # Write the updated code to file
                with open(base_file_name, "w", encoding='utf-8') as patch_file:
                    patch_file.write(current_code)

                # Create a backup copy for this iteration
                backup_file = os.path.join(
                    self.patch_candidates_dir, 
                    f"iterative_patch_step_{idx + 1}.{self.language}"
                )
                with open(backup_file, "w", encoding='utf-8') as backup:
                    backup.write(current_code)

                print(f"Completed iteration {idx + 1}/{len(self.patterns)} - Updated '{base_file_name}'")

            except Exception as e:
                print(f"Warning: Error in iteration {idx + 1}: {str(e)}")
                continue

        print(f"Completed all {len(self.patterns)} iterations. Final patch in '{base_file_name}'")
