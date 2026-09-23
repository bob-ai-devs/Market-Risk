import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

from datetime import datetime, timedelta
from google import genai


# ============================================================
# NSE INDEX TICKERS
# ============================================================

NSE_INDICES = {
    "Nifty 50": "^NSEI",
    "Nifty IT": "^CNXIT",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty Bank": "^NSEBANK",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Energy": "^CNXENERGY",
    "Nifty Metal": "^CNXMETAL",
    "Nifty Realty": "^CNXREALTY",
    "Nifty Media": "^CNXMEDIA",
    "Nifty Infra": "^CNXINFRA",
    "Nifty Consumption": "^CNXCONSUM",
    "Nifty Commodity": "^CNXCMDT",
    "Nifty MNC": "^CNXMNC",
    "Nifty PSU Bank": "^CNXPSUBANK",
    "Nifty PSE": "^CNXPSE",
    "Nifty Services": "^CNXSERVICE",
}


# ============================================================
# TIME INTERVALS
# ============================================================

INTERVAL_CONFIG = {
    "1D": {
        "days_back": 1,
        "type": "trading",
    },
    "5D": {
        "days_back": 5,
        "type": "trading",
    },
    "10D": {
        "days_back": 10,
        "type": "trading",
    },
    "1M": {
        "days_back": 30,
        "type": "calendar",
    },
    "3M": {
        "days_back": 90,
        "type": "calendar",
    },
    "6M": {
        "days_back": 180,
        "type": "calendar",
    },
    "1Y": {
        "days_back": 365,
        "type": "calendar",
    },
    "2Y": {
        "days_back": 730,
        "type": "calendar",
    },
    "3Y": {
        "days_back": 1095,
        "type": "calendar",
    },
}


# ============================================================
# FETCH NSE INDEX DATA
# ============================================================

def fetch_change_data():

    results = {}

    for index_name, ticker in NSE_INDICES.items():

        try:

            df = yf.download(
                ticker,
                period="max",
                interval="1d",
                progress=False,
            )

            if df.empty:
                results[index_name] = {
                    label: None
                    for label in INTERVAL_CONFIG
                }
                continue

            close_series = df["Close"].dropna().sort_index()

            if close_series.empty:
                results[index_name] = {
                    label: None
                    for label in INTERVAL_CONFIG
                }
                continue

            # Handle possible DataFrame returned by yfinance
            if isinstance(close_series, pd.DataFrame):
                close_series = close_series.iloc[:, 0]

            last_date = close_series.index[-1]
            current_price = float(close_series.iloc[-1])

            earliest_date = close_series.index[0]

            changes = {}

            for label, cfg in INTERVAL_CONFIG.items():

                days_needed = cfg["days_back"]

                # --------------------------------------------
                # Trading-day intervals
                # --------------------------------------------

                if cfg["type"] == "trading":

                    if len(close_series) > days_needed:

                        past_price = float(
                            close_series.iloc[-(days_needed + 1)]
                        )

                    else:

                        past_price = float(
                            close_series.iloc[0]
                        )

                # --------------------------------------------
                # Calendar-day intervals
                # --------------------------------------------

                else:

                    target_date = (
                        last_date
                        - timedelta(days=days_needed)
                    )

                    if target_date < earliest_date:

                        past_price = float(
                            close_series.iloc[0]
                        )

                    else:

                        nearest = close_series[
                            close_series.index <= target_date
                        ]

                        if not nearest.empty:

                            past_price = float(
                                nearest.iloc[-1]
                            )

                        else:

                            past_price = float(
                                close_series.iloc[0]
                            )

                # --------------------------------------------
                # Percentage change
                # --------------------------------------------

                if past_price != 0:

                    change = (
                        (current_price - past_price)
                        / past_price
                    ) * 100

                    changes[label] = round(
                        change,
                        2,
                    )

                else:

                    changes[label] = None

            results[index_name] = changes

        except Exception:

            results[index_name] = {
                label: None
                for label in INTERVAL_CONFIG
            }

    return pd.DataFrame(
        results
    ).T.astype(float)


# Single interval bar plot
def plot_single_bar(df, interval):
    st.subheader(f"📊 NSE Index % Change: {interval}")
    df_sorted = df[[interval]].dropna().sort_values(interval, ascending=False)
    fig = go.Figure(go.Bar(
        x=df_sorted.index,
        y=df_sorted[interval],
        text=[f"{v:.2f}%" for v in df_sorted[interval]],
        textposition="auto",
        marker_color="royalblue"
    ))
    fig.update_layout(yaxis_title="% Change", xaxis_title="Index", xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# Multiple interval grouped bar plot
def plot_grouped(df, intervals):
    st.subheader("📊 Grouped Index % Changes")
    df_sorted = df[intervals].dropna().sort_values(intervals[0], ascending=False)
    fig = go.Figure()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for i, label in enumerate(intervals):
        fig.add_trace(go.Bar(
            x=df_sorted.index,
            y=df_sorted[label],
            name=label,
            marker_color=colors[i % len(colors)],
            text=[f"{v:.2f}%" for v in df_sorted[label]],
            textposition="auto"
        ))
    fig.update_layout(barmode="group", yaxis_title="% Change", xaxis_title="Index", xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # --------------------------------------------------------
    # PAGE TITLE
    # --------------------------------------------------------

    st.title(
        "📈 NSE Index Analyzer"
    )

    # --------------------------------------------------------
    # GEMINI CLIENT
    # --------------------------------------------------------

    try:

        gemini_api = st.secrets["GEMINI_API_KEY"]

        client = genai.Client(
            api_key=gemini_api
        )

    except Exception as e:

        st.error(
            "Gemini API key is not configured correctly."
        )

        st.caption(
            f"Error: {e}"
        )

        client = None

    # --------------------------------------------------------
    # TIME PERIOD SELECTION
    # --------------------------------------------------------

    selected_intervals = st.multiselect(
        "Select time periods to display:",
        options=list(
            INTERVAL_CONFIG.keys()
        ),
        default=["1D"],
        key="index_analyzer_intervals",
    )

    # --------------------------------------------------------
    # SESSION STATE
    # --------------------------------------------------------

    if "index_analyzer_response" not in st.session_state:

        st.session_state.index_analyzer_response = ""

    # --------------------------------------------------------
    # LOAD NSE DATA ONLY ONCE PER SESSION
    # --------------------------------------------------------

    if (
        "index_analyzer_change_df"
        not in st.session_state
    ):

        with st.spinner(
            "Fetching NSE index data..."
        ):

            st.session_state.index_analyzer_change_df = (
                fetch_change_data()
            )

            st.session_state.index_analyzer_response = ""

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    change_df = (
        st.session_state.index_analyzer_change_df
    )

    # Sort by 1D
    if "1D" in change_df.columns:

        change_df = change_df.sort_values(
            by="1D",
            ascending=False,
        )

    # --------------------------------------------------------
    # RAW DATA TABLE
    # --------------------------------------------------------

    with st.expander(
        "📋 View Raw % Change Table"
    ):

        styled = (
            change_df.style
            .format(
                lambda x:
                f"{x:.2f}%"
                if pd.notnull(x)
                else "NA"
            )
            .background_gradient(
                cmap="RdYlGn",
                vmin=-20,
                vmax=20,
                axis=None,
            )
        )

        st.dataframe(
            styled,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # AI QUERY SECTION
    # --------------------------------------------------------

    st.header("🔎 AI Query")

    # --------------------------------------------------------
    # GET AVAILABLE GEMINI MODELS
    # --------------------------------------------------------

    # gen_models = []

    gen_models = ['gemini-flash-lite-latest', 'gemini-flash-lite']

    # if client is not None:

    #     try:

    #         for model in client.models.list():

    #             model_name = getattr(
    #                 model,
    #                 "name",
    #                 "",
    #             )

    #             # Keep only models that support
    #             # generateContent
    #             actions = getattr(
    #                 model,
    #                 "supported_actions",
    #                 [],
    #             )

    #             if (
    #                 "generateContent" in actions
    #                 or not actions
    #             ):

    #                 if model_name:

    #                     gen_models.append(
    #                         model_name
    #                     )

    #     except Exception as e:

    #         st.warning(
    #             f"Unable to retrieve Gemini models: {e}"
    #         )

    # --------------------------------------------------------
    # MODEL SELECTION
    # --------------------------------------------------------

    selected_model = None

    if gen_models:

        selected_model = st.selectbox(
            "Choose AI Model",
            options=gen_models,
            index=0,
            key="index_analyzer_model",
        )

    else:

        st.warning(
            "No Gemini models are available."
        )

    # --------------------------------------------------------
    # USER PROMPT
    # --------------------------------------------------------

    user_prompt = st.text_area(
        "Enter your prompt",
        placeholder=(
            "Type your query here..."
        ),
        max_chars=1000,
        key="index_analyzer_prompt",
    )

    # --------------------------------------------------------
    # SUBMIT AI QUERY
    # --------------------------------------------------------

    if st.button(
        "Submit",
        key="index_analyzer_submit",
    ):

        if not user_prompt.strip():

            st.error(
                "Please enter a prompt before submitting."
            )

        elif client is None:

            st.error(
                "Gemini client is not available."
            )

        elif not selected_model:

            st.error(
                "Please select a Gemini model."
            )

        else:

            with st.spinner(
                "Getting analysis..."
            ):

                try:

                    # ----------------------------------------
                    # Prepare financial data
                    # ----------------------------------------

                    data_df = (
                        change_df
                        .reset_index()
                        .rename(
                            columns={
                                "index":
                                "Index Name"
                            }
                        )
                    )

                    finance_data_json = (
                        data_df.to_json(
                            orient="records"
                        )
                    )

                    # ----------------------------------------
                    # Gemini prompt
                    # ----------------------------------------

                    final_prompt = f"""
You are a financial data analyst.

You are given percentage-change data
for NSE indices.

Data format:
JSON list of index names and their
percentage change for selected intervals.

Data:
{finance_data_json}

User question:
{user_prompt}

Provide a clear and concise analysis
based strictly on the supplied data.

Highlight relevant index movements,
comparisons and trends.

Provide a suitable financial conclusion
based on the available data.

Do not invent data that is not present
in the supplied dataset.
"""

                    # ----------------------------------------
                    # New Gemini SDK
                    # ----------------------------------------

                    response = client.models.generate_content(
                        model=selected_model,
                        contents=final_prompt,
                    )

                    st.session_state.index_analyzer_response = (
                        response.text
                        if response.text
                        else "No response received from Gemini."
                    )

                except Exception as e:

                    st.session_state.index_analyzer_response = ""

                    st.error(
                        f"Gemini analysis failed: {e}"
                    )

    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    if (
        st.session_state.index_analyzer_response
    ):

        with st.expander(
            "📊 AI Analysis Result",
            expanded=True,
        ):

            st.markdown(
                f"**Model Used:** `{selected_model}`"
            )

            st.write(
                st.session_state.index_analyzer_response
            )

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    if selected_intervals:

        if len(selected_intervals) == 1:

            plot_single_bar(
                change_df,
                selected_intervals[0],
            )

        else:

            plot_grouped(
                change_df,
                selected_intervals,
            )

    else:

        st.warning(
            "⚠️ Please select at least one time interval."
        )


# ============================================================
# STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":
    main()
