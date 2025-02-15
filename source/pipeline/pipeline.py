import json
import sys
import os

from rag.rag_db import RAG
from fault_loc.fault_localization import FaultLocalization
from pattern_match.pattern_matching import PatternMatch
from patch_gen.patch_generation import PatchGeneration
from patch_valid.patch_validation import PatchValidation

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from source.model.model import Model

"""
this pipeline will be the main process for the pipeline that is being integrated
"""
class Pipeline():
    def __init__(self):
        self.model = None
        self.rag = None
        self.stage1 = False
        self.stage2 = False
        self.stage3 = False
        self.stage4 = False

    def set_rag(self):
        self.rag = RAG()

    # define the model being used throughout the pipeline
    def set_model(self, model_selection: str):
        try:
            self.model = Model(model_selection)
        except Exception as e:
            print(f"Error setting model: {e}")

    # first stage which determines where the fault/vulnerability is
    def fault_localization(self, precode_content):
        fl = FaultLocalization(self.model, precode_content)
        fl.calculate_fault_localization()
        return fl.fault_localization

    # second stage determines the type of fault/vulnerability
    def pattern_matching(self, localization: str):
        pm = PatternMatch(self.model, localization)
        pm.execute_pattern_matching()
        return pm.get_matches()

    # third stage creates the patches and places them in the code
    def patch_generation(self, precode_content, patterns, output_dir="patch_candidates"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        pg = PatchGeneration(self.model, precode_content, patterns)
        pg.create_patch_files()
        return output_dir

    # last stage determines if the fixes are corrected
    def patch_validation(self, fixed_code_path):
        validator = PatchValidation(reference_file=fixed_code_path)
        return validator.validate_patches()

def create_code_dict(file_path):
    # Initialize the list to store dictionaries for each entry
    code_dicts = []
    
    # Open and read the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Process each entry in the JSON file
    for entry in data:
        # Initialize a dictionary for this entry
        code_dict = {}
        
        # Extract the pre_code
        if 'pre_code' in entry:
            code_dict['precode'] = entry['pre_code']
        else:
            code_dict['precode'] = "No pre code available"
        
        # Extract the post_code (if it exists)
        if 'post_code' in entry:
            code_dict['postcode'] = entry['post_code']
        else:
            code_dict['postcode'] = "No post code available"
        
        # Add additional information if available
        if 'id' in entry:
            code_dict['id'] = entry['id']
        if 'sub_id' in entry:
            code_dict['sub_id'] = entry['sub_id']
        if 'human_patch' in entry:
            code_dict['human_patch'] = entry['human_patch']
        if 'cve_id' in entry:
            code_dict['cve_id'] = entry['cve_id']
        if 'cwe_id' in entry:
            code_dict['cwe_id'] = entry['cwe_id']
        
        # Append this entry's dictionary to the list
        code_dicts.append(code_dict)
    
    return code_dicts

def write_to_file(content):
    # Open the file in write mode
    with open("output.txt", 'a') as file:
        # Write the content to the file
        file.write(content + "\n")
        # Close the file
        file.close()

def main():
    # create pipeline
    pipeline = Pipeline()
    
    # process file input
    code_dict = create_code_dict('C:\\Users\\micha\\OneDrive\\Desktop\\Projects\\code-repair-with-llms\\source\\pipeline\\00_initial_java.json')

    # Extract pre_code and post_code from the first entry for demonstration purposes
    pre_code = code_dict[0]['precode']
    post_code = code_dict[0]['postcode']

    # Save post_code to a temporary file for reference
    fixed_code_path = "fixed_code.java"
    with open(fixed_code_path, "w") as fixed_code_file:
        fixed_code_file.write(post_code)

    # set the model to whatever the selection is
    pipeline.set_model("meta-llama/Meta-Llama-3-8B-Instruct")

    file_path = "C:\\Users\\micha\\OneDrive\\Desktop\\Projects\\code-repair-with-llms\\ObjectArrayCodec.java"
    with open(file_path, 'r') as file:
        code_content = file.read()

    # pipeline.set_rag()
    # code_files = [{
    #     "filename": "ObjectArrayCodec.java",
    #     "content": code_content
    # }]
    # pipeline.rag.embed_code(code_files)

    # Fault localization
    write_to_file("#### Fault Localization ####\n")
    localization = pipeline.fault_localization(code_content)
    write_to_file(localization)

    # Pattern matching
    write_to_file("\n#### Pattern Matching ####\n")
    patterns = pipeline.pattern_matching(localization)
    for pattern in patterns:
        write_to_file(pattern)

    # Patch generation
    write_to_file("\n#### Patch Generation ####\n")
    patch_dir = pipeline.patch_generation(code_content, patterns)
    write_to_file(f"Patch candidates written to directory: {patch_dir}")

    # Patch validation using the post_code as the reference
    write_to_file("\n#### Patch Validation ####\n")
    best_patch = pipeline.patch_validation(fixed_code_path)
    if best_patch:
        write_to_file(f"Best patch selected: {best_patch}")
    else:
        write_to_file("No valid patch found.")

if __name__ == "__main__":
    main()
