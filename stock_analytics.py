"""
Framework-agnostic analytics layer for StockAlert.

Everything here is pure data-crunching (yfinance + pandas). It has no
knowledge of Streamlit, Flask, or Colab, so it can be unit-tested and reused
regardless of which UI wraps it. `app.py` is the only file that imports
Streamlit.
"""

import os
import re
import time
import html as html_lib

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup

from index_config import INDEX_NAMES_FETCH

# Folder (relative to this file) where the manually-uploaded index
# constituent CSVs live. On Streamlit Cloud this is just a normal folder
# committed to the GitHub repo.
INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index")


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def safe_pct_change(new, old):
    """Percentage change of `new` vs `old`, guarding against div-by-zero/NaN."""
    try:
        if old in (0, None) or pd.isna(old) or pd.isna(new):
            return 0
        return round(((new - old) / abs(old)) * 100, 2)
    except (TypeError, ZeroDivisionError):
        return 0


def text_to_html(text: str) -> str:
    """
    Turn a plain/markdown-ish AI response into simple HTML for display.
    The Gemini prompts already ask for <b>/<span> tags for flags, so this
    only needs to handle paragraphs, line breaks and **bold** / bullets.
    """
    if not text:
        return ""

    escaped_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            escaped_lines.append("<br/>")
            continue
        # Preserve intentional inline HTML (<b>, <span style=...>) that the
        # model was explicitly asked to emit, but escape everything else to
        # avoid accidentally injecting broken markup.
        if "<span" in stripped or "<b>" in stripped:
            processed = stripped
        else:
            processed = html_lib.escape(stripped)
            processed = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", processed)
        if stripped.startswith(("- ", "* ")):
            processed = f"<li>{processed[2:]}</li>"
        else:
            processed = f"<p style='margin:4px 0'>{processed}</p>"
        escaped_lines.append(processed)

    return "\n".join(escaped_lines)


def extract_flags(html: str):
    """Pull ticker -> full-text mapping out of green/red <span> flags."""
    soup = BeautifulSoup(html or "", "html.parser")

    def parse_flags(style_color):
        ticker_map = {}
        for span in soup.find_all("span", style=lambda x: x and style_color in x):
            full_text = span.get_text(strip=True)
            match = re.search(r"\((\w+)\)", full_text)
            if match:
                ticker_map[match.group(1)] = full_text
        return set(ticker_map.keys()), ticker_map

    green_tickers, green_map = parse_flags("green")
    red_tickers, red_map = parse_flags("red")
    return (green_tickers, green_map), (red_tickers, red_map)


# --------------------------------------------------------------------------
# Market data
# --------------------------------------------------------------------------

def get_stock_data(ticker: str):
    """Fetch full history for `ticker` and attach moving averages."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="max")
        if data is None or data.empty:
            return None
        for window in (20, 50, 100, 200, 400, 600):
            data[f"{window}DMA"] = data["Close"].rolling(window=window).mean()
        data["inav"] = stock.info.get("regularMarketPrice").values()
        return data
    except Exception:
        return None


def create_stock_dataframe(ticker: str, data: pd.DataFrame) -> pd.DataFrame:
    last_row = data.iloc[-1]
    current_price = last_row["Close"]
    inav = data["inav"]

    def pct_vs_dma(dma_col):
        dma = last_row[dma_col]
        if pd.isna(dma) or dma == 0:
            return 0
        return ((current_price - dma) / dma) * 100

    volume = data["Volume"].tail(200).dropna()
    avg_volume = volume.mean() if not volume.empty else 0

    display_ticker = ticker[:-3] if ticker.endswith(".NS") else ticker

    stock_data = {
        "Company Name": [""],
        "Ticker": [display_ticker],
        "Current Price": [round(current_price, 2)],
        "iNAV": [round(inav, 2)],
        "Death Cross": [int(last_row["50DMA"] < last_row["200DMA"]) if not pd.isna(last_row["50DMA"]) and not pd.isna(last_row["200DMA"]) else 0],
    }
    for window in (20, 50, 100, 200, 400, 600):
        stock_data[f"{window}DMA"] = [round(last_row[f"{window}DMA"], 2) if not pd.isna(last_row[f"{window}DMA"]) else 0]
    for window in (20, 50, 100, 200, 400, 600):
        stock_data[f"% Change {window}DMA"] = [round(pct_vs_dma(f"{window}DMA"), 2)]
    stock_data["Volume"] = [round(avg_volume)]

    return pd.DataFrame(stock_data)


def create_stock_dataframe_momentum(ticker: str, data: pd.DataFrame = None) -> pd.DataFrame:
    """
    Volume-weighted rate-of-change ("momentum") table.
    Accepts pre-fetched `data` (from get_stock_data) to avoid a second
    network round-trip per ticker; falls back to fetching it itself.
    """
    if data is None:
        data = get_stock_data(ticker)
    if data is None or data.empty:
        raise ValueError(f"No data for {ticker}")

    current_price = data["Close"].iloc[-1]
    volume = data["Volume"].tail(200).dropna()
    avg_volume = volume.mean() if not volume.empty else 0

    display_ticker = ticker[:-3] if ticker.endswith(".NS") else ticker

    periods = [1, 5, 10, 20, 50, 100, 200, 400, 600]
    price_change = data["Close"].diff()
    volume_weighted_change = (price_change / data["Close"].shift(1)) * data["Volume"]

    roc_values = {}
    for period in periods:
        roc = (
            volume_weighted_change.rolling(window=period).sum()
            / data["Volume"].rolling(window=period).sum()
        ) * 100
        roc_values[period] = round(roc.iloc[-1], 5) if not pd.isna(roc.iloc[-1]) else 0

    stock_data = {
        "Company Name": [""],
        "Ticker": [display_ticker],
        "Current Price": [round(current_price, 2)],
        "1DMoM": [roc_values[1]],
        "5DMoM": [roc_values[5]],
        "10DMoM": [roc_values[10]],
        "20DMoM": [roc_values[20]],
        "50DMoM": [roc_values[50]],
        "100DMoM": [roc_values[100]],
        "200DMoM": [roc_values[200]],
        "400DMoM": [roc_values[400]],
        "600DMoM": [roc_values[600]],
    }

    m1, m5, m10, m20, m50 = (
        stock_data["1DMoM"][0], stock_data["5DMoM"][0], stock_data["10DMoM"][0],
        stock_data["20DMoM"][0], stock_data["50DMoM"][0],
    )
    stock_data["%Chg_5D_to_1D"] = [safe_pct_change(m1, m5)]
    stock_data["%Chg_10D_to_5D"] = [safe_pct_change(m5, m10)]
    stock_data["%Chg_20D_to_10D"] = [safe_pct_change(m10, m20)]
    stock_data["%Chg_50D_to_20D"] = [safe_pct_change(m20, m50)]
    stock_data["Volume"] = [round(avg_volume)]

    return pd.DataFrame(stock_data)


def fetch_analyst_forecast(ticker_no_suffix: str, index_name: str):
    """
    Best-effort scrape of alphaspread.com analyst estimates.
    Returns (low, avg, high) or None if unavailable. Wrapped defensively
    since this is a third-party page scrape, not an official API, and can
    fail/rate-limit independently of everything else.
    """
    try:
        url = f"https://www.alphaspread.com/security/{index_name}/{ticker_no_suffix}/analyst-estimates"
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")

        forecast = []
        for div in soup.find_all("div", class_="mobile-only"):
            for item in div.find_all("div", class_="right-aligned"):
                text = item.get_text(strip=True)
                value = text.split("INR")[0].split("USD")[0].replace(" ", "")
                if value and value != "NotAvailable":
                    forecast.append(value)
                if len(forecast) == 3:
                    break
            if len(forecast) == 3:
                break

        if len(forecast) < 3:
            return None
        return float(forecast[0]), float(forecast[1]), float(forecast[2])
    except Exception:
        return None


# --------------------------------------------------------------------------
# CSV resolution (index/ folder is manually maintained now — no scraping)
# --------------------------------------------------------------------------

def resolve_names_source(main_value: str, name: str) -> str:
    """
    Map (category, internal-or-raw name) -> path of the constituents CSV
    inside the local `index/` folder. Raises FileNotFoundError with a
    helpful message if the file hasn't been uploaded yet.
    """
    if main_value == "etf":
        filename = "NASDAQ-ETF.csv" if name == "nasdaq etf" else "ETF-all.csv"
    elif "nasdaq" not in name:
        filename = f"{name}_list.csv"
    elif name == "nasdaq-100":
        filename = "NASDAQ.csv"
    else:
        filename = f"{name}_list.csv"

    path = os.path.join(INDEX_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Expected constituents file '{filename}' was not found in the "
            f"'index/' folder. Upload it to the repo (see README.md) before "
            f"running this selection."
        )
    return path


def load_names(main_value: str, name: str) -> pd.DataFrame:
    return pd.read_csv(resolve_names_source(main_value, name))


# --------------------------------------------------------------------------
# Main table builder (replaces Flask's `display_table`)
# --------------------------------------------------------------------------

def build_stock_table(
    main_value: str,
    name: str,
    view_value: str,
    pred_value: str,
    progress_callback=None,
) -> pd.DataFrame:
    """
    Build the full ranked stock table for one (category, index) selection.

    progress_callback(done, total, elapsed_seconds) is called after every
    ticker so the caller (Streamlit) can drive a progress bar; it is purely
    optional/side-effecting and never affects the returned DataFrame.
    """
    names = load_names(main_value, name)
    use_ns_suffix = "nasdaq" not in name

    rows = []
    start_time = time.time()
    total = len(names)

    for i in range(total):
        row = names.iloc[i]
        symbol = str(row.get("Symbol", "")).strip()
        if not symbol or "DUMMY" in symbol:
            if progress_callback:
                progress_callback(i + 1, total, time.time() - start_time)
            continue

        ticker = f"{symbol}.NS" if use_ns_suffix else symbol

        data = get_stock_data(ticker)
        if data is None or data.empty:
            if progress_callback:
                progress_callback(i + 1, total, time.time() - start_time)
            continue

        try:
            if view_value == "momentum":
                stock_df = create_stock_dataframe_momentum(ticker, data)
            else:
                stock_df = create_stock_dataframe(ticker, data)
                if view_value == "consolidated":
                    temp_df = create_stock_dataframe_momentum(ticker, data)
                    stock_df = stock_df.drop(columns=["Volume"])
                    temp_df = temp_df.drop(columns=["Company Name", "Current Price"])
                    stock_df = pd.concat(
                        [stock_df.set_index("Ticker"), temp_df.set_index("Ticker")],
                        axis=1,
                    ).reset_index()
                    cols = stock_df.columns.tolist()
                    cols[0], cols[1] = cols[1], cols[0]
                    stock_df = stock_df[cols]
        except Exception:
            if progress_callback:
                progress_callback(i + 1, total, time.time() - start_time)
            continue

        company_name = row.get("Company Name", row.get("Company", ""))
        stock_df["Company Name"] = company_name

        if main_value != "etf" and pred_value == "yes":
            index_name = "nasdaq"
            ticker_no_suffix = ticker
            if ticker.endswith(".NS"):
                index_name = "nse"
                ticker_no_suffix = ticker[:-3]
            time.sleep(1)  # be polite to the third-party site
            forecast = fetch_analyst_forecast(ticker_no_suffix, index_name)
            if forecast:
                low, avg, high = forecast
                current_price = float(stock_df["Current Price"].iloc[0])
                stock_df["Lowest"] = low
                stock_df["Below Low"] = current_price < low
                stock_df["% Change to Low"] = round(((low - current_price) / current_price) * 100, 2)
                stock_df["Average"] = avg
                stock_df["Below Average"] = current_price < avg
                stock_df["% Change to Avg"] = round(((avg - current_price) / current_price) * 100, 2)
                stock_df["Highest"] = high
                stock_df["% Change to High"] = round(((high - current_price) / current_price) * 100, 2)

        rows.append(stock_df)

        if progress_callback:
            progress_callback(i + 1, total, time.time() - start_time)

    if not rows:
        return pd.DataFrame()

    full_df = pd.concat(rows, ignore_index=True)
    full_df.fillna(0, inplace=True)

    if main_value != "etf":
        if "Volume" in full_df.columns:
            full_df.drop(columns=["Volume"], inplace=True)
    else:
        full_df["Volume Rank"] = full_df["Volume"].rank(method="min", ascending=False).astype(int)
        full_df.rename(columns={"Volume": "200D Avg Volume"}, inplace=True)

    if view_value != "momentum":
        n = len(full_df)
        top_25_pct = int(np.ceil(n * 0.25)) if n else 0

        full_df["Rank for Selling (1M)"] = full_df["% Change 20DMA"].rank(method="dense", ascending=False).astype(int)
        full_df["Rank for Holding (3M)"] = full_df["% Change 50DMA"].rank(method="dense", ascending=False).astype(int)
        full_df["Flag_1M_not_3M"] = (
            (full_df["Rank for Selling (1M)"] <= top_25_pct)
            & (full_df["Rank for Holding (3M)"] > top_25_pct)
        ).astype(int)

        full_df["Rank for Holding (6M)"] = full_df["% Change 100DMA"].rank(method="dense", ascending=False).astype(int)
        full_df["Flag_3M_not_6M"] = (
            (full_df["Rank for Holding (3M)"] <= top_25_pct)
            & (full_df["Rank for Holding (6M)"] > top_25_pct)
        ).astype(int)

        full_df["Rank for Holding (1Y)"] = full_df["% Change 200DMA"].rank(method="dense", ascending=False).astype(int)
        full_df["Flag_6M_not_1Y"] = (
            (full_df["Rank for Holding (6M)"] <= top_25_pct)
            & (full_df["Rank for Holding (1Y)"] > top_25_pct)
        ).astype(int)

        full_df["Rank for Long Term Holding (2Y)"] = full_df["% Change 400DMA"].rank(method="dense", ascending=False).astype(int)
        full_df["Rank for Long Term Holding (3Y)"] = full_df["% Change 600DMA"].rank(method="dense", ascending=False).astype(int)

        full_df["Recent Performance Rank"] = (
            3 * full_df["Rank for Holding (1Y)"]
            + 2 * full_df["Rank for Long Term Holding (2Y)"]
            + 1 * full_df["Rank for Long Term Holding (3Y)"]
        )
        full_df["Historical Performance Rank"] = (
            1 * full_df["Rank for Holding (1Y)"]
            + 2 * full_df["Rank for Long Term Holding (2Y)"]
            + 3 * full_df["Rank for Long Term Holding (3Y)"]
        )

    sort_col = "20DMoM" if view_value == "momentum" else "% Change 20DMA"
    if sort_col in full_df.columns:
        full_df = full_df.sort_values(by=[sort_col], ascending=True).reset_index(drop=True)

    return full_df
