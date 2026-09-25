"""
StockAlert - Nifty 50 Next-Close Predictor
===========================================

Streamlit port of the original Flask + Colab "index_predict" dashboard.

The app:
  1. Pulls recent closing prices for Dow, Nasdaq, Crude, S&P 500, Nifty 50
     and Nifty IT via yfinance.
  2. Feeds the last 31 trading days into a pre-trained Keras model to
     predict the next Nifty 50 close.
  3. Shows current value / predicted value / trend / error metrics,
     a rolling-average chart, and a sortable prediction-history table.
  4. Auto-refreshes on a configurable interval (replaces the old
     Flask `setInterval` + `/refresh-index-predict` JS polling).

Run with:
    streamlit run app.py

Expected repo layout:
    app.py
    requirements.txt
    models/best_model-3.keras   <-- your trained model
"""

import datetime
import os

import numpy as np
import pandas as pd
import pytz
import streamlit as st
import yfinance as yf
from matplotlib import pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.preprocessing import MinMaxScaler
from streamlit_autorefresh import st_autorefresh
from tensorflow.keras import backend as K
from tensorflow.keras.models import load_model

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

TICKERS = ["^dji", "^ixic", "bz=f", "^gspc", "^nsei", "^cnxit"]
NAMES = ["dow", "nasdaq", "crude", "sp500", "nifty50", "nifty_it"]
NIFTY_COL_INDEX = NAMES.index("nifty50")  # position of nifty50 among the (no-date) feature columns
LOOKBACK_DAYS = 31  # matches the original full_data[-31:] window

DEFAULT_MODEL_PATH = os.environ.get("MODEL_PATH", "models/best_model.keras")


# --------------------------------------------------------------------------- #
# Model loading
# --------------------------------------------------------------------------- #

def _rmse_metric(y_true, y_pred):
    """Custom Keras metric the model was trained/saved with."""
    return K.sqrt(K.mean(K.square(y_true - y_pred)))


@st.cache_resource(show_spinner="Loading prediction model...")
def get_model(model_path: str):
    return load_model(model_path, custom_objects={"rmse": _rmse_metric})


# --------------------------------------------------------------------------- #
# Data + prediction
# --------------------------------------------------------------------------- #

def fetch_market_data():
    """Fetch the last LOOKBACK_DAYS closes for all indices and scale them."""
    frames = []
    curr_org = high = low = None

    for ticker, name in zip(TICKERS, NAMES):
        hist = yf.Ticker(ticker).history(period="6mo")
        if hist.empty:
            raise RuntimeError(f"No data returned for {ticker} ({name}).")

        close = hist["Close"].reset_index()
        close.columns = ["Date", name]
        close["Date"] = pd.to_datetime(close["Date"]).dt.date
        frames.append(close)

        if name == "nifty50":
            curr_org = float(hist["Close"].iloc[-1])
            high = float(hist["High"].iloc[-1])
            low = float(hist["Low"].iloc[-1])

    full_data = frames[0]
    for frame in frames[1:]:
        full_data = pd.merge(full_data, frame, on="Date", how="inner")

    full_data = full_data.tail(LOOKBACK_DAYS).reset_index(drop=True)
    full_data_copy = full_data.copy()  # unscaled, with Date column

    feature_cols = [c for c in full_data.columns if c != "Date"]
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_values = scaler.fit_transform(full_data[feature_cols])
    full_data_scaled = pd.DataFrame(scaled_values, columns=feature_cols)

    return full_data_scaled, full_data_copy, scaler, curr_org, high, low


def compute_prediction(model):
    """Run the model over the latest window and build the history table + stats."""
    full_data_scaled, full_data_copy, scaler, curr_org, high, low = fetch_market_data()

    X = full_data_scaled.iloc[:-1, :].values
    last_row = full_data_scaled.iloc[-1]

    pred = np.asarray(model.predict(X, verbose=0)).flatten()

    temp_data = full_data_scaled.copy().iloc[1:].reset_index(drop=True)
    temp_data["nifty50"] = pred
    temp_data_inv = scaler.inverse_transform(temp_data)
    pred_n50 = temp_data_inv[:, NIFTY_COL_INDEX]

    last_val = np.asarray(model.predict(last_row.values.reshape(1, -1), verbose=0)).flatten()[0]
    new_row = last_row.copy()
    new_row.iloc[NIFTY_COL_INDEX] = last_val
    new_row_inv = scaler.inverse_transform(new_row.values.reshape(1, -1))
    new_val = float(new_row_inv[0][NIFTY_COL_INDEX])

    merged_data = full_data_copy.iloc[1:, [0, NIFTY_COL_INDEX + 1]].copy()  # +1 to skip Date offset
    merged_data.columns = ["Date", "Actual Value"]
    merged_data["Predicted Value"] = pred_n50
    merged_data.sort_values(by="Date", ascending=False, inplace=True)
    merged_data.reset_index(drop=True, inplace=True)

    merged_data["Difference"] = merged_data["Predicted Value"] - merged_data["Actual Value"]

    actual_trend = merged_data["Actual Value"] > merged_data["Actual Value"].shift(-1)
    predicted_trend = merged_data["Predicted Value"] > merged_data["Predicted Value"].shift(-1)
    merged_data["Actual Trend"] = actual_trend.astype(int)
    merged_data["Predicted Trend"] = predicted_trend.astype(int)
    merged_data["Correct Trend"] = (merged_data["Actual Trend"] == merged_data["Predicted Trend"]).astype(int)

    merged_data = merged_data.round(2)
    merged_data["Actual Trend"] = merged_data["Actual Trend"].map({1: "Up", 0: "Down"})
    merged_data["Predicted Trend"] = merged_data["Predicted Trend"].map({1: "Up", 0: "Down"})
    merged_data["Correct Trend"] = merged_data["Correct Trend"].map({1: "Same", 0: "Diff"})

    same_count = int((merged_data.iloc[:-1]["Correct Trend"] == "Same").sum())

    full_data_org = np.append(curr_org, merged_data["Actual Value"].values).flatten()
    full_data_pred = np.append(new_val, merged_data["Predicted Value"].values).flatten()

    mae = round(float(mean_absolute_error(full_data_org, full_data_pred)), 2)
    rmse_val = round(float(np.sqrt(np.mean((full_data_org - full_data_pred) ** 2))), 2)
    mape = round(float(mean_absolute_percentage_error(full_data_org, full_data_pred) * 100), 2)

    first_actual = merged_data.iloc[0]["Actual Value"]
    first_pred = merged_data.iloc[0]["Predicted Value"]

    current_trend_extra = (
        f"{round(abs(curr_org - first_actual), 2)} "
        f"({round(abs(curr_org - first_actual) * 100 / first_actual, 2)}%)"
    )
    pred_trend_extra = (
        f"{round(abs(new_val - first_pred), 2)} "
        f"({round(abs(new_val - first_pred) * 100 / first_pred, 2)}%)"
    )

    curr_val = round(new_val)
    curr_org_r = round(curr_org)
    curr_diff = round(curr_val - curr_org_r)

    current_trend_up = curr_org_r > first_actual
    pred_trend_up = curr_val > first_pred

    if current_trend_up == pred_trend_up:
        correct_pred = "Same"
        same_count += 1
    else:
        correct_pred = "Diff"

    merged_data.loc[merged_data.index[-1], ["Actual Trend", "Predicted Trend", "Correct Trend"]] = "-"
    merged_data = merged_data[
        ["Date", "Actual Value", "Actual Trend", "Predicted Value", "Predicted Trend", "Difference", "Correct Trend"]
    ]

    stats = {
        "curr_org": curr_org_r,
        "curr_val": curr_val,
        "curr_diff": curr_diff,
        "current_trend": ("Up \u2191 " if current_trend_up else "Down \u2193 ") + current_trend_extra,
        "current_trend_up": current_trend_up,
        "pred_trend": ("Up \u2191 " if pred_trend_up else "Down \u2193 ") + pred_trend_extra,
        "pred_trend_up": pred_trend_up,
        "correct_pred": correct_pred,
        "same_count": same_count,
        "same_perc": round((same_count / 30) * 100, 2),
        "mae": mae,
        "rmse": rmse_val,
        "mape": mape,
        "high": high,
        "low": low,
    }
    return stats, merged_data


# --------------------------------------------------------------------------- #
# Rolling averages (replaces the Flask in-memory buffers)
# --------------------------------------------------------------------------- #

def init_session_state():
    defaults = {
        "last_30s": [], "last_1m": [], "last_2m": [], "last_3m": [],
        "last_5m": [], "last_10m": [], "total_time": [],
        "avg_curr": [], "avg_30s": [], "avg_1m": [], "avg_2m": [],
        "avg_3m": [], "avg_5m": [], "avg_10m": [], "avg_total": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _add_item(lst, item, max_items):
    if len(lst) >= max_items:
        lst.pop(0)
    lst.append(item)


def update_rolling_averages(curr_org):
    ss = st.session_state
    _add_item(ss.last_30s, curr_org, 3)
    _add_item(ss.last_1m, curr_org, 6)
    _add_item(ss.last_2m, curr_org, 12)
    _add_item(ss.last_3m, curr_org, 18)
    _add_item(ss.last_5m, curr_org, 30)
    _add_item(ss.last_10m, curr_org, 60)
    ss.total_time.append(curr_org)

    ss.avg_curr.append(float(curr_org))
    ss.avg_30s.append(float(np.mean(ss.last_30s)))
    ss.avg_1m.append(float(np.mean(ss.last_1m)))
    ss.avg_2m.append(float(np.mean(ss.last_2m)))
    ss.avg_3m.append(float(np.mean(ss.last_3m)))
    ss.avg_5m.append(float(np.mean(ss.last_5m)))
    ss.avg_10m.append(float(np.mean(ss.last_10m)))
    ss.avg_total.append(float(np.mean(ss.total_time)))


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

# def render_metrics(stats):
#     trend_color = "green" if stats["current_trend_up"] else "red"
#     pred_color = "green" if stats["pred_trend_up"] else "red"
#     similarity_color = "green" if stats["correct_pred"] == "Same" else "red"
#     if stats["same_perc"] > 50:
#         perc_color = "green"
#     elif stats["same_perc"] < 50:
#         perc_color = "red"
#     else:
#         perc_color = "orange"

#     col1, col2, col3 = st.columns(3)
#     with col1:
#         st.metric("Current Original", stats["curr_org"])
#         st.markdown(f"**Current Trend:** :{trend_color}[{stats['current_trend']}]")
#     with col2:
#         st.metric("Current Predicted", stats["curr_val"])
#         st.markdown(f"**Predicted Trend:** :{pred_color}[{stats['pred_trend']}]")
#     with col3:
#         st.metric("Current Difference", stats["curr_diff"])
#         st.markdown(f"**Trend Similarity:** :{similarity_color}[{stats['correct_pred']}]")

#     st.markdown(f"**Similarity Percentage:** :{perc_color}[{stats['same_perc']}%]")

#     err1, err2, err3 = st.columns(3)
#     err1.metric("Mean Absolute Error", stats["mae"])
#     err2.metric("Root Mean Squared Error", stats["rmse"])
#     err3.metric("Mean Absolute % Error", f"{stats['mape']}%")


def render_metrics(stats):

    trend_color = "green" if stats["current_trend_up"] else "red"
    pred_color = "green" if stats["pred_trend_up"] else "red"
    similarity_color = "green" if stats["correct_pred"] == "Same" else "red"

    if stats["same_perc"] > 50:
        perc_color = "green"
    elif stats["same_perc"] < 50:
        perc_color = "red"
    else:
        perc_color = "orange"

    with st.container(border=True):

        st.markdown(
            """
            <style>
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background-color: #fff8ef;
                border: 1px solid #f7941d;
                border-radius: 8px;
                padding: 10px 14px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Current Original", stats["curr_org"])
            st.markdown(
                f"**Current Trend:** :{trend_color}[{stats['current_trend']}]"
            )

        with col2:
            st.metric("Current Predicted", stats["curr_val"])
            st.markdown(
                f"**Predicted Trend:** :{pred_color}[{stats['pred_trend']}]"
            )

        with col3:
            st.metric("Current Difference", stats["curr_diff"])
            st.markdown(
                f"**Trend Similarity:** :{similarity_color}[{stats['correct_pred']}]"
            )

        st.markdown(
            f"**Similarity Percentage:** :{perc_color}[{stats['same_perc']}%]"
        )

        err1, err2, err3 = st.columns(3)

        err1.metric("Mean Absolute Error", stats["mae"])
        err2.metric("Root Mean Squared Error", stats["rmse"])
        err3.metric(
            "Mean Absolute % Error",
            f"{stats['mape']}%"
        )


def render_averages_chart():
    ss = st.session_state
    if len(ss.avg_curr) < 2:
        st.info("The rolling-average chart will appear after a couple of refresh cycles.")
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(ss.avg_curr, label="Current", color="lightblue")
    ax.plot(ss.avg_30s, label="30s", color="green", linestyle="dashed")
    ax.plot(ss.avg_1m, label="1m", color="gold", linestyle="dashed")
    ax.plot(ss.avg_2m, label="2m", color="blue", linestyle="dashed")
    ax.plot(ss.avg_3m, label="3m", color="magenta", linestyle="dashed")
    ax.plot(ss.avg_5m, label="5m", color="deepskyblue", linestyle="dashed")
    ax.plot(ss.avg_10m, label="10m", color="red", linestyle="dashed")
    ax.plot(ss.avg_total, label="Total", color="plum", linestyle="dashed")
    ax.set_xlabel("Refresh cycle")
    ax.set_ylabel("Average value")
    ax.set_title("Current value vs. rolling averages")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
    plt.close(fig)


def render_table(merged_data: pd.DataFrame):
    st.subheader("Prediction history (last 30 trading days)")

    def highlight_trend(row):
        if row["Correct Trend"] == "Same":
            color = "background-color: #d4f4dd"
        elif row["Correct Trend"] == "Diff":
            color = "background-color: #fadada"
        else:
            color = ""
        return [color] * len(row)

    styled = merged_data.style.apply(highlight_trend, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    st.set_page_config(page_title="StockAlert - Nifty 50 Predictor", page_icon="\U0001F4C8", layout="wide")
    init_session_state()

    st.sidebar.header("Settings")
    model_path = st.sidebar.text_input("Model path", value=DEFAULT_MODEL_PATH)
    refresh_seconds = st.sidebar.number_input(
        "Auto-refresh interval (seconds)", min_value=10, max_value=3600, value=60, step=10
    )
    auto_refresh = st.sidebar.checkbox("Enable auto-refresh", value=True)
    if st.sidebar.button("Refresh now"):
        st.rerun()

    if auto_refresh:
        st_autorefresh(interval=refresh_seconds * 1000, key="data_autorefresh")

    # st.title("\U0001F4C8 StockAlert \u2014 Nifty 50 Next-Close Predictor")
    # st.caption("Live prediction dashboard (converted from the original Flask app).")
    st.markdown(
        """
        <div id="bob-banner">
            <h1>📈 StockAlert \u2014 Nifty 50 Next-Close Predictor</h1>
            <p>Live prediction dashboard  •  AI-powered market signals</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not os.path.exists(model_path):
        st.error(f"Model file not found at '{model_path}'. Update the path in the sidebar.")
        st.stop()

    try:
        model = get_model(model_path)
        with st.spinner("Fetching market data and generating prediction..."):
            stats, merged_data = compute_prediction(model)
    except Exception as exc:  # noqa: BLE001 - surface any fetch/predict failure to the UI
        st.error(f"Failed to fetch data or generate a prediction: {exc}")
        st.stop()

    update_rolling_averages(stats["curr_org"])

    render_metrics(stats)
    st.divider()
    render_averages_chart()
    st.divider()
    render_table(merged_data)

    ist_now = datetime.datetime.now(pytz.utc).astimezone(pytz.timezone("Asia/Kolkata"))
    st.caption(f"Last updated: {ist_now.strftime('%d-%m-%Y %H:%M:%S')} IST")


if __name__ == "__main__":
    main()
