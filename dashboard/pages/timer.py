import streamlit as st
import pandas as pd
import numpy as np
from utilities import init, run_query,sidebar_setup
from datetime import datetime,timedelta
import plotly.express as px

init()

st.title("Timer og lønn")
st.markdown(f"## Viser timer og lønn for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")
st.divider()
sidebar_setup()

query_timer =f"""SELECT * 
FROM genf.sesong_{st.session_state.sesong.replace("/","_")}
"""
df_raw = run_query(query_timer)
df_raw['dato'] = pd.to_datetime(df_raw['dato'],errors='coerce',utc=True)
    
df = df_raw.loc[
    (df_raw['dato'] >= pd.to_datetime(st.session_state.dates[0], utc=True)) &
    (df_raw['dato'] <= pd.to_datetime(st.session_state.dates[1], utc=True))
    ].copy()

hours = st.container(width="stretch")

delta_time = st.session_state.dates[1] - st.session_state.dates[0]
delta_start = st.session_state.dates[0] - delta_time - timedelta(days=1)
delta_df = df_raw.loc[
    (df_raw['dato'] >= pd.to_datetime(delta_start, utc=True)) &
    (df_raw['dato'] < pd.to_datetime(st.session_state.dates[0], utc=True))
    ].copy()



with hours:
    cols = st.columns(3)
    cols[0].metric(label = "Total antall timer", value = f"{df['timer'].sum():,.0f}", 
                   delta = f"{df['timer'].sum() - delta_df['timer'].sum():,.0f} fra forrige periode")
    cols[1].metric(label = "Totale kostnader", value = f"{df['kostnad'].sum():,.0f} NOK",
                   delta = f"{df['kostnad'].sum() - delta_df['kostnad'].sum():,.0f} NOK fra forrige periode")
    cols[2].metric(label = "Antall unike brukere", value = f"{df['navn'].nunique():,.0f}",
                   delta = f"{df['navn'].nunique() - delta_df['navn'].nunique():,.0f} fra forrige periode")

    dfg = df.groupby(["navn","rolle"])[["kostnad","timer","antall_enheter"]].sum().reset_index()
    st.dataframe(dfg.style.format({"kostnad":"{:,.0f} NOK",
                                   "timer":"{:,.0f}",
                                   "antall_enheter":"{:,.0f}"}),use_container_width=True,height=700)
    
season = st.container()
with season:
    line_data = df_raw.set_index('dato').resample('ME')[["kostnad","timer","antall_enheter"]].sum().reset_index()
    fig = px.line(
        line_data,
        x="dato",
        y=["kostnad"])

    fig.update_layout(
        title="Utvikling over sesongen",
        xaxis_title="Dato",
        yaxis_title="Sum per måned",
        legend_title="Metrikker",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)