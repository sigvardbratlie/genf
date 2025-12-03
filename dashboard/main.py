import streamlit as st
import pandas as pd
import numpy as np
from utilities import init, run_query,sidebar_setup

init()

st.title("GENF Dashboard")
sidebar_setup()

st.page_link("pages/timer.py", label = "Timer", icon="⏰")
st.page_link("pages/camp_status.py", label = "Camp Status", icon="🏕️")
