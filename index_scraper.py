"""
StockAlert — Streamlit port of the original Flask/Colab app.

Run locally:      streamlit run app.py
Run from elsewhere (e.g. a multipage router / another script that is itself
launched with `streamlit run`):

    import app
    app.main()

`main()` contains the entire UI and is idempotent-safe to call more than
once per session (guards st.set_page_config and session_state init), so it
is fine to import and invoke from another Streamlit entry point.
"""

import datetime
import io
import os
import time

import pandas as pd
import pytz
import streamlit as st

from index_config import CATEGORY_DISPLAY_NAMES, CATEGORY_LABELS, INDEX_NAMES_FETCH, VIEW_LABELS
from stock_analytics import build_stock_table, extract_flags, text_to_html
from genai_utils import DEFAULT_MODEL, generate_text, get_client, list_model_names

IST = pytz.timezone("Asia/Kolkata")

METHODOLOGY_NOTE = """
The table's key columns are:
- '% Change <N>DMA': how far the current price sits above/below its N-day moving average.
- 'Rank for Selling (1M)' / 'Rank for Holding (3M/6M/1Y)' / 'Rank for Long Term Holding (2Y/3Y)':
  dense ranks (1 = strongest) of stocks by their respective %-change-vs-moving-average.
- 'Recent Performance Rank' = 3x(1Y rank) + 2x(2Y rank) + 1x(3Y rank); lower is better.
- 'Historical Performance Rank' = 1x(1Y rank) + 2x(2Y rank) + 3x(3Y rank); lower is better.
- Momentum view columns ('<N>DMoM') are volume-weighted rate-of-change over N days.
""".strip()


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------

def _init_state():
    defaults = {
        "full_df": pd.DataFrame(),
        "final_df": pd.DataFrame(),
        "task_name": "",
        "generated_at": "",
        "curr_flag": "",
        "hist_flag": "",
        "new_green": [],
        "new_red": [],
        "last_selection": None,
        "ai_report_html": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --------------------------------------------------------------------------
# Gemini helpers
# --------------------------------------------------------------------------

def _api_key() -> str:
    try:
        return st.secrets.get("GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")


@st.cache_resource(show_spinner=False)
def _cached_client(api_key: str):
    return get_client(api_key)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_model_names(api_key: str):
    return list_model_names(get_client(api_key))


# --------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------

def _resolve_index_selection(category: str, display_name: str) -> str:
    """Map (category, display name) -> internal `name` used by build_stock_table."""
    if category in ("etf", "nasdaq"):
        return display_name.lower()
    return INDEX_NAMES_FETCH[display_name.lower()]


def _to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()


def _run_analysis(category: str, name: str, view_value: str, pred_value: str):
    progress_bar = st.progress(0.0)
    status = st.empty()

    def on_progress(done, total, elapsed):
        pct = (done / total) if total else 1.0
        remaining = (elapsed / done) * (total - done) if done else 0
        progress_bar.progress(min(pct, 1.0))
        status.caption(f"Progress: {pct * 100:.1f}%  ·  ~{remaining:.0f}s remaining")

    try:
        with st.spinner("Fetching market data and computing indicators…"):
            df = build_stock_table(category, name, view_value, pred_value, progress_callback=on_progress)
    except FileNotFoundError as exc:
        progress_bar.empty()
        status.empty()
        st.error(str(exc))
        return
    finally:
        progress_bar.empty()
        status.empty()

    if df.empty:
        st.warning("No data could be retrieved for this selection.")
        return

    df.index += 1

    st.session_state["full_df"] = df
    st.session_state["final_df"] = df.copy()
    st.session_state["task_name"] = name
    st.session_state["generated_at"] = (
        datetime.datetime.now(pytz.utc).astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
    )
    # Equivalent of the old `reset_flag=1` behaviour: a fresh selection
    # clears AI flag history so old/new comparisons start over.
    st.session_state["curr_flag"] = ""
    st.session_state["hist_flag"] = ""
    st.session_state["new_green"] = []
    st.session_state["new_red"] = []
    st.session_state["ai_report_html"] = ""


def _run_ai_report(prompt: str, model_name: str):
    client = _cached_client(_api_key())
    final_df = st.session_state["final_df"]
    full_prompt = f"""
You are an expert financial analyst and report writer.

Below is a DataFrame containing share market analysis data:

{final_df.to_string()}

Methodology reference:
{METHODOLOGY_NOTE}

The user has provided the following prompt for analysis:
"{prompt}"

Please generate a professional, detailed report strictly based on the user's prompt and
recent Global & Indian Macroeconomic trends. Use the data provided as needed, but your
response must align fully with the intent and focus of the prompt.

Your report should:
- Address exactly what the prompt is asking.
- Be data-backed, citing figures or patterns from the DataFrame where relevant.
- Use a clear, structured format with headings and bullet points if suitable.
- Maintain a professional and analytical tone.
- Avoid adding unrelated analysis or generic summaries.

Do not explain what the data is — jump straight into prompt-specific insights and interpretations.
Begin your response now.
""".strip()

    with st.spinner("Generating AI report…"):
        response_text = generate_text(client, full_prompt, model_name)
    st.session_state["ai_report_html"] = text_to_html(response_text)


def _run_ai_flagging(model_name: str):
    client = _cached_client(_api_key())
    final_df = st.session_state["final_df"]
    flag_prompt = f"""
Analyze the following share market data:
{final_df.to_string()}

Methodology reference:
{METHODOLOGY_NOTE}

Please consider recent Global & Indian Macroeconomic trends.

Based on all above conditions and macroeconomic trends, identify the top 10% (maximum 5 in
count) of stocks (including ticker symbols) in each category:

- <span style="color:green">Green Flag</span>: Strong Buy signals overall (significant momentum
  growth, undervalued, sound fundamentals by ranks, opportunity).
- <span style="color:red">Red Flag</span>: Strong Sell signals overall (significant momentum
  decline, poor fundamentals by ranks, risk).

Evaluate each stock as a whole, not column-wise.

Output format:
1. <b>Green Flag Stocks</b>: List items with reasons.
2. <b>Red Flag Stocks</b>: List items with reasons.

Wrap the full "Stock Name (TICKER)" inside:
- <span style="color:green">Stock Name (TICKER)</span>
- <span style="color:red">Stock Name (TICKER)</span>

Do not include the full dataset, headers, or explanations — only the result.
""".strip()

    with st.spinner("Running AI flag analysis…"):
        ai_response = generate_text(client, flag_prompt, model_name)

    if st.session_state["curr_flag"]:
        st.session_state["hist_flag"] = st.session_state["curr_flag"]
    st.session_state["curr_flag"] = ai_response

    (curr_green, curr_green_map), (curr_red, curr_red_map) = extract_flags(ai_response)
    (hist_green, _), (hist_red, _) = extract_flags(st.session_state["hist_flag"])

    new_green_tickers = curr_green - hist_green
    new_red_tickers = curr_red - hist_red

    st.session_state["new_green"] = [curr_green_map[t] for t in new_green_tickers]
    st.session_state["new_red"] = [curr_red_map[t] for t in new_red_tickers]


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------

def main():
    try:
        st.set_page_config(page_title="StockAlert", page_icon="📈", layout="wide")
    except Exception:
        # set_page_config can only be called once per session; ignore if a
        # host script already called it before importing this module.
        pass

    _init_state()

    st.markdown(
        """
        <div id="bob-banner">
            <h1>📈 Index Scraper</h1>
            <p>Market intelligence • Moving-average, momentum and AI-driven stock screening</p>
        </div>
        """, unsafe_allow_html=True
    )

    api_key = _api_key()
    if not api_key:
        st.warning(
            "No `GEMINI_API_KEY` found in `st.secrets` or the environment. "
            "The table/screening tools will still work; AI report & flagging will not."
        )

    with st.expander("Formulas & ranking methodology"):
        st.markdown(
            "**20-Day Momentum (volume-weighted ROC):**\n\n"
            r"$$\text{Weighted ROC}_t^{(20)} = \frac{\sum_{i=t-19}^{t}\left(\frac{P_i-P_{i-1}}{P_{i-1}}\times V_i\right)}"
            r"{\sum_{i=t-19}^{t} V_i}\times 100$$"
        )
        st.markdown(METHODOLOGY_NOTE)

    # ---- Selection controls -------------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        view_label = st.radio("Select View Type", list(VIEW_LABELS.values()), horizontal=True)
        view_value = next(k for k, v in VIEW_LABELS.items() if v == view_label)
    with col2:
        pred_label = st.radio(
            "Analyst Prediction",
            ["Don't Want Future Prediction", "Future Prediction"],
            horizontal=True,
        )
        pred_value = "yes" if pred_label == "Future Prediction" else "no"
        if pred_value == "yes":
            st.caption(
                "⚠️ Future-prediction pulls best-effort analyst-estimate data from a "
                "third-party page per stock — it's slower and can silently skip stocks "
                "if that page is unavailable."
            )

    col3, col4 = st.columns(2)
    with col3:
        category = st.selectbox(
            "Choose a category",
            options=list(CATEGORY_LABELS.keys()),
            format_func=lambda k: CATEGORY_LABELS[k],
        )
    with col4:
        display_options = CATEGORY_DISPLAY_NAMES[category]
        display_name = st.selectbox("Choose an index", options=display_options)

    col5, col6 = st.columns(2)
    with col5:
        ai_flagging = st.radio("AI Flagging", ["Not Needed", "Needed"], horizontal=True)
    with col6:
        model_names = _cached_model_names(api_key) if api_key else []
        model_name = st.selectbox("AI model", options=["Default Model"] + model_names)
        model_name = "" if model_name == "Default Model" else model_name

    run_clicked = st.button("Run Analysis", type="primary")

    if run_clicked:
        name = _resolve_index_selection(category, display_name)
        st.session_state["last_selection"] = (category, name, view_value, pred_value)
        _run_analysis(category, name, view_value, pred_value)

    # ---- Results --------------------------------------------------------
    final_df = st.session_state["final_df"]
    if not final_df.empty:
        st.subheader(f"Results: {st.session_state['task_name'].upper()}")
        st.caption(f"Generated at: {st.session_state['generated_at']} (IST)")
        st.dataframe(final_df, use_container_width=True, height=520)

        dl_col, ai_flag_col = st.columns([1, 3])
        with dl_col:
            st.download_button(
                "⬇️ Download as Excel",
                data=_to_xlsx_bytes(final_df),
                file_name=f"{st.session_state['task_name']}_{st.session_state['generated_at'].replace(':', '-')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        if ai_flagging == "Needed":
            with ai_flag_col:
                if st.button("Run AI Flagging"):
                    if not api_key:
                        st.error("Add GEMINI_API_KEY to secrets first.")
                    else:
                        _run_ai_flagging(model_name)

            if st.session_state["new_green"] or st.session_state["new_red"]:
                st.toast("New AI flags detected!", icon="🚩")
                with st.container(border=True):
                    st.markdown("**New flags since the last run**")
                    for item in st.session_state["new_green"]:
                        st.markdown(f"🟢 {item}", unsafe_allow_html=True)
                    for item in st.session_state["new_red"]:
                        st.markdown(f"🔴 {item}", unsafe_allow_html=True)

            if st.session_state["curr_flag"]:
                with st.expander("AI-Based Stock Risk and Opportunity Flags (Current)", expanded=True):
                    st.markdown(text_to_html(st.session_state["curr_flag"]), unsafe_allow_html=True)
            if st.session_state["hist_flag"]:
                with st.expander("AI-Based Stock Risk and Opportunity Flags (Historical)"):
                    st.markdown(text_to_html(st.session_state["hist_flag"]), unsafe_allow_html=True)

        st.divider()
        st.subheader("AI Analysis Report")
        prompt = st.text_input(
            "Enter AI Prompt",
            placeholder="5 Stocks which are undervalued but a good long-term buy",
        )
        if st.button("Generate AI Report"):
            if not api_key:
                st.error("Add GEMINI_API_KEY to secrets first.")
            elif not prompt.strip():
                st.error("Enter a prompt first.")
            else:
                _run_ai_report(prompt, model_name)

        if st.session_state["ai_report_html"]:
            with st.container(border=True):
                st.markdown("**Insight Report Generated from User Prompt**")
                st.markdown(st.session_state["ai_report_html"], unsafe_allow_html=True)
    else:
        st.info("Pick a category and index above, then click **Run Analysis**.")


if __name__ == "__main__":
    main()
