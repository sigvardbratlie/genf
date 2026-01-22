import streamlit as st
from google.cloud import bigquery
from datetime import datetime
from google.oauth2 import service_account
import uuid
from google.api_core import retry
import time
import os
def init_gcp_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    client = bigquery.Client(credentials=credentials)
    return client

def save_to_bigquery():
    """Callback function that runs when form is submitted"""
    
    responses = {
        'timestamp': datetime.now().isoformat(),
        'age': st.session_state.age,
        'gender': st.session_state.gender,
        'buk_groups': st.session_state.buk_groups,
        'dugnad_groups': st.session_state.dugnad_groups,
        'hours_buk': st.session_state.hours_buk,
        'hours_dugnad': st.session_state.hours_dugnad,
        'mentor_age_group': st.session_state.mentor_age_group,
        'motivation': st.session_state.motivation,
        'capacity': st.session_state.capacity,
        'activity_current': st.session_state.activity_current,
        'activity_desired': st.session_state.activity_desired,
        'events_frequency': st.session_state.events_freq,
        'improvement_text': st.session_state.improvement_text,
        'challenge_combine': st.session_state.challenge_combine,
        'challenge_both': st.session_state.challenge_both,
        'participation': st.session_state.participation,
        'meaningfulness': st.session_state.meaningfulness,
        'responsibility': st.session_state.responsibility,
        'work_pref': st.session_state.work_pref,
        'campaign': st.session_state.campaign,
        'youth_connection_13_16': st.session_state.youth_13_16,
        'youth_connection_16_18': st.session_state.youth_16_18,
        'youth_connection_18_23': st.session_state.youth_18_23,
        'youth_connection_23plus': st.session_state.youth_23plus,
        'friends_activity': st.session_state.friends_activity,
        'friends_more_active': st.session_state.friends_more_active,
        'uuid': st.session_state.uuid
    }
    
    table_id = "admin.mentor_survey"
    @retry.Retry(initial=1.0, maximum=10.0, multiplier=2.0, deadline=30.0)
    def insert_with_retry():
        client = init_gcp_client()
        return client.load_table_from_json([responses], table_id).result()
    try:
        insert_with_retry()
        st.success("Undersøkelsen er sendt inn! Takk for din deltakelse.")
    except Exception as e:
        st.error(f"Kunne ikke sende inn: {e}")

st.set_page_config(
    page_title="BUK Mentor Undersøkelse",
    page_icon="buk_img.png",
    layout="centered"
)

# Title with image
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/buk_img.jpg", width=80)
with col2:
    st.title("BUK Mentor Undersøkelse")
st.markdown("Vennligst svar på alle spørsmål så ærlig som mulig.")
st.markdown("**Undersøkelsen er anonym**")


st.session_state.uuid = str(uuid.uuid4())

with st.form("mentor_survey"):
    
    # Demographics
    st.subheader("Bakgrunnsinformasjon")
    st.slider("Hvor gammel er du?", min_value=13, max_value=36, value=23, key='age')
    st.radio("Kjønn", options=['Mann', 'Kvinne', 'Annet/Ønsker ikke å oppgi'], key='gender')
    
    # Groups and time
    st.multiselect(
        "Hvilke BUK-grupper er du med på?",
        options=['Tigers', 'Volleyball', 'Skatedogs', 'TGI', 'BSK', 'Klatring', 'U3', 'Ingen'],
        key='buk_groups'
    )
    
    st.multiselect(
        "Hvilken dugnadsgruppe er du med på?",
        options=['GEN-F', 'BD-Service', 'Ingen'],
        key='dugnad_groups'
    )
    
    st.slider(
        "Hvor mange timer i uken går med til BUK-gruppen din, både direkte eller indirekte?",
        min_value=0.0, max_value=40.0, value=2.0, step=0.5,
        key='hours_buk'
    )
    
    st.slider(
        "Hvor mange timer i uken går med til dugnad, både jobbing eller organisatorisk?",
        min_value=0.0, max_value=40.0, value=1.0, step=0.5,
        key='hours_dugnad'
    )
    
    # Mentor info
    st.subheader("Mentorarbeid")
    st.multiselect(
        "Hvilken aldersgruppe er du hovedsakelig mentor for?",
        options=['13-16', '16-18', '18-23', '23+'],
        key='mentor_age_group'
    )
    
    st.multiselect(
        "Hva er din motivasjon for å være mentor?",
        options=['Tjene penger', 'Dra på camper', 'Møte venner', 'Gjøre noe godt for andre'],
        key='motivation'
    )
    
    # Capacity and activity (MERGED - removed redundant questions)
    st.subheader("Kapasitet og aktivitet")
    st.radio(
        "Hvordan vurderer du din kapasitet?",
        options=[
            'Jeg har mye kapasitet',
            'Jeg har middels kapasitet',
            'Jeg har akkurat nok',
            'Jeg har lite ledig tid',
            'Jeg har ingen ledig tid'
        ],
        key='capacity'
    )
    
    st.radio(
        "Hvordan anser du ditt aktivitetsnivå i mentorarbeidet?",
        options=['Veldig aktiv', 'Middels aktiv', 'Lite aktiv', 'Ikke aktiv'],
        key='activity_current'
    )
    
    st.radio(
        "Hvordan ønsker du at ditt aktivitetsnivå skal være?",
        options=[
            'Jeg ønsker å bli mye mer aktiv',
            'Jeg kan godt bli litt mer aktiv',
            'Jeg er fornøyd',
            'Jeg kan godt bli litt mindre aktiv'
        ],
        key='activity_desired'
    )
    
    st.radio(
        "Hva synes du om mengden aktiviteter?",
        options=[
            'Det skjer for mye',
            'Det skjer mye men er ok',
            'Akkurat passe',
            'Det skjer litt lite',
            'Det skjer ingenting'
        ],
        key='events_freq'
    )
    
    # Challenges (MERGED - combined similar questions)
    st.subheader("Utfordringer")
    st.radio(
        "Jeg synes det er utfordrende å kombinere mentorarbeid med andre forpliktelser",
        options=['Sant', 'Usant'],
        key='challenge_combine'
    )

    st.radio(
        "Jeg føler jeg må velge mellom enten dugnad eller BUK-gruppe, og klarer ikke begge deler",
        options=['Sant', 'Usant'],
        key='challenge_both'
    )

    st.radio(
        "Hvordan opplever du deltakelse?",
        options=[
            'Jeg ønsker å være med, men føler ikke jeg trenges',
            'Jeg ønsker å være med, men vet ikke hvor eller hvordan',
            'Jeg ønsker ikke å være med',
            'Jeg er med på alt jeg kan',
            'Annet'
        ],
        key='participation'
    )
    
    # Feelings and value (MERGED - removed overlapping questions about meaning/contribution)
    st.subheader("Meningsfullhet")
    st.radio(
        "Hvordan opplever du mentorarbeidet for deg personlig?",
        options=[
            'Meningsfylt og givende - jeg trenger det',
            'Jeg forstår det er viktig, men det har ingen stor betydning for meg',
            'Ikke meningsfylt men jeg trenger det',
            'Jeg føler ikke det gjør noe fra eller til',
            "Jeg har negative følelser rundt det"
        ],
        key='meaningfulness'
    )
    
    # Responsibility and work preferences (MERGED)
    st.subheader("Ansvar og arbeidsform")
    st.radio(
        "Hvordan forholder du deg til ansvar?",
        options=[
            'Jeg synes det går fint å ta ansvar',
            'Jeg syntes det er helt ok, men liker det ikke',
            'Jeg synes det er skummelt å ta ansvar',
            'Jeg synes det er ubehagelig at noe belager seg på meg',
            'Jeg avskyr ansvar'
        ],
        key='responsibility'
    )
    
    st.multiselect(
        "Hvilke arbeidsformer passer deg? (kan velge flere)",
        options=[
            'Jeg kan ta ansvar selv',
            'Jeg trenger å bli fortalt hva jeg skal gjøre',
            'Jeg kan være aktiv fra sidelinjen',
            'Jeg kan være med hvis det ikke stilles krav',
            'Jeg kan ikke forplikte meg',
            'Jeg vil ikke være med'
        ],
        key='work_pref'
    )
    
    # Improvements
    st.subheader("Forbedringer")
    st.text_area(
        "Hvis du kunne endret én ting i mentorarbeidet i Oslo, hva ville det vært?",
        key='improvement_text',
        placeholder="Skriv dine forslag her..."
    )
    
    st.radio(
        "Hva tenker du om aksjonen?",
        options=[
            'Veldig engasjerende og givende',
            'Jeg har lyst til å være med, men sliter med å forstå',
            'Jeg har falt av og bryr meg ikke',
            'Lei av aksjoner'
        ],
        key='campaign'
    )
    
    # Connection with youth
    st.subheader("Forbindelse med ungdommen")
    st.slider("Hvor godt kjenner du ungdommen 13-16 år?", 
              min_value=1, max_value=10, value=5, key='youth_13_16')
    st.slider("Hvor godt kjenner du ungdommen 16-18 år?", 
              min_value=1, max_value=10, value=5, key='youth_16_18')
    st.slider("Hvor godt kjenner du ungdommen 18-23 år?", 
              min_value=1, max_value=10, value=5, key='youth_18_23')
    st.slider("Hvor godt kjenner du ungdommen 23+ år?", 
              min_value=1, max_value=10, value=5, key='youth_23plus')
    
    # Friends
    st.radio(
        "Hvordan anser du dine venner med tanke på aktivitet i mentorarbeidet?",
        options=['Aktive', 'Middels aktive', 'Lite aktive', 'Ikke aktive'],
        key='friends_activity'
    )
    
    st.radio(
        "Kunne du ønsket at dine venner var mer aktive?",
        options=['Ja', 'Nei'],
        key='friends_more_active'
    )
    
    try:
        submitted = st.form_submit_button("Send inn", on_click=save_to_bigquery)
        if submitted:
            st.success("Undersøkelsen er sendt inn! Takk for din deltakelse.")
    except Exception as e:
        st.error(f"Error submitting survey: {e}")