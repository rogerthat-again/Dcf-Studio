"""app.py - DCF Studio: a simple valuation dashboard for NSE-listed companies."""
import inspect

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import dcf_charts as ch
import dcf_core as dc
import dcf_ui as ui

st.set_page_config(page_title="DCF Studio | NSE valuation", layout="wide", initial_sidebar_state="auto")
st.markdown(ui.CSS, unsafe_allow_html=True)
components.html(ui.TOUCH_JS, height=0)


def _stretch(fn):
    return {"width": "stretch"} if "width" in inspect.signature(fn).parameters else {"use_container_width": True}


PLOT_CFG = dict(displayModeBar=False, scrollZoom=False, responsive=True)


def show(fig):
    st.plotly_chart(fig, config=PLOT_CFG, **_stretch(st.plotly_chart))


def table(df):
    st.dataframe(df, **_stretch(st.dataframe))


def money(x, dec=0):
    return "n/a" if x is None or not np.isfinite(x) else f"₹{x:,.{dec}f}"


@st.cache_data(ttl=86400, show_spinner="Loading NSE company list...")
def nse_list():
    return dc.load_nse_list()


@st.cache_data(ttl=3600, show_spinner="Fetching financials...")
def company(symbol):
    return dc.fetch_company(symbol)


@st.cache_data(ttl=1800, show_spinner="Reading recent headlines...")
def news(name):
    return dc.fetch_news(name)


companies, list_source = nse_list()
with st.sidebar:
    st.markdown("<div class='brand'>DCF Studio</div><div class='brand-sub'>NSE valuation lab</div>", unsafe_allow_html=True)
    query = st.text_input("Search company or NSE symbol", value="Reliance")
    matches = dc.search_companies(companies, query)
    if matches.empty:
        st.warning("No company found. Try a different name or the NSE symbol.")
        st.stop()
    labels = [f"{r.name} ({r.symbol})" for r in matches.itertuples()]
    symbol = matches.iloc[labels.index(st.selectbox("Select company", labels))]["symbol"]
    live_slot = st.container()

cd = company(symbol)
sug, notes = dc.suggest_assumptions(cd)
k = symbol

with st.sidebar.expander("Main assumptions", expanded=True):
    growth = st.number_input("Revenue growth (% per year)", -20.0, 40.0, round(sug["growth"] * 100, 1), 0.5, key=f"{k}_g") / 100
    margin = st.number_input("Profit margin (%)", -20.0, 60.0, round(sug["ebit_margin"] * 100, 1), 0.5, key=f"{k}_m") / 100
    tg = st.number_input("Long-run growth after year 5 (%)", 0.0, 8.0, 5.0, 0.25, key=f"{k}_tg") / 100
    w_mode = st.radio("Required return (WACC)", ["I enter it", "Build it (CAPM)"], horizontal=True, key=f"{k}_wm")
    wacc_manual = st.number_input("WACC (%)", 5.0, 25.0, 11.0, 0.25, key=f"{k}_w") / 100

with st.sidebar.expander("Company numbers"):
    price = st.number_input("CMP: market price (₹)", 0.0, value=float(round(cd.price or 0.0, 2)), step=10.0, key=f"{k}_px")
    revenue0 = st.number_input("Starting revenue (₹ cr)", 0.0, value=float(round(sug["revenue0"], 1)), step=100.0, key=f"{k}_rev")
    shares_cr = st.number_input("Shares outstanding (crore)", 0.0, value=float(round((cd.shares or 0) / dc.CR, 3)), step=1.0, key=f"{k}_sh")
    net_debt = st.number_input("Net debt (₹ cr)", value=float(round((cd.debt_cr or 0.0) - (cd.cash_cr or 0.0), 1)), step=100.0, key=f"{k}_nd")
    minority = st.number_input("Minority interest (₹ cr)", 0.0, value=float(round(max(cd.minority_cr or 0.0, 0.0), 1)), step=100.0, key=f"{k}_mi")

with st.sidebar.expander("More assumptions"):
    tax = st.number_input("Tax rate (%)", 0.0, 50.0, round(sug["tax_rate"] * 100, 1), 0.5, key=f"{k}_t") / 100
    da = st.number_input("Depreciation (% of revenue)", 0.0, 30.0, round(sug["da_pct"] * 100, 1), 0.5, key=f"{k}_da") / 100
    capex = st.number_input("Capex, forecast years (% of revenue)", 0.0, 30.0, round(sug["capex_pct"] * 100, 1), 0.5, key=f"{k}_cx") / 100
    tcx = st.number_input("Capex in the 'forever' year (x depreciation)", 0.5, 3.0, 1.3, 0.1, key=f"{k}_tcx")
    nwc = st.number_input("Working capital (% of revenue increase)", 0.0, 50.0, round(sug["nwc_pct"] * 100, 1), 1.0, key=f"{k}_nwc") / 100

wacc = wacc_manual
if w_mode == "Build it (CAPM)":
    with st.sidebar.expander("Build WACC (CAPM)", expanded=True):
        rf = st.number_input("Risk-free rate (%)", 0.0, 15.0, 7.0, 0.05, key=f"{k}_rf") / 100
        beta = st.number_input("Beta", 0.0, 3.0, float(np.clip(round(cd.beta, 2), 0.0, 3.0)) if cd.beta else 1.0, 0.05, key=f"{k}_beta")
        erp = st.number_input("Extra return for stocks (%)", 0.0, 15.0, 6.5, 0.25, key=f"{k}_erp") / 100
        kd = st.number_input("Interest on debt (%)", 0.0, 20.0, 9.0, 0.25, key=f"{k}_kd") / 100
        wc = dc.wacc_calc(rf, erp, beta, kd, tax, price * shares_cr, max(cd.debt_cr or 0.0, 0.0))
        wacc = float(np.clip(wc["wacc"], 0.05, 0.25))
        st.info(f"Shareholders want {wc['ke']:.2%}. WACC = {wacc:.2%}.")
if st.sidebar.button("Refresh data from the web"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption(f"Company list: {list_source}")

for w in cd.warnings:
    st.warning(w)
hero_slot = st.container()
selected = st.radio("Explore a case", ["Bear", "Base", "Bull"], index=1, horizontal=True)
tab_over, tab_ratios, tab_why, tab_math, tab_more = st.tabs(["Overview", "Financial Ratios", "Why this price", "Show the math", "More tools"])

if revenue0 <= 0 or shares_cr <= 0 or price <= 0:
    st.error("Revenue, shares outstanding and CMP must all be above zero.")
    st.stop()
base = dc.DCFInputs(revenue0, growth, margin, tax, da, capex, nwc, wacc, tg, net_debt, shares_cr, 5, minority, da * tcx)
if base.wacc <= base.terminal_growth:
    st.error("WACC must be above long-run growth.")
    st.stop()

scen = {s: dc.apply_scenario(base, s) for s in dc.SCENARIOS}
vals = {s: dc.value(scen[s]) for s in scen}
per_share = {s: vals[s]["per_share"] for s in vals}
inp, res = scen[selected], vals[selected]
if inp.wacc <= inp.terminal_growth:
    st.error(f"In the {selected} case WACC is not above long-run growth.")
    st.stop()
grid = dc.sensitivity(inp)
label, colour, diff = dc.verdict(res["per_share"], price)
stats = dc.hist_stats(cd.hist)
blurbs = {s: dc.scenario_blurb(s, scen[s], stats) for s in scen}
years = inp.years

hero_slot.markdown(ui.hero_html(cd.name, symbol, cd.sector, selected, res["per_share"], price, diff, label,
                                per_share, sug["revenue_basis"]), unsafe_allow_html=True)
live_slot.markdown(ui.live_html(per_share, price, selected), unsafe_allow_html=True)

with tab_over:
    st.markdown(ui.scenario_cards_html(per_share, price, blurbs, selected), unsafe_allow_html=True)
    st.caption("Each card compares a fair value with today's CMP.")
    st.markdown("#### What if our assumptions are a bit off?")
    show(ch.heatmap(grid, price))
    st.markdown("#### Fair value next to other price signals")
    bars = [("Our Bear to Bull", per_share["Bear"], per_share["Bull"], ch.TEAL),
            ("Required return ±1 pp", dc.value(dc.replace(inp, wacc=inp.wacc + 0.01))["per_share"],
             dc.value(dc.replace(inp, wacc=inp.wacc - 0.01))["per_share"], ch.BLUE)]
    if cd.range52:
        bars.append(("52-week range", cd.range52[0], cd.range52[1], ch.SLATE))
    if cd.targets:
        bars.append(("Analyst targets", cd.targets[0], cd.targets[2], ch.VIOLET))
    show(ch.football_field(bars, price))

with tab_ratios:
    st.markdown(f"#### Key Financial Ratios for {cd.name}")
    st.caption(f"Source: **{cd.ratio_source}**. All ratios are calculated mathematically from raw statements to prevent API decimal errors.")
    st.markdown(ui.ratios_html(cd), unsafe_allow_html=True)
    st.markdown("#### Understanding the Ratios")
    st.markdown("""
    - **ROE (Return on Equity):** Net Income / Total Equity. Measures how effectively management is using shareholder money.
    - **ROCE (Return on Capital Employed):** EBIT / (Total Assets - Current Liabilities). Shows how efficiently capital is used.
    - **Operating Margin:** EBIT / Revenue. Shows operating profitability.
    - **Debt to Equity:** Total Debt / Total Equity. A high ratio (> 2.0) indicates high leverage.
    - **Current Ratio:** Current Assets / Current Liabilities. A ratio over 1.5 shows good short-term health.
    """)

with tab_why:
    st.markdown("#### Can we trust the numbers?")
    st.markdown("".join(ui.callout(lv, m) for lv, m in dc.data_checks(cd, price, shares_cr)) or
                ui.callout("warn", "Not enough data to cross-check the share count."), unsafe_allow_html=True)
    if notes:
        st.markdown("".join(ui.callout("warn", n) for n in notes), unsafe_allow_html=True)
    st.markdown("#### How does it compare with other references?")
    rows = [("CMP (today's market price)", price)]
    if cd.targets:
        rows += [("Analyst low target", cd.targets[0]), ("Analyst average target", cd.targets[1]), ("Analyst high target", cd.targets[2])]
    if cd.range52:
        rows += [("52-week low", cd.range52[0]), ("52-week high", cd.range52[1])]
    refs = pd.DataFrame({"Reference": [r[0] for r in rows] + ["Our Bear", "Our Base", "Our Bull"],
                         "Price per share": [money(r[1]) for r in rows] + [money(per_share[s]) for s in ("Bear", "Base", "Bull")],
                         "Our Base vs this": [f"{(per_share['Base'] / r[1] - 1) * 100:+.0f}%" for r in rows] + ["", "", ""]}
                        ).set_index("Reference")
    table(refs)
    for line in (dc.gap_sentence(per_share["Base"], price, "today's CMP"),
                 dc.gap_sentence(per_share["Base"], cd.targets[1], "the analyst average target") if cd.targets else ""):
        if line:
            st.markdown(f"- {line}")
    st.markdown("#### What is the market assuming?")
    ig = dc.implied_growth(base, price)
    if ig is not None:
        more = "more optimistic than" if ig > base.growth else "more cautious than"
        past = f" The last {stats['n']} years averaged {stats['cagr']:.1%}." if "cagr" in stats else ""
        st.write(f"To justify today's CMP of {money(price)}, revenue would need to grow about **{ig:.1%} a year** for 5 years "
                 f"(all your other inputs unchanged). Your Base case assumes {base.growth:.1%}, so the market looks {more} you.{past}")
    else:
        st.write("No growth rate between -20% and +60% makes the DCF match today's CMP.")
    st.markdown("#### Check it yourself online")
    cols = st.columns(4)
    for col, (name, url) in zip(cols, dc.verify_links(symbol)):
        col.link_button(name, url)
    st.markdown("#### Why Bear, Base and Bull?")
    sc_table = pd.DataFrame({sn: {"Revenue growth": f"{scen[sn].growth:.1%}", "Profit margin": f"{scen[sn].ebit_margin:.1%}",
                                  "Required return (WACC)": f"{scen[sn].wacc:.2%}", "Long-run growth": f"{scen[sn].terminal_growth:.2%}",
                                  "Fair value per share": money(per_share[sn]), "vs CMP": f"{(per_share[sn] / price - 1) * 100:+.0f}%"}
                             for sn in ("Bear", "Base", "Bull")})
    table(sc_table)
    for s in ("Bear", "Base", "Bull"):
        with st.expander(f"{s} case: {money(per_share[s])} ({(per_share[s] / price - 1) * 100:+.0f}% vs CMP)"):
            st.write(blurbs[s])
            for line in dc.explain_scenario(scen[s], base, s, stats):
                st.markdown(f"- {line}")
            st.caption(dc.DRIVERS[s])
    with st.expander("Recent headlines (last 30 days)"):
        items = news(cd.name)
        if items:
            cnt = {t: sum(1 for n in items if n["tag"] == t) for t in ("bull", "bear", "neutral")}
            st.write(f"{cnt['bull']} positive, {cnt['bear']} negative, {cnt['neutral']} neutral out of {len(items)}.")
            n1, n2, n3 = st.columns(3)
            for col, tag, title in ((n1, "bull", "Good news"), (n2, "bear", "Bad news"), (n3, "neutral", "Context")):
                with col:
                    st.markdown(f"**{title}**")
                    st.markdown("".join(ui.news_item(n) for n in [n for n in items if n["tag"] == tag][:5]) or "<small>None</small>",
                                unsafe_allow_html=True)
        else:
            st.caption("No recent headlines could be loaded right now.")

with tab_math:
    st.markdown(f"#### How the {selected} value of {money(res['per_share'])} per share is calculated")
    t, term = res["table"], res["terminal"]
    st.markdown("##### Step 1. Forecast revenue")
    st.latex(r"\text{Revenue}_t = \text{Revenue}_0 \times (1 + g)^t")
    st.write(f"Year 1: {inp.revenue0:,.0f} × (1 + {inp.growth:.2%}) = **{t['Revenue'].iloc[0]:,.0f}**")
    st.markdown("##### Step 2. Profit after tax")
    st.latex(r"\text{NOPAT} = \text{EBIT} \times (1 - \text{tax})")
    st.write(f"Year 1: EBIT {t['EBIT'].iloc[0]:,.0f}; after {inp.tax_rate:.1%} tax = **{t['NOPAT'].iloc[0]:,.0f}**")
    st.markdown("##### Step 3. Free cash flow")
    st.latex(r"\text{FCFF} = \text{NOPAT} + \text{Depreciation} - \text{Capex} - \Delta\text{Working capital}")
    table(t[["Revenue", "EBIT", "NOPAT", "D&A", "Capex", "Increase in NWC", "FCFF"]].round(1))
    st.markdown("##### Step 4. Discount to today")
    st.latex(r"\text{PV} = \frac{\text{FCFF}_t}{(1 + \text{WACC})^t}")
    table(t[["FCFF", "Discount factor", "PV of FCFF"]].round(4))
    st.markdown("##### Step 5. Terminal value")
    st.latex(r"\text{Terminal value} = \frac{\text{FCFF}_{N+1}}{\text{WACC} - g}")
    st.write(f"Terminal value = **{res['tv']:,.0f}**, worth **{res['pv_tv']:,.0f}** today.")
    st.markdown("##### Step 6. Bridge to per share")
    st.write(f"Business = {res['pv_fcff']:,.0f} + {res['pv_tv']:,.0f} = **{res['ev']:,.0f}**. "
             f"Equity = {res['ev']:,.0f} - {inp.net_debt:,.0f} - {inp.minority:,.0f} = **{res['equity']:,.0f}**.")
    st.write(f"Per share = {res['equity']:,.0f} ÷ {inp.shares_cr:,.3f} crore = **{money(res['per_share'], 2)}**, "
             f"against CMP {money(price, 2)}.")
    ps2, d2, ok = dc.audit(inp)
    (st.success if ok else st.error)(
        f"Calculation check passed: independent re-computation gives {money(ps2, 4)} per share." if ok
        else "Calculation check FAILED.")

with tab_more:
    st.markdown("#### Model health check")
    st.markdown("".join(ui.callout(lv, m) for lv, m in dc.sanity_checks(inp, res)), unsafe_allow_html=True)
    st.markdown("#### Is the forecast realistic?")
    if len(cd.hist) and "revenue" in cd.hist.columns:
        show(ch.history_vs_forecast(cd.hist, res["table"], inp.ebit_margin))
    else:
        st.info("No historical financials were available for this company.")
    l, r = st.columns(2)
    with l:
        st.markdown("#### From the business to the shareholders")
        show(ch.waterfall(res["pv_fcff"], res["pv_tv"], inp.net_debt, inp.minority, years))
    with r:
        st.markdown("#### How much value comes after year 5?")
        show(ch.tv_donut(res["pv_fcff"], res["pv_tv"], years))
    st.markdown("#### Multiples: what the price implies")
    mrows = dc.multiples_check(cd, inp, res, price)
    if mrows:
        table(pd.DataFrame({"Metric": [x["metric"] for x in mrows], "At CMP": [f"{x['market']:.1f}x" for x in mrows],
                            f"At our {selected} value": [f"{x['dcf']:.1f}x" for x in mrows]}).set_index("Metric"))
    else:
        st.info("Not enough data to compute multiples for this company.")
    st.markdown("#### Download")
    try:
        st.download_button("Download Excel (.xlsx)", dc.export_excel(f"{cd.name} ({symbol}.NS)", selected, inp, res, per_share, grid, price),
                           file_name=f"{symbol}_DCF.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.info(f"Excel export is unavailable ({type(e).__name__}). Install openpyxl.")

st.markdown(ui.footer_html(), unsafe_allow_html=True)
