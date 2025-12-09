import streamlit as st
import pandas as pd
import numpy as np
from utilities import init, run_query,sidebar_setup, load_all_seasons,map_roles
from datetime import datetime,timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import calendar

init()

st.title("Timer og lønn")
st.divider()
sidebar_setup()

# query_timer =f"""SELECT * 
# FROM genf.sesong_{st.session_state.sesong.replace("/","_")}
# """
# df_raw = run_query(query_timer)
# df_raw['dato'] = pd.to_datetime(df_raw['dato'],errors='coerce',utc=True)

# ========================
#      LOAD DATA
# ========================
df_raw = load_all_seasons()
df_raw = map_roles(df_raw)

if not "epost" in df_raw.columns:
    df_raw["epost"] = np.nan
if not "kontonr" in df_raw.columns:
    df_raw["kontonr"] = np.nan
if not "antall_enheter" in df_raw.columns:
    df_raw["antall_enheter"] = np.nan
epost_map = df_raw.dropna(subset=['epost']).set_index('navn')['epost'].to_dict()
kontonr_map = df_raw.dropna(subset=['kontonr']).set_index('navn')['kontonr'].to_dict()
df_raw['epost'] = df_raw['epost'].fillna(df_raw['navn'].map(epost_map))
#df_raw['kontonr'] = df_raw['kontonr'].fillna(df_raw['navn'].map(kontonr_map))
df_raw["antall_enheter"] = df_raw["antall_enheter"].fillna(0)

sel_cols = st.columns(2)

name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df_raw["navn"].unique().tolist(), default=[])
every_sample = sel_cols[1].toggle("Skru av sammenslåing", value=False)

sel_cols2 = st.columns(2)
gruppe = sel_cols2[0].multiselect("Velg gruppe (tom for alle)", options=df_raw["gruppe"].unique().tolist(), default=[])
prosjekt = sel_cols2[1].multiselect("Velg prosjekt (tom for alle)", options=df_raw["prosjekt"].unique().tolist(), default=[])
    
st.info(f"Viser timer og lønn for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")

try:
    df = df_raw.loc[
    (df_raw['dato'] >= pd.to_datetime(st.session_state.dates[0], utc=True)) &
    (df_raw['dato'] <= pd.to_datetime(st.session_state.dates[1], utc=True)) & 
    (df_raw['gruppe'].isin(gruppe) if gruppe else True) &
    (df_raw['prosjekt'].isin(prosjekt) if prosjekt else True)
    ].copy()
except KeyError as e:
    st.error(f"Data loading error: {e}. Missing expected columns in the data.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    


#========================
#      HOUR DATAFRAME
#========================

hours = st.container(width="stretch")
with hours:
    delta_time = st.session_state.dates[1] - st.session_state.dates[0]
    delta_start = st.session_state.dates[0] - delta_time - timedelta(days=1)
    delta_df = df_raw.loc[
        (df_raw['dato'] >= pd.to_datetime(delta_start, utc=True)) &
        (df_raw['dato'] < pd.to_datetime(st.session_state.dates[0], utc=True))
        ].copy()
    cols = st.columns(3)
    cols[0].metric(label = "Total antall timer", value = f"{df['timer'].sum():,.0f}", 
                   delta = f"{df['timer'].sum() - delta_df['timer'].sum():,.0f} fra forrige periode")
    cols[1].metric(label = "Totale kostnader", value = f"{df['kostnad'].sum():,.0f} NOK",
                   delta = f"{df['kostnad'].sum() - delta_df['kostnad'].sum():,.0f} NOK fra forrige periode")
    cols[2].metric(label = "Antall unike brukere", value = f"{df['navn'].nunique():,.0f}",
                   delta = f"{df['navn'].nunique() - delta_df['navn'].nunique():,.0f} fra forrige periode")

    if name:
        df = df[df["navn"].isin(name)]
    
    if not set(["navn","rolle","kostnad","timer",]).issubset(df.columns):
        raise KeyError("One or more required columns are missing from the data.")
    else:
        if set(["epost","kontonr","antall_enheter"]).issubset(df.columns):
            if not every_sample:
                dfg = df.groupby(["navn","epost","kontonr","rolle"])[["kostnad","timer","antall_enheter"]].sum().reset_index()
            else:
                dfg = df[["navn","epost","kontonr","rolle","kostnad","timer","antall_enheter","dato",]].copy()
        else:
            st.warning("missing some columns")
            if not every_sample:
                dfg = df.groupby(["navn","rolle"])[["kostnad","timer"]].sum().reset_index()
            else:
                dfg = df[["navn","rolle","kostnad","timer","dato",]].copy()
    st.divider()
    st.dataframe(dfg.style.format({"kostnad":"{:,.0f} NOK",
                                   "timer":"{:,.1f}",
                                   "antall_enheter":"{:,.0f}"}),use_container_width=True,height=700)
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
    df_raw["month"] = df_raw['dato'].dt.month
    df_raw["year"] = df_raw['dato'].dt.year
    
    # Lag sesong (august til august)
    df_raw["season"] = df_raw.apply(
        lambda row: f"{row['year']}/{row['year']+1}" if row['month'] >= 8 
        else f"{row['year']-1}/{row['year']}", 
        axis=1
    )
    
    # Lag fiscal month (1=Aug, 2=Sep, ..., 12=Jul)
    df_raw["fiscal_month"] = ((df_raw['month'] - 8) % 12) + 1
    
    df_month = df_raw.groupby(['season', 'fiscal_month']).agg({'timer':'sum','kostnad':'sum'}).reset_index()
    df_month["kostnad"] = df_month.groupby('season')['kostnad'].cumsum()
    
    fig = go.Figure()
    for season in df_month['season'].unique():
        data = df_month[df_month['season'] == season]
        fig.add_trace(go.Scatter(
            x=data['fiscal_month'],
            y=data['kostnad'],
            name=season,
            mode='lines'
        ))
    
    fig.update_xaxes(
        tickmode='array',
        tickvals=list(range(1, 13)),
        ticktext=['Aug', 'Sep', 'Okt', 'Nov', 'Des', 'Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul']
    )
    st.plotly_chart(fig)

