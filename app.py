import streamlit as st
import json
import re
import google.generativeai as genai

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
**Chief Complaint**

**Reason for Visit (Summary/Chief Complaint):**  
A brief summary of the reason for the visit, including relevant past medical and surgical history, social history, family history, and any associated notes or documents.

**History, Assessment, and Plans By Problem:**  
Details of the problem description and associated information.

**Preventative Care Summary:**  
Preventative care items were reviewed, including their status, the due dates, and the completion dates. The health maintenance was reviewed and updated.

**Labs & Screening:**  
Details of the reviewed and ordered labs and screenings.

**Social Screening:**  
Updates on the patient’s social history and any relevant information.

**Encounter for [Specific Encounter]:**  
Description of the encounter, including any ordered tests or referrals.

**[Specific Problem/Condition]:**  
Details of the problem or condition, including associated information, prescribed treatments, or recommendations.

**Review of System:**  
For the respiratory system, gastrointestinal system, neurological system, and additional systems as needed, details were noted.

**Physical Examination:**  
Vital signs recorded include the date, time, blood pressure, pulse, respiration, temperature, temperature source, SpO2, weight, and height. The examination included the following:

- **Constitutional:** Relevant details.
- **ENT:** Relevant details.
- **Neck:** Relevant details.
- **Respiratory:** Relevant details.
- **Cardiovascular:** Relevant details.
- **Abdomen:** Relevant details.
- **Psychiatric:** Relevant details.
- **Skin:** Relevant details.
- **Neurologic:** Relevant details.

**Current Outpatient Medications:**  
The patient is currently taking medications with specific instructions provided for each. There are no facility-administered medications for this visit. No follow-up appointments are on file.

**Patient Education:**  
The patient expressed understanding of the care plan, with details about the understanding and any provided documentation.

**Signature and Notes:**  
The physician personally evaluated the patient and reviewed the history, physical examination, assessment, and plan as documented by the scribe, [Scribe Name]. Significant findings and changes have been incorporated into the note as needed. Permission to use a virtual scribe was obtained during the encounter by clinical staff.

**Scribe Acknowledgment:**  
The scribe, [Scribe Name], documented for [Physician Name] during the encounter with the patient, [Patient Name], on [Date] at [Time].
"""
template_2 = """
**Chief Complaint**

**Reason for Visit (Summary/Chief Complaint):**  
A brief summary of the reason for the visit, including relevant past medical and surgical history, social history, family history, and any associated notes or documents.

**History, Assessment, and Plans By Problem:**  
Details of the problem description and associated information.

**Preventative Care Summary:**  
Preventative care items were reviewed, including their status, the due dates, and the completion dates. The health maintenance was reviewed and updated.

**Labs & Screening:**  
Details of the reviewed and ordered labs and screenings.

**Social Screening:**  
Updates on the patient’s social history and any relevant information.

**Encounter for [Specific Encounter]:**  
Description of the encounter, including any ordered tests or referrals.

**[Specific Problem/Condition]:**  
Details of the problem or condition, including associated information, prescribed treatments, or recommendations.

**Review of System:**  
For the respiratory system, gastrointestinal system, neurological system, and additional systems as needed, details were noted.

**Physical Examination:**  
Vital signs recorded include the date, time, blood pressure, pulse, respiration, temperature, temperature source, SpO2, weight, and height. The examination included the following:

- **Constitutional:** Relevant details.
- **ENT:** Relevant details.
- **Neck:** Relevant details.
- **Respiratory:** Relevant details.
- **Cardiovascular:** Relevant details.
- **Abdomen:** Relevant details.
- **Psychiatric:** Relevant details.
- **Skin:** Relevant details.
- **Neurologic:** Relevant details.

**Current Outpatient Medications:**  
The patient is currently taking medications with specific instructions provided for each. There are no facility-administered medications for this visit. No follow-up appointments are on file.

**Patient Education:**  
The patient expressed understanding of the care plan, with details about the understanding and any provided documentation.

**Signature and Notes:**  
The physician personally evaluated the patient and reviewed the history, physical examination, assessment, and plan as documented by the scribe, [Scribe Name]. Significant findings and changes have been incorporated into the note as needed. Permission to use a virtual scribe was obtained during the encounter by clinical staff.

**Scribe Acknowledgment:**  
The scribe, [Scribe Name], documented for [Physician Name] during the encounter with the patient, [Patient Name], on [Date] at [Time].
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
    prompt = f"""Create chart notes as per the template: {template} based on this transcript:
    {transcript}
    The chart notes must include citations for specific information extracted from the transcript. 
    Ensure the citations follow these rules:
    1. Number the references sequentially in the order they first appear.
    2. Use a unique citation number for each unique statement. If the same statement is cited again, use the existing citation number.
    3. Avoid filler words like 'yes', 'okay', 'yeah'. 
    4. Format citations as: {{References: [1]: "citation text", [2]: "citation text"}}.
    """

    try:
        response = model.generate_content([prompt])
        if not response or not response.candidates:
            st.warning("No response from the model. Please check the template or try again.")
            return None
        st.write(response)
        return response
    except Exception as e:
        st.error(f"An error occurred while generating chart notes: {str(e)}")
        return None

def parse_chart_notes_for_citations(response):
    """Parse the raw response to extract sentences and associated citations."""
    #st.write(response)
    citation_pattern = re.compile(r'\{References: ([^}]+)\}')
    notes = []
    citations_dict = {}

    # Check if response has the right structure - adjust to your actual API response format
    try:
        # Assuming the response is a ProtoBuf or dict-like object with candidates
        content_text = response.candidates[0].output  # Adjust 'output' based on actual field in API response

        # Split the content into lines and parse each line
        lines = content_text.splitlines()

        for line in lines:
            # Extract the citation part
            citations = citation_pattern.findall(line)
            # Clean the line by removing citation text
            clean_sentence = citation_pattern.sub('', line).strip()

            if clean_sentence:
                # Add sentence without citations
                notes.append(clean_sentence)

            if citations:
                # Extract and organize the citation text
                citation_texts = citations[0].split(', ')
                citations_dict[clean_sentence] = citation_texts

    except AttributeError as e:
        st.error(f"An error occurred while parsing the response: {str(e)}")
        return notes, citations_dict

    return notes, citations_dict

def highlight_citations(transcript, citations_dict, selected_note):
    """Highlight all citations in the transcript based on the selected note."""
    highlighted_transcript = transcript
    
    # Check if the selected note has associated citations
    if selected_note in citations_dict:
        citation_texts = [citation.split(": ")[1].strip('"') for citation in citations_dict[selected_note]]
        
        for citation_text in citation_texts:
            citation_text_escaped = re.escape(citation_text)
            # Ensure highlighting is done in a case-insensitive manner
            highlighted_transcript = re.sub(
                citation_text_escaped,
                f"<mark style='background-color: yellow'>{citation_text}</mark>",
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
            
            st.session_state.chart_notes_with_citations = response.candidates[0].content.strip()
            st.session_state.notes = notes
            st.session_state.citations_dict = citations_dict

    notes = st.session_state.get("notes", [])
    
    if notes:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Transcript")
            transcript_area = st.empty()
            transcript_area.markdown(st.session_state.transcript, unsafe_allow_html=True)

        with col2:
            st.subheader("Generated Chart Notes")
            st.text_area("Chart Notes", value=st.session_state.chart_notes_with_citations, height=300, key="chart_notes_display")
            
            selected_note = st.selectbox("Select a note to see its citation:", notes, key="note_dropdown")
            st.session_state.selected_note = selected_note

            if selected_note and selected_note in st.session_state.citations_dict:
                citations = st.session_state.citations_dict[selected_note]
                for i, citation in enumerate(citations):
                    st.text_area(f"Citation {i+1}", value=citation, height=100, key=f"citation_{i}")
                
                highlighted_transcript = highlight_citations(st.session_state.transcript, st.session_state.citations_dict, selected_note)
                transcript_area.markdown(highlighted_transcript, unsafe_allow_html=True)
            
            # Download buttons
            chart_notes_file = f"Chart_Notes.txt"
            citations_file = f"Citations.txt"
            
            st.download_button(
                label="Download Chart Notes",
                data=st.session_state.chart_notes_with_citations,
                file_name=chart_notes_file,
                mime="text/plain"
            )
            
            citations_text = "\n".join([f"{note}: {', '.join(citations)}" for note, citations in st.session_state.citations_dict.items()])
            st.download_button(
                label="Download Citations",
                data=citations_text,
                file_name=citations_file,
                mime="text/plain"
            )
