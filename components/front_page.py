import gradio as gr
from api.initiate_pipeline_call import initiate_pipeline_call
from utils.convert_steps import convert_steps
from utils.storage import save_jwt_to_session
from components.interface import create_interface

def handle_initiate_pipeline(files, selected_steps):
    """Processes the file upload and initiates the pipeline."""
    binary_steps = convert_steps(selected_steps)

    response = initiate_pipeline_call(files, binary_steps)
    '''
        Delete print below in production
    '''
    print(response)
    save_jwt_to_session(response)  

    return gr.update(visible=False), gr.update(visible=True)

def create_full_ui():
    """Creates the full UI with a front page and the main interface."""
    with gr.Blocks(css="style.css") as app:
        # Front Page UI
        with gr.Column(visible=True) as front_page:
            gr.Markdown("# Welcome to Code Repair with LLMs")
            gr.Markdown("Upload your codebase and select the desired steps before proceeding.")

            file_input = gr.Files(
                label="Upload Codebase / Multiple Files",
                file_types=[".py", ".java", ".c", ".cpp"]
            )

            steps = ["Bug Finding", "Pattern Matching", "Patch Generation", "Patch Validation"]
            checkboxes = gr.CheckboxGroup(steps, label="Select Desired Steps", value=steps)
            initiate_button = gr.Button("Initiate Pipeline")

        # Main Interface UI (Initially Hidden)
        with gr.Column(visible=False) as main_interface:
            interface = create_interface()

        # Button click should happen inside the context
        initiate_button.click(
            fn=handle_initiate_pipeline,
            inputs=[file_input, checkboxes],
            outputs=[front_page, main_interface]
        )

    return app
