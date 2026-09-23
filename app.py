import streamlit as st

st.set_page_config(
    page_title="BOB AI Applications",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 Bank of Baroda")
st.subheader("AI & Emerging Technologies — Application Portal")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 Financial Risk")
    st.write(
        "AI-powered financial risk and reputation analysis."
    )

    if st.button(
        "Open Application →",
        key="financial",
        use_container_width=True,
    ):
        st.session_state["app"] = "financial"

with col2:
    st.subheader("🌱 ESG Analytics")
    st.write(
        "AI-powered Environmental, Social and Governance analysis."
    )

    if st.button(
        "Open Application →",
        key="esg",
        use_container_width=True,
    ):
        st.session_state["app"] = "esg"

with col3:
    st.subheader("🌐 Multilingual AI")
    st.write(
        "Multilingual AI assistant for banking products."
    )

    if st.button(
        "Open Application →",
        key="multilingual",
        use_container_width=True,
    ):
        st.session_state["app"] = "multilingual"
