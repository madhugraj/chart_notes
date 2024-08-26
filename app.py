import streamlit as st
import json
import google.generativeai as genai

# Configure the API key
GOOGLE_API_KEY = "AIzaSyAe8rheF4wv2ZHJB2YboUhyyVlM2y0vmlk"
genai.configure(api_key=GOOGLE_API_KEY)

# Generation configuration
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

def extract_recognized_text(json_data):
    recognized_text_list = []
    for turn in json_data["transcripts"][0]["speakerTurns"]:
        for alternative in turn["alternatives"]:
            recognized_text = alternative["recognizedText"]
            words = alternative["words"]
            start_time = words[0]["startTime"]
            end_time = words[-1]["endTime"]
            recognized_text_list.append(f"{recognized_text} ({start_time}, {end_time})")
    return " ".join(recognized_text_list)

def generate_chart_notes_with_citations(transcript, template):
    # Prepare the prompt
    prompt = f"""Create chart notes as per the {template} for the following healthcare transcript: {transcript}.
                 Include citations for specific information extracted from the transcript, strictly referencing all the exact statements throughout the transcript."""
    
    # Generate the content
    response = model.generate_content([prompt])
    content_text = response.candidates[0].content.parts[0].text
    return content_text.strip()

# Streamlit app
st.title("Chart Note Generator with Citations")

# Upload the transcript file
uploaded_file = st.file_uploader("Upload a JSON or TXT file", type=["json", "txt"])

# Upload the template file
template_file = st.file_uploader("Upload the template file (TXT)", type="txt")

if uploaded_file and template_file:
    # Load the template
    template = template_file.read().decode("utf-8")
    
    if uploaded_file.type == "application/json":
        json_data = json.load(uploaded_file)
        transcript = extract_recognized_text(json_data)
    else:
        transcript = uploaded_file.read().decode("utf-8")
    
    # Generate chart notes with citations
    chart_notes_with_citations = generate_chart_notes_with_citations(transcript, template)
    
    # Display the result
    st.subheader("Generated Chart Notes with Citations")
    st.write(chart_notes_with_citations)

    # Option to download the result
    st.download_button(
        label="Download Chart Notes",
        data=chart_notes_with_citations,
        file_name="chart_notes_with_citations.txt"
    )
