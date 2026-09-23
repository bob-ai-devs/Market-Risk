import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

from datetime import timedelta
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
# FETCH SINGLE INDEX
# ============================================================

def fetch_single_index(
    index_name: str,
    ticker: str,
    retries: int = 2,
):
    """
    Download one NSE index and calculate percentage changes.

    Returns:
        dict containing calculated interval changes.

    Returns None when data cannot be retrieved.
    """

    last_error = None

    for attempt in range(retries + 1):

        try:

            df = yf.download(
                ticker,
                period="max",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            # ------------------------------------------------
            # No data
            # ------------------------------------------------

            if df is None or df.empty:

                last_error = (
                    "Yahoo Finance returned no data"
                )

                continue

            # ------------------------------------------------
            # Extract Close safely
            # ------------------------------------------------

            if isinstance(
                df.columns,
                pd.MultiIndex,
            ):

                # Typical yfinance structure:
                #
                # Price       Close
                # Ticker      ^NSEI
                #
                if "Close" not in df.columns.get_level_values(
                    0
                ):

                    last_error = (
                        "Close column not found"
                    )

                    continue

                close_series = df["Close"]

                # If still a DataFrame,
                # select the first ticker column.
                if isinstance(
                    close_series,
                    pd.DataFrame,
                ):

                    if ticker in close_series.columns:

                        close_series = (
                            close_series[ticker]
                        )

                    else:

                        close_series = (
                            close_series.iloc[:, 0]
                        )

            else:

                if "Close" not in df.columns:

                    last_error = (
                        "Close column not found"
                    )

                    continue

                close_series = df["Close"]

            # ------------------------------------------------
            # Convert to numeric
            # ------------------------------------------------

            close_series = pd.to_numeric(
                close_series,
                errors="coerce",
            )

            close_series = (
                close_series
                .dropna()
                .sort_index()
            )

            if close_series.empty:

                last_error = (
                    "Close series is empty"
                )

                continue

            # ------------------------------------------------
            # Current value
            # ------------------------------------------------

            current_price = float(
                close_series.iloc[-1]
            )

            last_date = close_series.index[-1]

            earliest_date = close_series.index[0]

            changes = {}

            # ------------------------------------------------
            # Calculate each interval
            # ------------------------------------------------

            for label, config in INTERVAL_CONFIG.items():

                days_needed = config["days_back"]

                # ============================================
                # Trading-day intervals
                # ============================================

                if config["type"] == "trading":

                    if len(close_series) > days_needed:

                        past_price = float(
                            close_series.iloc[
                                -(days_needed + 1)
                            ]
                        )

                    else:

                        past_price = float(
                            close_series.iloc[0]
                        )

                # ============================================
                # Calendar-day intervals
                # ============================================

                else:

                    target_date = (
                        last_date
                        - timedelta(
                            days=days_needed
                        )
                    )

                    if target_date < earliest_date:

                        past_price = float(
                            close_series.iloc[0]
                        )

                    else:

                        nearest = close_series[
                            close_series.index <= target_date
                        ]

                        if nearest.empty:

                            past_price = float(
                                close_series.iloc[0]
                            )

                        else:

                            past_price = float(
                                nearest.iloc[-1]
                            )

                # ============================================
                # Percentage change
                # ============================================

                if past_price == 0:

                    changes[label] = None

                else:

                    percentage_change = (
                        (
                            current_price
                            - past_price
                        )
                        / past_price
                    ) * 100

                    changes[label] = round(
                        percentage_change,
                        2,
                    )

            return {
                "changes": changes,
                "records": len(close_series),
                "latest_price": current_price,
                "latest_date": last_date,
                "error": None,
            }

        except Exception as e:

            last_error = (
                f"{type(e).__name__}: {e}"
            )

    # --------------------------------------------------------
    # All attempts failed
    # --------------------------------------------------------

    return {
        "changes": {
            label: None
            for label in INTERVAL_CONFIG
        },
        "records": 0,
        "latest_price": None,
        "latest_date": None,
        "error": last_error,
    }


# ============================================================
# FETCH ALL NSE INDICES
# ============================================================

def fetch_change_data():

    results = {}

    failed_indices = []

    progress = st.progress(
        0,
        text="Fetching NSE index data...",
    )

    total = len(NSE_INDICES)

    for position, (
        index_name,
        ticker,
    ) in enumerate(
        NSE_INDICES.items(),
        start=1,
    ):

        progress.progress(
            position / total,
            text=(
                f"Fetching {index_name} "
                f"({position}/{total})..."
            ),
        )

        result = fetch_single_index(
            index_name,
            ticker,
            retries=2,
        )

        if result is None:

            results[index_name] = {
                label: None
                for label in INTERVAL_CONFIG
            }

            failed_indices.append(
                (
                    index_name,
                    ticker,
                    "Unknown error",
                )
            )

            continue

        results[index_name] = result["changes"]

        if result["error"]:

            failed_indices.append(
                (
                    index_name,
                    ticker,
                    result["error"],
                )
            )

    progress.empty()

    change_df = pd.DataFrame(
        results
    ).T

    # Make sure every interval exists
    for interval in INTERVAL_CONFIG:

        if interval not in change_df.columns:

            change_df[interval] = None

    # Maintain interval order
    change_df = change_df[
        list(INTERVAL_CONFIG.keys())
    ]

    change_df = change_df.astype(float)

    return change_df, failed_indices


# ============================================================
# SINGLE INTERVAL BAR CHART
# ============================================================

def plot_single_bar(
    df: pd.DataFrame,
    interval: str,
):

    st.subheader(
        f"📊 NSE Index % Change: {interval}"
    )

    df_sorted = (
        df[[interval]]
        .dropna()
        .sort_values(
            interval,
            ascending=False,
        )
    )

    if df_sorted.empty:

        st.info(
            f"No data available for {interval}."
        )

        return

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_sorted.index,
            y=df_sorted[interval],
            text=[
                f"{value:.2f}%"
                for value in df_sorted[interval]
            ],
            textposition="auto",
            marker_color="#0059B3",
        )
    )

    fig.update_layout(
        yaxis_title="% Change",
        xaxis_title="Index",
        xaxis_tickangle=-45,
        height=500,
        margin=dict(
            l=40,
            r=20,
            t=50,
            b=120,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# GROUPED BAR CHART
# ============================================================

def plot_grouped(
    df: pd.DataFrame,
    intervals: list,
):

    st.subheader(
        "📊 Grouped Index % Changes"
    )

    available_intervals = [
        interval
        for interval in intervals
        if interval in df.columns
    ]

    if not available_intervals:

        st.info(
            "No data available for the selected periods."
        )

        return

    df_sorted = (
        df[available_intervals]
        .dropna(
            how="all"
        )
        .sort_values(
            available_intervals[0],
            ascending=False,
            na_position="last",
        )
    )

    if df_sorted.empty:

        st.info(
            "No data available for the selected periods."
        )

        return

    colors = [
        "#0059B3",
        "#F7941D",
        "#2CA02C",
        "#D62728",
        "#9467BD",
    ]

    fig = go.Figure()

    for i, label in enumerate(
        available_intervals
    ):

        fig.add_trace(
            go.Bar(
                x=df_sorted.index,
                y=df_sorted[label],
                name=label,
                marker_color=colors[
                    i % len(colors)
                ],
                text=[
                    (
                        f"{value:.2f}%"
                        if pd.notna(value)
                        else ""
                    )
                    for value in df_sorted[label]
                ],
                textposition="auto",
            )
        )

    fig.update_layout(
        barmode="group",
        yaxis_title="% Change",
        xaxis_title="Index",
        xaxis_tickangle=-45,
        height=550,
        margin=dict(
            l=40,
            r=20,
            t=50,
            b=120,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # ========================================================
    # TITLE
    # ========================================================

    st.title(
        "📈 NSE Index Analyzer"
    )

    st.caption(
        "Analyze performance across major NSE indices "
        "and generate AI-powered insights."
    )

    # ========================================================
    # TIME PERIOD SELECTION
    # ========================================================

    selected_intervals = st.multiselect(
        "Select time periods to display:",
        options=list(
            INTERVAL_CONFIG.keys()
        ),
        default=["1D"],
        key="index_analyzer_intervals",
    )

    # ========================================================
    # SESSION STATE
    # ========================================================

    if (
        "index_analyzer_change_df"
        not in st.session_state
    ):

        st.session_state.index_analyzer_change_df = None

    if (
        "index_analyzer_failed"
        not in st.session_state
    ):

        st.session_state.index_analyzer_failed = []

    if (
        "index_analyzer_response"
        not in st.session_state
    ):

        st.session_state.index_analyzer_response = ""

    # ========================================================
    # REFRESH / LOAD DATA
    # ========================================================

    refresh_clicked = st.button(
        "🔄 Refresh NSE Data",
        key="index_analyzer_refresh",
    )

    if (
        st.session_state.index_analyzer_change_df is None
        or refresh_clicked
    ):

        with st.spinner(
            "Fetching latest NSE index data..."
        ):

            (
                new_df,
                failed_indices,
            ) = fetch_change_data()

            st.session_state.index_analyzer_change_df = (
                new_df
            )

            st.session_state.index_analyzer_failed = (
                failed_indices
            )

            st.session_state.index_analyzer_response = ""

    # ========================================================
    # DATA
    # ========================================================

    change_df = (
        st.session_state.index_analyzer_change_df.copy()
    )

    # ========================================================
    # FAILED DOWNLOADS
    # ========================================================

    failed_indices = (
        st.session_state.index_analyzer_failed
    )

    if failed_indices:

        with st.expander(
            "⚠️ Indices with unavailable data",
            expanded=False,
        ):

            st.warning(
                "Some Yahoo Finance downloads failed. "
                "These values are shown as NA rather than 0."
            )

            for (
                index_name,
                ticker,
                error,
            ) in failed_indices:

                st.write(
                    f"**{index_name}** "
                    f"`{ticker}` — {error}"
                )

    # ========================================================
    # SORT DATA
    # ========================================================

    if "1D" in change_df.columns:

        change_df = change_df.sort_values(
            by="1D",
            ascending=False,
            na_position="last",
        )

    # ========================================================
    # RAW TABLE
    # ========================================================

    with st.expander(
        "📋 View Raw % Change Table"
    ):

        styled = (
            change_df.style
            .format(
                lambda value:
                f"{value:.2f}%"
                if pd.notnull(value)
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

    # ========================================================
    # DATA STATUS
    # ========================================================

    total_indices = len(change_df)

    successful_indices = (
        change_df.notna()
        .any(axis=1)
        .sum()
    )

    failed_count = (
        total_indices
        - successful_indices
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Indices",
            total_indices,
        )

    with col2:

        st.metric(
            "Data Available",
            successful_indices,
        )

    with col3:

        st.metric(
            "Data Unavailable",
            failed_count,
        )

    # ========================================================
    # AI QUERY
    # ========================================================

    st.header("🔎 AI Query")

    # ========================================================
    # GEMINI CLIENT
    # ========================================================

    client = None

    try:

        gemini_api = st.secrets[
            "GEMINI_API_KEY"
        ]

        client = genai.Client(
            api_key=gemini_api
        )

    except Exception as e:

        st.warning(
            "Gemini API key is not configured correctly."
        )

        st.caption(
            f"Gemini configuration: {e}"
        )

    # ========================================================
    # GEMINI MODELS
    # ========================================================

    gen_models = []

    if client is not None:

        try:

            for model in client.models.list():

                model_name = getattr(
                    model,
                    "name",
                    "",
                )

                if model_name:

                    # Keep model names that can be
                    # used with generate_content.
                    gen_models.append(
                        model_name
                    )

        except Exception as e:

            st.warning(
                f"Unable to retrieve Gemini models: {e}"
            )

    # ========================================================
    # MODEL SELECTION
    # ========================================================

    selected_model = None

    if gen_models:

        selected_model = st.selectbox(
            "Choose AI Model",
            options=gen_models,
            index=0,
            key="index_analyzer_model",
        )

    else:

        st.info(
            "No Gemini models are currently available."
        )

    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = st.text_area(
        "Enter your prompt",
        placeholder=(
            "Example: Compare Bank Nifty, Nifty IT "
            "and Nifty Pharma over the selected periods."
        ),
        max_chars=1000,
        key="index_analyzer_prompt",
    )

    # ========================================================
    # SUBMIT
    # ========================================================

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
                "Getting AI analysis..."
            ):

                try:

                    # ----------------------------------------
                    # Prepare only available data
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
                    # Prompt
                    # ----------------------------------------

                    final_prompt = f"""
You are a financial data analyst.

You are given percentage-change data
for NSE indices.

Data:
{finance_data_json}

User question:
{user_prompt}

Instructions:

1. Analyze only the data supplied above.
2. Identify relevant index movements and trends.
3. Compare indices where appropriate.
4. Mention positive and negative movements.
5. Do not treat NA values as zero.
6. Do not invent missing market data.
7. Clearly state when data is unavailable.
8. Provide a concise financial-data-based conclusion.

This is an analytical summary based on
historical percentage-change data and should
not be presented as guaranteed future performance.
"""

                    # ----------------------------------------
                    # Generate Gemini response
                    # ----------------------------------------

                    response = client.models.generate_content(
                        model=selected_model,
                        contents=final_prompt,
                    )

                    response_text = getattr(
                        response,
                        "text",
                        None,
                    )

                    if response_text:

                        st.session_state.index_analyzer_response = (
                            response_text
                        )

                    else:

                        st.session_state.index_analyzer_response = (
                            "No response was returned by Gemini."
                        )

                except Exception as e:

                    st.session_state.index_analyzer_response = ""

                    st.error(
                        f"Gemini analysis failed: {e}"
                    )

    # ========================================================
    # AI RESPONSE
    # ========================================================

    if (
        st.session_state.index_analyzer_response
    ):

        with st.expander(
            "📊 AI Analysis Result",
            expanded=True,
        ):

            if selected_model:

                st.markdown(
                    f"**Model Used:** `{selected_model}`"
                )

            st.write(
                st.session_state.index_analyzer_response
            )

    # ========================================================
    # CHARTS
    # ========================================================

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
