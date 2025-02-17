import gradio as gr
from components.front_page import create_full_ui

# Create the UI
app = create_full_ui()

# Launch the app
if __name__ == "__main__":
    app.launch(show_api=False)

