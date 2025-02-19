import os
import re

class PatchGeneration:
    def __init__(self, model, file_contents: str, patterns):
        self.model = model
        self.patterns = patterns
        self.file_contents = file_contents
        self.patch_candidates_dir = "patch_candidates"

    def get_prompt(self, file_contents: str, pattern: str) -> str:
        return f"""
        Using the file contents provided (Labeled as file_contents), you will generate a patch file based on the pattern provided.
        The pattern is a fixed vulnerability of a code block inside the file contents.
        
        Use this format:
        ```
        Provide the code implementation here
        ```

        Make sure to keep the code format consistent, there should always be an opening ``` and closing ```.
        
        file_contents: {file_contents}
        pattern: {pattern}
        """

    def create_patch_files(self):
        # Ensure the output directory exists
        os.makedirs(self.patch_candidates_dir, exist_ok=True)

        current_file_contents = self.file_contents  # Start with the initial file contents

        for idx, pattern in enumerate(self.patterns):
            prompt = self.get_prompt(current_file_contents, pattern)
            response = self.model.generate_response(prompt)

            # Update the current file contents with the latest patch
            current_file_contents = self.return_code_block(response)

            # Save the patch to a file
            patch_file_name = os.path.join(self.patch_candidates_dir, f"patch_candidate_{idx + 1}.java")
            with open(patch_file_name, "w") as patch_file:
                patch_file.write(response)

        print(f"Generated {len(self.patterns)} patch candidate files in '{self.patch_candidates_dir}'.")
        
    def return_code_block(self, text: str) -> str:
        # regex pattern to match text between triple backticks
        pattern = r"```(?:[a-zA-Z]*)?\r?\n([\s\S]*?)```"

        # find first match and return only the code content (group 2)
        match = re.search(pattern, text)
        return match.group(1) if match else ""

# Example usage
if __name__ == "__main__":
    patch_gen = PatchGeneration()
    patch_gen.create_patch_files()
