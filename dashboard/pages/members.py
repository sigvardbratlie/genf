import streamlit as st
from utilities import run_query,init, sidebar_setup, load_all_seasons,map_roles
import pandas as pd


init()
sidebar_setup(disable_datepicker=True, disable_seasonpicker=True)   
st.title("Medlemmer")
st.divider()
df = run_query("SELECT * FROM genf.members_u16")
sel_cols = st.columns(2)
name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df["Display_name"].unique().tolist(), default=[])
mother = sel_cols[1].multiselect("Velg forelder (tom for alle)", options=df["Mother_name"].unique().tolist(), default=[])
father = sel_cols[1].multiselect("Velg forelder (tom for alle)", options=df["Father_name"].unique().tolist(), default=[])
mask = pd.Series([True] * len(df), index=df.index)
if name:
    mask &= df["Display_name"].isin(name)
if mother:
    mask &= df["Mother_name"].isin(mother)
if father:
    mask &= df["Father_name"].isin(father)

df_filtered = df.loc[mask].copy()
st.dataframe(df_filtered, use_container_width=True)