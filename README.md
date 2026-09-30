# 🏦 BOB AI Index

## AI & Emerging Technologies — Market Intelligence Platform

**BOB AI Index** is a Streamlit-based market intelligence platform designed to provide AI-assisted analysis of Indian stock-market indices, companies, stocks, and ETFs.

The application is organized as a central portal containing three specialized analytical modules:

```text
                 🏦 BOB AI Index
                       │
          AI & Emerging Technologies
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
 Index Scrapper   Index Analyzer   Index Predictor
        │              │              │
 Stock / Company   Core Index      Nifty 50
 / ETF Insights      Analysis      Prediction
```

---

# 📌 Applications

## 1. 📊 Index Scrapper

**Purpose:** Stock / Company / ETF-wise market insight.

The Index Scrapper module focuses on individual market instruments and provides information that can be used for company- or security-level analysis.

Typical use cases include:

* Stock-wise analysis
* Company-wise insights
* ETF analysis
* Market data retrieval
* Individual security performance analysis
* AI-assisted interpretation

The module is designed to provide a more granular view compared with the broader index-level analysis available in the Index Analyzer.

---

# 2. 📈 Index Analyzer

**Purpose:** Core index analysis.

The Index Analyzer focuses on major NSE indices and sectoral indices.

Examples include:

* Nifty 50
* Nifty Bank
* Nifty IT
* Nifty Pharma
* Nifty FMCG
* Nifty Auto
* Nifty Energy
* Nifty Metal
* Nifty Realty
* Nifty Media
* Nifty Infrastructure
* Nifty Consumption

The application combines historical market data, momentum calculations, moving-average analysis, rankings, interactive charts, and AI-generated interpretation.

---

# 3. 🔮 Index Predictor

**Purpose:** Future Nifty 50 index prediction and short-term monitoring.

The Index Predictor is focused primarily on the **Nifty 50 index** and provides predicted values across multiple future time horizons.

The interface includes current-value monitoring and prediction intervals such as:

```text
30 seconds
1 minute
2 minutes
3 minutes
5 minutes
10 minutes
```

The application also maintains rolling/current observations to support monitoring of the prediction behavior over successive refresh cycles.

---

# 🏗️ Application Architecture

The project uses a central Streamlit portal.

```text
BOB AI Index
│
├── app.py
│
├── index_scrapper.py
│
├── index_analyzer.py
│
└── index_predictor.py
```

### `app.py`

The main application acts as the portal.

Responsibilities include:

* Streamlit page configuration
* BOB branding
* Application navigation
* Application cards
* Loading the selected module
* Routing the user to the appropriate application

The individual modules expose their own `main()` functions.

```python
from index_scrapper import main as scrapper_main
from index_analyzer import main as analyzer_main
from index_predictor import main as predictor_main
```

The portal therefore provides a single entry point while keeping the three applications modular.

---

# 🎨 BOB Portal Design

The portal follows a Bank of Baroda-inspired visual design.

The main portal contains application cards for:

```text
📊 Index Scrapper
Stock / Company / ETFs wise insight

📈 Index Analyzer
Core index insight

🔮 Index Predictor
Predicts future Nifty 50 index
```

The application uses native Streamlit components such as:

* `st.container(border=True)`
* `st.columns()`
* `st.markdown()`
* `st.button()`

This avoids relying on unsupported raw HTML rendering for the primary application cards.

---

# 📊 Index Analyzer — Methodology

The Index Analyzer combines market-performance indicators with historical trend analysis.

## Supported Indices

The NSE index mapping includes:

| Index             | Ticker       |
| ----------------- | ------------ |
| Nifty 50          | `^NSEI`      |
| Nifty IT          | `^CNXIT`     |
| Nifty Pharma      | `^CNXPHARMA` |
| Nifty Bank        | `^NSEBANK`   |
| Nifty FMCG        | `^CNXFMCG`   |
| Nifty Auto        | `^CNXAUTO`   |
| Nifty Energy      | `^CNXENERGY` |
| Nifty Metal       | `^CNXMETAL`  |
| Nifty Realty      | `^CNXREALTY` |
| Nifty Media       | `^CNXMEDIA`  |
| Nifty Infra       | `^CNXINFRA`  |
| Nifty Consumption | `^CNXCONSUM` |

---

# 📈 Historical Market Data

The Index Analyzer retrieves historical market data using **Yahoo Finance / yfinance**.

The analysis supports different historical periods and intervals, allowing the application to examine both recent and longer-term index behavior.

The application uses market data for:

* Price analysis
* Historical returns
* Momentum
* Moving-average comparisons
* Ranking
* Interactive visualization

---

# ⚡ 20-Day Momentum

One of the core indicators is the **20-Day Momentum**, based on a volume-weighted rate of change approach.

The methodology is designed to identify recent directional momentum while incorporating trading-volume information.

Conceptually:

```text
20-Day Momentum
        │
        ├── Price movement
        │
        ├── Historical comparison
        │
        └── Volume weighting
```

---

# 📐 Moving-Average Analysis

The Index Analyzer evaluates index/company performance relative to different moving-average periods.

The analysis includes percentage-change columns such as:

```text
% Change <N>DMA
```

These comparisons provide a historical perspective across different investment horizons.

---

# 🏷️ Time-Horizon Classification

The analysis categorizes observations into different time horizons.

### Selling

Based on:

```text
1 Month
```

### Holding

Based on:

```text
3 Months
6 Months
1 Year
```

### Long-Term Holding

Based on:

```text
2 Years
3 Years
```

These classifications are analytical labels produced by the application's methodology and are intended to organize the historical-performance information.

---

# 🏆 Recent Performance Rank

The application calculates a **Recent Performance Rank** using weighted longer-term performance.

The methodology uses:

```text
Recent Performance Rank
=
3 × 1Y Rank
+
2 × 2Y Rank
+
1 × 3Y Rank
```

This gives the one-year performance a larger weight while retaining information from two- and three-year periods.

---

# 📊 Index Analyzer Visualization

The application uses interactive Plotly charts for market-data visualization.

The charts can be used to inspect:

* Price movement
* Historical performance
* Momentum
* Moving-average relationships
* Comparative index performance

The application also presents analytical results in Streamlit tables.

---

# 🤖 AI-Assisted Analysis

The Index Analyzer integrates Google's Gemini API for AI-assisted interpretation.

The application uses the Google GenAI client:

```python
from google import genai

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)
```

The Gemini API is used to generate analytical interpretations based on the processed market information.

The AI layer is intended to complement the quantitative calculations rather than replace the underlying market-data analysis.

---

# 🔐 Gemini API Configuration

The Gemini API key is configured through Streamlit secrets.

Create:

```text
.streamlit/secrets.toml
```

with:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

For Streamlit Cloud, the same secret should be configured through the application's **Secrets** settings.

The API key should not be committed to GitHub.

---

# 💾 Session State

The application uses Streamlit session state for maintaining application information across Streamlit reruns.

This is particularly useful for:

* Retaining analytical results
* Maintaining generated AI responses
* Managing refresh operations
* Avoiding unnecessary repeated processing

The application also uses caching where appropriate to improve performance.

---

# 🔮 Index Predictor

The Index Predictor focuses on future Nifty 50 values.

The dashboard presents current and predicted values through metric cards and charts.

Important displayed values include:

```text
Current Original
Current Predicted
Current Difference
```

---

# 📊 Predictor Monitoring

The predictor maintains rolling values for multiple prediction horizons.

The visualization includes:

```text
Current
30s
1m
2m
3m
5m
10m
Total
```

These series allow the user to visually compare current observations against predictions at different horizons.

---

# 📉 Current-Value Reference Lines

The predictor visualization includes horizontal reference lines representing the observed highest and lowest current values.

These are displayed using lightly styled dotted lines so that the historical/current series remain visually prominent.

Conceptually:

```text
Highest Current Value
- - - - - - - - - - - -

       Prediction / Current Series

- - - - - - - - - - - -
Lowest Current Value
```

---

# 🔄 Data Refresh

The Index Predictor includes a refresh-data control for updating the latest market information and prediction values.

The refresh workflow is designed for repeated monitoring of the predictor output.

---

# 🧩 Technology Stack

| Technology                   | Purpose                                              |
| ---------------------------- | ---------------------------------------------------- |
| Python                       | Core application                                     |
| Streamlit                    | Web application framework                            |
| Pandas                       | Data processing                                      |
| NumPy                        | Numerical calculations                               |
| yfinance                     | Market data retrieval                                |
| Plotly                       | Interactive charts                                   |
| Google Gemini                | AI-assisted analysis                                 |
| Hugging Face / ML components | Supporting analytical functionality where applicable |

---

# 📦 Installation

Clone the repository:

```bash
git clone <repository-url>
cd <repository-folder>
```

Create a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

# 📄 Example `requirements.txt`

Depending on the exact implementation and deployment environment, the project may use:

```text
streamlit
pandas
numpy
yfinance
plotly
google-genai
```

Additional dependencies should be added to `requirements.txt` if they are used by the Index Scrapper or Index Predictor modules.

---

# ▶️ Run Locally

Start the portal with:

```bash
streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

---

# ☁️ Streamlit Cloud Deployment

The application can be deployed using Streamlit Community Cloud.

Recommended project structure:

```text
BOB-AI-Index/
│
├── app.py
├── index_scrapper.py
├── index_analyzer.py
├── index_predictor.py
├── requirements.txt
└── README.md
```

After connecting the GitHub repository to Streamlit Cloud:

1. Select `app.py` as the main file.
2. Configure the required Python dependencies.
3. Add `GEMINI_API_KEY` under Streamlit Cloud Secrets.
4. Deploy the application.
5. Open the generated Streamlit application URL.

---

# 🛡️ Data Handling

The application retrieves market information from external market-data sources and processes it within the application.

The project does not require a traditional database for its core analytical workflow.

The application should be configured according to the applicable data-provider terms and organizational policies before production use.

---

# ⚠️ Important Considerations

Market-data availability can vary depending on:

* Market hours
* Data-provider availability
* Internet connectivity
* Symbol validity
* API/data-provider limitations
* Historical data availability

Some securities or indices may occasionally fail to download.

The application therefore includes data-processing and retrieval handling to deal with incomplete or unavailable data.

---

# 🧮 Data Quality Handling

The Index Analyzer processes retrieved datasets before generating the final analytical tables.

Rows where the relevant analytical values are entirely zero or missing can be excluded so that empty observations do not distort the displayed analysis.

This helps keep the final analytical output focused on valid market observations.

---

# 🔧 yfinance Handling

The cloud implementation uses a more controlled download strategy for market data.

The data retrieval process can use:

```python
yf.download(
    ticker,
    auto_adjust=False,
    threads=False
)
```

Sequential retrieval and retry handling help reduce problems that can occur when multiple market-data requests are made simultaneously.

The implementation also handles different dataframe structures returned by yfinance, including MultiIndex-style data.

---

# 🧠 AI + Quantitative Analysis

The overall architecture combines two complementary layers:

```text
              Market Data
                   │
                   ▼
          Quantitative Analysis
                   │
       ┌───────────┼───────────┐
       │           │           │
    Momentum     DMA        Rankings
       │           │           │
       └───────────┼───────────┘
                   │
                   ▼
             AI Analysis
                   │
                   ▼
             User Insight
```

The quantitative layer calculates measurable market indicators.

The AI layer provides natural-language interpretation of the processed information.

---

# 📊 Analytical Categories

The Index Analyzer's dashboard methodology uses visually differentiated categories for different analytical components.

Examples include:

| Component          | Category                        |
| ------------------ | ------------------------------- |
| Momentum           | Momentum analysis               |
| DMA                | Moving-average analysis         |
| Selling            | Short-term classification       |
| Holding            | Medium-term classification      |
| Long Term          | Long-term classification        |
| Recent Performance | Weighted historical performance |
| Historical         | Historical analysis             |
| Momentum View      | Momentum interpretation         |
| Interpretation     | AI/analytical interpretation    |

---

# 🎯 Intended Use Cases

BOB AI Index can support:

* Market intelligence
* Index monitoring
* Sector analysis
* Stock/company analysis
* ETF analysis
* Historical performance analysis
* Momentum analysis
* Moving-average analysis
* AI-assisted market interpretation
* Nifty 50 prediction monitoring
* Internal analytical PoCs
* Financial AI experimentation

---

# 🏦 BOB AI Architecture

The overall platform can be viewed as three analytical levels:

```text
                         🏦 BOB AI Index
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        Security Level      Index Level      Prediction Level
              │                 │                 │
              ▼                 ▼                 ▼
       Index Scrapper      Index Analyzer    Index Predictor
              │                 │                 │
       ┌──────┼──────┐          │                 │
       │      │      │          │                 │
      Stock Company  ETF        │                 │
                                │                 │
                         Nifty / Sectoral         │
                              Indices             │
                                                  │
                                             Nifty 50
                                             Prediction
```

This structure allows the platform to provide granular security-level information, broader index analysis, and predictive monitoring within a single Streamlit portal.

---

# 🚀 Future Enhancements

Potential extensions for the platform include:

* More NSE indices
* Additional global indices
* Expanded company/stock coverage
* ETF comparison
* Advanced technical indicators
* Automated alerts
* Historical prediction accuracy tracking
* Prediction-vs-actual analysis
* Model performance dashboards
* More AI-generated analytical reports
* Downloadable analytical reports
* Scheduled market summaries
* Portfolio-level analysis
* Enhanced real-time monitoring

---

# 📁 Recommended Repository Structure

```text
BOB-AI-Index/
│
├── app.py
│
├── index_scrapper.py
│
├── index_analyzer.py
│
├── index_predictor.py
│
├── requirements.txt
│
├── README.md
│
└── .streamlit/
    └── secrets.toml
```

---

# 🔑 Environment / Secrets

The following secret is required for Gemini-powered functionality:

```text
GEMINI_API_KEY
```

Example:

```toml
GEMINI_API_KEY = "your-api-key"
```

Do **not** commit the actual API key to source control.

---

# 📝 Disclaimer

This application is intended for **research, analytical, demonstration, and proof-of-concept purposes**.

Market analysis and AI-generated interpretations should not be treated as guaranteed outcomes or as a substitute for appropriate financial analysis, institutional controls, or investment decision-making processes.

Historical market performance does not guarantee future performance.

---

# 👨‍💻 Development

The project is designed as a modular Streamlit application.

Each module can be developed independently through its `main()` function while the central `app.py` provides the unified portal.

```text
app.py
  │
  ├── index_scrapper.main()
  │
  ├── index_analyzer.main()
  │
  └── index_predictor.main()
```

This structure allows individual applications to evolve without requiring major changes to the central portal.

---

# 🏦 BOB AI Index — Summary

**BOB AI Index** brings together:

```text
📊 Stock / Company / ETF Analysis
          +
📈 Core Index Analysis
          +
🔮 Nifty 50 Prediction
          +
🤖 Gemini AI Interpretation
          +
📊 Interactive Market Visualization

The result is a unified **AI-assisted market intelligence platform** built with Streamlit for the BOB AI / Emerging Technologies environment.
```
