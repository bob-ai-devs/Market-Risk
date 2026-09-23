"""
Static configuration: which indices exist, what category they belong to,
and what internal file-key each display name maps to.

This mirrors the `index_names_fetch` dict and the `options` object that used
to live in the Flask app / index.html JS. Nothing here hits the network —
it is only used to build the Streamlit dropdowns and to resolve which CSV
file (inside the local `index/` folder) to load.

NOTE: Index-constituent CSV files are no longer downloaded/updated by the
app. You upload/maintain them yourself in the `index/` folder in the GitHub
repo, named exactly as `{key}_list.csv` (see README.md for the full list of
expected filenames).
"""

# display name (lowercase, as typed by the user in the UI) -> internal key
# used to build the CSV filename "{key}_list.csv"
INDEX_NAMES_FETCH = {
    "nifty 50": "nifty50",
    "nifty next 50": "niftynext50",
    "nifty 100": "nifty100",
    "nifty 200": "nifty200",
    "nifty total market": "niftytotalmarket",
    "nifty 500": "nifty500",
    "nifty 500 multicap 50:25:25": "nifty500Multicap502525",
    "nifty 500 largemidsmall equal-cap weighted": "nifty500LargeMidSmallEqualCapWeighted",
    "nifty midcap 150": "niftymidcap150",
    "nifty midcap 50": "niftymidcap50",
    "nifty midcap select": "niftymidcapselect",
    "nifty midcap 100": "niftymidcap100",
    "nifty smallcap 250": "niftysmallcap250",
    "nifty smallcap 50": "niftysmallcap50",
    "nifty smallcap 100": "niftysmallcap100",
    "nifty microcap 250": "niftymicrocap250",
    "nifty largemidcap 250": "niftylargemidcap250",
    "nifty midsmallcap 400": "niftymidsmallcap400",
    "nifty auto": "niftyauto",
    "nifty bank": "niftybank",
    "nifty financial services": "niftyfinance",
    "nifty financial services 25/50": "niftyfinancialservices25-50",
    "nifty financial services ex-bank": "niftyfinancialservicesexbank",
    "nifty fmcg": "niftyfmcg",
    "nifty healthcare": "niftyhealthcare",
    "nifty it": "niftyit",
    "nifty media": "niftymedia",
    "nifty metal": "niftymetal",
    "nifty pharma": "niftypharma",
    "nifty private bank": "nifty_privatebank",
    "nifty psu bank": "niftypsubank",
    "nifty realty": "niftyrealty",
    "nifty consumer durables": "niftyconsumerdurables",
    "nifty oil and gas": "niftyoilgas",
    "nifty midsmall financial services": "niftymidsmallfinancailservice",
    "nifty midsmall healthcare": "niftymidsmallhealthcare",
    "nifty midsmall it & telecom": "niftymidsmallitAndtelecom",
    "nifty capital markets": "niftyCapitalMarkets",
    "nifty commodities": "niftycommodities",
    "nifty core housing": "niftyCoreHousing",
    "nifty cpse": "niftycpse",
    "nifty ev & new age automotive": "niftyEv_NewAgeAutomotive",
    "nifty energy": "niftyenergy",
    "nifty housing": "niftyhousing",
    "nifty india consumption": "niftyconsumption",
    "nifty india defence": "niftyindiadefence",
    "nifty india digital": "niftyindiadigital",
    "nifty india manufacturing": "niftyindiamanufacturing",
    "nifty india new age consumption": "niftyIndiaNewAgeConsumption",
    "nifty india railways psu": "niftyIndiaRailwaysPSU",
    "nifty india tourism": "niftyindiatourism",
    "nifty infrastructure": "niftyinfra",
    "nifty ipo": "niftyIPO",
    "nifty midsmall india consumption": "niftymidsmallindiaconsumption",
    "nifty mnc": "niftymnc",
    "nifty mobility": "niftymobility",
    "nifty pse": "niftypse",
    "nifty rural": "niftyRural",
    "nifty non-cyclical consumer": "niftynon-cyclicalconsumer",
    "nifty services sector": "niftyservice",
}

# category -> ordered list of display names (drives the "index" dropdown)
CATEGORY_DISPLAY_NAMES = {
    "equity": [
        "Nifty 50", "Nifty Next 50", "Nifty 100", "Nifty 200",
        "Nifty Total Market", "Nifty 500", "Nifty 500 Multicap 50:25:25",
        "Nifty 500 LargeMidSmall Equal-Cap Weighted", "Nifty Midcap 150",
        "Nifty Midcap 50", "Nifty Midcap Select", "Nifty Midcap 100",
        "Nifty Smallcap 250", "Nifty Smallcap 50", "Nifty Smallcap 100",
        "Nifty Microcap 250", "Nifty LargeMidcap 250", "Nifty MidSmallcap 400",
    ],
    "sectoral": [
        "Nifty Auto", "Nifty Bank", "Nifty Financial Services",
        "Nifty Financial Services 25/50", "Nifty Financial Services Ex-Bank",
        "Nifty FMCG", "Nifty Healthcare", "Nifty IT", "Nifty Media",
        "Nifty Metal", "Nifty Pharma", "Nifty Private Bank", "Nifty PSU Bank",
        "Nifty Realty", "Nifty Consumer Durables", "Nifty Oil and Gas",
        "Nifty MidSmall Financial Services", "Nifty MidSmall Healthcare",
        "Nifty MidSmall IT & Telecom",
    ],
    "thematic": [
        "Nifty Capital Markets", "Nifty Commodities", "Nifty Core Housing",
        "Nifty CPSE", "Nifty EV & New Age Automotive", "Nifty Energy",
        "Nifty Housing", "Nifty India Consumption", "Nifty India Defence",
        "Nifty India Digital", "Nifty India Manufacturing",
        "Nifty India New Age Consumption", "Nifty India Railways PSU",
        "Nifty India Tourism", "Nifty Infrastructure", "Nifty IPO",
        "Nifty MidSmall India Consumption", "Nifty MNC", "Nifty Mobility",
        "Nifty PSE", "Nifty Rural", "Nifty Non-Cyclical Consumer",
        "Nifty Services Sector",
    ],
    "etf": ["Indian ETF", "Nasdaq ETF"],
    "nasdaq": ["Nasdaq-100"],
}

CATEGORY_LABELS = {
    "equity": "Equity",
    "sectoral": "Sectoral",
    "thematic": "Thematic",
    "etf": "ETF",
    "nasdaq": "Nasdaq",
}

VIEW_LABELS = {
    "consolidated": "Consolidated View",
    "mva": "Moving Average View",
    "momentum": "Momentum View",
}
