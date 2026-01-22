import streamlit as st
import pandas as pd
import numpy as np
from utilities import init, run_query,sidebar_setup,  load_all_seasons
from datetime import datetime,timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import calendar
import logging
logger = logging.getLogger(__name__)

init()

st.title("Jobb typer")
st.divider()
sidebar_setup()

# ========================
#      LOAD DATA
# ========================


df = load_all_seasons()
df_raw = df.copy()
    
for col in ['email', 'bank_account_number']:
    mapping = df.dropna(subset=[col]).set_index('worker_name')[col].to_dict()
    df[col] = df[col].fillna(df['worker_name'].map(mapping))

df['number_of_units'] = df['number_of_units'].fillna(0)


try:
    df = df.loc[
    (df['date_completed'] >= pd.to_datetime(st.session_state.dates[0], utc=True)) 
    & (df['date_completed'] <= pd.to_datetime(st.session_state.dates[1], utc=True)) 
    #& (df['gruppe'].isin(gruppe) if gruppe else True) &
    #(df['prosjekt'].isin(prosjekt) if prosjekt else True)
    ].copy()
except KeyError as e:
    st.error(f"Data loading error: {e}. Missing expected columns in the data.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")

st.info(f"Viser for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")
st.write(f'**First registration**: {df["date_completed"].min().strftime("%Y-%m-%d")}, **Last registration**: {df["date_completed"].max().strftime("%Y-%m-%d")}')

tabs = st.tabs(["Vask, rigg og utomhus", "Ved og grus", "Jobbhvit", "Flasker"])

def view_project_stat(project_name,gruppe_name, show_units = False):
    st.markdown(f"## {project_name.capitalize()}")
    cols = st.columns(2) if not show_units else st.columns(3)
    cols[0].metric("Total timer", f"{df.loc[(df["gruppe"] == gruppe_name) & (df["prosjekt"] == project_name), "hours_worked"].sum():,.0f} timer")
    cols[1].metric("Lønn", f"{df.loc[(df["gruppe"] == gruppe_name) & (df["prosjekt"] == project_name), "cost"].sum():,.0f} kr")
    if show_units:
        cols[2].metric("Lønn", f"{df.loc[(df["gruppe"] == gruppe_name) & (df["prosjekt"] == project_name), "number_of_units"].sum():,.0f} stk")
    st.divider()

# ========================VASK, RIGG, UTOMHUS================================
with tabs[0]:
    st.header("Vask, rigg og utomhus")

    fig = px.pie(
        df[df['work_type'].str.contains('vask|rigg|utomhus', case=False, na=False)].groupby('prosjekt').agg(
            total_hours=('hours_worked', 'sum')
        ).reset_index(),
        names='prosjekt',
        values='total_hours',
        title='Fordeling av timer per prosjekt'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("## Totalt")
    cols = st.columns(2)
    cols[0].metric("Total timer", f"{df.loc[df["gruppe"] == "bccof", "hours_worked"].sum():,.0f} timer")
    cols[1].metric("Lønn", f"{df.loc[df["gruppe"] == "bccof", "cost"].sum():,.0f} kr")
    st.divider()
    
    view_project_stat("vask", "bccof")
    view_project_stat("rigg", "bccof")
    view_project_stat("utomhus", "bccof")
    


# ========================VED OG GRUS================================
with tabs[1]:
    st.header("Ved og grus")

    st.markdown("Antall sekker")
    cols = st.columns(2)
    cols[0].metric("Antall vedsekker", f'{df.loc[df["prosjekt"] == "vedpakking", "number_of_units"].sum():,.0f} sekker')
    cols[1].metric("Antall grussekker", f'{df.loc[df["prosjekt"] == "strogrus", "number_of_units"].sum():,.0f} sekker')
    
    df_ved = df[df['work_type'].str.contains('ved|grus', case=False, na=False)]
    #st.dataframe(df_ved["prosjekt"].value_counts())
    #st.dataframe(df_ved)
    
    fig = px.pie(
        df_ved.groupby('prosjekt').agg(
            total=("cost", 'sum')
        ).reset_index(),
        names='prosjekt',
        values='total',
        title='Fordeling av kostnader per prosjekt',
    )
    fig.update_traces(textinfo="label+value")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()




