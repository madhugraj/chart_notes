import streamlit as st
import re
import json

# Function to remove citation tags from a note
def remove_citations(note):
    return re.sub(r'\[CITATION\[.*?\]\]', '', note).strip()

# Function to highlight the selected citation in the transcript
def highlight_citation(transcript, citation):
    return transcript.replace(citation, f"**{citation}**")

# Sample notes and citations (replace with actual data)
notes = [
    "**Reason for Visit (Summary/Chief Complaint):**  Follow-up appointment for management of vitamin D deficiency, coronary artery disease, diabetes, hypertension, and obesity. [CITATION[1]: \"antonio rice is following up here.\"]",
    "**Coronary Artery Disease:**  Patient reports history of myocardial infarction and status post stenting. [CITATION[1]: \"i got coronary artery disease with a history of mi. status post stinting.\"] Patient follows with cardiology. [CITATION[1]: \"follows with cardiology.\"] Currently on aspirin 81 mg daily, atorvastatin 80 mg daily, and clopidogrel 75 mg daily. [CITATION[1]: \"you got your aspirin, plavix, tomosarcan, statin, code a.\"] Cardiology recommended discontinuing clopidogrel and adding amlodipine 2.5 mg daily to manage hypertension. [CITATION[1]: \"they said you could stop your plavix. they wanted to add two and a half of your amyloidapine to tap your pressure down a little bit more.\"]"
]

# Sample citations dictionary (replace with actual data)
citations_dict = {
    notes[0]: ["antonio rice is following up here."],
    notes[1]: [
        "i got coronary artery disease with a history of mi. status post stinting.",
        "follows with cardiology.",
        "you got your aspirin, plavix, tomosarcan, statin, code a.",
        "they said you could stop your plavix. they wanted to add two and a half of your amyloidapine to tap your pressure down a little bit more."
    ]
}

transcript = "Your full transcript goes here."

# Clean the notes by removing citations
cleaned_notes = [remove_citations(note) for note in notes]

# Side-by-side layout for Transcript and Chart Notes
col1, col2 = st.columns(2)

with col1:
    st.subheader("Transcript")
    transcript_area = st.empty()
    transcript_area.text_area("Transcript", value=transcript, height=300)

with col2:
    st.subheader("Generated Chart Notes")
    
    # Display the cleaned chart notes without citations
    st.text_area("Chart Notes", value="\n".join(cleaned_notes), height=300)
    
    # Select a note to view its citations
    selected_note = st.selectbox("Select a note to see its citation:", cleaned_notes)

    # Check if the selected note has citations
    if selected_note in citations_dict:
        citations = citations_dict[selected_note]
        st.write("Citations:")
        for citation in citations:
            st.text_area("Citation", value=citation, height=100)
            highlighted_transcript = highlight_citation(transcript, citation)
            transcript_area.text_area("Transcript", value=highlighted_transcript, height=300)

# Button to download the citations dictionary
st.subheader("Download Citations Dictionary")
if st.button("Download as JSON"):
    # Convert the dictionary to a JSON string
    json_dict = json.dumps(citations_dict, indent=4)
    
    # Provide a download link for the JSON file
    st.download_button(
        label="Download JSON file",
        data=json_dict,
        file_name="citations_dictionary.json",
        mime="application/json"
    )
