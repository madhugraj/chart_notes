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
    prompt = f"""Create chart notes as per the {template} for the {transcript}. Include citations for specific information extracted from the transcript, strictly referencing all the exact statements throughout the transcript. The citations must follow these rules:
    1. Number the references sequentially in the order they first appear in the text.
    2. Use a unique citation number for each unique statement. If the same statement is cited again, use the existing citation number.
    3. Format citations as: {{References: [1]: "citation text", [2]: "citation text"}}.

    For example:
    1. Patient reports experiencing dizziness for the past week.
    {{References: [1]: "The patient states that she has been experiencing dizziness for the past week.", [2]: "She was under sleeping pills."}}
    2. Patient denies any history of smoking.
    {{References: [3]: "The patient denies smoking.", [4]: "He was in rehab."}}"""

    response = model.generate_content([prompt])
    content_text = response.candidates[0].content.parts[0].text.strip()
    return content_text

def parse_chart_notes_for_citations(chart_notes):
    """Parse the chart notes to extract sentences and associated citations, ensuring correct sequential numbering."""
    citation_pattern = re.compile(r'\{References: ([^}]+)\}')
    notes = []
    citations_dict = {}
    all_citations = {}
    next_citation_number = 1

    for line in chart_notes.splitlines():
        citations = citation_pattern.findall(line)
        clean_sentence = citation_pattern.sub('', line).strip()

        if clean_sentence:
            notes.append(clean_sentence)
        
        if citations:
            # Extract individual citations
            citation_texts = citations[0].split(', ')
            for citation in citation_texts:
                match = re.search(r'\[(\d+)\]:\s*"(.*?)"', citation)
                if match:
                    citation_number, citation_text = match.groups()
                    
                    # Check if this citation text has already been assigned a number
                    if citation_text not in all_citations:
                        all_citations[citation_text] = f"[{next_citation_number}]"
                        next_citation_number += 1
                    
                    # Add the citation to the dictionary, associated with the clean sentence
                    if clean_sentence in citations_dict:
                        citations_dict[clean_sentence].append(f'{all_citations[citation_text]}: "{citation_text}"')
                    else:
                        citations_dict[clean_sentence] = [f'{all_citations[citation_text]}: "{citation_text}"']

    # Debugging output to verify the cleaned notes and citations
    st.write("Cleaned Notes:", notes)
    st.write("Citations Dictionary:", citations_dict)
    
    return notes, citations_dict

def highlight_citation(transcript, citation_text):
    """Highlight the part of the transcript matching the citation."""
    citation_text_escaped = re.escape(citation_text)
    highlighted = re.sub(citation_text_escaped, f"<mark style='background-color: yellow'>{citation_text}</mark>", transcript, flags=re.IGNORECASE)
    return highlighted

def format_citations_dictionary(citations_dict):
    """Format citations dictionary as a string for download."""
    formatted_citations = []
    for note, citations in citations_dict.items():
        formatted_citations.append(f"Note: {note}")
        for citation in citations:
            formatted_citations.append(f"  {citation}")
        formatted_citations.append("")  # Add a blank line between notes
    return "\n".join(formatted_citations)

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
            transcript_area.markdown("Transcript", unsafe_allow_html=True)

        with col2:
            st.subheader("Generated Chart Notes")
            st.text_area("Chart Notes", value="\n".join(notes), height=300)
            
            # Select note to view citations
            selected_note = st.selectbox("Select a note to see its citation:", notes)

            if selected_note in citations_dict:
                citations = citations_dict[selected_note]
                st.write("Citations:")
                for citation in citations:
                    st.text_area("Citation", value=citation, height=100)
                    highlighted_transcript = highlight_citation(transcript, citation.split(": ")[1].strip('"'))
                    transcript_area.markdown(highlighted_transcript, unsafe_allow_html=True)

        # Download button for chart notes
        st.download_button("Download Chart Notes", data="\n".join(notes), file_name="chart_notes.txt", mime="text/plain")

        # Download button for citations dictionary
        citations_text = format_citations_dictionary(citations_dict)
        st.download_button("Download Citations Dictionary", data=citations_text, file_name="citations_dictionary.txt", mime="text/plain")
