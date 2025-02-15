import os

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
        
        Don't add any additional text or formatting, return only the file contents WITH the fix from the pattern.
        
        Make sure to use the pattern fix with the file contents. Only use the code portions from the pattern fix.
        
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
            current_file_contents = response

            # Save the patch to a file
            patch_file_name = os.path.join(self.patch_candidates_dir, f"patch_candidate_{idx + 1}.java")
            with open(patch_file_name, "w") as patch_file:
                patch_file.write(response)

        print(f"Generated {len(self.patterns)} patch candidate files in '{self.patch_candidates_dir}'.")

# Example usage
if __name__ == "__main__":
    patch_gen = PatchGeneration()
    patch_gen.create_patch_files()
