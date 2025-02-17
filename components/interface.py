import gradio as gr
import os
import utils.interface_utils as iutils
from components.chat import create_chat_controls
from components.bug_finding import create_bug_finding_tab
from components.pattern_matching import create_pattern_matching_tab
from components.patch_generation import create_patch_generation_tab
from components.patch_validation import create_patch_validation_tab
from components.file_upload import create_file_upload_section

def create_interface():
    choices = {"ChatGPT", "Claude"}

    with gr.Blocks(css=iutils.custom_css()) as interface:
        with gr.Column():
            # Header with Logo
            with gr.Row():
                gr.Markdown("# Code Repair with LLMs")  
                gr.Markdown("")  # Filler to push logo to the right
                gr.Image("logo.png", label="Logo", show_download_button=False, show_fullscreen_button=False, show_label=False, height=250, width=450, container=False)

            # Tabs for Different Features
            with gr.Tab("Chat"):
                create_bug_finding_tab(choices)

            with gr.Tab("Bug Finding"):
                create_bug_finding_tab(choices)

            with gr.Tab("Pattern Matching"):
                create_pattern_matching_tab(choices)

            with gr.Tab("Patch Generation"):
                create_patch_generation_tab(choices)

            with gr.Tab("Patch Validation"):
                create_patch_validation_tab(choices)

            # Chatbot Always at the Bottom
            with gr.Column():
                chatbot = gr.Chatbot(value=None, type="messages", show_label=True, show_share_button=False)
                create_chat_controls()

    return interface
