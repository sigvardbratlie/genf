import streamlit as st
from dashboard import init
from components import SeasonalReviewComponent,YearlyReviewComponent

init()


tabs = st.tabs(["seasonal", "yearly"])
with tabs[0]:
    st.title("Sesonggjennomgang")
    #SeasonalReviewComponent().render_page()

with tabs[1]:
    st.title("Årsgjennomgang")
    #YearlyReviewComponent().render_page()