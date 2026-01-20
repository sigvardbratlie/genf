from io import BytesIO
from pdb import run
import streamlit as st
from utilities import init, sidebar_setup, load_members,load_active_users,fetch_profiles
import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery
from datetime import datetime


init()
sidebar_setup(disable_datepicker=True, disable_custom_datepicker=False)   
st.title("Medlemmer")
st.divider()


df = load_members(season=st.session_state.season)
#st.dataframe(df, use_container_width=True)
#st.dataframe(df["birthdate"].dt.year.value_counts(), use_container_width=True)

filters = st.columns(2)
with filters[0]:
    filter_inactive = st.toggle("Filter Inactive Members", value=False)
    filter_value = st.slider("Cut-off for Inactive Members (NOK)", min_value=0, max_value=3000, value=500, step=100)

filters[1].markdown(f"Medlemmer som har jobbet for mindre enn {filter_value}kr i løpet av en sesong regnes som inaktive.")
data = load_active_users(threshold=filter_value,)
df["status"] = df["person_id"].apply(lambda x: "Active" if x in data["person_id"].values else "Inactive")
if filter_inactive:
    df = df.loc[df["status"]=="Active"].copy()
    
# ====================
#     MEMBERS
# ====================
with st.container():
    st.markdown(f"# GEN-F & hjelpementorer")
    st.markdown(f"## sesong {st.session_state.season}\n\n")
    #st.divider()
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
    # cols = st.columns(3)
    # cols[0].metric("Antall", len(df_filtered))
    # cols[1].metric("Gutter", len(df_filtered.loc[df_filtered["gender"]=="Male"]))
    # cols[2].metric("Jenter", len(df_filtered.loc[df_filtered["gender"]=="Female"]))
    # cols = st.columns(3)
    # min_year = df_filtered['birthdate'].dt.year.min()
    # middle_year = min_year + 1
    # max_year = df_filtered['birthdate'].dt.year.max()
    # if max_year != min_year+2:
    #     st.warning("Unexpected age range detected. Please verify the data.")
    # cols[0].metric(f"{min_year}", len(df_filtered.loc[df_filtered['birthdate'].dt.year == min_year]))
    # cols[1].metric(f"{middle_year}", len(df_filtered.loc[df_filtered['birthdate'].dt.year == middle_year]))
    # cols[2].metric(f"{max_year}", len(df_filtered.loc[df_filtered['birthdate'].dt.year == max_year]))
    st.dataframe(df_filtered, use_container_width=True)

with st.container():
    fig = go.Figure()

    # GEN-F
    for gender in df_filtered['gender'].unique():
        fig.add_trace(go.Histogram(
            x=df_filtered.loc[(df_filtered["role"] == "genf") & (df_filtered["gender"] == gender), 'birthdate'].dt.year,
            name=f'GEN-F - {gender}',
            legendgroup='GEN-F'
        ))

    # Hjelpementor
    if int(st.session_state.season.split("/")[0]) >= 25:
        for gender in df_filtered['gender'].unique():
            fig.add_trace(go.Histogram(
                x=df_filtered.loc[(df_filtered["role"] == "hjelpementor") & (df_filtered["gender"] == gender), 'birthdate'].dt.year,
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


    

# ======= UPDATE MEMBERS =======
st.divider()
with st.container():
    st.markdown("## Hent medlemsliste fra buk.cash og oppdater database")
    data = fetch_profiles()
    members_bc = pd.DataFrame(data)
    members_bc = members_bc.loc[members_bc["role"] != "parent"].copy()
    #st.dataframe(members_bc, use_container_width=True)
    df_to_save = members_bc[["id","custom_id","email","role","first_name","last_name","bank_account_number","date_of_birth"]]

    st.dataframe(df_to_save, use_container_width=True)
    cols = st.columns(3)
    
    with cols[0]:
        #if st.button("Last ned (CSV)",icon="📥"):
        csv = df_to_save.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Last ned CSV",
            data=csv,
            file_name='members_buk_cash.csv',
            mime='text/csv',
            icon="📄"
        )
    with cols[1]:
        #if st.button("Last ned (Excel)",icon="📥"):
        buffer = BytesIO()
        df_to_save.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        st.download_button(
                label="Last ned (Excel)",
                data=buffer.getvalue(),
                file_name=f'members_buk_cash.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                icon="📄")

    with cols[2]:
        if st.button("Oppdater (BigQuery)",icon="🔄"):
            try:
                st.session_state.gcp_client.load_table_from_dataframe(df_to_save, "members.buk_cash", 
                                                            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"))
                st.success("Medlemsdatabase oppdatert fra buk.cash!")
            except Exception as e:
                st.error(f"Error updating members database: {e}")
    