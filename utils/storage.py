import gradio as gr

def save_jwt_to_session(response):
    """Extracts session_token and session_id from API response and saves them in Gradio State."""
    session_token = response.get("session_token")
    session_id = response.get("session_id")

    if session_token and session_id:
        return gr.update(value=session_token), gr.update(value=session_id)
    
    return gr.update(), gr.update()
