import streamlit as st
from utilities import init, run_query

init() 

st.title("GEN-F konkurranser 2025/2026!")

# query = """ 
# SELECT * FROM members.teams_25_26
# """
# df_teams = run_query(query)


# ====================== 
# Team Competition Section
# ======================
tabs = st.tabs(["Konkurranse", "Leaderboard"])
with tabs[0]:
    st.markdown("## Lagkonkurranse")
    colors = {
        "blue": "rgba(59, 130, 246, 0.15)",
        "green": "rgba(34, 197, 94, 0.15)", 
        "orange": "rgba(249, 115, 22, 0.15)",
        "pink": "rgba(236, 72, 153, 0.15)",
        "yellow": "rgba(234, 179, 8, 0.15)"
    }

    for i in range(len(colors)):
        team_name = list(colors.keys())[i]
        st.container(border=True).markdown(
            f"""
            <div style="background-color: {colors[team_name]}; padding: 20px; border-radius: 8px;">
                <h2>TEAM {team_name.upper()}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )


# ======================
# Leaderboard Section
# ======================
with tabs[1]:
    st.markdown("## Leaderboard")
    query = """
    SELECT * FROM contest_H26.leaderboard_25_26
        """