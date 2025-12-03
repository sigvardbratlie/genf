import streamlit as st
import pandas as pd
import numpy as np
from utilities import init, run_query,sidebar_setup
from datetime import datetime,timedelta
import plotly.express as px
import plotly.graph_objects as go

init()

st.title("Timer og lønn")
st.divider()
sidebar_setup()



query_timer =f"""SELECT * 
FROM genf.sesong_{st.session_state.sesong.replace("/","_")}
"""
df_raw = run_query(query_timer)
df_raw['dato'] = pd.to_datetime(df_raw['dato'],errors='coerce',utc=True)

sel_cols = st.columns(3)

every_sample = sel_cols[0].toggle("Vis alle rader (kan være mange rader)", value=False)
name = sel_cols[1].multiselect("Velg navn (tom for alle)", options=df_raw["navn"].unique().tolist(), default=[])
    
st.info(f"Viser timer og lønn for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")

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

    if name:
        df = df[df["navn"].isin(name)]
    if not every_sample:
        dfg = df.groupby(["navn","rolle"])[["kostnad","timer","antall_enheter"]].sum().reset_index()
    else:
        dfg = df[["navn","rolle","kostnad","timer","antall_enheter","dato"]].copy()
    st.divider()
    st.dataframe(dfg.style.format({"kostnad":"{:,.0f} NOK",
                                   "timer":"{:,.1f}",
                                   "antall_enheter":"{:,.0f}"}),use_container_width=True,height=700)
st.divider()
season = st.container()

datas = [run_query(f'SELECT * FROM genf.sesong_{season}') for season in ["24_25", "25_26"]]
line_datas = []
for data in datas:
    data['dato'] = pd.to_datetime(data['dato'], errors='coerce', utc=True)
    line_data = data.set_index('dato').resample('ME')[["kostnad","timer","antall_enheter"]].sum().reset_index()
    line_data["kostnad_cumsum"] = line_data["kostnad"].cumsum()
    line_data["timer_cumsum"] = line_data["timer"].cumsum()
    line_data["month"] = line_data["dato"].dt.month
    line_datas.append(line_data)

with season:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=line_datas[0]["month"],
        y=line_datas[0]["kostnad_cumsum"],
        mode="lines", 
        name="24/25"
    ))
    fig.add_trace(go.Scatter(
        x=line_datas[1]["month"],
        y=line_datas[1]["kostnad_cumsum"],
        mode="lines",   
        name="25/26"
    ))
    fig.update_layout(
        title="Utvikling over sesongen",
        xaxis_title="Måned",
        yaxis_title="Kostnad (NOK)",
        hovermode="x unified",
        xaxis=dict(type='category')
    )
    st.plotly_chart(fig, use_container_width=True)