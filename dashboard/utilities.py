import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime,timedelta
import calendar
import pandas as pd
from google.api_core.exceptions import NotFound
from supabase import create_client, Client
from datetime import date, datetime, timedelta
from typing import Optional,Any, List, Dict
from dashboard.components import get_supabase_api, get_supabase_module
import logging

import supabase

logger = logging.getLogger(__name__)

def init():
    st.session_state.setdefault("dates", ("2025-08-01", datetime.today().date().isoformat()))
    st.session_state.setdefault("role", ["GEN-F", "Hjelpementor", "Mentor"])
    st.session_state.setdefault("season", "25/26")

def load_all_seasons() -> pd.DataFrame:
    db_module = get_supabase_module()
    api = get_supabase_api()
    old = db_module.load_registrations()
    new = api.fetch_job_logs()
