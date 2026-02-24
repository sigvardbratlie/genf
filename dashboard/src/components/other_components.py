from io import BytesIO
import streamlit as st
import pandas as pd
from typing import Literal, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from dashboard.src.components.database_module import BigQueryModule


class DownloadComponent:
    def __init__(self,):
        pass 

    def render_csv_download(self, df: pd.DataFrame, filename: str):
        st.download_button(
            label="Last ned CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{filename}.csv",
            mime="text/csv",
            icon="📄",
            key = str(uuid4())  
        )

    def render_xlsx_download(self, df: pd.DataFrame, filename: str):
        buffer = BytesIO()
        df_excel = df.copy()
        for col in df_excel.select_dtypes(include=["datetimetz"]).columns:
            df_excel[col] = df_excel[col].dt.tz_localize(None)
        df_excel.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            label="Last ned Excel",
            data=buffer.getvalue(),
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            icon="📄",
            key = str(uuid4())
        )
        
    def render_bigquery_update(
        self,
        df: pd.DataFrame,
        bq_module: "BigQueryModule",
        target_table: str = "raw.buk_cash",
        write_type: Literal["append", "replace", "merge"] = "append",
        merge_on: "str | list[str]" = "id",
        key: str = "",
    ):
        btn_key = f"bq_update_{target_table}_{write_type}_{key}"
        if st.button("Oppdater data i BigQuery", icon="🔄", key=btn_key):
            with st.spinner(f"Laster opp til `{target_table}`..."):
                try:
                    n = bq_module.write_df(df, target_table=target_table, write_type=write_type, merge_on=merge_on)
                    if n == 0:
                        st.info("Ingen nye rader å legge til — dataen er allerede oppdatert.")
                    else:
                        st.success(f"{n} rader lastet opp til `{target_table}` ({write_type}).")
                except Exception as e:
                    st.error(f"Feil ved oppdatering av BigQuery: {e}")
                    raise

        
class PlotlyComponent:
    def __init__(self,):
        pass 

    