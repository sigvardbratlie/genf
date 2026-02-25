import streamlit as st
from dashboard import init
from components import SeasonalReviewComponent,YearlyReviewComponent,SidebarComponent
import logging
logger = logging.getLogger(__name__)
init()

SidebarComponent().sidebar_setup(disable_seasonpicker=True,disable_datepicker=True, disable_custom_datepicker=True)

tabs = st.tabs(["seasonal", "yearly"])
with tabs[0]:
    st.title("Sesonggjennomgang")
    try:
        SeasonalReviewComponent().render_page()
    except Exception as e:
        st.error(f"Det skjedde en feil under innlastning av sesonggjennomgangen: {e}")
        logger.error(f"Feil under innlastning av sesonggjennomgangen: {e}", exc_info=True)

with tabs[1]:
    st.title("Årsgjennomgang")
    try:
        YearlyReviewComponent().render_page()
    except Exception as e:
        st.error(f"Det skjedde en feil under innlastning av årsgjennomgangen: {e}")
        logger.error(f"Feil under innlastning av årsgjennomgangen: {e}", exc_info=True)