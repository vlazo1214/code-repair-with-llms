import json
import sys
import os
from typing import List, Dict, Optional, Any

from rag.rag import RAG
from fault_loc.fault_localization import FaultLocalization
from pattern_match.pattern_matching import PatternMatch
from patch_gen.patch_generation import PatchGeneration
from patch_valid.patch_validation import PatchValidation

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from source.model.model import Model

# global values for testing
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")  # Better to use environment variable
PROVIDER = "openrouter"
MODEL_NAME = "meta-llama/llama-3-8b-instruct:free"  # Model name without provider prefix


"""
this pipeline will be the main process for the pipeline that is being integrated
"""
class Pipeline:
    def __init__(self) -> None:
        self.model: Optional[Model] = None
        self.rag: Optional[RAG] = None
        self.stage1: bool = False
        self.stage2: bool = False
        self.stage3: bool = False
        self.stage4: bool = False

    def set_rag(self) -> None:
        self.rag = RAG()

    # define the model being used throughout the pipeline
    def set_model(self, model_selection: Optional[str] = None, api_key: Optional[str] = None, provider: Optional[str] = None, test: bool = False) -> None:
        try:
            self.model = Model(model_selection, api_key, provider, test)
        except Exception as e:
            print(f"Error setting model: {e}")

    # first stage which determines where the fault/vulnerability is
    def fault_localization(self, precode_content: str) -> Any:
        fl = FaultLocalization(self.model, precode_content)
        fl.calculate_fault_localization()
        return fl.fault_localization

    # second stage determines the type of fault/vulnerability
    def pattern_matching(self, localization: str) -> Any:
        pm = PatternMatch(self.model, self.rag, localization)
        pm.execute_pattern_matching()
        return pm.get_matches()

    # third stage creates the patches and places them in the code
    def patch_generation(self, precode_content: str, patterns: List[str], output_dir: str = "patch_candidates") -> str:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        pg = PatchGeneration(self.model, precode_content, patterns, "java")
        pg.create_patch_files()
        return output_dir

    # last stage determines if the fixes are corrected
    def patch_validation(self, faults: str) -> Any:
        validator = PatchValidation(self.model, patch_dir="patch_candidates", faults=faults, language="java")
        return validator.validate_patches()

def create_code_dict(file_path: str) -> List[Dict[str, str]]:
    # Initialize the list to store dictionaries for each entry
    code_dicts: List[Dict[str, str]] = []
    
    # Open and read the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Process each entry in the JSON file
    for entry in data:
        # Initialize a dictionary for this entry
        code_dict: Dict[str, str] = {}
        
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

def write_to_file(content: str) -> None:
    with open("output.txt", 'a', encoding='utf-8') as file:
        file.write(content + "\n")

def main() -> None:
    # create pipeline
    pipeline = Pipeline()

    pipeline.set_model(test=True)

    file_path = "C:\\Users\\Gavin Cruz\\Documents\\SD1\\finalspace\\code-repair-with-llms\\javafile.java" # for others change this to your file path
    with open(file_path, 'r') as file:
        code_content = file.read()

    pipeline.set_rag()
    code_files = [{
        "filename": "javafile.java",
        "content": code_content
    }]
    if pipeline.rag:
        pipeline.rag.embed_code(code_files)
    else:
        raise ValueError("RAG instance is not set.")


    # Fault localization
    write_to_file("#### Fault Localization ####\n")
    localization = pipeline.fault_localization(code_content)
    write_to_file(localization)

    # Pattern matching
    write_to_file("\n#### Pattern Matching ####\n")
    patterns = pipeline.pattern_matching(localization)
    for pattern in patterns:
        write_to_file(pattern)
        write_to_file("\n+++++++++++++++++++\n")

    # Patch generation
    write_to_file("\n#### Patch Generation ####\n")
    patch_dir = pipeline.patch_generation(code_content, patterns)
    write_to_file(f"Patch candidates written to directory: {patch_dir}")

    # Patch validation using the post_code as the reference
    write_to_file("\n#### Patch Validation ####\n")
    status, issues, corrections, explanation = pipeline.patch_validation(localization)
    write_to_file(status)
    write_to_file("\n+++++++++++++++++++\n")
    write_to_file(issues)
    write_to_file("\n+++++++++++++++++++\n")
    write_to_file(corrections)
    write_to_file("\n+++++++++++++++++++\n")
    write_to_file(explanation)
    write_to_file("\n+++++++++++++++++++\n")

if __name__ == "__main__":
    main()
