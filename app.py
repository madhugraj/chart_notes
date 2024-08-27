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
    3. Format citations as: {{References: [1]: "citation text", [2]: "citation text"}}."""

    response = model.generate_content([prompt])
    content_text = response.candidates[0].content.parts[0].text.strip()
    return content_text

def parse_chart_notes_for_citations(chart_notes):
    """Parse the chart notes to extract sentences and associated citations."""
    citation_pattern = re.compile(r'\{References: ([^}]+)\}')
    notes = []
    citations_dict = {}
    all_citations = {}
    next_citation_number = 1

    for line in chart_notes.splitlines():
        citations = citation_pattern.findall(line)
        clean_sentence = citation_pattern.sub('', line).strip()

        if clean_sentence and citations:
            notes.append(clean_sentence)
        
        if citations:
            citation_texts = citations[0].split(', ')
            for citation in citation_texts:
                match = re.search(r'\[(\d+)\]:\s*"(.*?)"', citation)
                if match:
                    citation_number, citation_text = match.groups()
                    
                    if citation_text not in all_citations:
                        all_citations[citation_text] = f"[{next_citation_number}]"
                        next_citation_number += 1
                    
                    if clean_sentence in citations_dict:
                        citations_dict[clean_sentence].append(f'{all_citations[citation_text]}: "{citation_text}"')
                    else:
                        citations_dict[clean_sentence] = [f'{all_citations[citation_text]}: "{citation_text}"']

    return notes, citations_dict

def highlight_citations(transcript, citations_dict, selected_note):
    """Highlight all citations in the transcript based on the selected note."""
    if selected_note in citations_dict:
        citation_texts = [citation.split(": ")[1].strip('"') for citation in citations_dict[selected_note]]
        for citation_text in citation_texts:
            citation_text_escaped = re.escape(citation_text)
            transcript = re.sub(citation_text_escaped, f"<mark style='background-color: yellow'>{citation_text}</mark>", transcript, flags=re.IGNORECASE)
    return transcript

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

# Initialize session state variables
if "citations_dict" not in st.session_state:
    st.session_state.citations_dict = {}
if "selected_note" not in st.session_state:
    st.session_state.selected_note = None
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "content_text" not in st.session_state:
    st.session_state.content_text = ""

# Upload file
uploaded_file = st.file_uploader("Upload a JSON or TXT file containing the transcript", type=["json", "txt"])

if uploaded_file:
    # Template input from user
    template = st.text_area("Paste your template here:")

    if uploaded_file.type == "application/json":
        transcript = extract_transcript_from_json(uploaded_file)
    elif uploaded_file.type == "text/plain":
        transcript = uploaded_file.read().decode("utf-8")

    st.session_state.transcript = transcript

    # Generate chart notes with citations
    if st.button("Generate Chart Notes"):
        content_text = generate_chart_notes_with_citations(transcript, template)
        st.session_state.content_text = content_text
        
        # Parse the chart notes to get notes without citations and the citation dictionary
        notes, citations_dict = parse_chart_notes_for_citations(content_text)
        st.session_state.citations_dict = citations_dict
        st.session_state.selected_note = notes[0] if notes else None

        # Side-by-side layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Transcript")
            if st.session_state.selected_note:
                highlighted_transcript = highlight_citations(st.session_state.transcript, st.session_state.citations_dict, st.session_state.selected_note)
                st.markdown(highlighted_transcript, unsafe_allow_html=True)

        with col2:
            st.subheader("Generated Chart Notes")
            st.text_area("Chart Notes", value=st.session_state.content_text, height=300, key="chart_notes_text_area")
            
            # Select note to view citations
            selected_note = st.selectbox("Select a note to see its citation:", list(st.session_state.citations_dict.keys()), index=0)
            st.session_state.selected_note = selected_note

            if selected_note in st.session_state.citations_dict:
                citations = st.session_state.citations_dict[selected_note]
                for citation in citations:
                    st.text_area("Citation", value=citation, height=100, key=f"citation_{citation}")

                # Highlight and display the transcript with the selected citation highlighted
                highlighted_transcript = highlight_citations(st.session_state.transcript, st.session_state.citations_dict, selected_note)
                col1.markdown(highlighted_transcript, unsafe_allow_html=True)

        # Download buttons
        st.download_button("Download Chart Notes", data=st.session_state.content_text, file_name="chart_notes.txt", mime="text/plain")
        citations_text = format_citations_dictionary(st.session_state.citations_dict)
        st.download_button("Download Citations Dictionary", data=citations_text, file_name="citations_dictionary.txt", mime="text/plain")
