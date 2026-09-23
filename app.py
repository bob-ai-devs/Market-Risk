import streamlit as st

# from financial_risk import main as financial_risk_main
# from esg import main as esg_main
# from multilingual import main as multilingual_main


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BOB AI Index Solutions Hub",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# BANK OF BARODA BRAND PALETTE
# ==============================================================================
BOB_ORANGE = "#F7941D"       # primary — "Baroda Sun"
BOB_ORANGE_DEEP = "#E8531B"  # sun-ray gradient end
BOB_MAROON = "#8E1B3A"       # sun-ray gradient end / accents
BOB_NAVY = "#12284C"         # wordmark / headings
BOB_NAVY_LIGHT = "#1E3E73"
BOB_CREAM = "#FFF8F1"        # page background
BOB_GREY = "#5B6675"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BOB_CREAM};
    }}
    #bob-banner {{
        background: radial-gradient(circle at 15% 50%, {BOB_ORANGE} 0%, {BOB_ORANGE_DEEP} 45%, {BOB_MAROON} 100%);
        padding: 22px 30px;
        border-radius: 12px;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
    }}
    #bob-banner h1 {{
        color: white;
        margin: 0;
        font-size: 1.9em;
        font-weight: 800;
        letter-spacing: 0.3px;
    }}
    #bob-banner p {{
        color: #FFEFE0;
        margin: 4px 0 0 0;
        font-size: 0.95em;
    }}
    h1, h2, h3 {{ color: {BOB_NAVY}; }}
        </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# BOB COLORS
# ============================================================

BOB_NAVY = "#002E6E"
BOB_BLUE = "#0059B3"
BOB_ORANGE = "#F7941D"
LIGHT_BG = "#F5F7FA"


# ============================================================
# SESSION STATE
# ============================================================

if "selected_app" not in st.session_state:
    st.session_state.selected_app = None


# ============================================================
# APPLICATION DEFINITIONS
# ============================================================

APPLICATIONS = [
    {
        "id": "financial",
        "number": "01",
        "icon": "📊",
        "title": "Index Scrapper",
        "description": (
            "Generate stock, company and ETF-wise insights by analyzing "
            "market data, financial information and relevant market signals."
        ),
        "features": [
            "Stock-wise insights",
            "Company & ETF analysis",
            "Market intelligence",
        ],
    },
    {
        "id": "esg",
        "number": "02",
        "icon": "📈",
        "title": "Index Analyzer",
        "description": (
            "Analyze core market indices and generate insights on indices "
            "such as Bank Nifty, Nifty Media and other major market segments."
        ),
        "features": [
            "Core index insights",
            "Bank Nifty & sector indices",
            "Index trend analysis",
        ],
    },
    {
        "id": "multilingual",
        "number": "03",
        "icon": "🔮",
        "title": "Index Predictor",
        "description": (
            "AI-powered prediction of future Nifty 50 index movement using "
            "historical market data and relevant market signals."
        ),
        "features": [
            "Nifty 50 prediction",
            "Future index movement",
            "AI-powered market signals",
        ],
    },
]


# ============================================================
# PORTAL
# ============================================================

def show_portal():

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    st.markdown(
        """
        <div id="bob-banner">
            <h1>🏦 BOB AI Index Solutions Hub</h1>
            <p>AI & Emerging Technologies  •  Intelligent Market Intelligence Solutions</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("### Explore AI Applications")

    st.caption(
        "Select an application below to launch the solution."
    )

    st.write("")


    # --------------------------------------------------------
    # Application Cards
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(
        3,
        gap="large"
    )

    columns = [col1, col2, col3]

    for col, app in zip(columns, APPLICATIONS):

        with col:

            # ------------------------------------------------
            # Native Streamlit Card
            # ------------------------------------------------

            with st.container(border=True):

                # Application number and availability
                st.caption(
                    f"APPLICATION {app['number']}  •  🟢 AVAILABLE"
                )

                # Icon
                st.markdown(
                    f"## {app['icon']}"
                )

                # Title
                st.markdown(
                    f"### {app['title']}"
                )

                # Description
                st.write(
                    app["description"]
                )

                st.write("")

                # Key capabilities
                st.markdown("**Key capabilities**")

                for feature in app["features"]:
                    st.write(
                        f"• {feature}"
                    )

                st.write("")

                # Launch button
                if st.button(
                    "Launch Application  →",
                    key=f"launch_{app['id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_app = app["id"]
                    st.rerun()


    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    st.write("")

    st.divider()

    st.caption(
        "Bank of Baroda  |  AI & Emerging Technologies"
    )


# ============================================================
# APPLICATION ROUTER
# ============================================================

def run_selected_application():

    selected_app = st.session_state.selected_app

    # --------------------------------------------------------
    # Back Button
    # --------------------------------------------------------

    if st.button(
        "← Back to AI Index Solutions Hub",
        key="back_to_portal",
    ):
        st.session_state.selected_app = None
        st.rerun()

    st.divider()


    # --------------------------------------------------------
    # Launch Selected Application
    # --------------------------------------------------------

    if selected_app == "financial":

        financial_risk_main()

    elif selected_app == "esg":

        esg_main()

    elif selected_app == "multilingual":

        multilingual_main()


# ============================================================
# MAIN
# ============================================================

if st.session_state.selected_app is None:

    show_portal()

else:

    run_selected_application()
