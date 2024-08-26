import streamlit as st
import json
import os
import google.generativeai as genai


# Retrieve the API key and password from secrets
api_key = st.secrets["api_key"]

# Configure the API key
genai.configure(api_key=api_key)

# Set up the model configuration
generation_config = {
    "temperature": 0,
    "top_p": 1.0,
    "top_k": 34,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def extract_transcript_from_json(json_file):
    """Extract recognizedText from the JSON file."""
    transcript_text = ""
    data = json.load(json_file)
    
    for transcript in data['transcripts']:
        for turn in transcript['speakerTurns']:
            for alt in turn['alternatives']:
                transcript_text += alt['recognizedText'] + " "
    
    return transcript_text.strip()

def generate_chart_notes_with_citations(transcript, template):
    """Generate chart notes with citations using the model."""
    prompt = f"""Create chart notes as per the {template} for the {transcript}. And from the following health care transcript: {transcript}
                Include citations for specific information extracted from the transcript, strictly referencing all the exact statements throughout the transcript. For example, here's how to include citations:
                1. Patient reports experiencing dizziness for the past week. [CITATION[1]: The patient states that she has been experiencing dizziness for the past week., CITATION[2]: She was under sleeping pills]
                2. Patient denies any history of smoking. [CITATION[1]: The patient denies smoking, CITATION[2]: He was in rehab..] """
    
    response = model.generate_content([prompt])
    content_text = response.candidates[0].content.parts[0].text.strip()
    return content_text

# Streamlit app interface
st.title("Chart Notes Generator with Citations")

# Upload file
uploaded_file = st.file_uploader("Upload a JSON or TXT file containing the transcript", type=["json", "txt"])

if uploaded_file:
    # Read the template file
    with open('/content/drive/MyDrive/ACN/CNTemplate.txt', 'r') as f2:
        template = f2.read()

    if uploaded_file.type == "application/json":
        # Process JSON file
        transcript = extract_transcript_from_json(uploaded_file)
        st.write("Transcript extracted from JSON:")
        st.text(transcript)
    elif uploaded_file.type == "text/plain":
        # Process TXT file
        transcript = uploaded_file.read().decode("utf-8")
        st.write("Transcript from TXT file:")
        st.text(transcript)
    
    # Generate chart notes with citations
    chart_notes_with_citations = generate_chart_notes_with_citations(transcript, template)
    st.subheader("Generated Chart Notes with Citations")
    st.text_area("Chart Notes", value=chart_notes_with_citations, height=300)
