import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import calendar
import logging
import os
from pathlib import Path
logger = logging.getLogger(__name__)
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
from components import SidebarComponent,DownloadComponent,get_supabase_api

init()

st.title("Timer og lønn")
st.divider()
SidebarComponent().sidebar_setup(disable_seasonpicker=True)

api = get_supabase_api()
df_raw = api.build_combined()
df_raw['gruppe'] = df_raw['work_type'].apply(lambda wt: api.mk_gruppe(wt))
df_raw["prosjekt"] = df_raw["work_type"].apply(lambda wt: api.mk_prosjekt(wt))
df = api.filter_df_by_dates(df_raw.copy())

sel_cols = st.columns(2)

name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df["worker_name"].unique().tolist(), default=[])
every_sample = sel_cols[1].toggle("Skru av sammenslåing", value=False)

sel_cols2 = st.columns(2)
gruppe = sel_cols2[0].multiselect("Velg gruppe (tom for alle)", options=df["gruppe"].unique().tolist(), default=[])
prosjekt = sel_cols2[1].multiselect("Velg arbeidstype (tom for alle)", options=df["prosjekt"].unique().tolist(), default=[])
if not gruppe:
    gruppe = df["gruppe"].unique().tolist()
if not prosjekt:
    prosjekt = df["prosjekt"].unique().tolist()

df = df.loc[(df["gruppe"].isin(gruppe)) & (df["prosjekt"].isin(prosjekt)) ,:]
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

    cols = st.columns(2)
    with cols[0]:
        DownloadComponent().render_csv_download(dfg, filename=f"timer_og_lønn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}.csv",)
    with cols[1]:
        DownloadComponent().render_xlsx_download(dfg, filename=f"timer_og_lønn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}.xlsx", )
        
st.divider()

def qc(row):
        date_of_week = calendar.day_name[row["date_completed"].weekday()].lower()
        if row["role"] in ["genf"]:
            if date_of_week in ["saturday","sunday"] and row["hours_worked"] > 4.5:
                return True
            if date_of_week in ["monday","tuesday","wednesday","thursday","friday"] and row["hours_worked"] > 2.5:
                return True
            return False
        else:
            return False

# df["qc_flag"] = df.apply(qc, axis=1)
# with st.expander("Vis registreringer som overgår normale timer", 
#                     ):
#     st.markdown("Maks antall timer per dag er normalt 2.5 for vanlige dager og 4.5 for helg. \
#                 Dette gjelder for genf-roller. Andre roller har ingen grense satt.")
#     for date, dfg in df.loc[df["qc_flag"] == True].groupby("date_completed"):
#         st.write(f"**{date} ({calendar.day_name[date.weekday()]})**")
#         st.dataframe(dfg[["worker_name","hours_worked","work_type"]])

threshold = 0.5
def har_avvik(dfg, threshold):                                                                                                                         
      if dfg["work_type"].iloc[0] in ["annet_jobbhvit"]:                                                                                      
          return False                                                                                                                        
      median = dfg["hours_worked"].median()
      return not dfg.loc[dfg["hours_worked"] > median * (1 + threshold)].empty                                                                

with st.expander("Vis avvik fra de andre i gruppen", expanded=False):
    avvik = sum(1 for _, dfg in df.groupby(["date_completed", "work_type"]) if har_avvik(dfg, threshold))  
    
    st.markdown(f"Viser registreringer hvor det er avvik i antall timer for samme arbeidstype og dato. Totalt avvik: {avvik}")
    for (date, work_type), dfg in df.groupby(["date_completed","work_type"]):
        if dfg["hours_worked"].nunique() > 1:
            
            median = dfg["hours_worked"].median()
            warning_df = dfg.loc[dfg["hours_worked"] > median * (1 + threshold), ["worker_name","hours_worked"]]
            if not warning_df.empty and work_type not in ["annet_jobbhvit"]:
                st.divider()
                st.markdown(f"Avvik i timer for 👷🏼‍♂️ **{work_type}** den 📅 **{date.date()}** ({calendar.day_name[date.weekday()]}):")
                for _, row in warning_df.iterrows():
                    st.write(f" * {row['worker_name']}:  {row['hours_worked']} timer, median er {median:.1f} timer.")
                st.dataframe(dfg[["worker_name","work_type","hours_worked",]])
