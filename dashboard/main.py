import streamlit as st
import pandas as pd
import numpy as np
from utilities import init, run_query,sidebar_setup,ensure_login

init()
st.title("GENF Dashboard")
st.markdown("### Velkommen til GENF Dashboard")
st.markdown("Velg en side nedenfor for å komme i gang:")

sidebar_setup()
#ensure_login()

st.divider()

# Timer og lønn side
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("## ⏰")
with col2:
    st.page_link("pages/timer.py", label="Timer og lønn", icon="⏰")
    st.markdown("""
    Oversikt over timer, lønn og kostnader:
    - Total antall timer og kostnader per periode
    - Filtrer på navn og rolle
    - Grafisk fremstilling av utvikling over sesongen
    """)

st.divider()

# Camp Status side
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("## 🏕️")
with col2:
    st.page_link("pages/camp_status.py", label="Camp Status", icon="🏕️")
    st.markdown("""
    Oversikt over camp-status og måloppnåelse:
    - Opptjent vs mål per rolle
    - Fordeling av camp-kostnader per gruppe
    - Visualisering av kostnadsfordeling
    """)
