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
from typing import Optional

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
    Robust Gemini Markdown/HTML renderer.

    Handles:
        - Normal Markdown
        - Gemini generated HTML
        - ESCAPED HTML such as \\<p> and \\<br/>
        - # / ## / ### headings
        - **bold**
        - *italic*
        - ***bold italic***
        - `inline code`
        - bullet lists
        - numbered lists
        - blockquotes
        - horizontal rules
        - Markdown tables
        - Markdown links
        - Gemini <b> and <span> formatting
        - Mixed Markdown + HTML
    """

    if not text:
        return ""

    # ============================================================
    # 1. NORMALIZE GEMINI ESCAPED HTML
    # ============================================================

    # Gemini sometimes returns:
    #
    # \<p style='...'>text\</p>
    # \<br/>
    #
    # Convert those back to real HTML.
    text = text.replace(r"\<", "<")
    text = text.replace(r"\>", ">")

    # Also handle HTML entities that may have been escaped.
    text = text.replace("&lt;p", "<p")
    text = text.replace("&lt;/p", "</p")
    text = text.replace("&lt;br", "<br")
    text = text.replace("&lt;/", "</")

    # ============================================================
    # 2. REMOVE UNWANTED GEMINI WRAPPER HTML
    # ============================================================

    # If Gemini already generated <p style='margin:4px 0'>
    # we don't want nested paragraph tags inside our renderer.

    text = re.sub(
        r"<p\b[^>]*>",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"</p>",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    # Convert <br>, <br/>, <br /> to newline
    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    # ============================================================
    # 3. PROTECT INTENTIONAL GEMINI INLINE HTML
    # ============================================================

    protected_html = {}

    def protect_html(match):
        key = f"___GEMINI_HTML_{len(protected_html)}___"
        protected_html[key] = match.group(0)
        return key

    # Preserve:
    # <b>...</b>
    # <strong>...</strong>
    # <i>...</i>
    # <em>...</em>
    # <span style="...">...</span>
    # <mark>...</mark>

    text = re.sub(
        r"</?(?:b|strong|i|em|u|mark|span)"
        r"(?:\s+style\s*=\s*(['\"])[\s\S]*?\1)?"
        r"\s*/?>",
        protect_html,
        text,
        flags=re.IGNORECASE
    )

    # ============================================================
    # 4. INLINE MARKDOWN
    # ============================================================

    def inline_markdown(value):

        # Protect placeholders before HTML escaping
        placeholders = {}

        for key, html_tag in protected_html.items():
            placeholder = f"___INLINE_{len(placeholders)}___"
            placeholders[placeholder] = html_tag
            value = value.replace(key, placeholder)

        # Escape everything else
        value = html_lib.escape(value)

        # --------------------------------------------------------
        # Markdown links
        # --------------------------------------------------------

        value = re.sub(
            r'\[([^\]]+)\]\((https?://[^\s\)]+)\)',
            r'<a href="\2" target="_blank" '
            r'style="'
            r'color:#0059b3;'
            r'text-decoration:none;'
            r'font-weight:600;'
            r'">'
            r'\1</a>',
            value
        )

        # --------------------------------------------------------
        # Inline code
        # --------------------------------------------------------

        value = re.sub(
            r'`([^`]+)`',
            r'<code style="'
            r'background:#f1f3f5;'
            r'color:#7a1f1f;'
            r'padding:2px 6px;'
            r'border-radius:5px;'
            r'font-family:Consolas,monospace;'
            r'font-size:0.90em;'
            r'">\1</code>',
            value
        )

        # --------------------------------------------------------
        # Bold + italic
        # --------------------------------------------------------

        value = re.sub(
            r'\*\*\*(.+?)\*\*\*',
            r'<strong><em>\1</em></strong>',
            value
        )

        # --------------------------------------------------------
        # Bold
        # --------------------------------------------------------

        value = re.sub(
            r'\*\*(.+?)\*\*',
            r'<strong>\1</strong>',
            value
        )

        value = re.sub(
            r'__(.+?)__',
            r'<strong>\1</strong>',
            value
        )

        # --------------------------------------------------------
        # Italic
        # --------------------------------------------------------

        value = re.sub(
            r'(?<!\*)\*([^*\n]+?)\*(?!\*)',
            r'<em>\1</em>',
            value
        )

        value = re.sub(
            r'(?<!_)_([^_\n]+?)_(?!_)',
            r'<em>\1</em>',
            value
        )

        # --------------------------------------------------------
        # Strikethrough
        # --------------------------------------------------------

        value = re.sub(
            r'~~(.+?)~~',
            r'<del>\1</del>',
            value
        )

        # --------------------------------------------------------
        # Restore Gemini HTML
        # --------------------------------------------------------

        for placeholder, html_tag in placeholders.items():
            value = value.replace(
                placeholder,
                html_tag
            )

        return value


    # ============================================================
    # 5. TABLE FUNCTIONS
    # ============================================================

    def is_table_separator(line):

        stripped = line.strip()

        if stripped.startswith("|"):
            stripped = stripped[1:]

        if stripped.endswith("|"):
            stripped = stripped[:-1]

        cells = stripped.split("|")

        if not cells:
            return False

        return all(
            re.match(
                r"^\s*:?-{3,}:?\s*$",
                cell
            )
            for cell in cells
        )


    def split_table_row(line):

        line = line.strip()

        if line.startswith("|"):
            line = line[1:]

        if line.endswith("|"):
            line = line[:-1]

        return [
            cell.strip()
            for cell in line.split("|")
        ]


    def render_table(table_lines):

        if len(table_lines) < 2:
            return None

        header = split_table_row(
            table_lines[0]
        )

        separator = split_table_row(
            table_lines[1]
        )

        if not is_table_separator(
            table_lines[1]
        ):
            return None

        # --------------------------------------------------------
        # Alignment
        # --------------------------------------------------------

        alignments = []

        for cell in separator:

            cell = cell.strip()

            if cell.startswith(":") and cell.endswith(":"):
                alignments.append("center")

            elif cell.endswith(":"):
                alignments.append("right")

            else:
                alignments.append("left")

        # --------------------------------------------------------
        # Rows
        # --------------------------------------------------------

        rows = []

        for line in table_lines[2:]:

            if not line.strip():
                continue

            if "|" not in line:
                continue

            cells = split_table_row(line)

            # Normalize number of columns
            if len(cells) < len(header):
                cells += [""] * (
                    len(header) - len(cells)
                )

            elif len(cells) > len(header):
                cells = cells[:len(header)]

            rows.append(cells)

        # --------------------------------------------------------
        # Table
        # --------------------------------------------------------

        html = """
        <div style="
            width:100%;
            overflow-x:auto;
            margin:16px 0 20px 0;
            border:1px solid #d9dee7;
            border-radius:10px;
            box-shadow:0 2px 8px rgba(0,0,0,0.06);
        ">

        <table style="
            width:100%;
            border-collapse:collapse;
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                'Segoe UI',
                Arial,
                sans-serif;
            font-size:14px;
            background:#ffffff;
        ">

        <thead>
        <tr>
        """

        # Header
        for i, cell in enumerate(header):

            align = (
                alignments[i]
                if i < len(alignments)
                else "left"
            )

            html += f"""
            <th style="
                padding:11px 13px;
                text-align:{align};
                background:linear-gradient(
                    135deg,
                    #002e6e 0%,
                    #0059b3 100%
                );
                color:#ffffff;
                font-weight:700;
                border-bottom:2px solid #f7941d;
                white-space:nowrap;
            ">
                {inline_markdown(cell)}
            </th>
            """

        html += """
        </tr>
        </thead>
        <tbody>
        """

        # Body
        for row_index, row in enumerate(rows):

            background = (
                "#ffffff"
                if row_index % 2 == 0
                else "#f6f8fb"
            )

            html += "<tr>"

            for col_index, cell in enumerate(row):

                align = (
                    alignments[col_index]
                    if col_index < len(alignments)
                    else "left"
                )

                html += f"""
                <td style="
                    padding:9px 13px;
                    text-align:{align};
                    background:{background};
                    color:#202124;
                    border-bottom:1px solid #e5e7eb;
                    vertical-align:middle;
                    line-height:1.45;
                ">
                    {inline_markdown(cell)}
                </td>
                """

            html += "</tr>"

        html += """
        </tbody>
        </table>
        </div>
        """

        return html


    # ============================================================
    # 6. MAIN PARSER
    # ============================================================

    lines = text.split("\n")

    output = []

    i = 0

    in_code = False
    code_lines = []

    in_ul = False
    in_ol = False


    def close_lists():

        nonlocal in_ul, in_ol

        if in_ul:
            output.append("</ul>")
            in_ul = False

        if in_ol:
            output.append("</ol>")
            in_ol = False


    while i < len(lines):

        raw = lines[i]
        stripped = raw.strip()

        # ========================================================
        # CODE BLOCK
        # ========================================================

        if stripped.startswith("```"):

            if not in_code:

                close_lists()

                in_code = True
                code_lines = []

            else:

                code = html_lib.escape(
                    "\n".join(code_lines)
                )

                output.append(
                    f"""
                    <div style="
                        margin:14px 0;
                        border-radius:10px;
                        overflow:hidden;
                        background:#0d1117;
                        border:1px solid #30363d;
                        box-shadow:
                            0 2px 8px
                            rgba(0,0,0,0.12);
                    ">

                        <div style="
                            padding:6px 12px;
                            background:#161b22;
                            color:#8b949e;
                            font-size:11px;
                            font-weight:700;
                            letter-spacing:0.5px;
                        ">
                            CODE
                        </div>

                        <pre style="
                            margin:0;
                            padding:14px;
                            overflow-x:auto;
                            color:#e6edf3;
                            font-family:
                                Consolas,
                                'Courier New',
                                monospace;
                            font-size:13px;
                            line-height:1.55;
                        "><code>{code}</code></pre>

                    </div>
                    """
                )

                in_code = False
                code_lines = []

            i += 1
            continue


        if in_code:

            code_lines.append(raw)
            i += 1
            continue


        # ========================================================
        # BLANK LINE
        # ========================================================

        if not stripped:

            close_lists()

            i += 1
            continue


        # ========================================================
        # TABLE
        # ========================================================

        if (
            i + 1 < len(lines)
            and "|" in stripped
            and is_table_separator(lines[i + 1])
        ):

            close_lists()

            table_lines = [
                lines[i],
                lines[i + 1]
            ]

            j = i + 2

            while j < len(lines):

                candidate = lines[j].strip()

                if not candidate:
                    break

                if "|" not in candidate:
                    break

                table_lines.append(
                    lines[j]
                )

                j += 1

            rendered = render_table(
                table_lines
            )

            if rendered:

                output.append(rendered)

                i = j
                continue


        # ========================================================
        # HEADINGS
        # ========================================================

        heading = re.match(
            r"^(#{1,6})\s+(.+)$",
            stripped
        )

        if heading:

            close_lists()

            level = len(
                heading.group(1)
            )

            title = heading.group(2)

            if level == 1:

                style = """
                    font-size:24px;
                    color:#002e6e;
                    border-bottom:
                        3px solid #f7941d;
                    padding-bottom:8px;
                    margin:
                        18px 0 12px 0;
                """

            elif level == 2:

                style = """
                    font-size:20px;
                    color:#002e6e;
                    border-left:
                        5px solid #f7941d;
                    padding-left:11px;
                    margin:
                        18px 0 10px 0;
                """

            elif level == 3:

                style = """
                    font-size:17px;
                    color:#0059b3;
                    margin:
                        15px 0 8px 0;
                """

            else:

                style = """
                    font-size:15px;
                    color:#333333;
                    margin:
                        12px 0 6px 0;
                """

            output.append(
                f"""
                <h{level} style="
                    {style}
                    font-weight:700;
                    line-height:1.35;
                ">
                    {inline_markdown(title)}
                </h{level}>
                """
            )

            i += 1
            continue


        # ========================================================
        # HORIZONTAL RULE
        # ========================================================

        if re.match(
            r"^([-*_])(?:\s*\1){2,}$",
            stripped
        ):

            close_lists()

            output.append(
                """
                <div style="
                    height:2px;
                    margin:16px 0;
                    background:
                        linear-gradient(
                            90deg,
                            transparent,
                            #d5dbe5,
                            #f7941d,
                            #d5dbe5,
                            transparent
                        );
                "></div>
                """
            )

            i += 1
            continue


        # ========================================================
        # BLOCKQUOTE
        # ========================================================

        if stripped.startswith(">"):

            close_lists()

            quote = re.sub(
                r"^>\s?",
                "",
                stripped
            )

            output.append(
                f"""
                <div style="
                    margin:10px 0;
                    padding:11px 15px;
                    border-left:
                        4px solid #f7941d;
                    background:#fff8ef;
                    color:#4b5563;
                    border-radius:
                        0 8px 8px 0;
                    line-height:1.55;
                ">
                    {inline_markdown(quote)}
                </div>
                """
            )

            i += 1
            continue


        # ========================================================
        # BULLET
        # ========================================================

        bullet = re.match(
            r"^[-*+]\s+(.+)$",
            stripped
        )

        if bullet:

            if in_ol:

                output.append("</ol>")
                in_ol = False

            if not in_ul:

                output.append(
                    """
                    <ul style="
                        margin:
                            7px 0 12px 24px;
                        padding-left:15px;
                    ">
                    """
                )

                in_ul = True

            item = bullet.group(1)

            output.append(
                f"""
                <li style="
                    margin:5px 0;
                    padding-left:3px;
                    line-height:1.55;
                ">
                    {inline_markdown(item)}
                </li>
                """
            )

            i += 1
            continue


        # ========================================================
        # NUMBERED LIST
        # ========================================================

        numbered = re.match(
            r"^\d+[.)]\s+(.+)$",
            stripped
        )

        if numbered:

            if in_ul:

                output.append("</ul>")
                in_ul = False

            if not in_ol:

                output.append(
                    """
                    <ol style="
                        margin:
                            7px 0 12px 24px;
                        padding-left:15px;
                    ">
                    """
                )

                in_ol = True

            item = numbered.group(1)

            output.append(
                f"""
                <li style="
                    margin:6px 0;
                    padding-left:3px;
                    line-height:1.55;
                ">
                    {inline_markdown(item)}
                </li>
                """
            )

            i += 1
            continue


        # ========================================================
        # NORMAL PARAGRAPH
        # ========================================================

        close_lists()

        paragraph = inline_markdown(
            stripped
        )

        output.append(
            f"""
            <div style="
                margin:6px 0;
                color:#202124;
                font-size:14px;
                line-height:1.65;
            ">
                {paragraph}
            </div>
            """
        )

        i += 1


    # ============================================================
    # CLOSE ANY OPEN ELEMENTS
    # ============================================================

    if in_code:

        code = html_lib.escape(
            "\n".join(code_lines)
        )

        output.append(
            f"""
            <pre style="
                background:#0d1117;
                color:#e6edf3;
                padding:14px;
                border-radius:8px;
                overflow-x:auto;
            ">{code}</pre>
            """
        )

    close_lists()


    # ============================================================
    # RESTORE ANY REMAINING PROTECTED HTML
    # ============================================================

    result = "\n".join(output)

    # ============================================================
    # FINAL FINANCIAL HIGHLIGHTING
    # ============================================================

    # Only highlight plain text occurrences.
    # Existing HTML is left untouched.

    result = re.sub(
        r"\bHIGH RISK\b",
        """
        <span style="
            display:inline-block;
            background:#fde8e8;
            color:#b42318;
            padding:3px 9px;
            border-radius:14px;
            font-weight:700;
            font-size:12px;
        ">HIGH RISK</span>
        """,
        result,
        flags=re.IGNORECASE
    )

    result = re.sub(
        r"\bMEDIUM RISK\b",
        """
        <span style="
            display:inline-block;
            background:#fff4d6;
            color:#9a6700;
            padding:3px 9px;
            border-radius:14px;
            font-weight:700;
            font-size:12px;
        ">MEDIUM RISK</span>
        """,
        result,
        flags=re.IGNORECASE
    )

    result = re.sub(
        r"\bLOW RISK\b",
        """
        <span style="
            display:inline-block;
            background:#e7f7ed;
            color:#18794e;
            padding:3px 9px;
            border-radius:14px;
            font-weight:700;
            font-size:12px;
        ">LOW RISK</span>
        """,
        result,
        flags=re.IGNORECASE
    )

    # ============================================================
    # OUTER CONTAINER
    # ============================================================

    return f"""
    <div style="
        width:100%;
        box-sizing:border-box;
        font-family:
            -apple-system,
            BlinkMacSystemFont,
            'Segoe UI',
            Roboto,
            Arial,
            sans-serif;
        color:#202124;
        line-height:1.6;
    ">
        {result}
    </div>
    """


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
    """
    Fetch full history for `ticker`, attach moving averages, and grab the
    latest quoted price (`iNAV`) from `stock.info`.

    Always returns a `(data, inav)` tuple — `(None, None)` on any failure —
    so callers can safely do `data, inav = get_stock_data(ticker)` without
    an extra type check first.
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="max")
        if data is None or data.empty:
            return None, None
        for window in (20, 50, 100, 200, 400, 600):
            data[f"{window}DMA"] = data["Close"].rolling(window=window).mean()
        try:
            inav = stock.info.get("regularMarketPrice")
        except Exception:
            inav = None
        return data, inav
    except Exception:
        return None, None


def create_stock_dataframe(ticker: str, data: pd.DataFrame, inav: Optional[float] = None) -> pd.DataFrame:
    last_row = data.iloc[-1]
    current_price = last_row["Close"]

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
        # `regularMarketPrice` from stock.info is frequently missing/None
        # (delisted tickers, off-hours, some NSE symbols) — never round(None).
        "iNAV": [round(inav, 2) if inav is not None else None],
        "Death Cross": [int(last_row["50DMA"] < last_row["200DMA"]) if not pd.isna(last_row["50DMA"]) and not pd.isna(last_row["200DMA"]) else 0],
    }
    for window in (20, 50, 100, 200, 400, 600):
        stock_data[f"{window}DMA"] = [round(last_row[f"{window}DMA"], 2) if not pd.isna(last_row[f"{window}DMA"]) else 0]
    for window in (20, 50, 100, 200, 400, 600):
        stock_data[f"% Change {window}DMA"] = [round(pct_vs_dma(f"{window}DMA"), 2)]
    stock_data["Volume"] = [round(avg_volume)]

    return pd.DataFrame(stock_data)


def create_stock_dataframe_momentum(
    ticker: str,
    data: pd.DataFrame = None,
    inav: Optional[float] = None,
) -> pd.DataFrame:
    """
    Volume-weighted rate-of-change ("momentum") table.
    Accepts pre-fetched `data`/`inav` (from get_stock_data) to avoid a
    second network round-trip per ticker; falls back to fetching them
    itself if only called with a ticker.
    """
    if data is None:
        data, inav = get_stock_data(ticker)
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
        "iNAV": [round(inav, 2) if inav is not None else None],
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

        data, inav = get_stock_data(ticker)
        if data is None or data.empty:
            if progress_callback:
                progress_callback(i + 1, total, time.time() - start_time)
            continue

        try:
            if view_value == "momentum":
                stock_df = create_stock_dataframe_momentum(ticker, data, inav)
            else:
                stock_df = create_stock_dataframe(ticker, data, inav)
                if view_value == "consolidated":
                    temp_df = create_stock_dataframe_momentum(ticker, data, inav)
                    stock_df = stock_df.drop(columns=["Volume"])
                    # Both dataframes now carry "iNAV" (and Company Name /
                    # Current Price) — drop the duplicates from temp_df
                    # before the column-wise concat below, or the merge
                    # would produce two "iNAV" columns.
                    temp_df = temp_df.drop(columns=["Company Name", "Current Price", "iNAV"])
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
