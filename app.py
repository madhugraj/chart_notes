import streamlit as st
import json
import re
import google.generativeai as genai
import time

# st.set_page_config(layout="wide")
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
    .note-dropdown {
        color: white;
        background-color: #005f40;
        border: 1px solid #004d33;
        padding: 5px;
    }
    .dropdown-container {
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display heading with color bar
st.markdown('<div class="heading">Smart Chart Notes</div>', unsafe_allow_html=True)
st.markdown('<div class="color-bar"></div>', unsafe_allow_html=True)
# st.set_page_config(layout="wide") 
# st.session_state.theme = "dark"

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

template_2 = """ Historian-
Refers to the individual providing the patient's medical history during the clinical encounter. This could be the patient themselves or someone else, such as a family member, caregiver, or guardian, especially in cases where the patient is unable to communicate effectively 

CHIEF COMPLAINT- 
The chief complaint includes:
1.AGE , GENDER, TYPE OF VISIT,  
2.REASON FOR VISIT- FIRST TIME COMPLAINT/ PROBLEM/ SYMPTOM- ACUTE/ SICK VISIT- evaluation
VISITS FOR F/U OR PERIODIC CHECK-UP OF DIAGNOSED CONDITION/ DISEASE -FOLLOW-UP VISIT

HAP-
This section combines the patient’s history, the provider’s assessment, and the treatment plan in one place.

(HPI) HISTORY OF PRESENTING ILLNESS- 
The HPI is a detailed account of the patient's reason for the visit. It must be written in simple present tense, in paragraph form, and include the following information:
Side effects/ benefits of medication.
Ongoing medications.
Diet/ lifestyle adherence.
Reasons for non-adherence.
Previous reports discussion. 
Associated sign and symptoms
Allergies/ family history/ social history/ past medical history/ travel history.
Immunization history.
Request for refills of medication OR reducing the dosage of meds OR referrals to specialists.
Upcoming Appt with other specialty.s
It must be in SIMPLE PRESENT TENSE.
The HPI is a chronological description.
The following eight elements may be used to characterize a specific somatic complaint. They are as follows:
Location,Quality,Severity,Duration,Timing,Context,Modifying Factors,Associated Signs and Symptoms.
Example: 
Location: Where is the pain/problem? (abdomen, chest, )

Quality: Describe the pain/problem? (sharp, dull)

Severity: How severe is the pain /problem? (slight, Mild, Moderate, Severe, Rates her pain as 3 on a scale of 10, 5 on a scale of 10)

Duration: How long have you had this pain/problem? When did it start? (Two weeks, started after I returned from my trip abroad)

Timing: If the pain or problem is constant or comes and goes or Does the /problem occur at a specific time? (one hour after eating, Experiences heartburn especially at night, intermittent runny nose, constant headache)

Context: Where were you at the onset of this pain/problem? (Complaints of sudden onset of chest pain. Abdominal pain started after eating a pizza. He tripped and fell which playing soccer and sustained injury to the left leg. )

Modifying Factors: What makes the pain/problem worse or better? (improves when lying down, worse after eating, Abdominal pain was better after taking an antacid, His left leg swelling improved after applying an ice pack)

Associated Signs/Symptoms: What other associated problems are present? (nausea and vomiting, rash, leg swelling)
HPI always in paragraph form.


If a patient has visited for a old problem then the HPI element will have : Current status of the problem and other new problem(if any)
If a patient has visited for a new problem then the HPI element will have : above given 8 elements.
HPI will be noted 99% of the time from audio and 1% from EHR.
Any suspicious point in the audio from the patient will be an inquiry for the provider.
Account specifications or physician preferences that could be encountered
Do not use the words mentions, states, and reports
Start the sentence with the subject (He, she)
Write all the things the patient discusses with the physician
There are two coding levels of HPI:
Brief
Extended
Brief HPI: A brief HPI includes documentation of one to three HPI elements.
CC: Left ear pain
HPI: Complains of dull ache in left ear for 2 days. 
In this example, only three HPI elements are documented. 
Complaints of dull ache (Quality) in left ear (Location) for 2 days(Duration).
Extended HPI: Should describe at least four elements of the present HPI or the status of at least three chronic or inactive conditions.
Hypertension: Her blood pressure today is 120/80 mmHg. 
Diabetes: She is currently on Metformin. States that her glucose levels are better after losing few pounds with high protein diet. 
Hypothyroidism: She is currently on Synthroid.  Her recent TSH levels are within normal limits. 
Right thyroid cancer: Status post right thyroidectomy
Right ear hearing loss: She states that her hearing in the right ear has gotten worse.



(ROS) Review of system- 

It’s an inventory of the body systems that is obtained through a series of questions in order to identify signs and/or symptoms which the patient may be experiencing. Designed to uncover dysfunction and disease. 
ROS entries are always symptoms.  They can never be disease conditions
ROS entries are given by the patient when asked by the physician (answers to leading questions / yes or no answers)
Both positive and negative  findings are documented. This questionnaire is mostly contextual based.
There are 14 recognized systems:
1.Constitutional (fevers, chills, night sweats, weight loss, weight gain, change in appetite, fatigue, somnolence)
2.Eyes (Vision loss or blurred vision, double vision/diplopia, eye pain, red eye)
3.Ears/Nose/Mouth/Throat (Ear pain, ear discharge, hearing loss, tinnitus, epistaxis, rhinorrhea or post nasal discharge, sinus pressure, sore throat, oral sores/lesions, tooth pain, bleeding gums, hoarseness, neck pain)
4.Cardiovascular (Chest pain, palpitations, leg swelling/edema, leg pain with walking/claudication)
5.Respiratory (Cough, hemoptysis, wheezing, snoring, shortness of breath [dyspnea, orthopnea, PND])
6.Gastrointestinal (Nausea or vomiting, diarrhea, constipation, abdominal pain, hematochezia, melana, stool incontinence [encopresis])
7.Genitourinary (Pelvic pain, dysuria, urinary frequency, urinary urgency, hematuria, incomplete bladder emptying, incontinence, STD) (Men – Testicular pain, Swelling in scrotum, ED)(Women – LMP, menorrhagia, metorrhagia, postmenopausal bleeding, dysmenorrhea, vaginal discharge)
8.Musculoskeletal (Bone pain, joint pain, joint swelling, muscle pain)
9.Integumentary (skin and/or breast) (Skin lesions, pruritus, breast lumps, mastalgia, galactorrhea, alopecia)
10.Neurological (Headache, muscle weakness, paresthesia, memory loss, seizure, dizziness in the forms of lightheadedness, room spinning(vertigo), fainting(syncope), imbalance (ataxaia)
11.Psychiatric (Anxiety, depression, irritability, insomnia, suicidal)
12.Endocrine (Heat or cold intolerance, excessive thirst/polydipsia, excessive hunger/polyphagia)
13.Hematologic/Lymphatic (Lymph node enlargement, easy bruising or bleeding)
14.Allergic/Immunologic (Hives, seasonal allergies, environmental allergies, exposure to HIV)

better assessment/ diagnosis. Rule out other probable disorder.
Leading Questions asked by the physician to the patient.
Qualifying factors
The question should be asked by the physician and the ans should be given by the patient.
It should be either a sign or symptom and not a disorder, diet, habit, lifestyle etc.
It should be about the present situation and not belong to the past.
If No leading question by the physician. – Replicate one symptom from the HPI in ROS section.
If No leading question is asked and no symptoms are discussed in the HPI-
Leave the ROS blank.


(PE) Physical examination - 
PE entries are always findings called out by the physician.
PE entries are always documented using medical terms.
Examinations performed by the physician on the patient during that day of visit. Examining the body systems.
It is either a measurement or an observation.
Vitals measured by the physician are documented in PE summary
In case the vitals are related to the chief complaint (eg: BP reading for a hypertensive patient), they are documented in PE summary and in HPI.


Plan - 

Treatment plan called out by the primary care provider  (PCP)/  physician - for the present day’s visit.

Referral to specialty. Referred to MGH orthopedic surgeon for further evaluation and management.
Continue the existing meds/ Discontinue/ Increase or decrease the dosages.
Prescribed new medication. Eg Prescribed Lisinopril 40 mg one tablet every day in the morning after breakfast. Side effects of lightheadedness and dizziness explained.
Taboo- twice/ thrice 
Prescribed / OTC (over the counter)


Continued OTC Isabgol one tablespoon every day at night.
Continued OTC Tylenol 1-2 tablets.

Follow up 
Advised to follow up after five days or sooner if required.

Current status- Follow up case- 
Currently, the condition is controlled or managed with the current medications.
Currently, the condition is poorly controlled / minimally controlled.
No improvement.

Plan is documented using medical terms.
Avoid “advised” for medications and tests.  Use “recommended” instead
Use “prescribed” for prescribed medications
Use “ordered” for lab tests and medications
Use “educated on” for any patient education
Below are 2 different Visits and the plan for them, SEQUENCE HAS TO BE FOLLOWED.

It must be in Past tense.


Patient education-

Food and lifestyle suggestion 
Explained the pathophysiology of the condition.
Explained/ Educated on the complications of the condition.
Orders and advise.
“Reviewed & discussed the [reports] in detail”
Lab orders / investigation
Refill / “Continued current medication” / Prescription/ Change in dosage
Patient education
Referral
Follow up

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
            st.write("Generating Citations...")

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
    2. Each note is permitted to have a maximum of 5 key (critical) references.
    3. Strictly Eliminate stop words and conjunctions
    4. Do not refer any filler words like 'so','um', 'yeah', 'okay','well','thank you', 'hello','just','you know'etc.
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
      }}]
    Response:
    {response}
    """

    try:
        with st.spinner('Parsing chart notes for citations...'):
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
                references = [ref.strip().strip('"') for ref in raw_ref.split(',')]
                
                # Limit to 5 references
                citations_dict[note] = references[:5]
            
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
            # Ensure highlighting is done in a case-insensitive manner, but only for the first occurrence
            highlighted_transcript = re.sub(
                citation_text_escaped,
                f"<mark style='background-color: yellow'>{citation_text.strip()}</mark>",
                highlighted_transcript,
                count=1,  # Only replace the first occurrence
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
uploaded_file = st.file_uploader("Upload a file containing the transcript", type=["json", "txt"])

if uploaded_file:
    if uploaded_file.type == "application/json":
        transcript = extract_transcript_from_json(uploaded_file)
    elif uploaded_file.type == "text/plain":
        transcript = uploaded_file.read().decode("utf-8")

    st.session_state.transcript = transcript

    if st.button("Generate Chart Notes"):
        response = generate_chart_notes_with_citations(transcript, st.session_state.selected_template)
        if response:
            with st.spinner('Parsing chart notes for citations...'):
                notes, citations_dict = parse_chart_notes_for_citations(response)
                
                st.session_state.chart_notes_with_citations = response
                st.session_state.notes = notes
                st.session_state.citations_dict = citations_dict

                # Add download buttons
                st.download_button(
                    label="Download Chart Notes with References",
                    data=st.session_state.chart_notes_with_citations,
                    file_name="chart_notes_with_references.txt",
                    mime="text/plain"
                )

                chart_notes_without_references = re.sub(r'{References:\s*\[\d+\]:\s*".*?"}', '', st.session_state.chart_notes_with_citations)
                st.download_button(
                    label="Download Chart Notes without References",
                    data=chart_notes_without_references,
                    file_name="chart_notes_without_references.txt",
                    mime="text/plain"
                )

# Set up a default value for `selected_note` before the selectbox is created
if st.session_state.notes and "selected_note" not in st.session_state:
    st.session_state.selected_note = st.session_state.notes[0]

# Move the "Select a note" dropdown to the top
if st.session_state.notes:
    selected_note = st.selectbox(
        "Select a note to see its citation:",
        options=st.session_state.notes,
        format_func=lambda note: note[:50] + '...' if len(note) > 50 else note,
        key="selected_note",
        help="Select a note from the generated chart notes to see the corresponding highlighted citations."
    )

    # Highlight the selected note's citations in the transcript
    highlighted_transcript = highlight_citations(st.session_state.transcript, st.session_state.citations_dict, selected_note)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Transcript")
        st.markdown(f"<div>{highlighted_transcript}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<h2 style="color: green;">Generated Chart Notes</h2>', unsafe_allow_html=True)
        st.markdown(f"<div style='color: green;'>{st.session_state.chart_notes_with_citations}</div>", unsafe_allow_html=True)
