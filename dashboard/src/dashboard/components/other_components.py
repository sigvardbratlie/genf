from datetime import datetime,timedelta
from io import BytesIO
import streamlit as st
import pandas as pd


class DownloadComponent:
    def __init__(self,):
        pass 

    def render_csv_xlsx_download_section(self, df, filename : str):
        cols = st.columns(2)
        cols[0].download_button(
            label="Last ned data som CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f'{filename}.csv',
            mime='text/csv',
            icon="📄"
        )
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        cols[1].download_button(
        label="Last ned data som Excel",
        data=buffer.getvalue(),
        file_name=f'{filename}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        icon="📄"
    )
        
class PlotlyComponent:
    def __init__(self,):
        pass 

    