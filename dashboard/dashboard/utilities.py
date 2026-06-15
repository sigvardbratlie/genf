import streamlit as st
from datetime import date, datetime, timedelta
import logging
from components import get_bigquery_module

logger = logging.getLogger(__name__)

def init():
    st.session_state.setdefault("dates", ("2026-01-01", datetime.today().date().isoformat()))
    st.session_state.setdefault("role", ["GEN-F", "Hjelpementor", "Mentor"])
    st.session_state.setdefault("season", "25/26")
    st.session_state.setdefault("rates", get_bigquery_module().load_rates().to_dict(orient="records"))

def ensure_max_date_range():
    if st.session_state.dates:
        to_date = date.fromisoformat(st.session_state.dates[1]) if isinstance(st.session_state.dates[1], str) else st.session_state.dates[1]
        from_date = date.fromisoformat(st.session_state.dates[0]) if isinstance(st.session_state.dates[0], str) else st.session_state.dates[0]
        if to_date - from_date > timedelta(days=90):
                st.warning("Du har valgt en periode på mer enn 90 dager. Vennligst velg en kortere periode for å unngå ytelsesproblemer. ")
                #st.session_state.dates = (from_date, (from_date + timedelta(days=89)).isoformat())
                #st.rerun()