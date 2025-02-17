import gradio as gr

def create_file_upload_section():
    with gr.Row(equal_height=True):  # Ensures both sections are the same height
        with gr.Column(scale=1):
            file_input = gr.File(label="Upload Codebase/Single File", file_types=[".py", ".java", ".c", ".cpp"])
        with gr.Column(scale=3):
            file_content = gr.Code(label="File Contents", language="python", interactive=False, elem_classes=["fixed-height"])
    
    return file_input, file_content
