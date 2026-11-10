"""
dcf_ui.py - dark finance look and feel.
"""
from __future__ import annotations

import html
import math

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
:root { --bg:#0D1220; --s1:#131A2B; --s2:#1A2238; --line:#2A3350; --text:#E8ECF4; --muted:#9AA7C0;
        --blue:#4C8DFF; --blue-t:#6EA2FF; --teal:#3CCFA0; --red:#FF8A86; --amber:#F5B544; --violet:#A99CFF; }
html { color-scheme: dark; }
.stApp, .stApp button, .stApp input, .stApp textarea, .stApp [data-baseweb] { font-family: 'IBM Plex Sans', system-ui, sans-serif !important; }
.stApp { color: var(--text); font-size: 15px; line-height: 1.6; font-variant-numeric: tabular-nums;
         background: radial-gradient(1100px 560px at 8% -8%, rgba(76,141,255,.14), transparent 60%),
                     radial-gradient(900px 480px at 100% 0%, rgba(139,124,246,.10), transparent 55%), var(--bg);
         animation: bgPulse 10s infinite alternate; }
@keyframes bgPulse { 0% { background-size: 100% 100%; } 100% { background-size: 120% 120%; } }

h1, h2, h3, h4, h5 { font-family: 'IBM Plex Sans', sans-serif !important; font-weight: 600; letter-spacing: -0.01em; color: var(--text) !important; }
h4 { font-size: 1.25rem; margin: 1.5rem 0 .3rem; }
.stMarkdown p, .stMarkdown li, label, [data-testid="stWidgetLabel"] p { color: var(--text); }
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--muted) !important; font-size: .85rem; }
.block-container { padding-top: 1rem; max-width: 1180px; }
footer, [data-testid="stAppDeployButton"], .stDeployButton { display: none !important; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] button, [data-testid="stToolbar"] svg { color: var(--muted); }
a { color: var(--blue-t); }
* { -webkit-tap-highlight-color: rgba(76,141,255,.25); }
button, a, label, [role="tab"], summary { touch-action: manipulation; }
:focus-visible { outline: 2px solid var(--blue-t) !important; outline-offset: 2px; }

@keyframes rise { from { opacity:0; transform:translateY(14px); filter:blur(4px); } to { opacity:1; transform:none; filter:none; } }
@keyframes grow { from { transform:scaleX(0); } to { transform:scaleX(1); } }
@keyframes sway { from { transform: translateY(-8px); } to { transform: translateY(8px); } }
@keyframes pulseGlow { 0%,100% { box-shadow: 0 0 0 0 rgba(76,141,255,.35); } 50% { box-shadow: 0 0 20px 5px rgba(76,141,255,.2); } }
@keyframes pulseText { 0%,100% { text-shadow: 0 0 10px rgba(76,141,255,0.2); } 50% { text-shadow: 0 0 20px rgba(76,141,255,0.8); } }
@keyframes ring { 0%,100% { box-shadow: 0 0 0 0 rgba(76,141,255,.35); } 50% { box-shadow: 0 0 0 6px rgba(76,141,255,0); } }
@keyframes flowLines { from { stroke-dashoffset: 400; } to { stroke-dashoffset: 0; } }

.rise { animation: rise .8s cubic-bezier(.2,.7,.2,1) both; animation-delay: calc(var(--d,0) * 100ms); }
.stPlotlyChart, [data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stDataFrame"] { animation: rise .55s cubic-bezier(.2,.7,.2,1) both; }

.topbar { display: flex; align-items: baseline; gap: .8rem; margin: .2rem 0 .6rem; flex-wrap: wrap; }
.brand { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
.brand-sub { color: var(--muted); font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; }
[data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="base-input"] { background: var(--s1) !important; border-radius: 12px !important;
        border: 1px solid var(--line) !important; min-height: 44px; }
[data-baseweb="input"] input { min-height: 40px; color: var(--text) !important; }
[data-testid="stNumberInput"] button { min-width: 40px; min-height: 40px; }
.stButton > button, .stDownloadButton > button { background: linear-gradient(135deg, #2F6FED, #6D5BE8); color: #fff; border: 0; border-radius: 12px;
        font-weight: 600; min-height: 44px; padding: .5rem 1.4rem; transition: transform .15s ease, box-shadow .2s ease; cursor: pointer;
        animation: pulseGlow 3s infinite; }
.stButton > button:hover, .stDownloadButton > button:hover { animation: none; box-shadow: 0 0 15px 5px rgba(76,141,255,.4); transform: translateY(-1px); }
.stButton > button:active, .stDownloadButton > button:active { transform: scale(.96); }
[data-testid="stLinkButton"] a { border: 1px solid var(--line); border-radius: 12px; background: var(--s1); color: var(--text); font-weight: 500;
        min-height: 44px; display: flex; align-items: center; justify-content: center; transition: background .2s ease, transform .15s ease; cursor: pointer; }
[data-testid="stLinkButton"] a:hover { background: var(--s2); border-color: var(--blue-t); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.3); }
[data-testid="stLinkButton"] a:active { transform: scale(.96); }
div[role="radiogroup"] { gap: .6rem; flex-wrap: wrap; }
div[role="radiogroup"] label { border: 1px solid var(--line); border-radius: 999px; padding: .4rem 1.1rem; min-height: 44px; display: flex; align-items: center;
        background: var(--s1); cursor: pointer; transition: background .2s ease, transform .15s ease; }
div[role="radiogroup"] label:active { transform: scale(.96); }
div[role="radiogroup"] label:has(input:checked) { background: linear-gradient(135deg, #2F6FED, #6D5BE8); border-color: transparent; color: #fff; }
div[role="radiogroup"] label:has(input:checked) * { color: #fff !important; }
[data-testid="stExpander"] details { border: 1px solid var(--line); border-radius: 16px; background: var(--s1); transition: border-color .2s; }
[data-testid="stExpander"] details:hover { border-color: var(--blue-t); }
[data-testid="stExpander"] summary { font-weight: 600; min-height: 48px; }
[data-testid="stExpander"] summary:active { background: var(--s2); border-radius: 16px; }
[data-testid="stMetric"] { background: var(--s1); border: 1px solid var(--line); border-radius: 16px; padding: 14px 18px; }
[data-testid="stMetricLabel"] { color: var(--muted); }
.stTabs [data-baseweb="tab-list"] { gap: .2rem; border-bottom: 1px solid var(--line); overflow-x: auto; scrollbar-width: none; }
.stTabs [data-baseweb="tab"] { font-size: .92rem; font-weight: 600; min-height: 48px; padding: .6rem 1rem; color: var(--muted); transition: color .2s; }
.stTabs [data-baseweb="tab"]:hover { color: var(--text); }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--text); }
.stTabs [data-baseweb="tab-highlight"] { background: linear-gradient(90deg, var(--blue), var(--teal)); height: 3px; transition: all .35s cubic-bezier(.2,.7,.2,1); }

section[data-testid="stSidebar"] { background: var(--s1); border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] .brand { margin-top: .2rem; }
[data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] {
    display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 1000000; }
[data-testid="stSidebarCollapsedControl"] button, [data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button { min-width: 44px; min-height: 44px; border-radius: 12px; background: var(--s2) !important;
    border: 1px solid var(--line); color: var(--text) !important; }
[data-testid="stSidebarCollapsedControl"] button:active, [data-testid="stExpandSidebarButton"]:active, [data-testid="stSidebarCollapseButton"] button:active { transform: scale(.95); }
section[data-testid="stSidebar"] [data-testid="stExpander"] details { background: var(--bg); }
section[data-testid="stSidebar"] .live { padding: .6rem .7rem; } section[data-testid="stSidebar"] .live .pills { gap: .4rem; }
section[data-testid="stSidebar"] .pill { font-size: .78rem; padding: .22rem .7rem; }

.hero { position: relative; overflow: hidden; border-radius: 24px; border: 1px solid var(--line); margin-bottom: 1.1rem; text-align: center;
        background: linear-gradient(180deg, #131B30 0%, #0F1627 100%); }
.mesh { position: absolute; inset: 0; width: 100%; height: 100%; }
.mesh path { transform-box: fill-box; transform-origin: center; }
.mesh .base path { animation: sway 7s ease-in-out infinite alternate; animation-delay: calc(var(--i, 0) * -.3s); }
.mesh .fl { stroke-dasharray: 26 374; animation: flowLines 4s linear infinite, sway 7s ease-in-out infinite alternate; animation-delay: calc(var(--i, 0) * -.37s), calc(var(--i, 0) * -.3s); }

.hero-in { position: relative; padding: 2rem 1.1rem 1.9rem; pointer-events: none; }
.hero-in * { pointer-events: auto; }
.brandpill { display: inline-block; font-size: .78rem; letter-spacing: .1em; text-transform: uppercase; color: #A9C8FF; font-weight: 600;
             background: rgba(76,141,255,.14); border: 1px solid rgba(76,141,255,.45); border-radius: 999px; padding: .3rem 1rem; margin-bottom: 1.1rem;
             backdrop-filter: blur(4px); }
.glass { max-width: 480px; margin: 0 auto; text-align: left; background: rgba(19,26,43,.65); backdrop-filter: blur(16px);
         border: 1px solid rgba(255,255,255,.09); border-radius: 20px; padding: 1.1rem 1.3rem 1.2rem; box-shadow: 0 20px 44px rgba(0,0,0,.35);
         transition: box-shadow .3s, border-color .3s; animation: sway 6s ease-in-out infinite alternate; }
.glass:hover { box-shadow: 0 20px 50px rgba(76,141,255,.15); border-color: rgba(76,141,255,.3); animation-play-state: paused; }
.g-top { display: flex; align-items: center; gap: .8rem; }
.logo { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #2F6FED, #8B7CF6); color: #fff; display: flex;
        align-items: center; justify-content: center; font-weight: 700; font-size: 1.25rem; flex: none; box-shadow: 0 4px 12px rgba(76,141,255,.3); }
.g-name { font-size: 1.25rem; font-weight: 600; line-height: 1.2; }
.g-sub { color: var(--muted); font-size: .82rem; }
.chips { display: flex; gap: .4rem; margin: .8rem 0 .6rem; flex-wrap: wrap; }
.chip { font-size: .78rem; background: rgba(26,34,56,.8); border: 1px solid var(--line); border-radius: 8px; padding: .12rem .6rem; color: var(--text);
        backdrop-filter: blur(4px); transition: transform .2s; }
.chip:hover { transform: translateY(-2px); border-color: var(--blue-t); }
.chip:nth-child(1) { color: var(--blue-t); } .chip:nth-child(2) { color: var(--violet); } .chip:nth-child(3) { color: var(--amber); } .chip:nth-child(4) { color: var(--teal); }
.g-text { color: var(--muted); font-size: .9rem; margin: 0 0 .9rem; }
.g-metrics { display: flex; justify-content: space-between; gap: .6rem; border-top: 1px solid var(--line); padding-top: .85rem; }
.g-metrics small { display: block; color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .06em; }
.g-metrics b { font-size: 1.6rem; font-weight: 600; letter-spacing: -0.02em; }
.g-metrics b[data-count] { animation: pulseText 2.5s infinite; }
.pos { color: var(--teal); } .neg { color: var(--red); } .mid { color: var(--amber); }
.pills { margin: 1.1rem 0 1.3rem; display: flex; justify-content: center; gap: .6rem; flex-wrap: wrap; }
.pill { font-size: .85rem; border: 1px solid var(--line); border-radius: 999px; padding: .3rem 1rem; background: rgba(26,34,56,.7); backdrop-filter: blur(4px);
        transition: all .3s; }
.pill:hover { border-color: var(--blue-t); transform: translateY(-2px); }
.pill.on { background: linear-gradient(135deg, #2F6FED, #6D5BE8); border-color: transparent; color: #fff; font-weight: 600; box-shadow: 0 0 15px rgba(76,141,255,.4); }
.headline { font-size: clamp(1.7rem, 4vw, 2.5rem); font-weight: 600; line-height: 1.15; letter-spacing: -0.02em; margin: 0 auto; max-width: 780px; }
.hero .lede { color: var(--muted); font-size: 1rem; width: min(660px, 100%); margin: .8rem auto 0 !important; text-align: center; }
.hero .headline { text-align: center; }
.hero .lede b { color: var(--text); }

.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: .4rem 0 1rem; }
.card { border-radius: 20px; padding: 1.2rem 1.3rem; border: 1px solid var(--line); background: var(--s1); transition: transform .3s cubic-bezier(.2,.7,.2,1), box-shadow .3s; cursor: pointer; position: relative; overflow: hidden; }
.card::after { content: ''; position: absolute; inset: 0; background: linear-gradient(180deg, transparent, rgba(255,255,255,.03)); pointer-events: none; }
.card:active { transform: scale(.985); }
@media (hover: hover) { .card:hover { transform: translateY(-6px); box-shadow: 0 20px 40px rgba(0,0,0,.5); } }
.card.sel { animation: ring 2.4s ease-in-out infinite; }
.c-Bear { background: linear-gradient(160deg, rgba(239,83,80,.15), #131A2B 70%); border-color: rgba(239,83,80,.40); }
.c-Base { background: linear-gradient(160deg, rgba(76,141,255,.15), #131A2B 70%); border-color: rgba(76,141,255,.40); }
.c-Bull { background: linear-gradient(160deg, rgba(60,207,160,.15), #131A2B 70%); border-color: rgba(60,207,160,.40); }
.c-top { display: flex; justify-content: space-between; align-items: center; gap: .5rem; }
.c-label { font-size: .8rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 600; }
.c-Bear .c-label { color: var(--red); } .c-Base .c-label { color: var(--blue-t); } .c-Bull .c-label { color: var(--teal); }
.tagdiff { font-size: .8rem; font-weight: 600; border-radius: 999px; padding: .15rem .65rem; background: rgba(255,255,255,.07); }
.c-val { font-size: 2.6rem; font-weight: 600; letter-spacing: -0.03em; line-height: 1.1; margin: .5rem 0 .1rem; }
.c-cmp { color: var(--muted); font-size: .85rem; margin-bottom: .7rem; }
.bars { display: grid; gap: .35rem; margin-bottom: .4rem; }
.bar { height: 8px; border-radius: 6px; width: var(--w); transform-origin: left; animation: grow 1s cubic-bezier(.2,.7,.2,1) both; animation-delay: .25s; }
.bar.cmpbar { background: rgba(255,255,255,.25); }
.c-Bear .valbar { background: #EF5350; } .c-Base .valbar { background: #4C8DFF; } .c-Bull .valbar { background: #3CCFA0; }
.legend { display: flex; justify-content: space-between; font-size: .75rem; color: var(--muted); margin-bottom: .7rem; }
.c-why { color: var(--text); font-size: .9rem; margin: 0; }

.ratios-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: .5rem 0 1.5rem; }
.ratio-card { background: rgba(26,34,56,.6); border: 1px solid var(--line); border-radius: 16px; padding: 1rem 1.2rem; backdrop-filter: blur(10px); transition: all .3s ease; display: flex; flex-direction: column; justify-content: space-between; }
.ratio-card:hover { border-color: var(--blue-t); box-shadow: 0 10px 25px rgba(76,141,255,.1); transform: translateY(-3px); }
.ratio-title { font-size: .8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: .3rem; line-height: 1.2; }
.ratio-val { font-size: 1.5rem; font-weight: 600; color: var(--text); }
.ratio-desc { font-size: .75rem; color: #6b7c93; margin-top: .3rem; flex-grow: 1; }
.ratio-footer { font-size: .6rem; color: rgba(255, 255, 255, 0.3); margin-top: .5rem; text-align: right; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; transition: color 0.3s ease; }
.ratio-card:hover .ratio-footer { color: rgba(255, 255, 255, 0.6); }
.hl-good { color: var(--teal); text-shadow: 0 0 10px rgba(60,207,160,.3); }
.hl-bad { color: var(--red); text-shadow: 0 0 10px rgba(239,83,80,.3); }
.hl-neutral { color: var(--amber); }

.live { background: var(--s1); border: 1px solid var(--line); border-radius: 16px; padding: .8rem 1rem; margin-bottom: .6rem; }
.live .pills { margin: .4rem 0 0; justify-content: flex-start; }
.live small { color: var(--muted); }
.callout { border-radius: 14px; padding: .8rem 1rem; margin: .4rem 0; font-size: .92rem; border-left: 4px solid; background: rgba(255,255,255,.04); transition: background .2s; }
.callout:hover { background: rgba(255,255,255,.06); }
.callout.ok { border-color: #3CCFA0; } .callout.warn { border-color: #F5B544; } .callout.bad { border-color: #EF5350; }
.news { padding: .6rem 0; border-bottom: 1px solid var(--line); font-size: .9rem; line-height: 1.5; transition: background .2s; }
.news:hover { background: rgba(255,255,255,.02); }
.news a { color: var(--text); text-decoration: none; } .news a:hover { color: var(--blue-t); text-decoration: underline; }
.news small { color: var(--muted); }
.foot { background: #070B14; border: 1px solid var(--line); color: #8896B3; border-radius: 20px; padding: 1.5rem 1.7rem; margin-top: 2.2rem; font-size: .82rem; line-height: 1.8; }
.foot b { color: var(--text); font-size: 1.1rem; }

/* --- DESKTOP STYLES END HERE --- */

@media (max-width: 768px) {
  .block-container { padding: .6rem .8rem 3rem; }
  .hero-in { padding: 1.4rem .7rem 1.4rem; } 
  .g-metrics b { font-size: 1.3rem; } 
  .c-val { font-size: 2.2rem; } 
  h4 { font-size: 1.15rem; }
  .ratios-grid { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
  
  /* --- MOBILE OPTIMIZATIONS (KEEP ANIMATIONS, REDUCE GPU LOAD) --- */
  
  /* 1. Stop background pulse to save battery, keep static gradient */
  .stApp { animation: none !important; background-size: 100% 100% !important; }

  /* 2. Hardware-Accelerate the SVG flow. 
     This forces the phone's GPU to handle the flowing lines smoothly without repainting the whole screen. */
  .mesh .fl, .mesh .base path {
    will-change: transform, stroke-dashoffset;
    transform: translateZ(0);
  }

  /* 3. Optimize the Glass Cards */
  .glass { 
    /* Replace the heavy real-time blur with a high-opacity solid color */
    background: rgba(19, 26, 43, 0.90) !important; 
    backdrop-filter: none !important; 
    -webkit-backdrop-filter: none !important;
    /* Keep the shadow for depth, but stop the continuous sway to save power */
    box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
    animation: none !important; 
  }
  
  /* 4. Optimize the Ratio Cards and UI elements */
  .ratio-card, .live, .pill, .chip, .brandpill {
    background: rgba(26, 34, 56, 0.95) !important; 
    backdrop-filter: none !important; 
    -webkit-backdrop-filter: none !important;
  }

  /* 5. Keep the Entry Animations (rise, grow), but stop the "breathing" loops */
  .card.sel, .stButton > button, .g-metrics b[data-count] {
    animation: none !important;
  }
  
  /* 6. Remove hover transforms for touch screens (prevents sticky states) */
  .card:hover, .ratio-card:hover, .chip:hover, .stButton > button:hover, [data-testid="stLinkButton"] a:hover {
    transform: none !important; 
    box-shadow: none !important; 
  }
}
</style>
"""

TOUCH_JS = """
<script>
(function () {
  try {
    var w = window.parent, d = w.document;
    if (w.__dcfTouch) return;
    w.__dcfTouch = true;
    var calm = false;

    if (!calm) {
      var seen = new w.WeakSet(), queued = false;
      var fmtNum = function (el, v) {
        var n = Math.round(v), txt = Math.abs(n).toLocaleString('en-US');
        return (n < 0 ? '-' : (el.dataset.sign && n > 0 ? '+' : '')) + (el.dataset.pre || '') + txt + (el.dataset.suf || '');
      };
      var run = function (el) {
        var target = parseFloat(el.dataset.count), final = el.textContent, t0 = null;
        if (!isFinite(target)) return;
        var step = function (t) {
          if (t0 === null) t0 = t;
          var p = Math.min(1, (t - t0) / 1500), e = 1 - Math.pow(1 - p, 4);
          el.textContent = p < 1 ? fmtNum(el, target * e) : final;
          if (p < 1) w.requestAnimationFrame(step);
        };
        el.textContent = fmtNum(el, 0);
        w.requestAnimationFrame(step);
      };
      var scan = function () {
        queued = false;
        d.querySelectorAll('[data-count]').forEach(function (el) { if (!seen.has(el)) { seen.add(el); run(el); } });
      };
      new w.MutationObserver(function () { if (!queued) { queued = true; w.requestAnimationFrame(scan); } })
        .observe(d.body, { childList: true, subtree: true });
      scan();
    }

    var EXPAND = ['[data-testid="stExpandSidebarButton"]', '[data-testid="stSidebarCollapsedControl"] button', '[data-testid="collapsedControl"] button'];
    var COLLAPSE = ['[data-testid="stSidebarCollapseButton"] button', 'section[data-testid="stSidebar"] button[kind="header"]'];
    function clickFirst(list) { for (var i = 0; i < list.length; i++) { var el = d.querySelector(list[i]); if (el) { el.click(); return true; } } return false; }
    function isOpen() { var sb = d.querySelector('section[data-testid="stSidebar"]'); return !!sb && sb.getAttribute('aria-expanded') !== 'false'; }
    var fab = d.createElement('button');
    fab.type = 'button'; fab.className = 'dcf-fab'; fab.setAttribute('aria-label', 'Open settings');
    fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/></svg>Settings';
    fab.addEventListener('click', function () { if (!clickFirst(EXPAND)) clickFirst(COLLAPSE); });
    d.body.appendChild(fab);
    function sync() { fab.classList.toggle('show', !isOpen()); }
    sync(); w.setInterval(sync, 500);
  } catch (err) { console.log("Animation error:", err); }
})();
</script>
"""


def _fmt(v) -> str:
    return "n/a" if v is None or not math.isfinite(v) else f"₹{v:,.0f}"


def _pct(d) -> str:
    return "n/a" if d is None or not math.isfinite(d) else f"{d * 100:+.0f}%"


def _cls(d) -> str:
    return "mid" if d is None or not math.isfinite(d) else "pos" if d > 0.10 else "neg" if d < -0.10 else "mid"


def _fmt_pct(v) -> str:
    return "n/a" if v is None or not math.isfinite(v) else f"{v * 100:.2f}%"


def _fmt_num(v) -> str:
    return "n/a" if v is None or not math.isfinite(v) else f"{v:.2f}"


def mesh_svg(n: int = 24) -> str:
    w, h, cy = 1200, 420, 210
    base, flow = [], []
    for side in (0, 1):
        for k in range(n):
            y0 = 12 + k * (h - 24) / (n - 1)
            ym = cy + (y0 - cy) * 0.30
            d = (f"M0,{y0:.0f} C250,{y0:.0f} 340,{ym:.0f} 520,{cy}" if side == 0 else
                 f"M{w},{y0:.0f} C{w - 250},{y0:.0f} {w - 340},{ym:.0f} {w - 520},{cy}")
            base.append(f"<path style='--i:{k}' d='{d}'/>")
            flow.append(f"<path class='fl' pathLength='400' style='--i:{k + side * 5}' d='{d}'/>")
    defs = ("<defs><linearGradient id='mg' x1='0' y1='0' x2='1200' y2='0' gradientUnits='userSpaceOnUse'>"
            "<stop offset='0' stop-color='#4C8DFF'/><stop offset='.5' stop-color='#3CCFA0'/><stop offset='1' stop-color='#8B7CF6'/>"
            "</linearGradient></defs>")
    return (f"<svg class='mesh' viewBox='0 0 {w} {h}' preserveAspectRatio='none' aria-hidden='true'>{defs}"
            f"<g class='base' fill='none' stroke='url(#mg)' stroke-opacity='.30' stroke-width='1.1'>{''.join(base)}</g>"
            f"<g fill='none' stroke='url(#mg)' stroke-opacity='.95' stroke-width='1.8' stroke-linecap='round'>{''.join(flow)}</g></svg>")


def _cnt(v, pre="", suf="", sign=False) -> str:
    if v is None or not math.isfinite(v):
        return ""
    return f" data-count='{v:.6g}' data-pre='{pre}' data-suf='{suf}'" + (" data-sign='1'" if sign else "")


def callout(level: str, text: str) -> str:
    return f"<div class='callout {level}'>{html.escape(text)}</div>"


def news_item(n: dict) -> str:
    title = html.escape(n["title"])
    link = f"<a href='{html.escape(n['link'])}' target='_blank' rel='noopener'>{title}</a>" if n.get("link") else title
    return f"<div class='news'>{link}<br><small>{html.escape(n.get('source', ''))} · {n.get('date', '')}</small></div>"


def hero_html(name: str, symbol: str, sector: str | None, scenario: str, per_share: float, price: float, diff: float,
              label: str, vals: dict, basis: str) -> str:
    short = name.replace(" Limited", "").replace(" Ltd.", "").replace(" Ltd", "").strip() or symbol
    if math.isfinite(diff):
        lede = (f"Our {scenario} case values each share at {_fmt(per_share)}, which is {abs(diff) * 100:.0f}% "
                f"{'above' if diff > 0 else 'below'} today's market price (CMP) of {_fmt(price)}. "
                f"On these assumptions the stock looks <b>{label}</b>.")
        g_text = f"{_fmt(per_share)} fair value vs {_fmt(price)} CMP."
    else:
        lede, g_text = "A valuation could not be computed with these inputs.", "No valuation available."
    pills = "".join(f"<span class='pill{' on' if s == scenario else ''}'>{s} {_fmt(vals[s])}</span>" for s in ("Bear", "Base", "Bull"))
    chips = "".join(f"<span class='chip'>{html.escape(c)}</span>" for c in
                    [f"{symbol}.NS", sector or "NSE-listed", f"{scenario} case", f"Revenue: {basis}"])
    return (f"<div class='hero'>{mesh_svg()}<div class='hero-in'>"
            f"<div class='brandpill rise' style='--d:0'>DCF Studio · NSE</div>"
            f"<div class='glass rise' style='--d:1'><div class='g-top'><div class='logo'>{html.escape(short[:1].upper())}</div>"
            f"<div><div class='g-name'>{html.escape(short)}</div><div class='g-sub'>Discounted cash flow valuation</div></div></div>"
            f"<div class='chips'>{chips}</div><div class='g-text'>{g_text}</div>"
            f"<div class='g-metrics'><div><small>CMP</small><b{_cnt(price, '₹')}>{_fmt(price)}</b></div>"
            f"<div><small>Fair value</small><b{_cnt(per_share, '₹')}>{_fmt(per_share)}</b></div>"
            f"<div><small>Difference</small><b class='{_cls(diff)}'{_cnt(diff * 100 if math.isfinite(diff) else None, '', '%', True)}>{_pct(diff)}</b></div></div></div>"
            f"<div class='pills rise' style='--d:2'>{pills}</div>"
            f"<div class='headline rise' style='--d:3'>Is {html.escape(short)} worth its price?</div>"
            f"<div class='lede rise' style='--d:4'>{lede}</div></div></div>")


def scenario_cards_html(vals: dict, price: float, blurbs: dict, selected: str) -> str:
    top = max([v for v in list(vals.values()) + [price] if v is not None and math.isfinite(v)] or [1.0])
    cards = []
    for i, s in enumerate(("Bear", "Base", "Bull")):
        v = vals[s]
        d = v / price - 1 if math.isfinite(v) and price > 0 else float("nan")
        w_val = max(2.0, min(100.0, v / top * 100)) if math.isfinite(v) and v > 0 else 2.0
        w_cmp = max(2.0, min(100.0, price / top * 100))
        cards.append(
            f"<div class='card c-{s} rise{' sel' if s == selected else ''}' style='--d:{i}'>"
            f"<div class='c-top'><span class='c-label'>{s} case</span><span class='tagdiff {_cls(d)}'>{_pct(d)} vs CMP</span></div>"
            f"<div class='c-val'{_cnt(v, '₹')}>{_fmt(v)}</div><div class='c-cmp'>fair value per share · CMP {_fmt(price)}</div>"
            f"<div class='bars'><div class='bar cmpbar' style='--w:{w_cmp:.1f}%'></div><div class='bar valbar' style='--w:{w_val:.1f}%'></div></div>"
            f"<div class='legend'><span>light bar = CMP</span><span>coloured bar = fair value</span></div>"
            f"<div class='c-why'>{html.escape(blurbs[s])}</div></div>")
    return f"<div class='cards'>{''.join(cards)}</div>"


def live_html(vals: dict, price: float, selected: str) -> str:
    pills = "".join(f"<span class='pill{' on' if s == selected else ''}'>{s} {_fmt(vals[s])} "
                    f"({_pct(vals[s] / price - 1 if math.isfinite(vals[s]) and price > 0 else float('nan'))})</span>"
                    for s in ("Bear", "Base", "Bull"))
    return f"<div class='live'><small>Live result vs CMP {_fmt(price)}: changes as you edit the boxes below</small><div class='pills'>{pills}</div></div>"


def ratios_html(cd) -> str:
    r = cd.ratios
    source = r.get("source", "Statements")
    
    def make_card(title, value, desc, color_class=""):
        return (
            f"<div class='ratio-card rise'>"
            f"<div class='ratio-title'>{title}</div>"
            f"<div class='ratio-val {color_class}'>{value}</div>"
            f"<div class='ratio-desc'>{desc}</div>"
            f"<div class='ratio-footer'>Source: {source}</div>"
            f"</div>"
        )

    roe = r.get("roe")
    roce = r.get("roce")
    opm = r.get("opm")
    npm = r.get("npm")
    de = r.get("debt_to_equity")
    cr = r.get("current_ratio")
    pe = r.get("pe_ratio")
    pb = r.get("pb_ratio")
    div = r.get("div_yield")

    cards = [
        make_card("Return on Equity (ROE)", _fmt_pct(roe), "Net Income / Total Equity", "hl-good" if (roe or 0) > 0.15 else "hl-neutral"),
        make_card("Return on Capital Employed (ROCE)", _fmt_pct(roce), "EBIT / (Assets - Current Liab)", "hl-good" if (roce or 0) > 0.15 else "hl-neutral"),
        make_card("Operating Margin", _fmt_pct(opm), "EBIT / Revenue", "hl-good" if (opm or 0) > 0.15 else "hl-neutral"),
        make_card("Net Margin", _fmt_pct(npm), "Net Income / Revenue", "hl-good" if (npm or 0) > 0.10 else "hl-neutral"),
        make_card("Debt to Equity", _fmt_num(de), "Total Debt / Total Equity", "hl-good" if (de or 0) < 1.0 else "hl-bad"),
        make_card("Current Ratio", _fmt_num(cr), "Current Assets / Current Liab", "hl-good" if (cr or 0) > 1.5 else "hl-neutral"),
        make_card("Trailing P/E", _fmt_num(pe), "Price / Earnings Per Share", ""),
        make_card("Price to Book", _fmt_num(pb), "Price / Book Value per Share", ""),
        make_card("Dividend Yield", _fmt_pct(div), "Dividends Paid / Price", "hl-good" if (div or 0) > 0.01 else ""),
    ]
    return f"<div class='ratios-grid'>{''.join(cards)}</div>"


def footer_html() -> str:
    return ("<div class='foot'><b>DCF Studio</b><br>A learning project, not investment advice. A DCF is only as good as its "
            "assumptions. Financial ratios are calculated mathematically from raw statements to ensure 100% accuracy. "
            "Always cross-check important numbers on NSE or Screener.in before relying on them. "
            "Not suitable for banks and financial companies.<br><br>"
            "<span style='color: #6EA2FF; font-weight: 600; font-size: 0.9rem; letter-spacing: 0.5px;'>Created by Shivam Chintawar</span></div>")
