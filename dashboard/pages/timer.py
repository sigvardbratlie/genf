import streamlit as st
import pandas as pd
import numpy as np
from utilities import init, run_query,sidebar_setup,  load_all_seasons, fetch_job_logs
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
sidebar_setup()

# ========================
#      LOAD DATA
# ========================
df = load_all_seasons()
df_raw = df.copy()
    
for col in ['email', 'bank_account_number']:
    mapping = df.dropna(subset=[col]).set_index('worker_name')[col].to_dict()
    df[col] = df[col].fillna(df['worker_name'].map(mapping))

df['units_completed'] = df['units_completed'].fillna(0)

sel_cols = st.columns(2)

name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df["worker_name"].unique().tolist(), default=[])
every_sample = sel_cols[1].toggle("Skru av sammenslåing", value=False)

sel_cols2 = st.columns(2)
gruppe = sel_cols2[0].multiselect("Velg gruppe (tom for alle)", options=df["gruppe"].unique().tolist(), default=[])
prosjekt = sel_cols2[1].multiselect("Velg prosjekt (tom for alle)", options=df["prosjekt"].unique().tolist(), default=[])

#st.dataframe(df.loc[df["prosjekt"] == "strogrus"])
#ks = fetch_job_logs()
#st.info(f'KS antall timer : {ks["hours_worked"].sum()}')


try:
    df = df.loc[
    (df['date_completed'] >= pd.to_datetime(st.session_state.dates[0], utc=True)) &
    (df['date_completed'] <= pd.to_datetime(st.session_state.dates[1], utc=True)) & 
    (df['gruppe'].isin(gruppe) if gruppe else True) &
    (df['prosjekt'].isin(prosjekt) if prosjekt else True)
    ].copy()
except KeyError as e:
    st.error(f"Data loading error: {e}. Missing expected columns in the data.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")

st.info(f"Viser timer og lønn for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")
st.write(f'**First registration**: {df["date_completed"].min().strftime("%Y-%m-%d")}, **Last registration**: {df["date_completed"].max().strftime("%Y-%m-%d")}')



#========================
#      HOUR DATAFRAME
#========================

hours = st.container(width="stretch")
with hours:
    delta_time = st.session_state.dates[1] - st.session_state.dates[0]
    delta_start = st.session_state.dates[0] - delta_time - timedelta(days=1)
    #st.info((delta_start, st.session_state.dates,delta_time))
    delta_df = df.loc[
        (df['date_completed'] >= pd.to_datetime(delta_start, utc=True)) &
        (df['date_completed'] < pd.to_datetime(st.session_state.dates[0], utc=True))
        ].copy()
    cols = st.columns(3)
    cols[0].metric(label = "Total antall timer", value = f"{df['hours_worked'].sum():,.0f}", 
                   delta = f"{df['hours_worked'].sum() - delta_df['hours_worked'].sum():,.0f} fra forrige periode")
    cols[1].metric(label = "Totale kostnader", value = f"{df['cost'].sum():,.0f} NOK",
                   delta = f"{df['cost'].sum() - delta_df['cost'].sum():,.0f} NOK fra forrige periode")
    cols[2].metric(label = "Antall unike brukere", value = f"{df['worker_name'].nunique():,.0f}",
                   delta = f"{df['worker_name'].nunique() - delta_df['worker_name'].nunique():,.0f} fra forrige periode")

    if name:
        df = df[df["worker_name"].isin(name)]
    
    #st.dataframe(df)
    if not set(["worker_name","role","cost","hours_worked",]).issubset(df.columns):
        raise KeyError("One or more required columns are missing from the data.")
    else:
        if set(["email","bank_account_number","units_completed"]).issubset(df.columns):
            if not every_sample:
                dfg = df.groupby(["worker_name","email","bank_account_number","role"])[["cost","hours_worked","units_completed"]].sum().reset_index()
            else:
                dfg = df[["worker_name","email","bank_account_number","role","cost","hours_worked","units_completed","date_completed",]].copy()
        else:
            st.warning(f"missing some columns {set(['email','bank_account_number','units_completed']) - set(df.columns)}")
            if not every_sample:
                dfg = df.groupby(["worker_name","role"])[["cost","hours_worked"]].sum().reset_index()
            else:
                dfg = df[["worker_name","role","cost","hours_worked","date_completed",]].copy()
    st.divider()
    st.dataframe(dfg.style.format({"cost":"{:,.0f} NOK",
                                   "hours_worked":"{:,.1f}",
                                   "units_completed":"{:,.0f}"}),use_container_width=True,height=700)
    # ========================
    #      DOWNLOAD DATA
    # ========================

    with st.expander("Last ned data"):
        cols = st.columns(2)
        cols[0].download_button(
            label="Last ned data som CSV",
            data=dfg.to_csv(index=False).encode('utf-8'),
            file_name=f'timer_og_lonn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}.csv',
            mime='text/csv',
            icon="📄"
        )
        buffer = BytesIO()
        dfg.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        cols[1].download_button(
        label="Last ned data som Excel",
        data=buffer.getvalue(),
        file_name=f'timer_og_lonn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        icon="📄"
    )
st.divider()
season = st.container()


#========================
# Cumulative Cost Over Months
#========================
cum_cost = st.container()
with cum_cost:
    st.markdown("## Kumulativ lønn per sesong")
    df_raw["month"] = df_raw['date_completed'].dt.month
    df_raw["year"] = df_raw['date_completed'].dt.year
    
    df_raw["fiscal_month"] = ((df_raw['month'] - 8) % 12) + 1
    
    df_month = df_raw.groupby(['season', 'fiscal_month']).agg({'hours_worked':'sum','cost':'sum'}).reset_index()
    df_month["cost"] = df_month.groupby('season')['cost'].cumsum()
    
    fig = go.Figure()
    for season in df_month['season'].unique():
        data = df_month[df_month['season'] == season]
        fig.add_trace(go.Scatter(
            x=data['fiscal_month'],
            y=data['cost'],
            name=season,
            mode='lines'
        ))
    
    fig.update_xaxes(
        tickmode='array',
        tickvals=list(range(1, 13)),
        ticktext=['Aug', 'Sep', 'Okt', 'Nov', 'Des', 'Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul']
    )
    st.plotly_chart(fig)

