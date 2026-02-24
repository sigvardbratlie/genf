import streamlit as st
import pandas as pd
import numpy as np
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

# Camp Status side
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("## 🏕️")
with col2:
    st.page_link("pages/review.py", label = "Review", icon="📊")
    st.markdown("""
    Oversikt over camp-status og måloppnåelse:
    - Opptjent vs mål per rolle
    - Fordeling av camp-kostnader per gruppe
    - Visualisering av kostnadsfordeling
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
    