import streamlit as st
import pandas as pd
import numpy as np
from utilities import init, run_query,sidebar_setup,ensure_login

init()
st.title("GENF Dashboard")
sidebar_setup()
#ensure_login()


st.page_link("pages/timer.py", label = "Timer", icon="⏰")
st.page_link("pages/camp_status.py", label = "Camp Status", icon="🏕️")
