import streamlit as st

# # Import the main() function from each application
# from financial_risk import main as financial_risk_main
# from esg import main as esg_main
# from multilingual import main as multilingual_main


# =========================================================
# PAGE CONFIG
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
LIGHT_BG = "#F5F7FA"


# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    f"""
    <style>

    /* ---------- Overall page ---------- */

    .stApp {{
        background: {LIGHT_BG};
    }}

    .block-container {{
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}


    /* ---------- Header ---------- */

    .portal-header {{
        background: linear-gradient(
            135deg,
            {BOB_NAVY} 0%,
            {BOB_BLUE} 100%
        );

        padding: 30px 38px;
        border-radius: 18px;
        color: white;
        margin-bottom: 35px;

        box-shadow: 0 8px 25px rgba(0, 46, 110, 0.18);
    }}

    .portal-header-title {{
        font-size: 34px;
        font-weight: 750;
        margin: 0;
        letter-spacing: -0.5px;
    }}

    .portal-header-subtitle {{
        font-size: 16px;
        margin-top: 8px;
        opacity: 0.88;
    }}


    /* ---------- Section title ---------- */

    .section-title {{
        color: {BOB_NAVY};
        font-size: 25px;
        font-weight: 700;
        margin-bottom: 4px;
    }}

    .section-subtitle {{
        color: #687385;
        font-size: 14px;
        margin-bottom: 25px;
    }}


    /* ---------- Application Card ---------- */

    .app-card {{
        background: white;
        border-radius: 18px;
        padding: 28px 26px 24px 26px;
        min-height: 330px;

        border: 1px solid #E6EAF0;
        border-top: 5px solid {BOB_ORANGE};

        box-shadow:
            0 5px 18px rgba(0, 0, 0, 0.06);

        transition:
            transform 0.2s ease,
            box-shadow 0.2s ease;

        margin-bottom: 8px;
    }}

    .app-card:hover {{
        transform: translateY(-4px);

        box-shadow:
            0 12px 28px rgba(0, 0, 0, 0.11);
    }}


    /* ---------- Icon ---------- */

    .app-icon {{
        width: 64px;
        height: 64px;

        display: flex;
        align-items: center;
        justify-content: center;

        background: #FFF3E5;
        border-radius: 16px;

        font-size: 32px;

        margin-bottom: 20px;
    }}


    /* ---------- Card content ---------- */

    .app-title {{
        color: {BOB_NAVY};
        font-size: 21px;
        font-weight: 700;

        line-height: 1.25;

        margin-bottom: 12px;
    }}

    .app-description {{
        color: #5E6877;
        font-size: 14px;

        line-height: 1.65;

        min-height: 72px;

        margin-bottom: 18px;
    }}


    /* ---------- Status ---------- */

    .status {{
        display: inline-flex;
        align-items: center;

        background: #EEF8F1;
        color: #287A3D;

        padding: 5px 11px;

        border-radius: 20px;

        font-size: 12px;
        font-weight: 600;

        margin-bottom: 14px;
    }}

    .status-dot {{
        width: 7px;
        height: 7px;

        background: #35A853;

        border-radius: 50%;

        margin-right: 6px;
    }}


    /* ---------- Streamlit buttons ---------- */

    div.stButton > button {{
        width: 100%;

        background: {BOB_ORANGE};
        color: white;

        border: none;
        border-radius: 9px;

        height: 45px;

        font-size: 14px;
        font-weight: 650;

        transition: all 0.2s ease;
    }}

    div.stButton > button:hover {{
        background: #E67E00;
        color: white;

        transform: translateY(-1px);

        box-shadow:
            0 5px 12px rgba(247, 148, 29, 0.25);
    }}


    /* ---------- Footer ---------- */

    .portal-footer {{
        text-align: center;

        color: #7A8492;

        font-size: 12px;

        margin-top: 40px;
        padding-top: 20px;

        border-top: 1px solid #E1E5EA;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================
st.markdown(
    """
    <div class="portal-header">

        <div class="portal-header-title">
            🏦 Bank of Baroda
        </div>

        <div class="portal-header-subtitle">
            AI & Emerging Technologies — Application Portal
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SECTION TITLE
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
# APPLICATION CARDS
# =========================================================

col1, col2, col3 = st.columns(3, gap="large")


# ---------------------------------------------------------
# CARD 1
# ---------------------------------------------------------
with col1:

    st.markdown(
        """
        <div class="app-card">

            <div class="app-icon">
                📊
            </div>

            <div class="app-title">
                AI Financial Risk & Reputation
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

    if st.button(
        "Open Application  →",
        key="open_financial_risk",
    ):
        st.session_state["selected_app"] = "financial_risk"
        st.rerun()


# ---------------------------------------------------------
# CARD 2
# ---------------------------------------------------------
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

    if st.button(
        "Open Application  →",
        key="open_esg",
    ):
        st.session_state["selected_app"] = "esg"
        st.rerun()


# ---------------------------------------------------------
# CARD 3
# ---------------------------------------------------------
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

    if st.button(
        "Open Application  →",
        key="open_multilingual",
    ):
        st.session_state["selected_app"] = "multilingual"
        st.rerun()


# =========================================================
# APPLICATION ROUTING
# =========================================================

selected_app = st.session_state.get("selected_app")


if selected_app:

    st.markdown("---")

    # Back button
    if st.button("← Back to Applications", key="back_to_portal"):
        st.session_state.pop("selected_app", None)
        st.rerun()

    st.markdown("")

    if selected_app == "financial_risk":
        financial_risk_main()

    elif selected_app == "esg":
        esg_main()

    elif selected_app == "multilingual":
        multilingual_main()


# =========================================================
# FOOTER
# =========================================================

if not selected_app:

    st.markdown(
        """
        <div class="portal-footer">
            Bank of Baroda&nbsp;&nbsp;|&nbsp;&nbsp;
            AI & Emerging Technologies
        </div>
        """,
        unsafe_allow_html=True,
    )
