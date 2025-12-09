import streamlit as st
from utilities import init, sidebar_setup, load_members
import pandas as pd
import plotly.graph_objects as go


init()
sidebar_setup(disable_datepicker=True, disable_custom_datepicker=False)   
st.title("Medlemmer")
st.divider()

df = load_members(season=st.session_state.season)

# ====================
#     MEMBERS
# ====================
with st.container():
    st.markdown(f"# Medlemmer (GEN-F & hjelpementorer) for sesong {st.session_state.season}")
    sel_cols = st.columns(3)
    name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df["display_name"].unique().tolist(), default=[])
    year = sel_cols[1].multiselect("Velg fødselsår (tom for alle)", options=sorted(df["birthdate"].dt.year.unique().tolist()), default=[])
    gender = sel_cols[2].multiselect("Velg kjønn (tom for alle)", options=df["gender"].unique().tolist(), default=[])
    #mother = sel_cols[1].multiselect("Velg forelder (tom for alle)", options=df["mother_name"].unique().tolist(), default=[])
    #father = sel_cols[1].multiselect("Velg forelder (tom for alle)", options=df["father_name"].unique().tolist(), default=[])
    mask = pd.Series([True] * len(df), index=df.index)
    if name:
        mask &= df["display_name"].isin(name)
    if year:
        mask &= df["birthdate"].dt.year.isin(year)
    # if mother:
    #     mask &= df["mother_name"].isin(mother)
    # if father:
    #     mask &= df["father_name"].isin(father)
    df_filtered = df.loc[mask].copy()
    cols = st.columns(3)
    cols[0].metric("Antall", len(df_filtered))
    cols[1].metric("Gutter", len(df_filtered.loc[df_filtered["gender"]=="Male"]))
    cols[2].metric("Jenter", len(df_filtered.loc[df_filtered["gender"]=="Female"]))
    cols = st.columns(3)
    min_year = df_filtered['birthdate'].dt.year.min()
    middle_year = min_year + 1
    max_year = df_filtered['birthdate'].dt.year.max()
    # if max_year != min_year+2:
    #     st.warning("Unexpected age range detected. Please verify the data.")
    cols[0].metric(f"{min_year}", len(df_filtered.loc[df_filtered['birthdate'].dt.year == min_year]))
    cols[1].metric(f"{middle_year}", len(df_filtered.loc[df_filtered['birthdate'].dt.year == middle_year]))
    cols[2].metric(f"{max_year}", len(df_filtered.loc[df_filtered['birthdate'].dt.year == max_year]))
    st.dataframe(df_filtered, use_container_width=True)

with st.container():
    fig = go.Figure()

    # GEN-F
    for gender in df_filtered['gender'].unique():
        fig.add_trace(go.Histogram(
            x=df_filtered.loc[(df_filtered["role"] == "GEN-F") & (df_filtered["gender"] == gender), 'birthdate'].dt.year,
            name=f'GEN-F - {gender}',
            legendgroup='GEN-F'
        ))

    # Hjelpementor
    if int(st.session_state.season.split("/")[0]) >= 25:
        for gender in df_filtered['gender'].unique():
            fig.add_trace(go.Histogram(
                x=df_filtered.loc[(df_filtered["role"] == "Hjelpementor") & (df_filtered["gender"] == gender), 'birthdate'].dt.year,
                name=f'Hjelpementor - {gender}',
                legendgroup='Hjelpementor'
            ))

    fig.update_layout(
        title='Fordeling av medlemmer etter fødselsår',
        xaxis_title='Fødselsår',
        yaxis_title='Antall medlemmer',
        barmode='stack',
        bargap=0.2,
    )
    st.plotly_chart(fig, use_container_width=True)