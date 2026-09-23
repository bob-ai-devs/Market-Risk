import streamlit as st

# # =========================================================
# # IMPORT YOUR THREE APPLICATIONS
# # =========================================================
# from financial_risk import main as financial_risk_main
# from esg import main as esg_main
# from multilingual import main as multilingual_main


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="BOB AI Applications",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# BOB COLORS
# =========================================================
BOB_NAVY = "#002E6E"
BOB_BLUE = "#0059B3"
BOB_ORANGE = "#F7941D"
BOB_LIGHT_ORANGE = "#FFF3E5"

BACKGROUND = "#F5F7FA"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#667085"


# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    f"""
    <style>

    /* =====================================================
       PAGE
       ===================================================== */

    .stApp {{
        background-color: {BACKGROUND};
    }}

    .block-container {{
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}


    /* =====================================================
       HEADER
       ===================================================== */

    .portal-header {{
        background: linear-gradient(
            135deg,
            {BOB_NAVY} 0%,
            {BOB_BLUE} 100%
        );

        padding: 32px 40px;

        border-radius: 18px;

        color: white;

        margin-bottom: 36px;

        box-shadow:
            0 8px 25px rgba(0, 46, 110, 0.18);
    }}

    .portal-header-title {{
        font-size: 34px;
        font-weight: 750;
        line-height: 1.2;
        margin: 0;
    }}

    .portal-header-subtitle {{
        font-size: 16px;
        font-weight: 400;
        margin-top: 9px;
        opacity: 0.90;
    }}


    /* =====================================================
       SECTION
       ===================================================== */

    .section-title {{
        color: {BOB_NAVY};
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 4px;
    }}

    .section-subtitle {{
        color: {TEXT_MUTED};
        font-size: 14px;
        margin-bottom: 26px;
    }}


    /* =====================================================
       APPLICATION CARD
       ===================================================== */

    .app-card {{
        background-color: white;

        border-radius: 18px;

        padding: 28px 26px 24px 26px;

        min-height: 320px;

        border: 1px solid #E5E7EB;

        border-top: 5px solid {BOB_ORANGE};

        box-shadow:
            0 4px 15px rgba(0, 0, 0, 0.06);

        transition:
            transform 0.20s ease,
            box-shadow 0.20s ease;
    }}

    .app-card:hover {{
        transform: translateY(-5px);

        box-shadow:
            0 12px 30px rgba(0, 0, 0, 0.11);
    }}


    /* =====================================================
       ICON
       ===================================================== */

    .app-icon {{
        width: 66px;
        height: 66px;

        background-color: {BOB_LIGHT_ORANGE};

        border-radius: 16px;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 34px;

        margin-bottom: 20px;
    }}


    /* =====================================================
       CARD TITLE
       ===================================================== */

    .app-title {{
        color: {BOB_NAVY};

        font-size: 21px;

        font-weight: 700;

        line-height: 1.3;

        margin-bottom: 12px;
    }}


    /* =====================================================
       CARD DESCRIPTION
       ===================================================== */

    .app-description {{
        color: {TEXT_DARK};

        font-size: 14px;

        line-height: 1.65;

        min-height: 70px;

        margin-bottom: 17px;
    }}


    /* =====================================================
       STATUS
       ===================================================== */

    .status {{
        display: inline-flex;

        align-items: center;

        background-color: #ECFDF3;

        color: #18794E;

        padding: 5px 11px;

        border-radius: 20px;

        font-size: 12px;

        font-weight: 600;

        margin-bottom: 15px;
    }}

    .status-dot {{
        width: 7px;
        height: 7px;

        background-color: #22C55E;

        border-radius: 50%;

        margin-right: 7px;
    }}


    /* =====================================================
       OPEN BUTTON
       ===================================================== */

    div.stButton > button {{
        width: 100%;

        height: 45px;

        border-radius: 9px;

        border: none;

        background-color: {BOB_ORANGE};

        color: white;

        font-size: 14px;

        font-weight: 650;

        transition: all 0.2s ease;
    }}

    div.stButton > button:hover {{
        background-color: #E67E00;

        color: white;

        box-shadow:
            0 5px 15px rgba(247, 148, 29, 0.25);

        transform: translateY(-1px);
    }}


    /* =====================================================
       BACK BUTTON
       ===================================================== */

    div.stButton > button[kind="secondary"] {{
        border: 1px solid #D0D5DD;

        background-color: white;

        color: {BOB_NAVY};
    }}


    /* =====================================================
       FOOTER
       ===================================================== */

    .portal-footer {{
        text-align: center;

        color: #7A8492;

        font-size: 12px;

        margin-top: 45px;

        padding-top: 20px;

        border-top: 1px solid #E1E5EA;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
#
# IMPORTANT:
# The entire HTML is inside one st.markdown call and
# unsafe_allow_html=True is explicitly enabled.
# =========================================================

st.markdown(
    f"""
    <div class="portal-header">

        <div class="portal-header-title">
            🏦 Bank of Baroda
        </div>

        <div class="portal-header-subtitle">
            AI &amp; Emerging Technologies — Application Portal
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# APPLICATION SECTION
# =========================================================

st.markdown(
    """
    <div class="section-title">
        AI Applications
    </div>

    <div class="section-subtitle">
        Select an application to continue
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CHECK WHICH APPLICATION IS SELECTED
# =========================================================

selected_app = st.session_state.get("selected_app", None)


# =========================================================
# PORTAL HOME PAGE
# =========================================================

if selected_app is None:

    # -----------------------------------------------------
    # THREE COLUMNS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(
        3,
        gap="large"
    )


    # =====================================================
    # FINANCIAL RISK CARD
    # =====================================================

    with col1:

        st.markdown(
            """
            <div class="app-card">

                <div class="app-icon">
                    📊
                </div>

                <div class="app-title">
                    AI Financial Risk &amp; Reputation
                </div>

                <div class="app-description">
                    Analyze financial performance, market indicators,
                    news sentiment, reputation signals and
                    company-level financial risk.
                </div>

                <div class="status">
                    <span class="status-dot"></span>
                    Application Available
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:8px'></div>",
                    unsafe_allow_html=True)

        if st.button(
            "Open Application  →",
            key="open_financial_risk",
        ):
            st.session_state["selected_app"] = "financial_risk"
            st.rerun()


    # =====================================================
    # ESG CARD
    # =====================================================

    with col2:

        st.markdown(
            """
            <div class="app-card">

                <div class="app-icon">
                    🌱
                </div>

                <div class="app-title">
                    AI ESG Analytics
                </div>

                <div class="app-description">
                    Monitor Environmental, Social and Governance
                    indicators using AI-powered news analysis,
                    sentiment and ESG scoring.
                </div>

                <div class="status">
                    <span class="status-dot"></span>
                    Application Available
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:8px'></div>",
                    unsafe_allow_html=True)

        if st.button(
            "Open Application  →",
            key="open_esg",
        ):
            st.session_state["selected_app"] = "esg"
            st.rerun()


    # =====================================================
    # MULTILINGUAL CARD
    # =====================================================

    with col3:

        st.markdown(
            """
            <div class="app-card">

                <div class="app-icon">
                    🌐
                </div>

                <div class="app-title">
                    AI Multilingual Product Assistant
                </div>

                <div class="app-description">
                    Interact with banking products using
                    multilingual AI, speech recognition,
                    translation and intelligent assistance.
                </div>

                <div class="status">
                    <span class="status-dot"></span>
                    Application Available
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:8px'></div>",
                    unsafe_allow_html=True)

        if st.button(
            "Open Application  →",
            key="open_multilingual",
        ):
            st.session_state["selected_app"] = "multilingual"
            st.rerun()


    # =====================================================
    # FOOTER
    # =====================================================

    st.markdown(
        """
        <div class="portal-footer">
            Bank of Baroda &nbsp;|&nbsp;
            AI &amp; Emerging Technologies
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# FINANCIAL RISK APPLICATION
# =========================================================

elif selected_app == "financial_risk":

    if st.button(
        "← Back to Applications",
        key="back_financial_risk",
    ):
        st.session_state.pop("selected_app", None)
        st.rerun()

    st.markdown("")

    financial_risk_main()


# =========================================================
# ESG APPLICATION
# =========================================================

elif selected_app == "esg":

    if st.button(
        "← Back to Applications",
        key="back_esg",
    ):
        st.session_state.pop("selected_app", None)
        st.rerun()

    st.markdown("")

    esg_main()


# =========================================================
# MULTILINGUAL APPLICATION
# =========================================================

elif selected_app == "multilingual":

    if st.button(
        "← Back to Applications",
        key="back_multilingual",
    ):
        st.session_state.pop("selected_app", None)
        st.rerun()

    st.markdown("")

    multilingual_main()
