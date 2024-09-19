import streamlit as st
import json
import re
import google.generativeai as genai
import time

# Retrieve the API key from secrets
api_key = st.secrets["api_key"]
genai.configure(api_key=api_key)

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

# Custom CSS for background color and other styles
st.markdown(
    """
    <style>
    body {
        background-color: #013220;
    }
    .heading {
        font-size: 40px;
        color: white;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .color-bar {
        width: 100%;
        height: 5px;
        background-color: gold;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display heading with color bar
st.markdown('<div class="heading">Smart Chart Notes</div>', unsafe_allow_html=True)
st.markdown('<div class="color-bar"></div>', unsafe_allow_html=True)

# Template definitions
template_1 = """
[Your detailed template 1 structure here]
""" 

template_2 = """ Historian-
[Your detailed template 2 structure here]
"""  

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

    try:
        with st.spinner('Generating chart notes...'):
            start_time = time.time()
            response = model.generate_content([prompt])
            end_time = time.time()
            elapsed_time = end_time - start_time
            st.write(f"Time taken to generate the chart notes: {elapsed_time:.2f} seconds")

            #content = response.candidates[0].content.parts[0].text.strip()

            # Check the response structure
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                    content = candidate.content.parts[0].text.strip()
                    if isinstance(content, str):
                        return content
                    else:
                        st.warning("Response content is not a string. Content may not be properly formatted.")
                        return None
            st.warning("No response from the model. Please check the template or try again.")
            return None
    except Exception as e:
        st.error(f"An error occurred while generating chart notes: {str(e)}")
        return None

def parse_chart_notes_for_citations(response):
    """Parse the chart notes and citations using regex."""
    
    prompt = f"""In the response {response}, you'll observe structured content with subheadings, notes, and references.
    Remove the subheadings, and retain only the important notes and their references. Ensure you follow the instructions below:
    1. Avoid Notes without reference.
    2. Each note is permitted to have only 5 key references.
    3. Eliminate filler words like 'um', 'yeah', 'okay','well','thank you', 'hello' etc.
    4. Repeat this for all the subheadings.
    
    5. Structure the output as:
    [
      {{
        "note": "note text",
        "Reference": [
          "reference text 1",
          "reference text 2",
          "reference text 3",
          "reference text 4",
          "reference text 5"
        ]
      }},
      ...
    ]
    
    Response:
    {response}
    """

    try:
        # Generate the content using the model
        generated_response = model.generate_content([prompt])

        # Extract the parsed content as text
        content_text = generated_response.candidates[0].content.parts[0].text.strip()

        # Check if content_text is empty
        if not content_text:
            st.error("Generated content is empty.")
            return None, None

        # Regex pattern to match notes and references
        note_pattern = r'"note":\s*"([^"]+)"'
        reference_pattern = r'"Reference":\s*\[\s*([^]]+)\s*\]'

        # Find all notes
        notes = re.findall(note_pattern, content_text)

        # Find all references and split them into individual references
        raw_references = re.findall(reference_pattern, content_text)
        citations_dict = {}

        for note, raw_ref in zip(notes, raw_references):
            # Split references and clean up any unnecessary characters
            references = [ref.strip().strip('"') for ref in raw_ref.split(',')]
            
            # Limit to 8 references
            citations_dict[note] = references[:8]
        
        st.write("Generated citations_dict:", citations_dict)

        return notes, citations_dict

    except Exception as e:
        st.error(f"An error occurred while processing the response: {str(e)}")
        return None, None

def highlight_citations(transcript, citations_dict, selected_note):
    """Highlight all citations in the transcript based on the selected note."""
    highlighted_transcript = transcript

    # Check if the selected note has associated citations
    if selected_note in citations_dict:
        citation_texts = citations_dict[selected_note]

        for citation_text in citation_texts:
            citation_text_escaped = re.escape(citation_text.strip())
            # Ensure highlighting is done in a case-insensitive manner
            highlighted_transcript = re.sub(
                citation_text_escaped,
                f"<mark style='background-color: yellow'>{citation_text.strip()}</mark>",
                highlighted_transcript,
                flags=re.IGNORECASE
            )

    return highlighted_transcript

# Initialize session state variables
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "chart_notes_with_citations" not in st.session_state:
    st.session_state.chart_notes_with_citations = ""
if "notes" not in st.session_state:
    st.session_state.notes = []
if "citations_dict" not in st.session_state:
    st.session_state.citations_dict = {}
if "selected_note" not in st.session_state:
    st.session_state.selected_note = ""
if "selected_template" not in st.session_state:
    st.session_state.selected_template = template_1  # Default to template 1

# Template selection
template_options = {"Template 1": template_1, "Template 2": template_2}
template_choice = st.radio("Select a template:", list(template_options.keys()))
st.session_state.selected_template = template_options[template_choice]

# Display selected template
with st.expander("View Selected Template", expanded=False):
    st.text(st.session_state.selected_template)

# Upload file
uploaded_file = st.file_uploader("Upload a TXT or JSON file containing the transcript", type=["json", "txt"])

if uploaded_file:
    if uploaded_file.type == "application/json":
        transcript = extract_transcript_from_json(uploaded_file)
    elif uploaded_file.type == "text/plain":
        transcript = uploaded_file.read().decode("utf-8")

    st.session_state.transcript = transcript

    if st.button("Generate Chart Notes"):
        response = generate_chart_notes_with_citations(transcript, st.session_state.selected_template)
        if response:
            notes, citations_dict = parse_chart_notes_for_citations(response)
            
            st.session_state.chart_notes_with_citations = response
            st.session_state.notes = notes
            st.session_state.citations_dict = citations_dict

    if st.session_state.get("notes", []):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Transcript")
            transcript_area = st.empty()
            transcript_area.markdown(st.session_state.transcript, unsafe_allow_html=True)

        with col2:
            st.subheader("Generated Chart Notes")
            st.text_area("Chart Notes", value=st.session_state.chart_notes_with_citations, height=300, key="chart_notes_display")

            # Dropdown for note selection
            selected_note = st.selectbox("Select a note to see its citation:", st.session_state.notes, key="note_dropdown")
            st.session_state.selected_note = selected_note

            # Check if a note is selected and update the transcript with highlights
            if st.session_state.selected_note:
                highlighted_transcript = highlight_citations(
                    st.session_state.transcript, st.session_state.citations_dict, st.session_state.selected_note
                )
                # Re-render the transcript with highlighted citations
                transcript_area.markdown(highlighted_transcript, unsafe_allow_html=True)
