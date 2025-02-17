import gradio as gr

def create_chat_controls():
    with gr.Row():
        with gr.Column(scale=10):
            msg = gr.Textbox(label="Prompt", placeholder="Enter prompt")

    with gr.Row():
        with gr.Column(min_width=0, scale=10):
            submit_button = gr.Button("Submit Prompt")

    return msg, submit_button

