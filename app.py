import streamlit as st

# from financial_risk import main as financial_risk_main
# from esg import main as esg_main
# from multilingual import main as multilingual_main


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BOB AI Solutions Hub",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
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
        "title": "AI Financial Risk",
        "description": (
            "AI-powered financial risk and reputation analysis combining "
            "financial indicators, market information and news intelligence."
        ),
        "features": [
            "Financial risk indicators",
            "Market intelligence",
            "News & reputation analysis",
        ],
    },
    {
        "id": "esg",
        "number": "02",
        "icon": "🌱",
        "title": "AI ESG Analytics",
        "description": (
            "AI-powered Environmental, Social and Governance analytics "
            "using news intelligence, sentiment analysis and ESG scoring."
        ),
        "features": [
            "Environmental, Social & Governance scoring",
            "News intelligence",
            "ESG trends & monitoring",
        ],
    },
    {
        "id": "multilingual",
        "number": "03",
        "icon": "🌐",
        "title": "AI Multilingual Assistant",
        "description": (
            "Intelligent multilingual banking assistance with speech "
            "recognition, translation and AI-powered product interaction."
        ),
        "features": [
            "Speech recognition",
            "Multilingual translation",
            "Banking product assistance",
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

    st.markdown("## 🏦 Bank of Baroda")

    st.markdown(
        f"# AI Solutions Hub"
    )

    st.caption(
        "AI & Emerging Technologies  •  Intelligent Banking Solutions"
    )

    st.divider()

    st.markdown("### Explore AI Applications")
    st.caption("Select an application below to launch the solution.")

    st.write("")


    # --------------------------------------------------------
    # Cards
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3, gap="large")

    columns = [col1, col2, col3]

    for col, app in zip(columns, APPLICATIONS):

        with col:

            # Native Streamlit card
            with st.container(border=True):

                # Application number
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

                # Capabilities
                st.markdown("**Key capabilities**")

                for feature in app["features"]:
                    st.write(f"• {feature}")

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

    # Back button
    if st.button(
        "← Back to AI Solutions Hub",
        key="back_to_portal",
    ):
        st.session_state.selected_app = None
        st.rerun()

    st.divider()

    # Run selected application
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
