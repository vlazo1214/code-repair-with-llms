import gradio
import os
import sys

sys.path.insert(0, os.path.abspath("./"))

from source.api_calls.initiate_pipeline_call import initiate_pipeline_call
from utils.process_steps import process_steps

pipeline_steps = 21

class FrontPage:
    def __init__(self):
        with gradio.Blocks(css=self.custom_css()) as self.page:
            gradio.Markdown("# Code Repair with LLMs")
            gradio.Markdown("Upload a Python, Java, C, or C++ file for processing")
            
            with gradio.Row():
                file_input = gradio.File(label="Upload  Code File", file_types=[".py", ".java", ".c", ".cpp"])
                language_input = gradio.Dropdown(choices=["Python", "Java", "C", "C++"], label="Language")
            
            file_content = gradio.Code(label="File Contents", language="python", interactive=False, elem_classes=["fixed-height"])
            process_button = gradio.Button("Process")

            with gradio.Row():
                stage1 = gradio.Textbox(label="Fault Localization", value="Pending", interactive=False, elem_classes=["stage-box"])
                stage2 = gradio.Textbox(label="Pattern Matching", value="Pending", interactive=False, elem_classes=["stage-box"])
                stage3 = gradio.Textbox(label="Patch Generation", value="Pending", interactive=False, elem_classes=["stage-box"])
                stage4 = gradio.Textbox(label="Patch Validation", value="Pending", interactive=False, elem_classes=["stage-box"])

            output = gradio.Code(label="Processed Output", language="python", elem_classes=["fixed-height"])

            pipeline_steps_input = gradio.Number(value=pipeline_steps, label="Pipeline Steps")

            file_input.change(fn=self.display_file_content, inputs=[file_input], outputs=[file_content])
            process_button.click(fn=self.initiate_pipeline, 
                                 inputs=[file_input, language_input, pipeline_steps_input], outputs=[])

    def custom_css(self):
        return """
        .fixed-height {
            height: 300px !important;
            overflow-y: auto !important;
        }
        .stage-box {
            text-align: center !important;
            font-weight: bold !important;
        }
        """

    def display_file_content(self, file):
        if file is None:
            return "No file uploaded yet."
        try:
            if isinstance(file, str):
                with open(file, 'r') as f:
                    return f.read()
            elif hasattr(file, 'name'):
                return file.name
            elif hasattr(file, 'read'):
                return file.read().decode('utf-8')
            else:
                return str(file)
        except Exception as e:
            return f"An error occurred while reading the file: {str(e)}"


    def initiate_pipeline(self, file_input, language_input, pipeline_steps):
        if file_input is None or (isinstance(file_input, list) and len(file_input) == 0):
            return "No file uploaded."

        self.process_file(file_input, language_input)
        
        # If file_input is a list, take the first file
        if isinstance(file_input, list):
            file_input = file_input[0]
            
        print(f"Processing file: {file_input}")
        return initiate_pipeline_call(file_input, pipeline_steps)
    
    def process_file(self, file, language):
        if file is None:
            return "Skipped", "Skipped", "Skipped", "Skipped", "Please upload a file."
        
        try:
            content = self.display_file_content(file)
            stage1_result = "Complete"
            stage2_result = "Complete"
            stage3_result = "Complete"
            stage4_result = "Complete"
            processed_content = self.process_content(content, language)
            return stage1_result, stage2_result, stage3_result, stage4_result, processed_content
        except Exception as e:
            return "Error", "Error", "Error", "Error", f"An error occurred: {str(e)}"

    def process_content(self, content, language):
        # This is where you would implement your actual processing logic
        # For now, we'll just return the file content with a message
        return f"Processing {language} code:\n\n{content}\n\nProcessing complete."
