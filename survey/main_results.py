import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Page config
st.set_page_config(
    page_title="BUK Mentor Resultater",
    page_icon="📊",
    layout="wide"
)

# Clean CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        text-align: center;
        border: 1px solid #E5E7EB;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4F46E5;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #6B7280;
        margin-top: 0.5rem;
    }
    .question-box {
        background: #F3F4F6;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #4F46E5;
    }
    .question-text {
        font-size: 0.9rem;
        color: #374151;
        font-style: italic;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 8px 8px 0 0;
    }
    h1 {
        color: #1F2937;
        font-weight: 700;
    }
    h3 {
        color: #374151;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    .feedback-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.75rem;
        border: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_gcp_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials)


@st.cache_data(ttl=300)
def load_survey_data():
    client = init_gcp_client()
    query = "SELECT * FROM `admin.mentor_survey` ORDER BY timestamp DESC"
    return client.query(query).to_dataframe()


def show_question(text):
    """Display original question in a styled box"""
    st.markdown(f"""
    <div class="question-box">
        <div class="question-text">Spørsmål: "{text}"</div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(value, label):
    """Custom metric card"""
    return f"""
    <div class="metric-container">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def pie_chart(df, column, title):
    counts = df[column].value_counts().reset_index()
    counts.columns = ['kategori', 'antall']
    fig = px.pie(counts, values='antall', names='kategori', hole=0.45)
    fig.update_traces(textposition='outside', textinfo='percent+label')
    fig.update_layout(
        showlegend=False,
        margin=dict(t=30, b=30, l=30, r=30),
        title=dict(text=title, x=0.5, font=dict(size=14))
    )
    return fig


def bar_chart(df, column, title):
    counts = df[column].value_counts().reset_index()
    counts.columns = ['kategori', 'antall']
    counts = counts.sort_values('antall', ascending=True)

    fig = px.bar(counts, y='kategori', x='antall', orientation='h',
                 color_discrete_sequence=['#4F46E5'])

    fig.update_layout(
        showlegend=False,
        margin=dict(t=40, b=20, l=20, r=20),
        title=dict(text=title, x=0.5, font=dict(size=14)),
        xaxis_title="Antall", yaxis_title="",
        height=max(250, len(counts) * 40)
    )
    return fig


def multiselect_bar(df, column, title):
    """Handle multiselect columns - explode arrays and count each option"""
    import ast
    import json

    def parse_to_list(val):
        """Convert any value to a flat list of strings"""
        if val is None:
            return []
        if isinstance(val, (list, tuple)):
            # Flatten in case of nested lists
            result = []
            for item in val:
                if isinstance(item, (list, tuple)):
                    result.extend([str(x).strip() for x in item])
                else:
                    result.append(str(item).strip())
            return result
        if isinstance(val, str):
            val = val.strip()
            if not val:
                return []
            # String representation of list: "['a', 'b']"
            if val.startswith('[') and val.endswith(']'):
                try:
                    parsed = ast.literal_eval(val)
                    if isinstance(parsed, (list, tuple)):
                        return [str(x).strip() for x in parsed]
                except:
                    pass
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, (list, tuple)):
                        return [str(x).strip() for x in parsed]
                except:
                    pass
            # Comma-separated
            if ',' in val:
                return [v.strip() for v in val.split(',') if v.strip()]
            return [val]
        return [str(val)]

    # Parse all values to lists
    all_items = []
    for val in df[column].dropna():
        items = parse_to_list(val)
        all_items.extend(items)

    # Filter out empty strings
    all_items = [x for x in all_items if x and x.strip()]

    if not all_items:
        logger.warning(f"No items found for column {column}")
        return None

    # Count occurrences
    counts = pd.Series(all_items).value_counts().reset_index()
    counts.columns = ['kategori', 'antall']
    counts = counts.sort_values('antall', ascending=True)

    logger.info(f"Column {column}: {len(all_items)} total selections, {len(counts)} unique values")

    fig = px.bar(counts, y='kategori', x='antall', orientation='h',
                 color_discrete_sequence=['#4F46E5'])
    fig.update_layout(
        showlegend=False,
        margin=dict(t=40, b=20, l=20, r=20),
        title=dict(text=title, x=0.5, font=dict(size=14)),
        xaxis_title="Antall", yaxis_title="",
        height=max(300, len(counts) * 40)
    )
    return fig


def slider_chart(df, column, title):
    """Horizontal histogram for slider values 1-10"""
    counts = df[column].value_counts().sort_index().reset_index()
    counts.columns = ['score', 'antall']
    counts['score'] = counts['score'].astype(str)

    mean_val = df[column].mean()

    fig = px.bar(counts, y='score', x='antall', orientation='h',
                 color_discrete_sequence=['#4F46E5'])
    fig.update_layout(
        margin=dict(t=40, b=40, l=40, r=40),
        title=dict(text=f"{title}<br><sup>Snitt: {mean_val:.1f}</sup>", x=0.5, font=dict(size=14)),
        xaxis_title="Antall", yaxis_title="Score",
        height=350
    )
    return fig


# Header
st.title("📊 BUK Mentor Undersøkelse")
st.caption("Resultater fra mentorundersøkelsen")

try:
    df = load_survey_data()
    #st.dataframe(df)

    if df.empty:
        st.warning("Ingen data funnet.")
        #st.stop()

    # Key metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(metric_card(len(df), "Totalt svar"), unsafe_allow_html=True)
    with col2:
        avg_hours = df['hours_buk'].mean() if 'hours_buk' in df.columns else 0
        st.markdown(metric_card(f"{avg_hours:.1f}", "Snitt timer/uke"), unsafe_allow_html=True)
    with col3:
        avg_chal = df['challenge_combine'].mean() if 'challenge_combine' in df.columns else 0
        st.markdown(metric_card(f"{avg_chal:.1f}", "Utfordringsscore"), unsafe_allow_html=True)
    with col4:
        if 'timestamp' in df.columns:
            latest = pd.to_datetime(df['timestamp']).max().strftime("%d.%m")
            st.markdown(metric_card(latest, "Siste svar"), unsafe_allow_html=True)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "👥 Demografi",
        "💪 Motivasjon",
        "📊 Aktivitet",
        "⚡ Utfordringer",
        "❤️ Opplevelse",
        "💬 Tilbakemeldinger"
    ])

    # TAB 1: Demografi
    with tab1:
        st.header("Demografisk oversikt")
        st.markdown("Hvem er mentorene våre?")

        col1, col2 = st.columns(2)

        with col1:
            show_question("Hvor gammel er du?")
            if 'age' in df.columns:
                st.plotly_chart(pie_chart(df, 'age', 'Aldersfordeling'), use_container_width=True)

        with col2:
            show_question("Kjønn")
            if 'gender' in df.columns:
                st.plotly_chart(pie_chart(df, 'gender', 'Kjønnsfordeling'), use_container_width=True)

        st.markdown("---")

        #

        with st.container():
            show_question("Hvor er du mentor? (kan velge flere)")
            if 'buk_groups' in df.columns:
                data = df['buk_groups'].explode().value_counts().reset_index()
                #st.dataframe(data)
                fig = px.bar(data, y='count', x='buk_groups', #orientation='h',
                                color_discrete_sequence=['#4F46E5'])
                #fig = multiselect_bar(df, 'buk_groups', 'Fordeling på grupper')
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Ingen gruppedata funnet")
                    with st.expander("Debug: rådata"):
                        st.write(df['buk_groups'].head(5).tolist())
            else:
                st.warning("Ingen gruppedata funnet")


    # TAB 2: Motivasjon og kapasitet
    with tab2:
        st.header("Motivasjon og kapasitet")
        st.markdown("Hva driver mentorene og hvor mye kapasitet har de?")

        col1, col2 = st.columns(2)

        with col1:
            show_question("Hva er din motivasjon for å være mentor? (kan velge flere)")
            if 'motivation' in df.columns:
                data = df['motivation'].explode().value_counts().reset_index()
                fig = px.bar(data, y='count', x='motivation', #orientation='h',
                                color_discrete_sequence=['#4F46E5'])
                #fig = multiselect_bar(df, 'motivation', 'Motivasjonsfaktorer')
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Ingen motivasjonsdata funnet")
                    with st.expander("Debug: rådata"):
                        st.write(df['motivation'].head(5).tolist())

        with col2:
            show_question("Hvordan vurderer du din kapasitet?")
            if 'capacity' in df.columns:
                data = df['capacity'].value_counts().reset_index()
                #st.dataframe(data)
                fig = px.bar(df['capacity'].value_counts().reset_index(), y='count', x='capacity', #orientation='h',
                             color_discrete_sequence=['#4F46E5'])
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        show_question("Hvor mange timer bruker du i snitt på mentoroppgaven per uke?")
        if 'hours_buk' in df.columns:
            # Group hours into bins for horizontal display
            bins = [0, 1, 2, 3, 4, 5, 7, 10, 15, 20, 40]
            labels = ['0-1', '1-2', '2-3', '3-4', '4-5', '5-7', '7-10', '10-15', '15-20', '20+']
            df_hours = df.copy()
            df_hours['timer_gruppe'] = pd.cut(df_hours['hours_buk'], bins=bins, labels=labels, right=False)
            counts = df_hours['timer_gruppe'].value_counts().sort_index().reset_index()
            counts.columns = ['timer', 'antall']
            counts.sort_values('timer', inplace=True)

            fig = px.bar(counts, y='antall', x='timer', #orientation='h',
                        color_discrete_sequence=['#4F46E5'])
            fig.update_layout(
                title=dict(text=f"Timer brukt per uke (snitt: {df['hours_buk'].mean():.1f})", x=0.5),
                xaxis_title="Antall mentorer", yaxis_title="Timer",
                margin=dict(t=40, b=40),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    # TAB 3: Aktivitetsnivå
    with tab3:
        st.header("Aktivitetsnivå")
        st.markdown("Hvordan er aktivitetsnivået blant mentorene?")

        show_question("Kåre Smith kommer på mentorsamlingen, vi har tenkt å stille ham en del spørsmål (kanskje ditt). \nSkriv minst ett spørsmål som du ønsker at han skal svare på i forbindelse med hyrdetjenesten/mentorarbeidet/BUK.")
        if 'events_frequency' in df.columns:
            st.markdown(f'Det er kommet inn {(df["events_frequency"].nunique())} svar på dette spørsmålet.')

            with st.expander("Se noen eksempler på spørsmål sendt inn"):
                sample_questions = df['events_frequency'].dropna().tolist()
                for i, question in enumerate(sample_questions, 1):
                    if question.strip():
                        st.markdown(f"{question}")
                        st.markdown("---")

    # TAB 4: Utfordringer
    with tab4:
        st.header("Utfordringer")
        st.markdown("Hvilke utfordringer møter mentorene?")

        col1, col2 = st.columns(2)

        with col1:
            show_question("Hvor enig er du i påstanden: Jeg synes det er utfordrende å kombinere mentorarbeid med andre forpliktelser\n\n(1 = helt uenig, 10 = helt enig)")
            if 'challenge_combine' in df.columns:   
                #st.dataframe(df['challenge_combine'])
                fig = px.bar(df['challenge_combine'].value_counts().reset_index(), y='count', x='challenge_combine', #orientation='h',
                             color_discrete_sequence=['#4F46E5'])
                #fig = slider_chart(df, 'challenge_combine', 'Utfordring: Kombinere forpliktelser')
                st.plotly_chart(fig,
                               use_container_width=True)

        with col2:
            show_question("Hvor enig er du i påstanden: Jeg føler jeg må velge mellom å enten være on-track i BUK/Samvirk selv eller være aktiv i mentorarbeidet.\n\n(1 = helt uenig, 10 = helt enig)")
            if 'challenge_both' in df.columns:
                fig = px.bar(df['challenge_both'].value_counts().reset_index(), y='count', x='challenge_both', #orientation='h',
                             color_discrete_sequence=['#4F46E5'])
                #st.plotly_chart(slider_chart(df, 'challenge_both', 'Utfordring: Velge mellom aktiviteter'), use_container_width=True)
                st.plotly_chart(fig,
                               use_container_width=True)

        st.markdown("---")

        show_question("Hvilken av disse påstandene om mentorarbeidet passer best for deg?")
        if 'participation' in df.columns:
            # st.plotly_chart(bar_chart(df, 'participation', 'Opplevelse av deltakelse'),
            #                use_container_width=True)
            fig  = px.bar(df['participation'].value_counts().reset_index(), y='count', x='participation', #orientation='h',
                             color_discrete_sequence=['#4F46E5'])
            st.plotly_chart(fig,
                               use_container_width=True)

    # TAB 5: Opplevelse
    with tab5:
        st.header("Opplevelse og meningsfullhet")
        st.markdown("Hvordan opplever mentorene arbeidet sitt?")

        col1, col2 = st.columns(2)

        with col1:
            show_question("Hvordan opplever du mentorarbeidet for deg personlig?")
            if 'meaningfulness' in df.columns:
                data = df['meaningfulness'].explode().value_counts().reset_index()
                #st.dataframe(data)
                # st.plotly_chart(bar_chart(df, 'meaningfulness', 'Meningsfullhet'),
                #                use_container_width=True)
                fig = px.bar(data, y='count', x='meaningfulness', #orientation='h',
                             color_discrete_sequence=['#4F46E5'])
                st.plotly_chart(fig,
                               use_container_width=True)

        with col2:
            show_question("Hvordan forholder du deg til ansvar?")
            if 'responsibility' in df.columns:
                fig = px.bar(df['responsibility'].value_counts().reset_index(), y='count', x='responsibility', #orientation='h',
                             color_discrete_sequence=['#4F46E5'])
                st.plotly_chart(fig,
                               use_container_width=True)
                #st.plotly_chart(bar_chart(df, 'responsibility', 'Forhold til ansvar'),use_container_width=True)
                               

        st.markdown("---")

        cols = st.columns(2)
        with cols[0]:
            show_question("Hvor viktig har aksjonene (pace, unboxing, osv) vært for å være on-track i Samvirk og BUK? (1 = ikke viktig, 10 = veldig viktig)")
            if 'campaign' in df.columns:
                data = df['campaign'].value_counts().reset_index()
                #st.dataframe(data)
                fig = px.bar(data, y='count', x='campaign', #orientation='h',
                            color_discrete_sequence=['#4F46E5'])
                st.plotly_chart(fig,
                            use_container_width=True)
                #st.plotly_chart(bar_chart(df, 'campaign', 'Tanker om aksjonen'),use_container_width=True)
        with cols[1]:
            show_question("Er det ditt ønske å være en helhjertet mentor og hyrde i menigheten?")
            if "participation_church" in df.columns:
                fig = px.pie(df.dropna(subset = ["participation_church"]), names='participation_church', title='Ønske om å være helhjertet mentor/hyrde')
                fig.update_traces(textposition='outside', textinfo='percent+label')
                fig.update_layout(
                    showlegend=False,
                    margin=dict(t=30, b=30, l=30, r=30),
                    title=dict(text='Ønske om å være helhjertet mentor/hyrde', x=0.5, font=dict(size=14))
                )
                st.plotly_chart(fig, use_container_width=True)
                           

    # TAB 6: Tilbakemeldinger
    with tab6:
        st.header("Tilbakemeldinger")

        show_question("Har du innspill eller tilbakemeldinger til mentorarbeidet i Oslo? Hvis du kunne endret én ting, hva ville det vært?")

        if 'improvement_text' in df.columns:
            suggestions = df['improvement_text'].dropna()
            suggestions = suggestions[suggestions.str.strip() != '']

            st.metric("Antall tilbakemeldinger", len(suggestions))

            if len(suggestions) > 0:
                st.markdown("---")
                for i, suggestion in enumerate(suggestions, 1):
                    st.markdown(f"""
                    <div class="feedback-card">
                        <strong>#{i}</strong><br>{suggestion}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Ingen tilbakemeldinger ennå.")

        st.markdown("---")

        # Download section
        st.subheader("Last ned data")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Last ned alle svar (CSV)",
            data=csv,
            file_name="mentor_survey_results.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Kunne ikke laste data: {e}")
    logger.error("Error loading survey data", exc_info=True)
    st.info("Sjekk at BigQuery er konfigurert i `.streamlit/secrets.toml`")
