"""
dcf_core.py - data layer + valuation engine. 
Features AI Anomaly Detection, Expanded Valuation Metrics, and Analyst Safeguards.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from email.utils import parsedate_to_datetime
from io import BytesIO, StringIO
from urllib.parse import quote
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

CR = 1e7

NSE_URLS = [
    "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
    "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
]
_FALLBACK = {
    "RELIANCE": "Reliance Industries Limited", "TCS": "Tata Consultancy Services Limited",
    "INFY": "Infosys Limited", "HDFCBANK": "HDFC Bank Limited", "ICICIBANK": "ICICI Bank Limited",
    "ITC": "ITC Limited", "HINDUNILVR": "Hindustan Unilever Limited", "LT": "Larsen & Toubro Limited",
    "ASIANPAINT": "Asian Paints Limited", "TATASTEEL": "Tata Steel Limited",
    "MARUTI": "Maruti Suzuki India Limited", "SUNPHARMA": "Sun Pharmaceutical Industries Limited",
    "BAJFINANCE": "Bajaj Finance Limited", "TITAN": "Titan Company Limited",
    "NESTLEIND": "Nestle India Limited", "ULTRACEMCO": "UltraTech Cement Limited",
    "WIPRO": "Wipro Limited", "HCLTECH": "HCL Technologies Limited", "DMART": "Avenue Supermarts Limited",
    "IRCTC": "Indian Railway Catering And Tourism Corporation Limited", "SUZLON": "Suzlon Energy Limited",
    "ZOMATO": "Zomato Limited", "ADANIPORTS": "Adani Ports and Special Economic Zone Limited",
    "POWERGRID": "Power Grid Corporation of India Limited", "NTPC": "NTPC Limited",
}


def load_nse_list() -> tuple[pd.DataFrame, str]:
    try:
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
        for url in NSE_URLS:
            try:
                r = requests.get(url, headers=headers, timeout=15)
                r.raise_for_status()
                df = pd.read_csv(StringIO(r.text))
                df.columns = [c.strip() for c in df.columns]
                df = df.rename(columns={"SYMBOL": "symbol", "NAME OF COMPANY": "name"})
                if {"symbol", "name"} <= set(df.columns) and len(df) > 500:
                    df = df[["symbol", "name"]].dropna().drop_duplicates("symbol").reset_index(drop=True)
                    return df, f"NSE live list ({len(df):,} companies)"
            except Exception:
                continue
    except Exception:
        pass
    df = pd.DataFrame({"symbol": list(_FALLBACK), "name": list(_FALLBACK.values())})
    return df, f"built-in fallback list ({len(df)} companies; NSE download failed)"


def search_companies(df: pd.DataFrame, query: str, limit: int = 15) -> pd.DataFrame:
    q = query.strip().lower()
    if not q:
        return df.head(0)
    sym, name = df["symbol"].str.lower(), df["name"].str.lower()
    rank = np.select([sym == q, sym.str.startswith(q), name.str.startswith(q),
                      name.str.contains(q, regex=False) | sym.str.contains(q, regex=False)],
                     [0, 1, 2, 3], default=9)
    return df[rank < 9].assign(_r=rank[rank < 9]).sort_values(["_r", "name"]).drop(columns="_r").head(limit)


def _safe_float(x, default=None):
    if x is None:
        return default
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if np.isfinite(v) else default


def _get_latest(df, names):
    if df is None or getattr(df, "empty", True):
        return None
    for n in names:
        if n in df.index:
            s = pd.to_numeric(df.loc[n], errors="coerce").dropna()
            if len(s):
                return float(s.iloc[0])
    return None


def calculate_ratios(ticker, price: float | None, shares_out: float | None) -> dict:
    """Calculates expanded valuation metrics from raw statements."""
    try:
        inc = ticker.financials
        bs = ticker.balance_sheet
        cf = ticker.cashflow
    except Exception:
        return {"source": "Calculation Failed"}

    revenue = _get_latest(inc, ["Total Revenue", "Operating Revenue"])
    ebit = _get_latest(inc, ["EBIT", "Operating Income"])
    net_income = _get_latest(inc, ["Net Income", "Net Income Common Stockholders"])
    
    total_assets = _get_latest(bs, ["Total Assets"])
    curr_assets = _get_latest(bs, ["Current Assets", "Total Current Assets"])
    curr_liab = _get_latest(bs, ["Current Liabilities", "Total Current Liabilities"])
    total_debt = _get_latest(bs, ["Total Debt"])
    cash = _get_latest(bs, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"])
    equity = _get_latest(bs, ["Stockholders Equity", "Total Equity Gross Minority Interest"])
    
    op_cash = _get_latest(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
    capex = _get_latest(cf, ["Capital Expenditure", "Purchase Of PPE"])
    capex = abs(capex) if capex is not None else 0

    div_yield = None
    try:
        divs = ticker.dividends
        if divs is not None and len(divs) > 0 and price and price > 0:
            one_year_ago = datetime.now() - timedelta(days=365)
            if divs.index.tz is not None:
                one_year_ago = pd.Timestamp(one_year_ago).tz_localize(divs.index.tz)
            else:
                one_year_ago = pd.Timestamp(one_year_ago)
            ttm_divs = divs[divs.index > one_year_ago]
            div_yield = ttm_divs.sum() / price
    except Exception:
        pass

    roe = (net_income / equity) if (net_income is not None and equity and equity > 0) else None
    opm = (ebit / revenue) if (ebit is not None and revenue and revenue > 0) else None
    npm = (net_income / revenue) if (net_income is not None and revenue and revenue > 0) else None
    
    de = (total_debt / equity) if (total_debt is not None and equity and equity > 0) else None
    cr = (curr_assets / curr_liab) if (curr_assets is not None and curr_liab and curr_liab > 0) else None
    
    capital_employed = (total_assets - curr_liab) if (total_assets is not None and curr_liab is not None) else None
    roce = (ebit / capital_employed) if (ebit is not None and capital_employed and capital_employed > 0) else None

    # --- Expanded Valuation Metrics ---
    eps = _safe_float(ticker.info.get("trailingEps"))
    pe = (price / eps) if (price and eps and eps > 0) else None
    
    book_value = (equity / shares_out) if (equity is not None and shares_out and shares_out > 0) else None
    pb = (price / book_value) if (price and book_value and book_value > 0) else None
    
    mcap = price * shares_out if (price and shares_out) else None
    ps = (mcap / revenue) if (mcap and revenue and revenue > 0) else None
    
    ev = (mcap + (total_debt or 0) - (cash or 0)) if mcap else None
    ev_ebit = (ev / ebit) if (ev and ebit and ebit > 0) else None
    
    fcf = (op_cash - capex) if op_cash is not None else None
    fcf_yield = (fcf / mcap) if (fcf and mcap and mcap > 0) else None
    
    peg = None
    if pe and ticker.info.get("earningsGrowth") and ticker.info["earningsGrowth"] > 0:
        peg = pe / (ticker.info["earningsGrowth"] * 100)
    elif pe and ticker.info.get("pegRatio"):
        peg = _safe_float(ticker.info["pegRatio"])

    return {
        "source": "Statements",
        "roe": roe, "roce": roce, "opm": opm, "npm": npm,
        "debt_to_equity": de, "current_ratio": cr,
        "pe_ratio": pe, "pb_ratio": pb, "div_yield": div_yield,
        "ps_ratio": ps, "ev_ebit": ev_ebit, "fcf_yield": fcf_yield, "peg": peg,
    }


@dataclass
class CompanyData:
    symbol: str
    name: str = ""
    sector: str | None = None
    price: float | None = None
    shares: float | None = None
    cash_cr: float | None = None
    debt_cr: float | None = None
    minority_cr: float | None = None
    mcap_cr: float | None = None
    ttm_revenue_cr: float | None = None
    beta: float | None = None
    eps: float | None = None
    targets: tuple | None = None
    n_analysts: int | None = None
    recommendation: str | None = None
    hist: pd.DataFrame = field(default_factory=pd.DataFrame)
    range52: tuple | None = None
    warnings: list = field(default_factory=list)
    ratios: dict = field(default_factory=dict)
    ratio_source: str = ""

    def available(self) -> dict:
        h = self.hist
        has = lambda c: (c in h.columns) and h[c].notna().any()
        return {"price": self.price is not None, "shares": self.shares is not None,
                "revenue": has("revenue"), "ebit": has("ebit"), "da": has("da"),
                "capex": has("capex"), "tax": has("tax") and has("pretax"),
                "cash": self.cash_cr is not None, "debt": self.debt_cr is not None,
                "minority": self.minority_cr is not None}


def _pick(df, names):
    if df is None or getattr(df, "empty", True):
        return None
    for n in names:
        if n in df.index:
            s = pd.to_numeric(df.loc[n], errors="coerce").dropna()
            if len(s):
                return s
    return None


def fetch_company(symbol: str) -> CompanyData:
    cd = CompanyData(symbol=symbol, name=symbol)
    try:
        import yfinance as yf
    except ImportError:
        cd.warnings.append("yfinance is not installed.")
        return cd
    try:
        t = yf.Ticker(f"{symbol}.NS")
        info = {}
        try:
            info = t.info or {}
        except Exception:
            cd.warnings.append("Yahoo company profile unavailable.")
        cd.name = info.get("longName") or info.get("shortName") or symbol
        cd.sector = info.get("sector")
        cd.price = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
        
        # Share count override
        yahoo_shares = _safe_float(info.get("sharesOutstanding"))
        if info.get("marketCap") and cd.price and cd.price > 0:
            cd.mcap_cr = _safe_float(info["marketCap"]) / CR
            implied_shares = (cd.mcap_cr * CR) / cd.price
            if yahoo_shares is None or (abs(yahoo_shares - implied_shares) / implied_shares > 0.10):
                cd.shares = implied_shares
                cd.warnings.append("Yahoo's reported share count was severely mismatched with Market Cap. Corrected using implied shares.")
            else:
                cd.shares = yahoo_shares
        else:
            cd.shares = yahoo_shares

        cd.beta = _safe_float(info.get("beta"))
        cd.eps = _safe_float(info.get("trailingEps"))
        cd.n_analysts = info.get("numberOfAnalystOpinions")
        cd.recommendation = info.get("recommendationKey")
        
        fin_currency = info.get("financialCurrency", "INR")
        if fin_currency != "INR":
            cd.warnings.append(f"CRITICAL WARNING: Financial statements are reported in {fin_currency}. A standard DCF will produce wildly inaccurate results.")

        ratios = calculate_ratios(t, cd.price, cd.shares)
        cd.ratios = ratios
        cd.ratio_source = ratios.get("source", "Statements")

        tl, tm, th = (info.get(k) for k in ("targetLowPrice", "targetMeanPrice", "targetHighPrice"))
        if all(tl and tm and th and _safe_float(v) is not None for v in (tl, tm, th)):
            cd.targets = (_safe_float(tl), _safe_float(tm), _safe_float(th))
        try:
            fi = t.fast_info
            if cd.price is None:
                cd.price = _safe_float(fi.get("last_price"))
            if cd.shares is None:
                cd.shares = _safe_float(fi.get("shares"))
        except Exception:
            pass

        inc, bs, cf = t.financials, t.balance_sheet, t.cashflow
        da = _pick(cf, ["Depreciation And Amortization", "Depreciation Amortization Depletion"])
        if da is None:
            da = _pick(inc, ["Reconciled Depreciation"])
        capex = _pick(cf, ["Capital Expenditure", "Purchase Of PPE"])
        series = {
            "revenue": _pick(inc, ["Total Revenue", "Operating Revenue"]),
            "ebit": _pick(inc, ["EBIT", "Operating Income"]),
            "tax": _pick(inc, ["Tax Provision"]), "pretax": _pick(inc, ["Pretax Income"]),
            "da": da, "capex": capex.abs() if capex is not None else None,
        }
        series = {k: v for k, v in series.items() if v is not None}
        if series:
            h = pd.DataFrame(series)
            h.index = pd.to_datetime(h.index).year
            cd.hist = h[~h.index.duplicated()].sort_index() / CR

        try:
            q = _pick(t.quarterly_financials, ["Total Revenue", "Operating Revenue"])
            if q is not None and len(q) >= 4:
                q = q.sort_index(ascending=False)
                if (pd.Timestamp.today() - pd.Timestamp(q.index[0])).days < 400:
                    cd.ttm_revenue_cr = float(q.iloc[:4].sum()) / CR
        except Exception:
            pass
        cash = _pick(bs, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"])
        debt = _pick(bs, ["Total Debt"])
        mino = _pick(bs, ["Minority Interest"])
        cd.cash_cr = _safe_float(cash.iloc[0]) / CR if cash is not None else None
        cd.debt_cr = _safe_float(debt.iloc[0]) / CR if debt is not None else None
        cd.minority_cr = _safe_float(mino.iloc[0]) / CR if mino is not None else None
        try:
            hh = t.history(period="1y")
            if len(hh):
                cd.range52 = (float(hh["Low"].min()), float(hh["High"].max()))
        except Exception:
            pass
    except Exception as e:
        cd.warnings.append(f"Data fetch failed: {type(e).__name__}: {e}")

    if cd.sector and "financial" in cd.sector.lower():
        cd.warnings.append("CRITICAL WARNING: This is a bank/financial company. A standard FCFF DCF is mathematically invalid for banks.")

    return cd


def suggest_assumptions(cd: CompanyData) -> tuple[dict, list]:
    h, notes = cd.hist, []

    def ratio(col, lo, hi, default, label):
        if col in h.columns and "revenue" in h.columns:
            r = (h[col] / h["revenue"]).replace([np.inf, -np.inf], np.nan).dropna().tail(3)
            if len(r):
                return float(np.clip(r.mean(), lo, hi))
        notes.append(f"{label}: no data found, default {default:.0%} used.")
        return default

    growth, rev0 = 0.10, 0.0
    if "revenue" in h.columns and h["revenue"].notna().any():
        rev = h["revenue"].dropna()
        rev0 = float(rev.iloc[-1])
        
        if len(rev) >= 3:
            cagr = (rev.iloc[-1] / rev.iloc[0]) ** (1 / (len(rev) - 1)) - 1
            yoy = rev.pct_change().dropna()
            median_yoy = yoy.median()
            
            blended_growth = (cagr * 0.4) + (median_yoy * 0.6)
            growth = float(np.clip(blended_growth, -0.15, 0.30))
            
            if yoy.min() < -0.20:
                # CONTEXTUAL AI ANOMALY DETECTION (1-YEAR LOOKBACK)
                news_items = fetch_news(cd.name, limit=50, days=365)
                titles = " ".join([n["title"].lower() for n in news_items])
                
                demerger_words = ["demerger", "spin-off", "spin off", "scheme of arrangement", "hiving off", "merger"]
                distress_words = ["loss", "fraud", "penalty", "market share", "probe", "downgrade", "ban", "slump", "decline"]
                
                is_demerger = any(w in titles for w in demerger_words)
                is_distress = any(w in titles for w in distress_words)
                
                if is_demerger:
                    notes.append("🤖 AI ANALYSIS: A massive revenue drop was detected, and recent news confirms a demerger/restructuring. The model has automatically smoothed the historical growth rate to reflect the new entity.")
                elif is_distress:
                    notes.append("🚨 AI ANALYSIS: A massive revenue drop was detected, and recent news points to operational distress (losses/penalties). The model has not artificially inflated the growth rate. Please review the assumptions.")
                else:
                    notes.append("⚠️ AI ANALYSIS: A massive revenue drop was detected, but the news context is unclear. The model has smoothed the growth rate, but manual verification is required.")
        elif len(rev) >= 2:
            growth = float(np.clip((rev.iloc[-1] / rev.iloc[0]) ** (1 / (len(rev) - 1)) - 1, -0.15, 0.30))
        else:
            notes.append("Revenue growth: not enough history, default 10% used.")
    else:
        notes.append("Revenue: no data found, please enter it manually.")

    tax = 0.25
    if {"tax", "pretax"} <= set(h.columns):
        r = (h["tax"] / h["pretax"]).where(h["pretax"] > 0).replace([np.inf, -np.inf], np.nan).dropna().tail(3)
        if len(r):
            tax = float(np.clip(r.mean(), 0.15, 0.35))
    else:
        notes.append("Tax rate: no data found, default 25% used.")

    ebit_margin = ratio("ebit", -0.1, 0.6, 0.15, "EBIT margin")
    da_pct = ratio("da", 0.0, 0.3, 0.04, "D&A")
    capex_pct = ratio("capex", 0.0, 0.25, 0.05, "Capex")

    if ebit_margin < 0.02 and rev0 > 1000:
        notes.append("WARNING: The historical EBIT margin is extremely low (<2%). This is likely due to a recent demerger, one-off losses, or a capital-intensive phase.")

    basis = "last fiscal year"
    if cd.ttm_revenue_cr and cd.ttm_revenue_cr > 0:
        rev0, basis = cd.ttm_revenue_cr, "trailing 12 months"
        
    return {"revenue0": rev0, "revenue_basis": basis, "growth": growth,
            "ebit_margin": ebit_margin, "tax_rate": tax,
            "da_pct": da_pct, "capex_pct": capex_pct,
            "nwc_pct": 0.10}, notes


@dataclass(frozen=True)
class DCFInputs:
    revenue0: float
    growth: float
    ebit_margin: float
    tax_rate: float
    da_pct: float
    capex_pct: float
    nwc_pct: float
    wacc: float
    terminal_growth: float
    net_debt: float
    shares_cr: float
    years: int = 5
    minority: float = 0.0
    terminal_capex_pct: float | None = None


def _cash_flow_year(i: DCFInputs, rev: float, prev_rev: float, capex_pct: float | None = None) -> dict:
    ebit = rev * i.ebit_margin
    tax = max(ebit, 0.0) * i.tax_rate
    nopat = ebit - tax
    da, d_nwc = rev * i.da_pct, (rev - prev_rev) * i.nwc_pct
    capex = rev * (i.capex_pct if capex_pct is None else capex_pct)
    return {"Revenue": rev, "EBIT": ebit, "Tax on EBIT": tax, "NOPAT": nopat, "D&A": da, "Capex": capex,
            "Increase in NWC": d_nwc, "FCFF": nopat + da - capex - d_nwc, "EBITDA": ebit + da}


def project(i: DCFInputs) -> pd.DataFrame:
    rows, prev = [], i.revenue0
    for t in range(1, i.years + 1):
        rev = i.revenue0 * (1 + i.growth) ** t
        rows.append({"Year": t, **_cash_flow_year(i, rev, prev)})
        prev = rev
    df = pd.DataFrame(rows).set_index("Year")
    df["Discount factor"] = 1 / (1 + i.wacc) ** df.index.values
    df["PV of FCFF"] = df["FCFF"] * df["Discount factor"]
    return df


def terminal_year(i: DCFInputs) -> dict:
    rev_n = i.revenue0 * (1 + i.growth) ** i.years
    return _cash_flow_year(i, rev_n * (1 + i.terminal_growth), rev_n, i.terminal_capex_pct)


def value(i: DCFInputs) -> dict:
    tbl, term = project(i), terminal_year(i)
    pv_fcff = float(tbl["PV of FCFF"].sum())
    out = dict(table=tbl, terminal=term, pv_fcff=pv_fcff, tv=np.nan, pv_tv=np.nan, ev=np.nan,
               equity=np.nan, per_share=np.nan, tv_share=np.nan, exit_multiple=np.nan)
    if i.wacc <= i.terminal_growth or i.shares_cr <= 0:
        return out
    tv = term["FCFF"] / (i.wacc - i.terminal_growth)
    pv_tv = tv / (1 + i.wacc) ** i.years
    ev = pv_fcff + pv_tv
    equity = ev - i.net_debt - i.minority
    n_ebitda = float(tbl["EBITDA"].iloc[-1])
    out.update(tv=tv, pv_tv=pv_tv, ev=ev, equity=equity, per_share=equity / i.shares_cr,
               tv_share=pv_tv / ev if ev else np.nan, exit_multiple=tv / n_ebitda if n_ebitda > 0 else np.nan)
    return out


def audit(i: DCFInputs) -> tuple[float, float, bool]:
    prev, pv = i.revenue0, 0.0
    for t in range(1, i.years + 1):
        rev = i.revenue0 * (1 + i.growth) ** t
        ebit = rev * i.ebit_margin
        fcff = (ebit - max(ebit, 0.0) * i.tax_rate) + rev * i.da_pct - rev * i.capex_pct - (rev - prev) * i.nwc_pct
        pv += fcff / (1 + i.wacc) ** t
        prev = rev
    rev_t = prev * (1 + i.terminal_growth)
    ebit_t = rev_t * i.ebit_margin
    cx_t = i.capex_pct if i.terminal_capex_pct is None else i.terminal_capex_pct
    fcff_t = ((ebit_t - max(ebit_t, 0.0) * i.tax_rate) + rev_t * i.da_pct - rev_t * cx_t
              - (rev_t - prev) * i.nwc_pct)
    ps = (pv + fcff_t / (i.wacc - i.terminal_growth) / (1 + i.wacc) ** i.years
          - i.net_debt - i.minority) / i.shares_cr
    eng = value(i)["per_share"]
    return ps, abs(ps - eng), bool(abs(ps - eng) < 1e-6 * max(1.0, abs(ps)))


def sanity_checks(i: DCFInputs, r: dict) -> list[tuple[str, str]]:
    if not np.isfinite(r["per_share"]):
        return [("bad", "WACC must be above terminal growth, otherwise the terminal value cannot be computed.")]
    out = []
    if r["equity"] <= 0:
        out.append(("bad", "Equity value is zero or negative: net debt and minority interest exceed enterprise value."))
    if r["terminal"]["FCFF"] <= 0:
        out.append(("bad", "Terminal-year free cash flow is not positive, so the terminal value is meaningless. "
                           "Raise the margin or lower capex."))
    if i.wacc - i.terminal_growth < 0.03:
        out.append(("warn", f"WACC minus terminal growth is only {(i.wacc - i.terminal_growth) * 100:.1f} pp. "
                            "Value is extremely sensitive when this gap is small."))
    if r["tv_share"] > 0.80:
        out.append(("warn", f"{r['tv_share'] * 100:.0f}% of enterprise value is terminal value, so the answer "
                            f"rests mostly on what happens after year {i.years}."))
    em = r["exit_multiple"]
    if np.isfinite(em) and em > 25:
        out.append(("warn", f"Terminal value implies {em:.1f}x EV/EBITDA, which is very rich."))
    if np.isfinite(em) and 0 < em < 4:
        out.append(("warn", f"Terminal value implies only {em:.1f}x EV/EBITDA, which is very low."))
    cx_t = i.capex_pct if i.terminal_capex_pct is None else i.terminal_capex_pct
    if cx_t < i.da_pct:
        out.append(("warn", "Final-year capex is below D&A, so the company is assumed to grow forever while "
                            "investing less than it depreciates. Raise terminal capex to at least D&A."))
    if i.terminal_growth > 0.06:
        out.append(("warn", "Terminal growth above 6% is hard to justify as a perpetual rate."))
    return out or [("ok", "No red flags found in the main model checks.")]


SCENARIOS = {
    "Bear": dict(growth=-0.02, ebit_margin=-0.015, wacc=+0.005, terminal_growth=-0.005),
    "Base": dict(growth=0.0, ebit_margin=0.0, wacc=0.0, terminal_growth=0.0),
    "Bull": dict(growth=+0.02, ebit_margin=+0.010, wacc=-0.005, terminal_growth=+0.005),
}


def apply_scenario(base: DCFInputs, name: str) -> DCFInputs:
    d = SCENARIOS[name]
    return replace(base, growth=base.growth + d["growth"], ebit_margin=base.ebit_margin + d["ebit_margin"],
                   wacc=base.wacc + d["wacc"], terminal_growth=base.terminal_growth + d["terminal_growth"])


def sensitivity(i: DCFInputs, wacc_span=0.02, wacc_step=0.005, g_span=0.0075, g_step=0.0025) -> pd.DataFrame:
    waccs = np.round(i.wacc + np.arange(-wacc_span, wacc_span + 1e-9, wacc_step), 5)
    gs = np.round(i.terminal_growth + np.arange(-g_span, g_span + 1e-9, g_step), 5)
    grid = pd.DataFrame(index=waccs, columns=gs, dtype=float)
    for w in waccs:
        for g in gs:
            grid.loc[w, g] = value(replace(i, wacc=float(w), terminal_growth=float(g)))["per_share"]
    return grid


def verdict(per_share: float, price: float, band: float = 0.10) -> tuple[str, str, float]:
    if not np.isfinite(per_share) or not price or price <= 0:
        return "n/a", "grey", float("nan")
    d = per_share / price - 1
    if d > band:
        return "undervalued", "green", d
    if d < -band:
        return "overvalued", "red", d
    return "fairly valued", "yellow", d


def wacc_calc(rf: float, erp: float, beta: float, kd_pre: float, tax: float,
              mcap_cr: float, debt_cr: float) -> dict:
    ke, kd = rf + beta * erp, kd_pre * (1 - tax)
    e, d = max(mcap_cr, 0.0), max(debt_cr, 0.0)
    we = e / (e + d) if e + d > 0 else 1.0
    return dict(ke=ke, kd_after=kd, we=we, wd=1 - we, wacc=we * ke + (1 - we) * kd)


def hist_stats(hist: pd.DataFrame) -> dict:
    st = {}
    if "revenue" in hist.columns and hist["revenue"].notna().sum() >= 2:
        rev = hist["revenue"].dropna()
        yoy = rev.pct_change().dropna()
        if rev.iloc[0] > 0 and rev.iloc[-1] > 0:
            st.update(n=len(rev) - 1, cagr=(rev.iloc[-1] / rev.iloc[0]) ** (1 / (len(rev) - 1)) - 1,
                      best=float(yoy.max()), worst=float(yoy.min()))
    if {"revenue", "ebit"} <= set(hist.columns):
        m = (hist["ebit"] / hist["revenue"]).replace([np.inf, -np.inf], np.nan).dropna()
        if len(m):
            st.update(m_last=float(m.iloc[-1]), m_min=float(m.min()), m_max=float(m.max()))
    return st


DRIVERS = {
    "Bear": "What would push the company here: slower demand or lost market share, rising input costs or "
            "competition squeezing margins, regulatory or legal trouble, and higher interest rates or risk "
            "premiums raising the return investors demand.",
    "Base": "What this assumes: the business keeps doing roughly what it has done recently, with no big "
            "surprise in demand, costs or interest rates.",
    "Bull": "What would push the company here: strong demand, new capacity or contracts, operating leverage "
            "lifting margins, and lower rates or lower perceived risk reducing the discount rate.",
}


def explain_scenario(s: DCFInputs, base: DCFInputs, name: str, stats: dict) -> list[str]:
    out = []
    if "cagr" in stats:
        diff = (s.growth - stats["cagr"]) * 100
        rel = ("in line with" if abs(diff) < 0.5 else f"{abs(diff):.1f} pp {'above' if diff > 0 else 'below'}")
        extra = ""
        if s.growth > stats["best"]:
            extra = f" This is above the best single year in the data ({stats['best']:.1%})."
        elif s.growth < stats["worst"]:
            extra = f" This is below the worst single year in the data ({stats['worst']:.1%})."
        out.append(f"Revenue growth {s.growth:.1%} a year is {rel} the {stats['n']}-year historical growth "
                   f"of {stats['cagr']:.1%}.{extra}")
    else:
        out.append(f"Revenue growth {s.growth:.1%} a year (not enough history to compare).")
    if "m_min" in stats:
        where = ("below" if s.ebit_margin < stats["m_min"] - 5e-4 else
                 "above" if s.ebit_margin > stats["m_max"] + 5e-4 else "within")
        out.append(f"EBIT margin {s.ebit_margin:.1%} is {where} the historical range of "
                   f"{stats['m_min']:.1%} to {stats['m_max']:.1%}.")
    out.append(f"Discount rate (WACC) {s.wacc:.2%} and terminal growth {s.terminal_growth:.2%}"
               + ("." if name == "Base" else f" ({(s.wacc - base.wacc) * 100:+.1f} pp and "
                                              f"{(s.terminal_growth - base.terminal_growth) * 100:+.1f} pp vs base)."))
    return out


def ebitda_last(cd: CompanyData):
    h = cd.hist
    if {"ebit", "da"} <= set(h.columns):
        x = (h["ebit"] + h["da"]).dropna()
        if len(x) and x.iloc[-1] > 0:
            return float(x.iloc[-1])
    return None


def multiples_check(cd: CompanyData, i: DCFInputs, r: dict, price: float) -> list[dict]:
    rows, mkt_ev = [], price * i.shares_cr + i.net_debt + i.minority
    if cd.eps and cd.eps > 0 and np.isfinite(r["per_share"]):
        rows.append(dict(metric="P/E (trailing)", market=price / cd.eps, dcf=r["per_share"] / cd.eps))
    e = ebitda_last(cd)
    if e and np.isfinite(r["ev"]):
        rows.append(dict(metric="EV / EBITDA", market=mkt_ev / e, dcf=r["ev"] / e))
    if i.revenue0 > 0 and np.isfinite(r["ev"]):
        rows.append(dict(metric="EV / Revenue", market=mkt_ev / i.revenue0, dcf=r["ev"] / i.revenue0))
    return rows


_BULL = ["record", "surge", "surges", "jumps", "soars", "rallies", "rally", "beats", "tops estimates", "upgrade",
         "upgrades", "raises target", "order win", "bags order", "wins order", "bags", "expansion", "expands",
         "profit rises", "profit jumps", "profit up", "strong growth", "buy rating", "outperform", "dividend",
         "bonus", "acquires", "acquisition", "launches", "approval", "approves", "robust", "growth", "gains"]
_BEAR = ["falls", "slumps", "plunges", "drops", "misses", "downgrade", "downgrades", "cuts target", "probe",
         "penalty", "fine", "fraud", "loss", "profit falls", "profit declines", "profit down", "slowdown",
         "weak", "concern", "concerns", "sell rating", "underperform", "lawsuit", "raid", "default",
         "resigns", "recall", "ban", "warning", "sinks", "tumbles", "decline", "declines", "cuts", "risk"]


def tag_headline(title: str) -> str:
    t = title.lower()
    b = sum(bool(re.search(rf"\b{re.escape(k)}\b", t)) for k in _BULL)
    d = sum(bool(re.search(rf"\b{re.escape(k)}\b", t)) for k in _BEAR)
    return "bull" if b > d else "bear" if d > b else "neutral"


def fetch_news(name: str, limit: int = 15, days: int = 30) -> list[dict]:
    try:
        import xml.etree.ElementTree as ET
        import requests
        short = re.sub(r"\b(limited|ltd\.?|corporation|corp\.?)\b", "", name, flags=re.I).strip()
        url = (f"https://news.google.com/rss/search?q={quote(short + ' stock when:' + str(days) + 'd')}"
               "&hl=en-IN&gl=IN&ceid=IN:en")
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        items = []
        for it in ET.fromstring(r.content).iter("item"):
            title, src = (it.findtext("title") or "").strip(), (it.findtext("source") or "").strip()
            if src and title.endswith(f" - {src}"):
                title = title[: -len(src) - 3]
            try:
                date = parsedate_to_datetime(it.findtext("pubDate")).strftime("%d %b %Y")
            except Exception:
                date = ""
            items.append(dict(title=title, source=src, link=(it.findtext("link") or "").strip(),
                              date=date, tag=tag_headline(title)))
            if len(items) >= limit:
                break
        return items
    except Exception:
        return []


def export_excel(name: str, scenario: str, i: DCFInputs, r: dict, scen_values: dict,
                 grid: pd.DataFrame, price: float) -> bytes:
    summary = pd.DataFrame([
        ("Company", name), ("Scenario shown", scenario), ("Market price (INR)", price),
        ("Value per share (INR)", r["per_share"]), ("Enterprise value (INR cr)", r["ev"]),
        ("PV of forecast FCFF (INR cr)", r["pv_fcff"]), ("Terminal value (INR cr)", r["tv"]),
        ("PV of terminal value (INR cr)", r["pv_tv"]), ("Net debt (INR cr)", i.net_debt),
        ("Minority interest (INR cr)", i.minority), ("Equity value (INR cr)", r["equity"]),
        ("Shares (crore)", i.shares_cr), ("Latest revenue (INR cr)", i.revenue0),
        ("Revenue growth", i.growth), ("EBIT margin", i.ebit_margin), ("Tax rate", i.tax_rate),
        ("D&A % revenue", i.da_pct), ("Capex % revenue", i.capex_pct),
        ("NWC % of revenue increase", i.nwc_pct), ("Forecast years", i.years), ("WACC", i.wacc),
        ("Terminal growth", i.terminal_growth),
    ], columns=["Item", "Value"])
    g = grid.copy()
    g.index = [f"WACC {x * 100:.1f}%" for x in g.index]
    g.columns = [f"g {x * 100:.2f}%" for x in g.columns]
    scen = pd.DataFrame({"Scenario": list(scen_values), "Value per share (INR)": list(scen_values.values()),
                         "vs market": [v / price - 1 if price else None for v in scen_values.values()]})
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        summary.to_excel(xw, sheet_name="Summary", index=False)
        r["table"].round(2).to_excel(xw, sheet_name="Projection")
        g.round(1).to_excel(xw, sheet_name="Sensitivity")
        scen.to_excel(xw, sheet_name="Scenarios", index=False)
        for ws in xw.sheets.values():
            ws.column_dimensions["A"].width = 34
            for col in "BCDEFGHIJKL":
                ws.column_dimensions[col].width = 18
    return buf.getvalue()


def implied_growth(i: DCFInputs, price: float):
    f = lambda g: value(replace(i, growth=g))["per_share"] - price
    lo, hi = -0.20, 0.60
    flo, fhi = f(lo), f(hi)
    if not (np.isfinite(flo) and np.isfinite(fhi)) or flo * fhi > 0:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        fm = f(mid)
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def data_checks(cd: CompanyData, price: float, shares_cr: float) -> list[tuple[str, str]]:
    out = []
    if cd.mcap_cr and price > 0 and shares_cr > 0:
        gap = price * shares_cr / cd.mcap_cr - 1
        if abs(gap) > 0.15:
            out.append(("warn", f"Price x shares is {gap:+.0%} different from Yahoo's market cap "
                                f"(₹{cd.mcap_cr:,.0f} cr). The share count or price may be wrong: please check both "
                                "against NSE or Screener."))
        else:
            out.append(("ok", "Price x shares matches Yahoo's market cap, so the share count looks right."))
    if cd.ttm_revenue_cr and "revenue" in cd.hist.columns and cd.hist["revenue"].notna().any():
        last = float(cd.hist["revenue"].dropna().iloc[-1])
        if last > 0 and abs(cd.ttm_revenue_cr / last - 1) > 0.5:
            out.append(("warn", "Trailing-12-month revenue differs by more than 50% from the last annual figure. "
                                "Check for a recent merger, demerger or data error."))
    if cd.sector and "financial" in cd.sector.lower():
        out.append(("warn", "This is a bank/financial company. A standard DCF does not suit it, so ignore the result."))
    return out


def verify_links(symbol: str) -> list[tuple[str, str]]:
    return [("Google Finance", f"https://www.google.com/finance/quote/{symbol}:NSE"),
            ("Screener.in", f"https://www.screener.in/company/{symbol}/"),
            ("NSE India", f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"),
            ("Yahoo Finance", f"https://finance.yahoo.com/quote/{symbol}.NS")]


def gap_sentence(ours: float, ref: float, ref_name: str) -> str:
    if not (np.isfinite(ours) and ref and ref > 0):
        return ""
    d = ours / ref - 1
    how = "about the same as" if abs(d) < 0.05 else f"{abs(d):.0%} {'above' if d > 0 else 'below'}"
    return f"Our Base value is {how} {ref_name} (₹{ref:,.0f})."


def scenario_blurb(name: str, s: DCFInputs, stats: dict) -> str:
    g = f"revenue grows {s.growth:.1%} a year"
    if "cagr" in stats:
        g += f" (past {stats['n']} years: {stats['cagr']:.1%})"
    m = f"profit margin is {s.ebit_margin:.1%}"
    if "m_last" in stats:
        m += f" (last year: {stats['m_last']:.1%})"
    r = f"investors demand a {s.wacc:.1%} return"
    lead = {"Bear": "Things go worse than usual: ", "Base": "Things continue as they have: ",
            "Bull": "Things go better than usual: "}[name]
    return f"{lead}{g}, {m}, and {r}."
