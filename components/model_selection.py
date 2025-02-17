import gradio as gr

def create_model_selection_dropdown(choices, multiselect):
    return gr.Dropdown(label="Model Selection", choices=choices, multiselect=multiselect)
