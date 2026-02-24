import streamlit as st
import pandas as pd
import numpy as np
from dashboard import init
from components import SidebarComponent,DownloadComponent,get_supabase_api
from datetime import datetime,timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import calendar
import logging
logger = logging.getLogger(__name__)

init()

st.title("Timer og lønn")
st.divider()
SidebarComponent().sidebar_setup()

api = get_supabase_api()
df_raw = api.build_combined()

sel_cols = st.columns(2)

name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df_raw["worker_name"].unique().tolist(), default=[])
every_sample = sel_cols[1].toggle("Skru av sammenslåing", value=False)

sel_cols2 = st.columns(2)
work_types = sel_cols2[0].multiselect("Velg arbeidstype (tom for alle)", options=df_raw["work_type"].unique().tolist(), default=[])


df = api.filter_df_by_dates(df_raw.copy())
df = api.filter_work_type(df, work_types)
if name:
    df = df[df["worker_name"].isin(name)]


st.info(f"Viser timer og lønn for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")
min_date = df["date_completed"].min().strftime("%Y-%m-%d") if not df.empty else "N/A"
max_date = df["date_completed"].max().strftime("%Y-%m-%d") if not df.empty else "N/A"
st.write(f'**First registration**: {min_date}, **Last registration**: {max_date}')


#========================
#      HOUR DATAFRAME
#========================

hours = st.container(width="stretch")
with hours:
    api.render_metrics(df, df_raw)
    st.divider()
    dfg = api.apply_grouping(df, every_sample=every_sample)
    st.dataframe(dfg.style.format({"cost":"{:,.0f} NOK",
                                   "hours_worked":"{:,.1f}",
                                   "units_completed":"{:,.0f}"}),use_container_width=True,height=700)
    # ========================
    #      DOWNLOAD DATA
    # ========================

    with st.expander("Last ned data"):
        download_component = DownloadComponent()
        download_component.render_csv_xlsx_download_section(dfg, f'timer_og_lonn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}')
        
st.divider()
season = st.container()
