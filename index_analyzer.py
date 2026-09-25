import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from google import genai
import json
import numpy as np

# ======================================================== # GEMINI CLIENT # ======================================================== 
client = None 

try: 
    gemini_api = st.secrets["GEMINI_API_KEY"] 
    client = genai.Client(api_key=gemini_api) 
except Exception as e: 
    st.warning("Gemini API key is not configured correctly.") 
    st.caption( f"Gemini configuration: {e}" )

# NSE tickers
nse_indices = {
    'Nifty 50': '^NSEI',
    'Nifty IT': '^CNXIT',
    'Nifty Pharma': '^CNXPHARMA',
    'Nifty Bank': '^NSEBANK',
    'Nifty FMCG': '^CNXFMCG',
    'Nifty Auto': '^CNXAUTO',
    'Nifty Energy': '^CNXENERGY',
    'Nifty Metal': '^CNXMETAL',
    'Nifty Realty': '^CNXREALTY',
    'Nifty Media': '^CNXMEDIA',
    'Nifty Infra': '^CNXINFRA',
    'Nifty Consumption': '^CNXCONSUM',
    'Nifty Commodity': '^CNXCMDT',
    'Nifty MNC': '^CNXMNC',
    'Nifty PSU Bank': '^CNXPSUBANK',
    'Nifty PSE': '^CNXPSE',
    'Nifty Services': '^CNXSERVICE',
}

# Time intervals
interval_config = {
    '1D': {'days_back': 1, 'type': 'trading'},
    '5D': {'days_back': 5, 'type': 'trading'},
    '10D': {'days_back': 10, 'type': 'trading'},
    '1M': {'days_back': 30, 'type': 'calendar'},
    '3M': {'days_back': 90, 'type': 'calendar'},
    '6M': {'days_back': 180, 'type': 'calendar'},
    '1Y': {'days_back': 365, 'type': 'calendar'},
    '2Y': {'days_back': 730, 'type': 'calendar'},
    '3Y': {'days_back': 1095, 'type': 'calendar'},
}


# Function to fetch data
def fetch_change_data():
    results = {}

    for index_name, ticker in nse_indices.items():
        try:
            df = yf.download(
                ticker,
                period="max",
                interval="1d",
                progress=False
            )

            # FIX ONLY:
            # yfinance may now return Close as a DataFrame
            # even when downloading a single ticker.
            close_series = df["Close"]

            if isinstance(close_series, pd.DataFrame):
                close_series = close_series.iloc[:, 0]

            close_series = close_series.dropna().sort_index()

            if close_series.empty:
                results[index_name] = {
                    label: None for label in interval_config
                }
                continue

            last_date = close_series.index[-1]
            current_price = close_series.iloc[-1]
            earliest_date = close_series.index[0]
            changes = {}

            for label, cfg in interval_config.items():
                days_needed = cfg['days_back']

                if cfg['type'] == 'trading':
                    if len(close_series) > days_needed:
                        past_price = close_series.iloc[-(days_needed + 1)]
                    else:
                        past_price = close_series.iloc[0]
                else:
                    target_date = last_date - timedelta(days=days_needed)

                    if target_date < earliest_date:
                        past_price = close_series.iloc[0]
                    else:
                        nearest = close_series[
                            close_series.index <= target_date
                        ]

                        past_price = (
                            nearest.iloc[-1]
                            if not nearest.empty
                            else close_series.iloc[0]
                        )

                changes[label] = round(
                    ((current_price - past_price) / past_price) * 100,
                    2
                )

            results[index_name] = changes

        except Exception:
            results[index_name] = {
                label: None for label in interval_config
            }

    return pd.DataFrame(results).T.astype("float")


# Load NSE data only once per session
if "change_df" not in st.session_state:
    with st.spinner("Fetching NSE index data..."):
        st.session_state.change_df = fetch_change_data()
        st.session_state.analyzer_response = None

# change_df = st.session_state.change_df

# Sort by '1D' column ascending
change_df = st.session_state.change_df.sort_values(
    by='1D',
    ascending=False
)


# Single interval bar plot
def plot_single_bar(df, interval):
    st.subheader(f"📊 NSE Index % Change: {interval}")
    df = df.loc[df.fillna(0).ne(0).any(axis=1)].copy()
    df_sorted = (
        df[[interval]]
        .dropna()
        .sort_values(interval, ascending=False)
    )

    fig = go.Figure(
        go.Bar(
            x=df_sorted.index,
            y=df_sorted[interval],
            text=[f"{v:.2f}%" for v in df_sorted[interval]],
            textposition="auto",
            marker_color="royalblue"
        )
    )

    fig.update_layout(
        yaxis_title="% Change",
        xaxis_title="Index",
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)


# Multiple interval grouped bar plot
def plot_grouped(df, intervals):
    st.subheader("📊 Grouped Index % Changes")

    df = df.loc[df.fillna(0).ne(0).any(axis=1)].copy()

    df_sorted = (
        df[intervals]
        .dropna()
        .sort_values(intervals[0], ascending=False)
    )

    fig = go.Figure()

    colors = [
        '#1f77b4',
        '#ff7f0e',
        '#2ca02c',
        '#d62728',
        '#9467bd'
    ]

    for i, label in enumerate(intervals):
        fig.add_trace(
            go.Bar(
                x=df_sorted.index,
                y=df_sorted[label],
                name=label,
                marker_color=colors[i % len(colors)],
                text=[f"{v:.2f}%" for v in df_sorted[label]],
                textposition="auto"
            )
        )

    fig.update_layout(
        barmode="group",
        yaxis_title="% Change",
        xaxis_title="Index",
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)


def main():

    if "analyzer_response" not in st.session_state:
        st.session_state.analyzer_response = None

    # Streamlit UI setup
    st.set_page_config(
        page_title="NSE Index Analyzer",
        layout="wide",
        page_icon="📈"
    )

    # st.title("📈 NSE Index Analyzer")
    st.markdown(
        """
        <div id="bob-banner">
            <h1>📈 NSE Index Analyzer</h1>
            <p>Core index insights  •  Index trend analysis</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Inject custom CSS only for the Refresh button
    st.markdown("""
        <style>
        div.refresh-button button {
            background-color: #0066cc;
            color: white;
            border-radius: 6px;
            border: none;
            font-weight: 600;
        }
    
        div.refresh-button button:hover {
            background-color: #0052a3;
            color: white;
        }
    
        div.refresh-button button:active {
            background-color: #004080;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="refresh-button">', unsafe_allow_html=True)
    refresh_clicked = st.button("🔄 Refresh Data", key="refresh_data_button")
    st.markdown('</div>', unsafe_allow_html=True)
    
    selected_intervals = st.multiselect(
        "Select time periods to display:",
        options=list(interval_config.keys()),
        default=["1D"]
    )
    
    # Show raw table
    with st.expander("📋 View Raw % Change Table"):
        # Clamp values between -100 and 100 for gradient mapping
        clamped_df = change_df.clip(lower=-100, upper=100)
    
        # Apply custom gradient scaling between -100 and 100
        styled = (
            change_df.style
            .format(
                lambda x: f"{x:.2f}%"
                if pd.notnull(x)
                else "NA"
            )
            .background_gradient(
                cmap="RdYlGn",
                vmin=-20,
                vmax=20,
                axis=None
            )
        )
    
        st.dataframe(
            styled,
            use_container_width=True
        )
    
    # Get Gemini models
    # gen_models = [m.name.split("/")[1] for m in genai.list_models()]
    gen_models = [
        'gemini-flash-lite-latest',
        'gemini-flash-latest'
    ]
    
    # AI Query Section
    st.header("🔎 AI Query")

    selected_model = st.selectbox(
        "Choose AI Model",
        options=gen_models,
        index=0
    )

    user_prompt = st.text_area(
        "Enter your prompt",
        placeholder="Type your query here...",
        max_chars=1000
    )
    
    if st.button("Submit"):
        if not user_prompt.strip():
            st.error("Please enter a prompt before submitting.")
        else:
            with st.spinner("Getting analysis..."):
                try:
                    # Prepare finance data to include in the prompt
                    data_df = (
                        change_df
                        .reset_index()
                        .rename(columns={"index": "Index Name"})
                    )

                    finance_data_json = data_df.to_json(
                        orient="records"
                    )
        
                    final_prompt = f""" You are a financial data analyst. 
                    You are given percentage-change data for NSE indices. 
                    Data: {finance_data_json} User question: {user_prompt} 
                    Instructions: 1. Analyze only the data supplied above. 
                    2. Identify relevant index movements and trends. 
                    3. Compare indices where appropriate. 
                    4. Mention positive and negative movements. 
                    5. Do not treat NA values as zero. 
                    6. Do not invent missing market data. 
                    7. Clearly state when data is unavailable. 
                    8. Provide a concise financial-data-based conclusion. 
                    This is an analytical summary based on historical percentage-change data 
                    and should not be presented as guaranteed future performance. """ 
                    
                    # ----------------------------------------
                    # Generate Gemini response 
                    # ---------------------------------------- 
                    response = client.models.generate_content(
                        model=selected_model,
                        contents=final_prompt
                    )

                    response_text = getattr(
                        response,
                        "text",
                        None
                    )

                    if response_text: 
                        st.session_state.analyzer_response = response_text 
                    else: 
                        st.session_state.analyzer_response = (
                            "No response was returned by Gemini."
                        )

                except Exception as e: 
                    st.session_state.analyzer_response = None
                    st.error(
                        f"Gemini analysis failed: {e}"
                    )
    
    if st.session_state.analyzer_response:
        with st.expander("📊 AI Analysis Result", expanded=True):
            st.markdown(
                f"**Model Used:** `{selected_model}`"
            )
            st.write(st.session_state.analyzer_response)
    
    # Show plots
    if selected_intervals:
        if len(selected_intervals) == 1:
            plot_single_bar(
                change_df,
                selected_intervals[0]
            )
        else:
            plot_grouped(
                change_df,
                selected_intervals
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
