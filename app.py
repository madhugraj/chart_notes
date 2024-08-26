import streamlit as st
import json
import re
import google.generativeai as genai

# Retrieve the API key from secrets
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

def parse_chart_notes_for_citations(chart_notes):
    """Parse the chart notes to extract sentences and associated citations."""
    citation_pattern = re.compile(r'\[CITATION\[(\d+)\]: ([^\]]+)\]')
    notes = []
    citations_dict = {}
    
    # Split the chart notes by newlines and periods to get individual sentences
    for line in chart_notes.splitlines():
        clean_sentence = re.sub(r'\[CITATION\[.*?\]\]', '', line).strip()
        if clean_sentence:  # Only add non-empty sentences
            notes.append(clean_sentence)
        
        citations = citation_pattern.findall(line)
        if citations:
            citations_dict[clean_sentence] = [citation_text for _, citation_text in citations]

    return notes, citations_dict

def highlight_citation(transcript, citation_text):
    """Highlight the part of the transcript matching the citation."""
    citation_text_escaped = re.escape(citation_text)
    highlighted = re.sub(citation_text_escaped, f"**{citation_text}**", transcript, flags=re.IGNORECASE)
    return highlighted

# Streamlit app interface
st.title("Chart Notes Generator with Dynamic Citations")

# Upload file
uploaded_file = st.file_uploader("Upload a JSON or TXT file containing the transcript", type=["json", "txt"])

if uploaded_file:
    # Template input from user
    template = st.text_area("Paste your template here:")

    if uploaded_file.type == "application/json":
        # Process JSON file
        transcript = extract_transcript_from_json(uploaded_file)
        st.write("Transcript extracted from JSON:")
    elif uploaded_file.type == "text/plain":
        # Process TXT file
        transcript = uploaded_file.read().decode("utf-8")
        st.write("Transcript from TXT file:")
    
    # Generate chart notes with citations
    if st.button("Generate Chart Notes"):
        chart_notes_with_citations = generate_chart_notes_with_citations(transcript, template)
        
        # Parse the chart notes to get notes without citations and the citation dictionary
        notes, citations_dict = parse_chart_notes_for_citations(chart_notes_with_citations)

        # Side-by-side layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Transcript")
            transcript_area = st.empty()
            transcript_area.text_area("Transcript", value=transcript, height=300)

        with col2:
            st.subheader("Generated Chart Notes")
            selected_note = st.selectbox("Select a note to see its citation:", notes)
            st.text_area("Chart Notes", value="\n".join(notes), height=300)

            if selected_note in citations_dict:
                citations = citations_dict[selected_note]
                st.write("Citations:")
                for citation in citations:
                    st.text_area("Citation", value=citation, height=100)
                    highlighted_transcript = highlight_citation(transcript, citation)
                    transcript_area.text_area("Transcript", value=highlighted_transcript, height=300)

        # Download button for chart notes
        st.download_button("Download Chart Notes", data="\n".join(notes), file_name="chart_notes.txt", mime="text/plain")
