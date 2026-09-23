import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="BOB AI Application Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# COLORS
# =========================================================

BOB_NAVY = "#002E6E"
BOB_BLUE = "#0059B3"
BOB_ORANGE = "#F7941D"

LIGHT_BG = "#F4F7FB"
CARD_BORDER = "#E1E7F0"
TEXT = "#172B4D"
MUTED = "#667085"


# =========================================================
# CSS
# =========================================================

st.markdown(
    f"""
    <style>

    /* =====================================================
       PAGE
       ===================================================== */

    .stApp {{
        background: {LIGHT_BG};
    }}

    .block-container {{
        max-width: 1280px;
        padding-top: 35px;
        padding-bottom: 40px;
    }}


    /* =====================================================
       HEADER
       ===================================================== */

    .portal-title {{
        color: {BOB_NAVY};
        font-size: 36px;
        font-weight: 750;
        letter-spacing: -0.8px;
        margin-bottom: 3px;
    }}

    .portal-subtitle {{
        color: {MUTED};
        font-size: 16px;
        margin-bottom: 32px;
    }}


    /* =====================================================
       TOP ACCENT
       ===================================================== */

    .top-line {{
        height: 5px;
        width: 75px;
        background: {BOB_ORANGE};
        border-radius: 10px;
        margin-bottom: 18px;
    }}


    /* =====================================================
       CARD
       ===================================================== */

    .card {{
        background: white;
        border: 1px solid {CARD_BORDER};
        border-radius: 20px;

        padding: 28px;

        min-height: 355px;

        box-shadow:
            0 5px 20px rgba(16, 24, 40, 0.06);

        position: relative;
    }}


    /* =====================================================
       CARD TOP
       ===================================================== */

    .card-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;

        margin-bottom: 25px;
    }}

    .number {{
        color: #B6C2D4;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1px;
    }}

    .available {{
        color: #18794E;
        background: #ECFDF3;

        border-radius: 20px;

        padding: 5px 10px;

        font-size: 11px;
        font-weight: 650;
    }}


    /* =====================================================
       ICON
       ===================================================== */

    .icon-box {{
        width: 72px;
        height: 72px;

        border-radius: 18px;

        background: linear-gradient(
            135deg,
            #FFF5E8,
            #FFE5C2
        );

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 37px;

        margin-bottom: 23px;
    }}


    /* =====================================================
       CARD TITLE
       ===================================================== */

    .card-title {{
        color: {BOB_NAVY};

        font-size: 22px;
        font-weight: 750;

        line-height: 1.28;

        margin-bottom: 12px;
    }}


    /* =====================================================
       DESCRIPTION
       ===================================================== */

    .card-description {{
        color: {MUTED};

        font-size: 14px;

        line-height: 1.65;

        min-height: 72px;
    }}


    /* =====================================================
       BUTTON
       ===================================================== */

    div.stButton {{
        margin-top: -8px;
    }}

    div.stButton > button {{
        width: 100%;

        height: 48px;

        border-radius: 10px;

        background: {BOB_NAVY};

        color: white;

        border: none;

        font-size: 14px;

        font-weight: 650;

        transition: 0.2s ease;
    }}

    div.stButton > button:hover {{
        background: {BOB_ORANGE};

        color: white;

        border: none;

        box-shadow:
            0 6px 15px rgba(247, 148, 29, 0.25);
    }}


    /* =====================================================
       FOOTER
       ===================================================== */

    .footer {{
        text-align: center;

        color: #98A2B3;

        font-size: 12px;

        margin-top: 45px;
    }}


    /* =====================================================
       APP SCREEN
       ===================================================== */

    .app-heading {{
        color: {BOB_NAVY};

        font-size: 28px;

        font-weight: 750;

        margin-bottom: 5px;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "selected_app" not in st.session_state:
    st.session_state.selected_app = None


# =========================================================
# APPLICATION DATA
# =========================================================

applications = [
    {
        "id": "financial",
        "number": "01",
        "icon": "📊",
        "title": "AI Financial Risk",
        "description": (
            "AI-powered financial risk and reputation analysis "
            "combining financial indicators, market information "
            "and news sentiment."
        ),
    },
    {
        "id": "esg",
        "number": "02",
        "icon": "🌱",
        "title": "AI ESG Analytics",
        "description": (
            "Analyze Environmental, Social and Governance signals "
            "using AI-powered news intelligence, sentiment analysis "
            "and ESG scoring."
        ),
    },
    {
        "id": "multilingual",
        "number": "03",
        "icon": "🌐",
        "title": "AI Multilingual Assistant",
        "description": (
            "Intelligent multilingual banking assistance with "
            "speech recognition, translation and AI-powered "
            "product interaction."
        ),
    },
]


# =========================================================
# PORTAL
# =========================================================

if st.session_state.selected_app is None:

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    st.markdown(
        '<div class="top-line"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "🏦 Bank of Baroda",
        unsafe_allow_html=False,
    )

    st.markdown(
        '<div class="portal-title">AI Application Portal</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="portal-subtitle">'
        'AI &amp; Emerging Technologies&nbsp;&nbsp;•&nbsp;&nbsp;'
        'Intelligent Banking Solutions'
        '</div>',
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # CARDS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(
        3,
        gap="large",
    )


    for col, app in zip(
        [col1, col2, col3],
        applications,
    ):

        with col:

            # Card
            st.markdown(
                f"""
                <div class="card">

                    <div class="card-top">

                        <span class="number">
                            APPLICATION {app["number"]}
                        </span>

                        <span class="available">
                            ● AVAILABLE
                        </span>

                    </div>

                    <div class="icon-box">
                        {app["icon"]}
                    </div>

                    <div class="card-title">
                        {app["title"]}
                    </div>

                    <div class="card-description">
                        {app["description"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            # Button outside card
            if st.button(
                "Launch Application  →",
                key=f"launch_{app['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_app = app["id"]
                st.rerun()


    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="footer">
            Bank of Baroda &nbsp;|&nbsp;
            AI & Emerging Technologies
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# APPLICATION ROUTING
# =========================================================

else:

    selected = st.session_state.selected_app


    # -----------------------------------------------------
    # BACK
    # -----------------------------------------------------

    if st.button(
        "←  Back to AI Applications",
        key="back_to_portal",
    ):
        st.session_state.selected_app = None
        st.rerun()


    st.markdown("")


    # -----------------------------------------------------
    # FINANCIAL RISK
    # -----------------------------------------------------

    if selected == "financial":

        st.markdown(
            '<div class="app-heading">'
            '📊 AI Financial Risk'
            '</div>',
            unsafe_allow_html=True,
        )

        from financial_risk import main as financial_risk_main

        financial_risk_main()


    # -----------------------------------------------------
    # ESG
    # -----------------------------------------------------

    elif selected == "esg":

        st.markdown(
            '<div class="app-heading">'
            '🌱 AI ESG Analytics'
            '</div>',
            unsafe_allow_html=True,
        )

        from esg import main as esg_main

        esg_main()


    # -----------------------------------------------------
    # MULTILINGUAL
    # -----------------------------------------------------

    elif selected == "multilingual":

        st.markdown(
            '<div class="app-heading">'
            '🌐 AI Multilingual Assistant'
            '</div>',
            unsafe_allow_html=True,
        )

        from multilingual import main as multilingual_main

        multilingual_main()
