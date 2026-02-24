import streamlit as st
from dashboard import init
from components import SeasonalReviewComponent,YearlyReviewComponent

init()


tabs = st.tabs({"Seasonal Review": "seasonal", "Yearly Review": "yearly"})
with tabs["seasonal"]:
    st.title("Sesonggjennomgang")
    SeasonalReviewComponent().render_page()

with tabs["yearly"]:
    st.title("Årsgjennomgang")
    YearlyReviewComponent().render_page()