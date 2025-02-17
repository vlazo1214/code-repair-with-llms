# event handlers


def custom_css():
    return """
    .fixed-height 
    {
        height: 300px !important;
        overflow-y: auto !important;
    }

    .stage-box 
    {
        text-align: center !important;
        font-weight: bold !important;
    }

    .title 
    { 
        text-align: center; 
        font-size: 2rem; 
        font-weight: bold; 
    }

    .subtitle 
    { 
        text-align: center;
        font-size: 1.2rem;
    }

    .big-checkboxes label 
    { 
        font-size: 1.5rem;
        display: block; 
        text-align: center;
    }

    .big-button 
    { 
        font-size: 1.5rem; 
        padding: 10px 20px; 
        display: block; 
        margin: 0 auto; 
    }

    """

def display_file_content(file):
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

def process_file(file, language):
    if file is None:
        return "Skipped", "Skipped", "Skipped", "Skipped", "Please upload a file."
    
    try:
        content = display_file_content(file)
        stage1_result = "Complete"
        stage2_result = "Complete"
        stage3_result = "Complete"
        stage4_result = "Complete"
        processed_content = process_content(content, language)
        return stage1_result, stage2_result, stage3_result, stage4_result, processed_content
    except Exception as e:
        return "Error", "Error", "Error", "Error", f"An error occurred: {str(e)}"

def process_content(content, language):
    # This is where you would implement your actual processing logic
    # For now, we'll just return the file content with a message
    return f"Processing {language} code:\n\n{content}\n\nProcessing complete."
