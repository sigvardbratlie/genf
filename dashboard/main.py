from pathlib import Path
import os
import logging
import streamlit as st
import pandas as pd
import numpy as np
logger = logging.getLogger(__name__)

#st.info(Path(".").resolve().name)
def set_cwd():
    if Path(".").resolve().name != "dashboard":
        logger.warning(f'Unexpected working directory: {Path(".").resolve()}. Expected to be in "dashboard" directory.')
        try:
            os.chdir("./dashboard")
        except Exception as e:
            logger.error(f"Failed to change directory to 'dashboard': {e}")
            st.error("Feil ved oppstart: Kunne ikke sette arbeidskatalog til 'dashboard'. Vennligst start applikasjonen fra riktig katalog.")
            st.stop()
set_cwd()

from dashboard import init
from components import SidebarComponent

init()
st.title("GENF Dashboard")
st.markdown("### Velkommen til GENF Dashboard")
st.markdown("Velg en side nedenfor for å komme i gang:")

SidebarComponent().sidebar_setup()

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

# Review side
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("## 📊")
with col2:
    st.page_link("pages/review.py", label = "Review", icon="📊")
    st.markdown("""
    Sesong- og årsgjennomgang av lønn og aktivitet:
    - **Sesong**: Opptjent vs mål, avviksfordeling og aktive vs registrerte per rolle
    - **År**: Årlige kostnader, gjennomsnitt per år per rolle, og kumulativ lønnsutvikling
    - Filter for inaktive medlemmer i begge faner
    """)

st.divider()
st.markdown("### Buk Cash")
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("## 💰")
with col2:
    st.page_link("pages/buk_cash.py", label = "Buk Cash", icon="💰")
    st.markdown("""
    Oversikt fra Buk.cash:
    """)
    