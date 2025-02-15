import os
import subprocess
import shutil

class PatchValidation:
    def __init__(self, patch_file="patch_candidates/patch_candidate_1.java"):
        self.patch_file = patch_file

    def validate_patch(self):
        if not os.path.exists(self.patch_file):
            print(f"Patch file '{self.patch_file}' does not exist.")
            return None

        print(f"Compiling patch file: {self.patch_file}...")

        # Run the Java compiler
        result = subprocess.run(["javac", self.patch_file], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error compiling {self.patch_file}:")
            print(result.stderr)
            return None
        else:
            print(f"{self.patch_file} compiled successfully and is good to go!")
            shutil.copy(self.patch_file, "best_patch.java")
            return self.patch_file

# Example usage:
if __name__ == "__main__":
    validator = PatchValidation()  # Uses the default patch file.
    validator.validate_patch()
