import streamlit as st
from datetime import datetime
import logging
from components import get_bigquery_module

logger = logging.getLogger(__name__)

def init():
    st.session_state.setdefault("dates", ("2026-01-01", datetime.today().date().isoformat()))
    st.session_state.setdefault("role", ["GEN-F", "Hjelpementor", "Mentor"])
    st.session_state.setdefault("season", "25/26")
    st.session_state.setdefault("rates", get_bigquery_module().load_rates().to_dict(orient="records"))

