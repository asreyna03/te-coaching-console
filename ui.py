"""Editorial design system for the T&E coaching app.

Art direction: warm cream canvas, ink-black type, one hot-orange accent.
Archivo (heavy grotesque) for display, Space Mono for [bracket] microlabels.
Inspired by editorial fashion layouts — restrained palette, strong hierarchy,
subtle motion. (No Inter. One accent. Moderation = quality.)
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
import streamlit as st
import coachlib as cl

YEAR = "2026"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,600&family=Space+Mono:wght@400;700&display=swap');

:root{
  --cream:#EFEDE6; --paper:#FBFAF6; --sand:#E8E4DB;
  --ink:#17150F; --muted:#78736A; --line:#DCD6C9;
  --accent:#E4531F; --accent2:#C9430F;
}

/* ---------- base ---------- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"],
.stMarkdown, p, span, div, li, label, input, textarea, select,
[data-testid="stWidgetLabel"] * {
  font-family:'Archivo', -apple-system, BlinkMacSystemFont, sans-serif;
  color:var(--ink);
}
[data-testid="stAppViewContainer"]{ background:var(--cream); }
[data-testid="stHeader"]{ background:transparent; }
[data-testid="stMain"] .block-container{
  max-width:1180px; padding-top:2rem; padding-bottom:4rem;
  animation:fadeup .45s ease both;
}
@keyframes fadeup{ from{opacity:0; transform:translateY(8px)} to{opacity:1; transform:none} }
#MainMenu, footer, [data-testid="stToolbar"]{ visibility:hidden; }
/* ...but keep the sidebar reopen button usable. On iPad/tablet widths Streamlit
   auto-collapses the sidebar, and its only reopen control lives inside the
   toolbar we just hid — so un-hide that one button (and make it show on top). */
[data-testid="stExpandSidebarButton"]{ visibility:visible !important; }
[data-testid="stExpandSidebarButton"] button{ color:var(--ink) !important; }

h1,h2,h3,h4{ font-family:'Archivo'; font-weight:800; letter-spacing:-.025em;
  color:var(--ink); }
h2{ font-size:1.5rem; margin-top:1.2rem; }
h3{ font-size:1.12rem; }
a{ color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent); }

/* ---------- mono microlabels ---------- */
.mono{ font-family:'Space Mono', monospace; text-transform:uppercase;
  letter-spacing:.12em; font-size:.68rem; color:var(--muted); }
.mono.ink{ color:var(--ink); }
.mono.acc{ color:var(--accent); }

/* ---------- hero ---------- */
.hero{ position:relative; padding:30px 0 24px; margin-bottom:14px;
  border-bottom:1.5px solid var(--ink); overflow:hidden; }
.hero:before{ content:""; position:absolute; right:-140px; top:-160px;
  width:420px; height:420px; border-radius:50%;
  border:1px solid var(--line); box-shadow:0 0 0 34px rgba(0,0,0,0) ,
  40px 40px 0 -1px var(--line) inset; opacity:.5; pointer-events:none; }
.hero-top{ display:flex; justify-content:space-between; align-items:center;
  margin-bottom:20px; }
.hero h1{ font-size:3.15rem; line-height:.98; font-weight:900;
  letter-spacing:-.035em; margin:0; max-width:15ch; }
.hero .ast{ color:var(--accent); font-weight:700; }
.hero-sub{ margin-top:14px; max-width:56ch; color:#453f34; font-size:1rem;
  line-height:1.5; }

/* ---------- stat row ---------- */
.statrow{ display:flex; gap:44px; flex-wrap:wrap; margin:6px 0 4px; }
.stat .num{ font-family:'Archivo'; font-weight:900; font-size:2.1rem;
  letter-spacing:-.03em; line-height:1; }
.stat .num .u{ color:var(--accent); }
.stat .cap{ margin-top:6px; }

/* ---------- cards ---------- */
.card{ background:var(--paper); border:1px solid var(--line);
  border-radius:16px; padding:18px 20px; height:100%;
  transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
.card:hover{ transform:translateY(-3px);
  box-shadow:0 14px 30px -18px rgba(0,0,0,.35); border-color:#C7C0B0; }
.card .k{ margin-bottom:12px; }
.card h3{ margin:2px 0 6px; font-size:1.05rem; }
.card p{ color:var(--muted); font-size:.86rem; margin:0; line-height:1.45; }
.card .cut{ border-top-right-radius:2px; }

/* ---------- metrics as editorial stat cards ---------- */
[data-testid="stMetric"]{ background:var(--paper); border:1px solid var(--line);
  border-radius:14px; padding:14px 16px 12px; }
[data-testid="stMetricLabel"] p{ font-family:'Space Mono', monospace;
  text-transform:uppercase; letter-spacing:.09em; font-size:.66rem;
  color:var(--muted); }
[data-testid="stMetricValue"]{ font-family:'Archivo'; font-weight:900;
  font-size:1.7rem; letter-spacing:-.02em; }
[data-testid="stMetricDelta"]{ font-family:'Space Mono', monospace;
  font-size:.72rem; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button{
  border-radius:999px; border:1.6px solid var(--ink); background:var(--ink);
  color:var(--paper); font-family:'Space Mono', monospace; font-weight:700;
  letter-spacing:.03em; font-size:.78rem; padding:.5rem 1.25rem;
  transition:all .16s ease; }
.stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover{
  background:var(--accent); border-color:var(--accent); color:#fff;
  transform:translateY(-1px); }
button[kind="primary"], [data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] button{ background:var(--accent);
  border-color:var(--accent); color:#fff; }
button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{
  background:var(--accent2); border-color:var(--accent2); }

/* ---------- inputs ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, .stTextArea textarea,
[data-baseweb="base-input"]{ background:var(--paper) !important;
  border-radius:10px !important; }
[data-testid="stWidgetLabel"] p{ font-family:'Space Mono', monospace;
  font-size:.72rem; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{ background:var(--sand); border-right:1.5px solid var(--ink); }
[data-testid="stSidebar"] .block-container{ padding-top:2.4rem; }
[data-testid="stSidebarNav"] a span{ font-family:'Space Mono', monospace !important;
  font-size:.8rem !important; letter-spacing:.02em; }
[data-testid="stSidebar"] h3{ font-family:'Space Mono', monospace;
  font-size:.72rem; text-transform:uppercase; letter-spacing:.1em;
  color:var(--muted); font-weight:700; }
.brandmark{ font-family:'Archivo'; font-weight:900; font-size:1.5rem;
  letter-spacing:-.03em; line-height:1; margin-bottom:2px; }
.brandmark .d{ color:var(--accent); }

/* ---------- dataframes / editor ---------- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{
  border:1px solid var(--line); border-radius:12px; overflow:hidden; }

/* ---------- radio as pills ---------- */
[data-testid="stRadio"] [role="radiogroup"]{ gap:8px; }
[data-testid="stRadio"] label{ background:var(--paper); border:1px solid var(--line);
  border-radius:999px; padding:5px 14px; font-family:'Space Mono',monospace;
  font-size:.76rem; }

/* ---------- misc ---------- */
hr, [data-testid="stDivider"]{ border-color:var(--line); }
[data-testid="stExpander"]{ border:1px solid var(--line); border-radius:12px;
  background:var(--paper); }
.rule{ height:1.5px; background:var(--ink); margin:26px 0 18px; }

/* ---------- supplement cards ---------- */
.supp{ background:var(--paper); border:1px solid var(--line); border-radius:12px;
  border-left:3px solid var(--accent); padding:13px 16px; margin-bottom:10px;
  transition:transform .15s ease, box-shadow .15s ease; }
.supp:hover{ transform:translateY(-2px);
  box-shadow:0 12px 26px -18px rgba(0,0,0,.35); }
.supp b{ font-size:1rem; font-weight:800; }
.supp .r{ color:var(--muted); font-size:.85rem; margin-top:3px; line-height:1.4; }
.supp .d{ font-family:'Space Mono', monospace; color:var(--accent);
  font-size:.74rem; margin-top:7px; letter-spacing:.02em; }

/* ---------- marquee ---------- */
.marquee{ overflow:hidden; border-top:1.5px solid var(--ink);
  border-bottom:1.5px solid var(--ink); padding:12px 0; margin-top:32px;
  -webkit-mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent); }
.marquee .track{ display:inline-block; white-space:nowrap;
  animation:scroll 26s linear infinite; }
.marquee .track span{ font-family:'Archivo'; font-weight:900; font-size:1.15rem;
  letter-spacing:-.01em; margin:0 26px; }
.marquee .track .s{ color:var(--accent); font-weight:700; }
@keyframes scroll{ from{transform:translateX(0)} to{transform:translateX(-50%)} }
</style>
"""


def _configured_password():
    """Shared access password for a deployed instance, from st.secrets or the
    APP_PASSWORD env var. Empty string => no gate (local development)."""
    import os
    pw = ""
    try:
        pw = str(st.secrets.get("app_password", "") or "")
    except Exception:
        pw = ""
    return (pw or os.environ.get("APP_PASSWORD", "")).strip()


def require_auth():
    """Password-gate the whole app whenever an access password is configured.
    No-op locally (no password set), so `streamlit run` stays frictionless."""
    pw = _configured_password()
    if not pw or st.session_state.get("_authed"):
        return
    st.markdown(
        '<div class="hero"><div class="hero-top">'
        '<span class="mono acc">[ PRIVATE ]</span>'
        '<span class="mono">T&amp;E · COACHING CONSOLE</span></div>'
        '<h1>Train&amp;Eat<span class="ast">.</span></h1>'
        '<div class="hero-sub">This console is private. Enter the access '
        'password to continue.</div></div>', unsafe_allow_html=True)
    with st.form("auth_gate"):
        entered = st.text_input("Access password", type="password")
        if st.form_submit_button("Enter", type="primary"):
            if entered == pw:
                st.session_state["_authed"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()


def setup(page_title, icon="✳"):
    st.set_page_config(page_title=f"{page_title} · T&E", page_icon=icon,
                       layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)
    require_auth()
    with st.sidebar:
        st.markdown('<div class="brandmark">TRAIN&EAT<span class="d">.</span></div>'
                    '<div class="mono">[ COACHING CONSOLE ]</div>',
                    unsafe_allow_html=True)
        st.write("")


def hero(title, subtitle="", kicker="OVERVIEW"):
    st.markdown(
        f'<div class="hero"><div class="hero-top">'
        f'<span class="mono acc">[ {kicker} ]</span>'
        f'<span class="mono">T&amp;E · ©{YEAR}</span></div>'
        f'<h1>{title} <span class="ast">✳</span></h1>'
        f'<div class="hero-sub">{subtitle}</div></div>',
        unsafe_allow_html=True)


def label(text):
    st.markdown(f'<div class="mono ink" style="margin:14px 0 4px">[ {text} ]</div>',
                unsafe_allow_html=True)


def stat_row(items):
    """items = [(number, caption), ...]"""
    cells = "".join(
        f'<div class="stat"><div class="num">{n}</div>'
        f'<div class="cap mono">{c}</div></div>' for n, c in items)
    st.markdown(f'<div class="statrow">{cells}</div>', unsafe_allow_html=True)


def card(kicker, title, body):
    return (f'<div class="card"><div class="k mono acc">[ {kicker} ]</div>'
            f'<h3>{title}</h3><p>{body}</p></div>')


def marquee(word="TRAIN & EAT", n=8):
    unit = f'<span>{word}</span><span class="s">✳</span>'
    st.markdown(f'<div class="marquee"><div class="track">{unit*n}{unit*n}</div></div>',
                unsafe_allow_html=True)


def client_picker():
    clients = cl.load_clients()
    names = sorted(clients.keys())
    with st.sidebar:
        st.markdown("### Active client")
        options = ["＋ New client…"] + names
        # Keyed picker with stable identity (a keyless index=-driven selectbox
        # changes widget identity between runs and drops the user's selection
        # every other switch). Seed once, then let widget state own it.
        pending = st.session_state.pop("client_pick_pending", None)
        if pending in options:
            st.session_state["client_pick"] = pending
        if ("client_pick" not in st.session_state
                or st.session_state["client_pick"] not in options):
            cur = st.session_state.get("client")
            st.session_state["client_pick"] = (
                cur if cur in options else (options[1] if names else options[0]))
        choice = st.selectbox("client", options, key="client_pick",
                              label_visibility="collapsed")
        if choice == "＋ New client…":
            newname = st.text_input("Name for new client")
            if st.button("Create client", width="stretch") and newname.strip():
                cl.upsert_client(newname.strip(), {})
                st.session_state["client"] = newname.strip()
                st.session_state["client_pick_pending"] = newname.strip()
                st.rerun()
            return None
        st.session_state["client"] = choice
        return choice
