"""Editorial design system for the T&E coaching app.

Art direction: warm cream canvas, ink-black type, one hot-orange accent.
Bricolage Grotesque (ink-trap display) for headlines and big numbers,
Archivo for body/UI, Space Mono for [bracket] microlabels.
Signature: the measuring-tape tick ruler under every hero — this app is
about measurement (grams, lbs, steps, weeks). Restrained palette, strong
hierarchy, one orchestrated load sequence. (No Inter. One accent.
Moderation = quality.)
"""
import re as _re
import sys
import html as _html
from datetime import date as _date
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
import streamlit as st
import coachlib as cl
from i18n import t

YEAR = "2026"

# ---------------- theme engine (semantic tokens, light/dark/system) ----------
# Components reference ROLES (via the legacy aliases), never raw hexes, so
# both themes are defined in one place. Dark's "invert" bars are an elevated
# warm panel — not pure black — so they stay distinct on a dark page.
_TOKENS_LIGHT = {
    "bg": "#EFEDE6", "surface": "#FBFAF6", "surface-2": "#E8E4DB",
    "fg": "#17150F", "fg-muted": "#78736A",
    "border": "#CDC6B8", "border-soft": "#E4E0D6",
    "invert-bg": "#17150F", "invert-fg": "#EFEDE6",
    "invert-muted": "#cfc9bf",
    "accent": "#E4531F", "accent-2": "#C9430F",
    "good": "#3F7A5B", "warn": "#B07A22", "over": "#B23A2E",
    "good-soft": "#E2ECE5", "warn-soft": "#F6E9D2",
    "over-soft": "#F3DBD8", "hover": "#F3F1EA",
}
_TOKENS_DARK = {
    "bg": "#15120C", "surface": "#201C14", "surface-2": "#2A251C",
    "fg": "#F1EEE7", "fg-muted": "#9E978B",
    "border": "#39332B", "border-soft": "#39332B",
    "invert-bg": "#322C22", "invert-fg": "#F5F2EB",
    "invert-muted": "#B5AC9E",
    "accent": "#F2662F", "accent-2": "#F58A55",
    "good": "#67A987", "warn": "#CDA24A", "over": "#D8695C",
    "good-soft": "#233A2E", "warn-soft": "#3B3220",
    "over-soft": "#422620", "hover": "#2E2820",
}


def _vars_block(tok):
    pairs = "".join(f"--{k}:{v};" for k, v in tok.items())
    legacy = ("--cream:var(--bg);--paper:var(--surface);"
              "--sand:var(--surface-2);--ink:var(--fg);"
              "--muted:var(--fg-muted);--line:var(--border);"
              "--accent2:var(--accent-2);")
    return pairs + legacy


def current_lang():
    """'en' | 'es' — the session language (loaded from the user's record)."""
    lang = st.session_state.get("_lang", "en")
    return lang if lang in ("en", "es") else "en"


def load_prefs():
    """Load the signed-in user's lang/theme into the session once. Records
    without prefs (or anonymous visitors) default to en/system — never
    errors. Called from setup() on every run (no-ops after the first)."""
    if "_lang" in st.session_state and "_theme" in st.session_state:
        return
    lang = theme = None
    try:
        role = current_role()
        if role == "client":
            rec = cl.get_client(
                st.session_state.get("_client_self") or "") or {}
            lang, theme = rec.get("lang"), rec.get("theme")
        elif role == "coach" and st.session_state.get("_authed"):
            prefs = cl.get_settings().get("coach_prefs") or {}
            p = prefs.get(current_coach() or "coach") or {}
            lang, theme = p.get("lang"), p.get("theme")
    except Exception:
        pass
    st.session_state.setdefault(
        "_lang", lang if lang in ("en", "es") else "en")
    st.session_state.setdefault(
        "_theme", theme if theme in ("light", "dark", "system")
        else "system")


def save_pref(field, value):
    """Persist a lang/theme choice to the signed-in user's record and apply
    it to the session immediately. Callback-safe."""
    st.session_state["_" + field] = value
    try:
        role = current_role()
        if role == "client":
            me = st.session_state.get("_client_self")
            if me:
                cl.upsert_client(me, {field: value})
        elif role == "coach" and st.session_state.get("_authed"):
            prefs = dict(cl.get_settings().get("coach_prefs") or {})
            who = current_coach() or "coach"
            p = dict(prefs.get(who) or {})
            p[field] = value
            prefs[who] = p
            cl.save_settings({"coach_prefs": prefs})
    except Exception:
        pass   # a failed write must never break the page


def _cycle_theme():
    order = ["system", "light", "dark"]
    cur = current_theme()
    save_pref("theme", order[(order.index(cur) + 1) % 3])


def _pref_toggles():
    """EN | ES + theme cycle — squared mini-blocks, shared by both bars."""
    with st.container(key="tb_prefs"):
        c1, c2, c3 = st.columns(3, gap="small")
        lang = current_lang()
        c1.button("EN", key="tb_lang_en",
                  type=("primary" if lang == "en" else "secondary"),
                  on_click=save_pref, args=("lang", "en"),
                  use_container_width=True)
        c2.button("ES", key="tb_lang_es",
                  type=("primary" if lang == "es" else "secondary"),
                  on_click=save_pref, args=("lang", "es"),
                  use_container_width=True)
        icon = {"system": "◐", "light": "☀", "dark": "☾"}[current_theme()]
        c3.button(icon, key="tb_theme", on_click=_cycle_theme,
                  help=t("tb_theme_help"),
                  use_container_width=True)


def current_theme():
    """The stored preference: 'system' | 'light' | 'dark'."""
    t = st.session_state.get("_theme", "system")
    return t if t in ("system", "light", "dark") else "system"


def effective_theme():
    """'light' | 'dark' — resolves 'system' via the browser when the
    runtime exposes it (st.context.theme), else light."""
    t = current_theme()
    if t in ("light", "dark"):
        return t
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def chart_palette():
    return dict(_TOKENS_DARK if effective_theme() == "dark"
                else _TOKENS_LIGHT)


def theme_css():
    """The :root token block for the stored preference. 'system' emits both
    palettes behind prefers-color-scheme — no JS, survives every rerun."""
    light, dark = _vars_block(_TOKENS_LIGHT), _vars_block(_TOKENS_DARK)
    t = current_theme()
    if t == "dark":
        return f"<style>:root{{{dark}}}</style>"
    if t == "light":
        return f"<style>:root{{{light}}}</style>"
    return (f"<style>:root{{{light}}}"
            f"@media (prefers-color-scheme: dark){{:root{{{dark}}}}}"
            "</style>")


def _hex_rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,600&family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=Space+Mono:wght@400;700&display=swap');

/* Color tokens are injected per-run by theme_css() (light/dark/system) —
   the legacy names (--cream/--paper/--sand/--ink/--muted/--line/--accent2)
   are aliased to the semantic roles there. Only fonts live here. */
:root{
  --body:'Archivo',-apple-system,BlinkMacSystemFont,sans-serif;
  --mono:'Space Mono',monospace;
  --display:'Bricolage Grotesque','Archivo',sans-serif;
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
}
@keyframes fadeup{ from{opacity:0; transform:translateY(8px)} to{opacity:1; transform:none} }
@keyframes fadein{ from{opacity:0} to{opacity:1} }
/* Motion only when the visitor hasn't asked for less. The main container fades
   opacity-ONLY: a transform here (even the identity matrix that animation
   fill-mode leaves behind) turns it into the containing block for the
   position:fixed nav rail, shoving the rail inward on wide screens. */
@media (prefers-reduced-motion: no-preference){
  [data-testid="stMain"] .block-container{ animation:fadein .45s ease both; }
}
@media (prefers-reduced-motion: reduce){
  *, *::before, *::after{ animation-duration:.001ms !important;
    animation-iteration-count:1 !important; transition-duration:.001ms !important; }
}
/* Visible keyboard focus — the accent ring, never removed. */
:where(a, button, input, textarea, select, [role="button"], [tabindex]):focus-visible{
  outline:2.5px solid var(--accent); outline-offset:2px; border-radius:6px; }
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
/* Signature: a measuring-tape tick ruler closes every hero — minor ticks,
   taller major ticks, ink baseline. Measurement is what this console does. */
.hero{ position:relative; padding:30px 0 30px; margin-bottom:14px; }
.hero:after{ content:""; position:absolute; left:0; right:0; bottom:0; height:15px;
  pointer-events:none;
  background:
    repeating-linear-gradient(90deg, var(--ink) 0 1.5px, transparent 1.5px 56px),
    repeating-linear-gradient(90deg, #B9B29F 0 1px, transparent 1px 8px),
    linear-gradient(var(--ink), var(--ink));
  background-size:auto 15px, auto 8px, 100% 1.5px;
  background-position:bottom left, bottom left, bottom left;
  background-repeat:repeat-x, repeat-x, no-repeat; }
.hero-top{ display:flex; justify-content:space-between; align-items:center;
  margin-bottom:20px; }
.hero h1{ font-family:'Bricolage Grotesque','Archivo',sans-serif;
  font-size:clamp(2rem, 1.3rem + 3vw, 3.15rem); line-height:.98; font-weight:800;
  letter-spacing:-.03em; margin:0; max-width:15ch; }
.hero .ast{ color:var(--accent); font-weight:700; }
.hero-sub{ margin-top:14px; max-width:56ch; color:#453f34;
  color:color-mix(in srgb, var(--fg) 78%, var(--bg)); font-size:1rem;
  line-height:1.5; }
/* One orchestrated load sequence: kicker → headline → sub → stats. */
@media (prefers-reduced-motion: no-preference){
  .hero .hero-top{ animation:fadeup .4s ease both; }
  .hero h1{ animation:fadeup .5s ease .06s both; }
  .hero-sub{ animation:fadeup .5s ease .14s both; }
  .statrow .stat{ animation:fadeup .5s ease .2s both; }
  .statrow .stat:nth-child(2){ animation-delay:.27s }
  .statrow .stat:nth-child(3){ animation-delay:.34s }
  .statrow .stat:nth-child(4){ animation-delay:.41s }
  .statrow .stat:nth-child(5){ animation-delay:.48s }
}

/* ---------- stat row ---------- */
.statrow{ display:flex; gap:44px; flex-wrap:wrap; margin:6px 0 4px; }
.stat .num{ font-family:'Bricolage Grotesque','Archivo',sans-serif;
  font-weight:800; font-size:2.1rem; letter-spacing:-.02em; line-height:1;
  font-variant-numeric:tabular-nums; }
.stat .num .u{ color:var(--accent); }
.stat .cap{ margin-top:6px; }

/* ---------- multiselect chips: sand, not a wall of orange ---------- */
span[data-baseweb="tag"]{background-color:var(--sand)!important;border:1px solid var(--line)!important}
span[data-baseweb="tag"] span{color:var(--ink)!important}
span[data-baseweb="tag"] svg{fill:var(--muted)!important;color:var(--muted)!important}

/* labels never clip ("Save this plan to clien") */
.stButton button,.stFormSubmitButton>button{min-width:max-content!important;overflow:visible!important}

/* Applications row actions: Decline = quiet outline, Delete = danger —
   three identical ink pills hide which one is destructive. */
[class*="st-key-conv_"] button{background:var(--accent)!important;border:1.5px solid var(--accent)!important;color:var(--invert-fg)!important}
[class*="st-key-conv_"] button:hover{background:var(--accent2)!important;border-color:var(--accent2)!important}
[class*="st-key-conv_"] button p{color:var(--invert-fg)!important}
[class*="st-key-dec_"] button{background:transparent!important;border:1px solid var(--line)!important;color:var(--ink)!important;box-shadow:none!important}
[class*="st-key-dec_"] button:hover{border-color:var(--ink)!important}
[class*="st-key-dec_"] button p{color:inherit!important}
[class*="st-key-del_"] button{background:transparent!important;border:1px solid var(--over)!important;color:var(--over)!important;box-shadow:none!important}
[class*="st-key-del_"] button:hover{background:var(--over)!important;border-color:var(--over)!important;color:var(--invert-fg)!important}
[class*="st-key-del_"] button p{color:inherit!important}

/* ---------- cards ---------- */
.card{ background:var(--paper); border:1px solid var(--line);
  border-radius:16px; padding:18px 20px; height:100%;
  transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; }
.card:hover{ transform:translateY(-3px);
  box-shadow:none; border-color:#C7C0B0; }
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
[data-testid="stMetricValue"]{ font-family:'Bricolage Grotesque','Archivo',sans-serif;
  font-weight:800; font-size:1.7rem; letter-spacing:-.015em;
  font-variant-numeric:tabular-nums; }
[data-testid="stMetricDelta"]{ font-family:'Space Mono', monospace;
  font-size:.72rem; }

/* ---------- buttons — squared index-block system (3px, no pills) ----------
   secondary = paper, hairline, muted · primary = solid ink. Accent CTAs
   (Convert, Create client, dashboard Log/Start) come from key-scoped rules. */
.stButton button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button{
  border-radius:3px !important; border:1.5px solid var(--line);
  background:var(--paper); color:var(--muted);
  font-family:'Space Mono', monospace !important; font-weight:700;
  letter-spacing:.06em; text-transform:uppercase; font-size:.78rem;
  padding:11px 18px !important; white-space:nowrap; box-shadow:none;
  transition:all .16s ease; }
/* Button labels render as button > div > p — every layer must inherit the
   button's colour (inherit only reaches one level up), or the global ink
   text rule wins and same-on-same buttons show no text at all. */
.stButton button *, .stDownloadButton > button *,
[data-testid="stFormSubmitButton"] button *{
  color:inherit !important; font-family:inherit !important;
  font-size:inherit !important; }
.stButton button:hover, .stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] button:hover{
  border-color:var(--ink); color:var(--ink); transform:none; box-shadow:none; }
button[kind="primary"], button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"]{ background:var(--invert-bg) !important;
  border:1.5px solid var(--invert-bg) !important;
  color:var(--invert-fg) !important;
  box-shadow:none; }
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover{
  background:var(--invert-bg) !important; border-color:var(--accent) !important; }
.stButton button:active, .stDownloadButton > button:active,
[data-testid="stFormSubmitButton"] button:active{
  transform:scale(.985); box-shadow:none; }
/* index-tab number prefix (e.g. "01 · Push") — accent on the active block */
button[kind="primary"] .tabnum{ color:var(--accent) !important; }
/* quiet text-link button (sidebar logout) */
[class*="st-key-sb_logout"] .stButton button{
  background:transparent; border-color:transparent; color:var(--muted);
  box-shadow:none; padding:.3rem .5rem; font-size:.72rem; }
[class*="st-key-sb_logout"] .stButton button:hover{
  background:transparent; border-color:transparent; color:var(--accent);
  transform:none; box-shadow:none; }
/* ---------- inputs ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, .stTextArea textarea,
[data-baseweb="base-input"]{ background:var(--paper) !important;
  border-radius:10px !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within,
.stTextArea:focus-within textarea{ border-color:var(--accent) !important; }
[data-testid="stWidgetLabel"] p{ font-family:'Space Mono', monospace;
  font-size:.72rem; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{ background:var(--sand); border-right:1.5px solid var(--ink); }
[data-testid="stSidebar"] .block-container{ padding-top:2.4rem; }
[data-testid="stSidebarNav"] a span{ font-family:'Space Mono', monospace !important;
  font-size:.8rem !important; letter-spacing:.02em; }
[data-testid="stSidebarNav"] a{ border-radius:8px;
  transition:background .15s ease; }
/* Current page: paper chip + accent tab, so you always know where you are. */
[data-testid="stSidebarNav"] a[aria-current="page"]{ background:var(--paper);
  box-shadow:inset 3px 0 0 var(--accent); }
/* The public Apply form is applicant-facing — keep it out of the coach nav.
   (Visitors never see this nav at all; coaches can still open /Apply.) */
[data-testid="stSidebarNav"] a[href$="/Apply"]{ display:none; }
[data-testid="stSidebarNav"] a[aria-current="page"] span{
  color:var(--ink) !important; font-weight:700; }
[data-testid="stSidebar"] h3{ font-family:'Space Mono', monospace;
  font-size:.72rem; text-transform:uppercase; letter-spacing:.1em;
  color:var(--muted); font-weight:700; }
.brandmark{ font-family:'Bricolage Grotesque','Archivo',sans-serif;
  font-weight:800; font-size:1.5rem; letter-spacing:-.02em; line-height:1;
  margin-bottom:2px; }
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
.rule{ height:1.5px; background:var(--invert-bg); margin:26px 0 18px; }

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
.marquee .track span{ font-family:'Bricolage Grotesque','Archivo',sans-serif;
  font-weight:800; font-size:1.15rem; letter-spacing:-.01em; margin:0 26px; }
.marquee .track .s{ color:var(--accent); font-weight:700; }
@keyframes scroll{ from{transform:translateX(0)} to{transform:translateX(-50%)} }
.marquee .track{ animation-play-state:running; }
@media (prefers-reduced-motion: reduce){ .marquee .track{ animation:none; } }

/* ---------- semantic data colours (used sparingly, data only) ---------- */
.good{ color:var(--good) !important; }
.over{ color:var(--over) !important; }

/* ---------- alerts, on-brand ---------- */
/* st.info/success/error read as part of the paper system, not dashboard neon.
   Kind is signalled by the left tab only. */
[data-testid="stAlert"]{ background:var(--paper) !important;
  border:1px solid var(--line); border-left:3px solid var(--accent);
  border-radius:12px; }
[data-testid="stAlert"] p{ color:var(--ink); font-size:.9rem; }
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]){
  border-left-color:var(--good); }
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]){
  border-left-color:var(--over); }
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]){
  border-left-color:var(--warn); }

/* ---------- empty states ---------- */
.empty{ border:1.5px dashed #C4BCAA; border-radius:16px;
  padding:24px 26px 20px; margin:6px 0 4px; }
.empty h3{ margin:8px 0 4px; }
.empty p{ color:var(--muted); font-size:.9rem; margin:0; line-height:1.5;
  max-width:52ch; }

/* ---------- scroll progress hairline (progressive enhancement) ---------- */
@supports (animation-timeline: scroll()){
  [data-testid="stMain"]::before{ content:""; position:fixed; top:0; left:0;
    width:100%; height:2.5px; background:var(--accent); z-index:9999;
    transform-origin:0 0; transform:scaleX(0); pointer-events:none;
    animation:growbar linear both; animation-timeline:scroll(nearest); }
  @keyframes growbar{ to{ transform:scaleX(1) } }
}

/* ---------- responsive: tablet & phone ---------- */
@media (max-width: 900px){
  [data-testid="stMain"] .block-container{ padding-top:1.2rem; }
  .statrow{ gap:26px 30px; }
  .stat .num{ font-size:1.75rem; }
}
@media (max-width: 560px){
  .hero h1{ max-width:100%; }
  .hero-sub{ font-size:.95rem; }
  .statrow{ gap:20px 24px; }
}

/* ---------- redesigned public landing + active-client panel (te-*) ------- */
.te-hero{padding:34px 0 6px}
.te-hero .kicker{font-family:"Space Mono",monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent2);margin-bottom:18px}
.te-hero h1{font-family:"Bricolage Grotesque",serif;font-weight:800;font-size:clamp(44px,7.5vw,96px);line-height:.94;letter-spacing:-.03em;max-width:15ch;color:var(--ink);margin:0}
.te-hero .sub{font-size:19px;color:var(--muted);max-width:46ch;margin:24px 0 30px;line-height:1.5}
.te-hero .mark{position:relative;white-space:nowrap}
.te-hero .mark:before{content:"";position:absolute;left:-.06em;right:-.06em;bottom:.08em;height:.42em;background:var(--accent);z-index:-1;transform:skewX(-9deg) scaleX(0);transform-origin:left;border-radius:1px;animation:teSwipe .7s .45s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes teSwipe{to{transform:skewX(-9deg) scaleX(1)}}
@media(prefers-reduced-motion:reduce){.te-hero .mark:before{transform:skewX(-9deg) scaleX(1);animation:none}}
a.applycta{font-family:"Space Mono",monospace;font-weight:700;font-size:14px;letter-spacing:.06em;text-transform:uppercase;background:var(--accent);color:var(--invert-fg)!important;text-decoration:none;border:0;padding:15px 26px;border-radius:3px;display:inline-flex;gap:12px;align-items:center;white-space:nowrap;transition:.18s}
a.applycta:hover{background:var(--accent2);gap:16px}
a.applycta span{display:inline-block}
[class*="st-key-coach_access"] button{background:transparent!important;border:none!important;box-shadow:none!important;padding:6px 0!important;min-height:0!important;justify-content:flex-start!important}
[class*="st-key-coach_access"] button p{font-family:"Space Mono",monospace!important;font-size:13px!important;letter-spacing:.04em!important;color:var(--muted)!important}
[class*="st-key-coach_access"] button:hover p{color:var(--ink)!important}
[class*="st-key-coach_access"] .stButton button:hover{transform:none}
.te-ruler{height:34px;margin:16px 0 6px;opacity:.5;border-bottom:1.5px solid var(--ink);background-image:repeating-linear-gradient(90deg,var(--ink) 0 1px,transparent 1px 11px),repeating-linear-gradient(90deg,var(--ink) 0 1.5px,transparent 1.5px 55px);background-size:100% 10px,100% 20px;background-repeat:no-repeat;background-position:left bottom,left bottom}
.te-ruler.thin{height:20px;margin:26px 0 0;opacity:.35;background-size:100% 8px,100% 16px}
/* landing sections below the hero (public page only) */
.te-kicker{font-family:"Space Mono",monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent2)}
.te-stats{padding:30px 0 4px}
.te-statgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin-top:16px}
.te-stat{padding:8px 28px 8px 0;border-right:1px solid var(--line)}
.te-stat:not(:first-child){padding-left:28px}
.te-stat:last-child{border-right:0;padding-right:0}
.te-stat .cap{font-family:"Space Mono",monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.te-stat .num{font-family:"Bricolage Grotesque",serif;font-weight:800;font-size:clamp(44px,6.5vw,84px);line-height:1;letter-spacing:-.03em;color:var(--ink);font-variant-numeric:tabular-nums}
.te-spread{background:var(--invert-bg);border-radius:6px;padding:52px 44px 40px;margin-top:34px}
.te-spread .te-kicker{color:var(--accent)}
/* .te-h2 is a styled div, not a real h2: Streamlit rewrites headings inside
   markdown (anchor + span wrap), and the injected span picks up the global
   ink colour — invisible on the ink background. */
.te-spread .te-h2{font-family:"Bricolage Grotesque",serif;font-weight:800;font-size:clamp(28px,4.6vw,54px);line-height:1.04;letter-spacing:-.02em;color:var(--invert-fg);max-width:20ch;margin:16px 0 0}
.te-spread .te-h2 em{font-style:normal;color:var(--accent)}
.te-proof{display:flex;gap:20px 56px;margin-top:40px;flex-wrap:wrap}
.te-proof .n{font-family:"Bricolage Grotesque",serif;font-weight:800;font-size:clamp(38px,5vw,52px);letter-spacing:-.03em;line-height:1;color:var(--invert-fg);font-variant-numeric:tabular-nums}
.te-proof .c{font-family:"Space Mono",monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--invert-muted);margin-top:8px}
.te-spread .te-ruler{filter:invert(1);opacity:.28;margin:48px 0 0}
.te-foot{padding:30px 0 6px;text-align:center;font-family:"Space Mono",monospace;font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
@media(max-width:720px){
  .te-statgrid{grid-template-columns:1fr}
  .te-stat{border-right:0;border-bottom:1px solid var(--line);padding:18px 0}
  .te-stat:not(:first-child){padding-left:0}
  .te-stat:last-child{border-bottom:0}
  .te-spread{padding:36px 24px 30px;border-radius:5px}
  .te-proof{gap:22px 34px}
}
.te-panel{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:30px 34px}
.te-panel .head{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:26px}
.te-panel h2{font-family:"Bricolage Grotesque",serif;font-weight:800;font-size:clamp(28px,4vw,40px);letter-spacing:-.02em;line-height:1;margin:0;color:var(--ink)}
.te-panel .contact{font-family:"Space Mono",monospace;font-size:12px;color:var(--muted);letter-spacing:.03em;margin-top:9px}
.te-status{flex:none;font-family:"Space Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;border-radius:999px;padding:5px 12px;white-space:nowrap}
.te-status.good{color:var(--good);border:1px solid var(--good)}
.te-status.warn{color:var(--warn);border:1px solid var(--warn)}
.te-status.over{color:var(--over);border:1px solid var(--over)}
.te-metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:26px;row-gap:26px;align-items:start}
.te-metric .l{font-family:"Space Mono",monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.te-metric .v{font-family:"Bricolage Grotesque",serif;font-weight:800;font-size:clamp(30px,4vw,36px);letter-spacing:-.02em;line-height:1;color:var(--ink);font-variant-numeric:tabular-nums}
.te-metric .v small{font-size:15px;font-weight:600;color:var(--muted);margin-left:3px}
.te-metric .delta{font-family:"Space Mono",monospace;font-size:12px;margin-top:9px;display:inline-flex;gap:6px;align-items:center}
.te-metric .delta.good{color:var(--good)}
.te-metric .delta.over{color:var(--over)}
.te-metric .delta.neutral{color:var(--muted)}
@media(min-width:1100px){.te-metrics{grid-template-columns:repeat(4,minmax(0,1fr))}}

/* ---------- styled editable table (st.data_editor is canvas-rendered and
   can't be restyled — cells here are real keyed inputs in a paper frame) --- */
[class*="st-key-et_box_"]{background:var(--paper);border:1px solid var(--line);
  border-radius:8px;padding:4px 14px 12px}
[class*="st-key-et_box_"] [data-testid="stVerticalBlock"]{gap:6px}
[class*="st-key-et_box_"] .eth{font-family:var(--mono);font-size:10px;
  letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
  padding:10px 2px 7px;border-bottom:1px solid var(--line);white-space:nowrap}
[class*="st-key-et_box_"] [data-testid="stTextInput"]{margin:0}
[class*="st-key-et_box_"] [data-baseweb="input"]{background:var(--cream)!important;
  border:1px solid var(--line)!important;border-radius:5px!important}
[class*="st-key-et_box_"] [data-baseweb="input"]:focus-within{border-color:var(--ink)!important}
[class*="st-key-et_box_"] [data-baseweb="input"] input{background:transparent!important;
  border:none!important;padding:7px 10px!important;font-size:14px!important;
  font-family:var(--body)!important}
/* per-row delete: a quiet ✕, not a pill */
[class*="st-key-et_box_"] .stButton button{background:transparent!important;
  border:none!important;box-shadow:none!important;color:var(--muted)!important;
  padding:2px 6px!important;min-height:0!important;min-width:0!important}
[class*="st-key-et_box_"] .stButton button:hover{color:var(--over)!important;transform:none!important}
[class*="st-key-et_box_"] .stButton button p{color:inherit!important;font-size:15px!important}
/* add-row control under the frame — mono accent link, not a pill */
[class*="st-key-et_add_"] button{background:transparent!important;border:none!important;
  box-shadow:none!important;padding:6px 2px!important;min-height:0!important;
  justify-content:flex-start!important}
[class*="st-key-et_add_"] button p{font-family:var(--mono)!important;font-size:12.5px!important;
  letter-spacing:.04em!important;color:var(--accent2)!important}
[class*="st-key-et_add_"] button:hover p{color:var(--ink)!important}
[class*="st-key-et_add_"] button:hover{transform:none!important}

/* ---------- read-only editorial table (client-facing / summaries) --------- */
.te-tblwrap{overflow-x:auto}
.te-tbl{width:100%;border-collapse:separate;border-spacing:0;background:var(--paper);
  border:1px solid var(--line);border-radius:8px;overflow:hidden}
.te-tbl th{font-family:var(--mono);font-size:10px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted);text-align:left;padding:12px 14px;
  border-bottom:1px solid var(--line);background:var(--sand)}
.te-tbl td{padding:10px 14px;border-bottom:1px solid var(--line);font-size:14px;
  vertical-align:middle}
.te-tbl tr:last-child td{border-bottom:none}
.te-tbl td.mono{font-family:var(--mono);font-size:13px;text-align:center}

/* ---------- client training view (read-only program cards) ---------------- */
.te-blockchip{font-family:var(--mono);font-size:11px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);white-space:nowrap}
.te-ex{background:var(--paper);border:1px solid var(--line);border-radius:8px;
  padding:16px 18px}
.te-ex .name{font-family:var(--display);font-weight:800;font-size:19px;
  letter-spacing:-.01em;color:var(--ink)}
.te-ex .scheme{font-family:var(--mono);font-size:14px;color:var(--ink);margin-top:4px}
.te-ex .scheme b{color:var(--accent2)}
.te-ex .cue{font-size:13.5px;color:var(--muted);margin-top:7px}
.te-ex a.vid{font-family:var(--mono);font-size:12px;color:var(--accent2);
  margin-top:9px;display:inline-flex;gap:6px;align-items:center;
  text-decoration:none;border-bottom:none}
.te-ex a.vid:hover{color:var(--ink)}
/* whole-workout done: green when complete (disabled = the done state) */
[class*="st-key-tl_doneall"] button:disabled{background:var(--good)!important;
  border-color:var(--good)!important;color:#fff!important;opacity:1!important;
  cursor:default!important}
/* the mark-done column: a 22px rounded box, green when checked */
[class*="st-key-tl_list"] [data-testid="stVerticalBlock"]{gap:12px}
[class*="st-key-tl_list"] [data-testid="stCheckbox"]{margin:0}
[class*="st-key-tl_list"] [data-testid="stCheckbox"] label > span:first-of-type{
  width:22px;height:22px;border-radius:5px}
[class*="st-key-tl_list"] label:has(input:checked) > span:first-of-type{
  background-color:var(--good)!important;border-color:var(--good)!important}

/* Sticky must live on Streamlit's per-element LayoutWrapper — a sticky child
   can't escape its own wrapper (it's exactly bar-height, so it just scrolls
   away). This pins BOTH bars' wrappers to the scrollport top. */
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-te_topbar"]){
  position:sticky;top:0;z-index:50}

/* ---------- client top bar: sticky + slim (te_topbar_client extends the
   base st-key-te_topbar styles by substring; these later rules win) -------- */
[class*="st-key-te_topbar_client"]{position:sticky;top:0;z-index:50;
  background:rgba(239,237,230,.90);
  background:color-mix(in srgb, var(--bg) 90%, transparent);
  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line);box-shadow:none;
  padding:11px 0;margin-bottom:8px}
[class*="st-key-te_topbar_client"] .te-brand .sq{width:32px;height:32px;
  border-radius:8px;font-size:16px}
[class*="st-key-te_topbar_client"] .te-brand .wm{font-size:11px}
[class*="st-key-te_topbar_client"] .te-brand::after{height:22px}
[class*="st-key-te_topbar_client"] [class*="st-key-tb_avatar"]
  [data-testid="stPopoverButton"]{width:34px!important;height:34px!important;
  font-size:14px!important}
[class*="st-key-te_topbar_client"] [class*="st-key-tb_help"]
  [data-testid="stPopoverButton"]{width:34px!important;height:34px!important}

/* ---------- top-bar pref toggles (EN|ES · theme) — both bars ------------- */
[class*="st-key-tb_prefs"] [data-testid="stColumn"]{min-width:0}
[class*="st-key-tb_prefs"] [data-testid="stHorizontalBlock"]{gap:5px}
[class*="st-key-tb_prefs"] .stButton button{
  min-height:30px;height:30px;padding:2px 6px !important;
  font-size:.66rem !important;letter-spacing:.08em;border-width:1px}
[class*="st-key-tb_prefs"] .stButton button p{font-size:.66rem !important}

/* ---------- client dashboard (td-*) --------------------------------------- */
.te-coachchip2{font-family:var(--mono);font-size:10px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted);text-align:right;line-height:1.35}
.te-coachchip2 b{display:block;color:var(--ink);font-weight:700;font-size:11px}
/* client avatar: accent circle, ink ring (coach keeps ink circle, orange ring) */
[class*="st-key-tb_avatar_client"] [data-testid="stPopoverButton"]{
  background:var(--accent)!important;
  box-shadow:0 0 0 2px var(--cream),0 0 0 4px var(--ink)!important}
/* hero-forward landing: the greeting sits high, no tall header gap */
.td-hero{padding-top:8px!important}
.td-hero h1{font-size:clamp(38px,6vw,68px)!important}
.td-sub{font-family:var(--mono);font-size:12.5px;color:var(--muted);
  letter-spacing:.04em;margin-top:16px;text-transform:uppercase}
.td-streak{display:inline-block;font-family:var(--mono);font-size:10.5px;
  letter-spacing:.1em;color:var(--good);border:1px solid var(--good);
  border-radius:999px;padding:3px 10px;margin-left:10px}
.td-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px;
  padding:20px 0 4px}
.td-stats .l{font-family:var(--mono);font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ink);font-weight:700;margin-bottom:9px;
  line-height:1.35;overflow-wrap:normal;word-break:keep-all}
.td-stats .v{font-family:var(--display);font-weight:800;
  font-size:clamp(40px,5vw,52px);letter-spacing:-.02em;line-height:1;
  color:var(--ink);font-variant-numeric:tabular-nums;white-space:nowrap}
.td-stats .v small{font-size:16px;font-weight:600;color:var(--muted)}
.td-stats .v.warn{color:var(--warn);font-size:32px}
.td-stats .d{font-family:var(--mono);font-size:12px;margin-top:9px;
  display:inline-flex;gap:6px;align-items:center}
.td-stats .d.good{color:var(--good)}.td-stats .d.over{color:var(--over)}
.td-stats .d.warn{color:var(--warn)}.td-stats .d.mut{color:var(--muted)}
.td-pill{display:inline-block;font-family:var(--mono);font-size:11px;
  letter-spacing:.1em;text-transform:uppercase;border-radius:999px;
  padding:4px 10px;margin-top:8px;color:var(--warn);border:1px solid var(--warn)}
.td-trend{display:flex;gap:14px 34px;flex-wrap:wrap;font-family:var(--mono);
  font-size:12px;color:var(--muted);letter-spacing:.03em;padding:12px 0 2px;
  border-top:1px solid var(--line);margin-top:16px}
.td-trend b{color:var(--ink);font-weight:700}
.td-trend .g{color:var(--good)}.td-trend .o{color:var(--over)}
[class*="st-key-td_card_"]{background:var(--paper);border:1px solid var(--line);
  border-radius:8px;padding:18px 22px}
[class*="st-key-td_card_"] [data-testid="stVerticalBlock"]{gap:10px}
.td-h3{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted);margin:0 0 6px}
.td-ico{width:34px;height:34px;border-radius:8px;background:var(--sand);
  display:flex;align-items:center;justify-content:center;font-size:16px}
.td-todo-n{font-weight:600;font-size:15px;color:var(--ink)}
.td-todo-s{font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:2px}
.td-done{color:var(--good);font-family:var(--mono);font-size:12px;white-space:nowrap}
.td-rule{height:1px;background:var(--line);margin:2px 0}
/* orange / ghost page-link buttons inside the to-do card */
[class*="st-key-td_go_"] a{background:var(--accent);border-radius:4px;
  padding:9px 15px;text-decoration:none;display:inline-flex;border:none}
[class*="st-key-td_go_"] a:hover{background:var(--accent2)}
[class*="st-key-td_go_"] a p,[class*="st-key-td_go_"] a span{
  color:#fff!important;font-family:var(--mono)!important;font-weight:700!important;
  font-size:12px!important;letter-spacing:.05em!important;text-transform:uppercase!important;
  margin:0!important}
[class*="st-key-td_ghost_"] a{background:transparent;border:1px solid var(--line);
  border-radius:4px;padding:8px 14px;text-decoration:none;display:inline-flex}
[class*="st-key-td_ghost_"] a:hover{border-color:var(--ink)}
[class*="st-key-td_ghost_"] a p,[class*="st-key-td_ghost_"] a span{
  color:var(--ink)!important;font-family:var(--mono)!important;font-size:12px!important;
  letter-spacing:.05em!important;text-transform:uppercase!important;margin:0!important}
/* quick cards + their open links */
.td-qcard{position:relative;background:var(--paper);border:1px solid var(--line);
  border-radius:8px;padding:18px 20px;overflow:hidden}
.td-qcard:after{content:"";position:absolute;top:0;left:0;width:30px;height:3px;
  background:var(--accent)}
.td-qcard .qn{font-family:var(--mono);font-size:10px;color:var(--accent);
  letter-spacing:.14em}
.td-qcard h4{font-family:var(--display);font-weight:800;font-size:19px;
  margin:10px 0 6px;letter-spacing:-.01em;color:var(--ink)}
.td-qcard p{font-size:13px;color:var(--muted);margin:0}
/* whole-card click targets: the page_link stretches invisibly over the card */
[class*="st-key-td_qwrap_"]{position:relative}
[class*="st-key-td_qwrap_"] [data-testid="stVerticalBlock"]{gap:0}
[class*="st-key-td_qwrap_"] .td-qcard{transition:transform .16s ease,
  box-shadow .16s ease,border-color .16s ease}
[class*="st-key-td_qwrap_"]:hover .td-qcard{transform:translateY(-3px);
  box-shadow:0 14px 30px -18px rgba(23,21,15,.35);border-color:var(--ink)}
[class*="st-key-td_qwrap_"] [data-testid="stPageLink"] a{position:absolute;
  inset:0;z-index:5;opacity:0}
.td-qcard .qgo{font-family:var(--mono);font-size:12px;color:var(--accent2);
  letter-spacing:.04em;margin-top:12px}
[class*="st-key-td_qwrap_"]:hover .qgo{color:var(--ink)}
/* note from coach — dark, personal */
.td-note{background:var(--invert-bg);border-radius:8px;padding:20px 22px;margin-top:16px}
.td-note .h{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--accent);margin-bottom:10px}
.td-note p{font-size:15px;line-height:1.5;color:var(--invert-fg);margin:0}
@media(max-width:760px){.td-stats{grid-template-columns:1fr 1fr}}

/* ---------- clients sheet (coach landing) --------------------------------- */
.st-key-clients_sheet{position:relative}
.cs-wrap{border:1.5px solid var(--ink);border-radius:8px;overflow:hidden}
.cs-bar{background:var(--invert-bg);padding:13px 17px;font-family:var(--mono);
  font-size:12px;letter-spacing:.13em;text-transform:uppercase;font-weight:700;
  display:flex;justify-content:space-between;align-items:center;gap:10px}
.cs-bar span{color:var(--invert-fg)}
.cs-bar span.mt{color:var(--invert-muted);font-weight:400;letter-spacing:.03em}
.cs-scroll{overflow-x:auto}
.cs-tbl{width:100%;border-collapse:collapse;background:var(--paper);
  min-width:920px}
.cs-tbl th,.cs-tbl td{border:1px solid var(--line)}
.cs-tbl thead th{background:var(--sand);color:var(--ink);
  font-family:var(--mono);font-size:10px;letter-spacing:.06em;
  text-transform:uppercase;font-weight:700;padding:10px 12px;text-align:left;
  white-space:nowrap;height:37px}
.cs-tbl thead th.c{text-align:center}
.cs-tbl thead th.r{text-align:right}
.cs-tbl td{background:var(--paper);padding:0 13px;height:57px;
  vertical-align:middle;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}
.cs-tbl tr:hover td{background:var(--hover)}
.cs-client{display:flex;align-items:center;gap:10px}
.cs-av{width:30px;height:30px;border-radius:999px;background:var(--sand);
  border:1.5px solid var(--ink);display:flex;align-items:center;
  justify-content:center;font-family:var(--display);font-weight:800;
  font-size:13px;color:var(--ink);flex:none}
.cs-nm{font-family:var(--display);font-weight:800;font-size:15px;
  color:var(--ink)}
.cs-goal{font-family:var(--mono);font-size:11px;letter-spacing:.05em;
  text-transform:uppercase;color:var(--muted)}
.cs-week{font-family:var(--mono);font-size:12px;text-align:center;
  color:var(--ink)}
.cs-wt{font-family:var(--mono);font-size:13px;text-align:right;
  font-variant-numeric:tabular-nums;color:var(--ink)}
.cs-wt b{font-weight:700}
.cs-wt b.good{color:var(--good)}
.cs-wt b.over{color:var(--over)}
.cs-wt b.mut{color:var(--muted)}
.cs-chip{display:inline-block;font-family:var(--mono);font-size:9.5px;
  letter-spacing:.08em;text-transform:uppercase;font-weight:700;
  border-radius:3px;padding:4px 9px}
.cs-chip.due{background:var(--warn-soft);color:var(--warn)}
.cs-chip.done{background:var(--good-soft);color:var(--good)}
.cs-chip.miss{background:var(--over-soft);color:var(--over)}
.cs-chip.none{background:var(--sand);color:var(--muted)}
.cs-al{font-family:var(--mono);font-size:9.5px;color:var(--over);
  font-weight:700}
.cs-todo{font-family:var(--mono);font-size:11px}
.cs-todo.over{color:var(--over)}
.cs-todo.warn{color:var(--warn)}
.cs-todo.good{color:var(--good)}
.cs-open{font-family:var(--mono);font-size:12px;color:var(--accent2);
  font-weight:700;text-align:right}

/* ---------- supplement cost grid (coach) ---------------------------------- */
.sc-band{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;
  background:var(--invert-bg);border-radius:8px;padding:18px 22px;margin-bottom:20px}
.sc-band .l{font-family:var(--mono);font-size:9.5px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--invert-muted);margin-bottom:7px}
.sc-band .v{font-family:var(--display);font-weight:800;font-size:24px;
  letter-spacing:-.02em;line-height:1;color:var(--invert-fg);
  font-variant-numeric:tabular-nums}
.sc-band .v.acc{color:var(--accent)}
.sc-band .vs{font-size:11.5px;color:var(--invert-muted);margin-top:6px;
  font-family:var(--mono)}
.sc-wrap{border:1.5px solid var(--ink);border-radius:8px;overflow:hidden}
.sc-gbar{background:var(--invert-bg);padding:12px 17px;font-family:var(--mono);
  font-size:12px;letter-spacing:.14em;text-transform:uppercase;
  font-weight:700;display:flex;justify-content:space-between;
  align-items:center}
.sc-gbar span{color:var(--invert-fg)}
.sc-gbar span.mt{color:var(--invert-muted);letter-spacing:.03em;font-weight:400}
.sc-scroll{overflow-x:auto}
.sc-tbl{width:100%;border-collapse:collapse;background:var(--paper);
  min-width:760px}
.sc-tbl th,.sc-tbl td{border:1px solid var(--line)}
.sc-tbl thead th{font-family:var(--mono);font-size:10px;
  letter-spacing:.07em;text-transform:uppercase;color:var(--ink);
  background:var(--sand);padding:12px 12px;text-align:right;font-weight:700;
  white-space:nowrap}
.sc-tbl thead th.l{text-align:left}
.sc-tbl td.sup{text-align:left;font-weight:600;font-size:15px;
  padding:14px 14px;color:var(--ink)}
.sc-tbl td.brand{text-align:left;font-family:var(--mono);font-size:11px;
  letter-spacing:.06em;text-transform:uppercase;color:var(--accent2);
  font-weight:700;padding:14px 12px;white-space:nowrap;
  background:var(--cream)}
.sc-tbl td.brand.none{color:var(--muted);font-weight:400}
.sc-tbl td.num{font-family:var(--mono);font-size:13.5px;color:var(--ink);
  text-align:right;padding:14px 12px;font-variant-numeric:tabular-nums;
  white-space:nowrap}
.sc-tbl td.num small{color:var(--muted);font-size:11px}
.sc-tbl td.price{font-weight:700;font-size:14px}
.sc-tbl td.unit{color:var(--muted)}
.sc-tbl tr.tot td{background:var(--invert-bg);color:var(--invert-fg);
  font-family:var(--mono);font-weight:700;font-size:14px;padding:15px 12px;
  text-align:right;border-color:var(--ink)}
.sc-tbl tr.tot td.lbl{text-align:left;text-transform:uppercase;
  letter-spacing:.12em;font-size:12px;color:var(--invert-muted)}
.sc-tbl tr.tot td span.big{font-family:var(--display);font-size:19px;
  color:var(--accent);letter-spacing:-.01em}
.sc-tbl tbody tr:not(.tot):hover td{background:var(--hover)}
/* client supplements grid cells (same system, read-only columns) */
.sc-tbl td.rsn{text-align:left;font-size:13px;color:var(--muted);
  padding:14px 14px;line-height:1.45;min-width:280px;white-space:normal}
.sc-tbl td.dose{text-align:left;font-family:var(--mono);font-size:12px;
  color:var(--accent2);padding:14px 12px;letter-spacing:.02em;
  white-space:normal;min-width:140px}
.sc-tbl td.ctr{text-align:center}
.sc-tbl td a.buy{font-family:var(--mono);font-size:12px;color:var(--accent2);
  font-weight:700;text-decoration:none;border-bottom:none;white-space:nowrap}
.sc-tbl td a.buy:hover{color:var(--ink)}

/* ---------- allergy slim bar (the toned-down treatment) ------------------- */
.al-bar{background:var(--over-soft);border:1px solid var(--over);
  border-left:4px solid var(--over);border-radius:6px;padding:9px 14px;
  display:flex;gap:12px;align-items:center;margin:2px 0 14px;flex-wrap:wrap}
.al-bar span.lbl{font-family:var(--mono);font-size:10px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--over);font-weight:700;
  white-space:nowrap}
.al-bar b{color:var(--ink);font-weight:700;font-size:13.5px}

/* ---------- supplements cards --------------------------------------------- */
.sp-card{background:var(--paper);border:1px solid var(--line);border-radius:8px;
  padding:18px 20px;margin-bottom:12px}
.sp-card .top{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.sp-card .nm{font-family:var(--display);font-weight:800;font-size:19px;
  letter-spacing:-.01em;color:var(--ink)}
.sp-ess{font-family:var(--mono);font-size:10px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--good);border:1px solid var(--good);
  border-radius:999px;padding:3px 10px;white-space:nowrap}
.sp-card .rsn{font-size:13.5px;color:var(--muted);margin-top:7px;line-height:1.5}
.sp-card .dose{font-family:var(--mono);font-size:12px;color:var(--accent2);
  margin-top:9px;letter-spacing:.03em}
.sp-card a.buy{font-family:var(--mono);font-size:12px;color:var(--accent2);
  text-decoration:none;border-bottom:none;margin-left:auto;white-space:nowrap}
.sp-card a.buy:hover{color:var(--ink)}

/* ---------- meal plan full grid (client view, locked layout) -------------- */
.mg-targets{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;
  background:var(--invert-bg);border-radius:8px;padding:16px 22px;margin:4px 0 12px}
.mg-targets .l{font-family:var(--mono);font-size:9.5px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--invert-muted);margin-bottom:6px}
.mg-targets .v{font-family:var(--display);font-weight:800;font-size:26px;
  letter-spacing:-.02em;line-height:1;color:var(--invert-fg);
  font-variant-numeric:tabular-nums}
.mg-targets .v small{font-size:12px;color:var(--invert-muted);font-weight:600}
.mg-targets .v.acc{color:var(--accent)}
.mg-inst{border:2px solid var(--ink);border-radius:8px;overflow:hidden;
  margin-bottom:18px}
.mg-inst .h{background:var(--accent2);color:#fff;font-family:var(--mono);
  font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;
  padding:10px 16px}
.mg-inst .r{background:var(--accent);color:#fff;font-family:var(--mono);
  font-size:12px;letter-spacing:.04em;padding:9px 16px;display:flex;
  gap:8px 28px;flex-wrap:wrap}
.mg-inst .r span{color:#fff}
.mg-mealwrap{margin-bottom:22px;border:1.5px solid var(--ink);border-radius:8px;
  overflow:hidden}
.mg-mbar{background:var(--invert-bg);color:var(--invert-fg);padding:13px 18px;
  font-family:var(--mono);font-size:13px;letter-spacing:.14em;
  text-transform:uppercase;font-weight:700;display:flex;
  justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.mg-mbar span{color:var(--invert-fg)}
.mg-mbar span.mt{color:var(--invert-muted);letter-spacing:.03em;font-weight:400;font-size:12px}
.mg-scroll{overflow-x:auto}
.mg-tbl{width:100%;border-collapse:collapse;background:var(--paper);
  min-width:820px}
.mg-tbl th,.mg-tbl td{border:1px solid var(--line)}
.mg-tbl thead th{font-family:var(--mono);font-size:11px;letter-spacing:.06em;
  text-transform:uppercase;color:var(--ink);background:var(--sand);
  padding:13px 12px;text-align:right;font-weight:700;white-space:nowrap}
.mg-tbl thead th.l{text-align:left}
.mg-tbl td.cat{background:var(--cream);font-family:var(--mono);font-size:11px;
  letter-spacing:.09em;text-transform:uppercase;color:var(--accent2);
  font-weight:700;text-align:left;padding:16px 14px;white-space:nowrap;
  width:120px}
.mg-tbl td.food{text-align:left;font-weight:600;font-size:16px;
  padding:16px 14px;white-space:nowrap;color:var(--ink)}
.mg-tbl td.q,.mg-tbl td.num{font-family:var(--mono);font-size:14px;
  color:var(--ink);text-align:right;padding:16px 12px;white-space:nowrap;
  font-variant-numeric:tabular-nums}
.mg-tbl td.cal{font-weight:700;font-size:15px}
.mg-tbl tr.tot td{background:var(--sand);font-family:var(--mono);
  font-weight:700;font-size:13px;color:var(--ink);padding:14px 12px;
  text-align:right}
.mg-tbl tr.tot td.lbl{text-align:left;text-transform:uppercase;
  letter-spacing:.12em;font-size:12px}
.mg-daytot{background:var(--invert-bg);border-radius:8px;padding:16px 22px;
  margin-top:20px;display:flex;justify-content:space-between;flex-wrap:wrap;
  gap:12px;font-family:var(--mono);font-size:13px;color:var(--invert-fg)}
.mg-daytot span{color:var(--invert-fg)}
.mg-daytot b{font-family:var(--display);font-weight:800;font-size:20px;
  color:var(--invert-fg)}
.mg-daytot .acc{color:var(--accent)}
.mg-daytot .ok{color:#8fd0ab;text-transform:uppercase;letter-spacing:.1em;
  font-size:11px}

/* ---------- native chrome that Streamlit paints light --------------------
   Our own popover/expander CONTENT uses token colors, so the shells must
   follow the theme too. BaseWeb portal popups (select menus, the date
   calendar) render OUTSIDE the app root, and the global ink text rule DOES
   reach them — in dark mode that left dark-on-dark, unreadable options.
   Theme the portals explicitly: surface panel, fg text, hover state. */
/* real DOM (verified): popover > div > … > ul > … > li[role=option] — no
   data-baseweb="menu"/listbox hooks. The panel keeps Streamlit's cream and
   the li's inner spans inherit the global ink (light in dark) = invisible. */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] ul{
  background:var(--surface)!important}
div[data-baseweb="popover"] ul{border:1px solid var(--line)!important}
div[data-baseweb="popover"] li[role="option"],
div[data-baseweb="popover"] li[role="option"] *{
  color:var(--fg)!important;background:transparent!important}
div[data-baseweb="popover"] li[role="option"]:hover{
  background:var(--hover)!important}
div[data-baseweb="popover"] li[role="option"][aria-selected="true"]{
  background:var(--hover)!important}
[data-baseweb="popover"] [data-baseweb="calendar"],
[data-baseweb="calendar"]{background:var(--surface)!important}
[data-baseweb="calendar"] *:not([aria-selected="true"]):not(svg):not(path){
  color:var(--fg)}
[data-baseweb="calendar"] button:hover{background:var(--hover)!important}
.stApp{background:var(--bg)}
/* widget text is baked to the config-theme ink — repaint it with the token
   so values stay readable when the token flips dark */
[data-baseweb="input"] input, [data-baseweb="base-input"] input,
.stTextArea textarea, [data-baseweb="select"] input{
  color:var(--fg)!important; caret-color:var(--fg)!important;
  -webkit-text-fill-color:var(--fg)!important}
[data-baseweb="input"] input::placeholder, .stTextArea textarea::placeholder{
  color:var(--fg-muted)!important; -webkit-text-fill-color:var(--fg-muted)!important;
  opacity:.75}
[data-testid="stTextAreaRootElement"]{background:var(--paper)!important}
[data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"]{
  background:var(--sand)!important; color:var(--fg)!important}
[data-testid="stNumberInputStepDown"] svg,
[data-testid="stNumberInputStepUp"] svg{fill:var(--fg)!important}
[data-testid="stProgress"] [data-baseweb="progress-bar"] > div > div{
  background-color:var(--sand)}
[data-testid="stProgress"] [data-baseweb="progress-bar"] > div > div > div{
  background-color:var(--accent)}
[data-testid="stElementToolbarButtonContainer"]{
  background:var(--surface-2)!important}
[data-testid="stElementToolbarButtonContainer"] svg{fill:var(--fg-muted)}
#vg-tooltip-element, .vg-tooltip{background:var(--invert-bg)!important;
  border:1px solid var(--border)!important}
#vg-tooltip-element *, .vg-tooltip *{color:var(--invert-fg)!important}
[data-testid="stPopoverBody"]{background:var(--surface)!important;
  border:1px solid var(--line)!important}
[data-testid="stForm"]{border-color:var(--line)}
[data-baseweb="checkbox"]:has(input:not(:checked)) span:first-of-type{
  background:var(--paper);border-color:var(--line)}
[data-testid="stHeader"] svg{fill:var(--muted)}
/* BaseWeb tooltips ship a light skin whose text our global ink rule
   repaints — light-on-light. Invert them in both themes. */
div[data-baseweb="tooltip"]{background:var(--invert-bg)!important;
  border:1px solid var(--border)!important}
div[data-baseweb="tooltip"], div[data-baseweb="tooltip"] *{
  color:var(--invert-fg)!important}
div[data-baseweb="tooltip"] div{background:transparent!important}

/* ---------- coach meal planner: meal blocks read as real headers -------- */
.mp-meal-h{font-family:var(--display);font-weight:800;font-size:24px;
  letter-spacing:-.01em;color:var(--ink);margin:26px 0 8px;
  padding-top:14px;border-top:1px solid var(--line)}
.mp-meal-h .br{color:var(--accent);font-weight:600}
.st-key-mp_meals_box span[data-baseweb="tag"]{
  padding:8px 10px!important;border-radius:5px!important}
.st-key-mp_meals_box span[data-baseweb="tag"] span{
  font-family:var(--display)!important;font-weight:700!important;
  font-size:15px!important;letter-spacing:0!important}

/* ================= mobile / responsive (360–430px phones) =================
   Streamlit stacks st.columns vertically below ~640px — right for content
   columns, wrong for the top bar, tab switchers and editable-table rows.
   Those three get forced back to rows (wrap or sideways scroll). */
/* wide HTML tables always scroll sideways instead of crushing */
.mg-tbl{min-width:700px}
.sc-tbl{min-width:640px}
.cs-tbl{min-width:920px}
@media (max-width: 680px){
  /* 4-up stat bands -> 2-up */
  .mg-targets{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
  .sc-band{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
  .td-stats{grid-template-columns:repeat(2,minmax(0,1fr))}
  /* red instruction bar: the pairs stack */
  .mg-inst .r{flex-wrap:wrap;gap:6px 18px}
  /* tab switchers WRAP to a second line (never one-per-row) */
  [class*="st-key-tabs__"] [data-testid="stHorizontalBlock"]{
    flex-flow:row wrap!important;gap:8px!important}
  [class*="st-key-tabs__"] [data-testid="stColumn"]{
    width:auto!important;flex:0 0 auto!important;min-width:0!important}
  [class*="st-key-tabs__"] .stButton button{width:auto}
  /* both top bars stay a single row */
  [class*="st-key-te_topbar"] [data-testid="stHorizontalBlock"]{
    flex-flow:row nowrap!important;align-items:center!important;
    gap:8px!important}
  [class*="st-key-te_topbar"] [data-testid="stColumn"]{
    width:auto!important;flex:1 1 auto!important;min-width:0!important}
  [class*="st-key-te_topbar"] [class*="st-key-tb_prefs"]
    [data-testid="stColumn"]{flex:0 0 auto!important}
  /* coach bar carries too much for one 390px row — it wraps, and the
     client-switcher tile takes a full-width second row. (Exact-class
     token = coach bar only; the client bar keeps the single row.) */
  .st-key-te_topbar > div > [data-testid="stHorizontalBlock"]{
    flex-flow:row wrap!important}
  .st-key-te_topbar > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(1){flex:0 0 auto!important}
  .st-key-te_topbar > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(2){order:9;flex:1 1 100%!important}
  .st-key-te_topbar > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(3){display:none}
  .st-key-te_topbar > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(4){
    flex:0 0 auto!important;margin-left:auto}
  .st-key-te_topbar > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(7){flex:0 0 auto!important}
  /* client training: the done-tick sits BESIDE its exercise card */
  .st-key-tl_list [data-testid="stHorizontalBlock"]{
    flex-flow:row nowrap!important;align-items:center!important}
  .st-key-tl_list [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:first-child{
    width:auto!important;flex:0 0 34px!important;min-width:0!important}
  .st-key-tl_list [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:last-child{
    width:auto!important;flex:1 1 0!important;min-width:0!important}
  /* "Pendiente"/"Due" fits its stat cell in one piece */
  .td-stats .v.warn{font-size:24px}

  /* ---- client dashboard mobile polish (te_mobile_fix mock) ----------- */
  /* client bar: brand hard-left · spacer · [EN|ES seg · theme · avatar]
     hard-right — no floating middle cluster */
  [class*="st-key-te_topbar_client"]{padding:10px 0;margin-bottom:6px}
  [class*="st-key-te_topbar_client"] .te-brand .sq{
    width:30px;height:30px;border-radius:7px;font-size:15px}
  .st-key-te_topbar_client > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(1){flex:0 0 auto!important}
  .st-key-te_topbar_client > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(2){flex:1 1 auto!important}
  .st-key-te_topbar_client > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(3),
  .st-key-te_topbar_client > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(6){flex:0 0 auto!important}
  /* EN|ES becomes ONE segmented pill (halves share a border), theme
     keeps its own square beside it */
  [class*="st-key-tb_prefs"] [data-testid="stHorizontalBlock"]{
    gap:0!important}
  [class*="st-key-tb_prefs"] [data-testid="stColumn"]:nth-child(3){
    margin-left:8px}
  [class*="st-key-tb_lang_en"] button{
    border-radius:3px 0 0 3px!important;border-right-width:0!important}
  [class*="st-key-tb_lang_es"] button{border-radius:0 3px 3px 0!important}
  [class*="st-key-tb_prefs"] .stButton button{min-height:30px;height:30px}
  [class*="st-key-te_topbar_client"] [class*="st-key-tb_avatar"]
    [data-testid="stPopoverButton"]{
    width:32px!important;height:32px!important;font-size:13px!important}
  /* help + chip COLUMNS collapse (hiding just their content left the
     empty columns flex-growing a gap into the control cluster) */
  .st-key-te_topbar_client > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(4),
  .st-key-te_topbar_client > div > [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:nth-child(5){display:none}
  [class*="st-key-tb_theme"] button{
    width:30px!important;min-width:30px!important;padding:0!important}
  /* dead space above the bar: every style-injection markdown is a
     0-height flex child that still earns the column's 1rem gap — drop
     style-only containers from the flex flow (their CSS still applies) */
  [data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"]
    > style:only-child){display:none}
  [data-testid="stMain"] .block-container{padding-top:.35rem;
    padding-left:18px;padding-right:18px}
  .te-hero{padding:14px 0 4px}
  .te-hero .kicker{margin-bottom:10px}
  .td-sub{margin-top:10px}
  /* stat strip rhythm: 2-up, even breathing, mock value sizing */
  .td-stats{gap:24px 16px;padding:18px 0 4px}
  .td-stats .v{font-size:clamp(34px,10vw,44px)}
  .td-stats .v small{font-size:15px}
  /* editable tables (weigh-ins, training builder, supplement costs):
     keep header + rows horizontal and scroll the frame sideways */
  [class*="st-key-et_box_"]{overflow-x:auto}
  [class*="st-key-et_box_"] [data-testid="stHorizontalBlock"]{
    flex-flow:row nowrap!important;min-width:620px;gap:6px!important}
  [class*="st-key-et_box_"] [data-testid="stColumn"]{
    width:auto!important;flex:1 1 0!important;min-width:0!important}
  /* comfortable tap targets */
  .stButton button, .stDownloadButton button,
  [data-testid="stFormSubmitButton"] button{min-height:44px}
  [class*="st-key-tb_prefs"] .stButton button{
    min-height:34px;height:34px}
  [class*="st-key-et_box_"] .stButton button{min-height:0}
}
@media (max-width: 560px){
  /* identity chips give way — brand, toggles and avatar stay reachable */
  .te-coachchip, .te-coachchip2{display:none}
  [class*="st-key-tb_help"]{display:none}
  .te-brand .wm{display:none}
  .te-brand::after{display:none}
  [data-testid="stMain"] .block-container{
    padding-left:18px;padding-right:18px}
}
</style>
"""


def _configured_password():
    """Legacy shared access password, from st.secrets or the APP_PASSWORD
    env var. Empty string => not configured."""
    import os
    pw = ""
    try:
        pw = str(st.secrets.get("app_password", "") or "")
    except Exception:
        pw = ""
    return (pw or os.environ.get("APP_PASSWORD", "")).strip()


def _configured_users():
    """Per-coach logins as {username: password}, from st.secrets['app_users']
    or the APP_USERS env var, format 'Eric:12345,Tristan:12345'.
    Empty dict => users mode not configured (legacy password or open dev)."""
    import os
    raw = ""
    try:
        raw = str(st.secrets.get("app_users", "") or "")
    except Exception:
        raw = ""
    raw = (raw or os.environ.get("APP_USERS", "")).strip()
    users = {}
    for pair in raw.split(","):
        if ":" in pair:
            u, p = pair.split(":", 1)
            if u.strip() and p.strip():
                users[u.strip()] = p.strip()
    return users


# CSS that strips the console chrome (sidebar + nav) for visitors:
# the public apply route, the lock screen, and the logged-out landing.
_HIDE_CHROME = (
    "<style>"
    "[data-testid='stSidebar'],"
    "[data-testid='stSidebarNav'],"
    "[data-testid='stExpandSidebarButton']"
    "{display:none !important;}"
    "[data-testid='stMain'] .block-container"
    "{max-width:760px;}"
    "</style>")

# The public landing is an editorial page, not a form: give it the concept
# board's wide 1080px canvas (the 760px cap above stays for /Apply).
_WIDE_LANDING = (
    "<style>[data-testid='stMain'] .block-container"
    "{max-width:1080px;}</style>")


# ---------- Supabase-style hover-expand nav rail + top bar ----------
APP_VERSION = "1.0"

_RAIL_ICONS = {
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    "meal": '<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/>',
    "scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "check": '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    "pill": '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/>',
    "dumbbell": '<path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/>',
    "sync": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    "inbox": '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
}
# (label, href, icon_key, nav_key) — label None => a section divider
_RAIL_NAV = [
    ("Home", "/", "home", "home"),
    ("Clients", "/Clients", "users", "clients"),
    ("Meal Planner", "/Meal_Planner", "meal", "meal"),
    ("Weigh-ins", "/Weigh_Ins", "scale", "weigh"),
    ("Check-in", "/Check_In", "check", "check"),
    (None, None, None, None),
    ("Supplements", "/Supplements", "pill", "supp"),
    ("Training", "/Training", "dumbbell", "train"),
    (None, None, None, None),
    ("Applications", "/Applications", "inbox", "apps"),
]
_PAGE_KEY = {"Home": "home", "Clients": "clients", "Meal Planner": "meal",
             "Weigh-ins": "weigh", "Check-in": "check",
             "Supplements": "supp", "Training": "train",
             "Applications": "apps"}
# page files for st.page_link (paths relative to app.py, the main script)
_PAGE_FILE = {
    "/": "app.py",
    "/Clients": "pages/8_Clients.py",
    "/Meal_Planner": "pages/1_Meal_Planner.py",
    "/Weigh_Ins": "pages/2_Weigh_Ins.py",
    "/Check_In": "pages/3_Check_In.py",
    "/Supplements": "pages/4_Supplements.py",
    "/Training": "pages/5_Training.py",
    "/Applications": "pages/7_Applications.py",
}
# Clients see only their own scoped pages — coach tools never appear.
_RAIL_NAV_CLIENT = [
    ("Home", "/", "home", "home"),
    ("My Training", "/Training", "dumbbell", "train"),
    ("Weigh-ins", "/Weigh_Ins", "scale", "weigh"),
    ("Check-in", "/Check_In", "check", "check"),
    (None, None, None, None),
    ("My Plan", "/Meal_Planner", "meal", "meal"),
    ("Supplements", "/Supplements", "pill", "supp"),
]

_RAIL_CSS = """
<style>
/* the rail replaces Streamlit's native sidebar + nav */
[data-testid="stSidebar"], [data-testid="stSidebarNav"],
[data-testid="stExpandSidebarButton"]{ display:none !important; }
/* stMain keeps width:100% — without the calc() the margin shifts the whole
   column PAST the right viewport edge (clipped, no scrollbar). Invisible on
   desktop only because the 1180px container centers inside the excess. */
[data-testid="stMain"]{ margin-left:66px; width:calc(100% - 66px); }

/* Fixed hover-expand rail — a real Streamlit container so its rows are
   st.page_link (SPA navigation: the session SURVIVES clicking around the
   gated app; the old raw <a> anchors caused full reloads = logout every nav). */
.st-key-te_rail{ position:fixed; top:0; left:0; height:100vh; width:66px;
  z-index:1000; background:var(--sand); border-right:1.5px solid var(--ink);
  padding:16px 0; overflow:hidden;
  transition:width .24s cubic-bezier(.2,.6,.3,1), box-shadow .24s ease; }
.st-key-te_rail:hover{ width:236px;
  box-shadow:12px 0 34px -14px rgba(0,0,0,.42); }
.st-key-te_rail [data-testid="stVerticalBlock"]{ gap:2px; }
.st-key-te_rail [data-testid="stMarkdownContainer"]{ margin-bottom:0 !important; }
.st-key-te_rail .tbrand{ display:flex; align-items:center; height:40px;
  padding:0 21px; margin-bottom:12px; white-space:nowrap; overflow:hidden; }
.st-key-te_rail .tbi{ font-family:'Bricolage Grotesque',sans-serif;
  font-weight:800; font-size:1.5rem; color:var(--ink); flex:0 0 24px; }
.st-key-te_rail .tbl{ font-family:'Bricolage Grotesque',sans-serif;
  font-weight:800; font-size:1.15rem; letter-spacing:-.01em; margin-left:11px;
  color:var(--ink); opacity:0; transition:opacity .16s ease; }
.st-key-te_rail:hover .tbl{ opacity:1; }
.st-key-te_rail .tdiv{ height:1px; background:var(--line); margin:10px 18px; }
/* page-link rows (covers the tfall anchor fallback used in AppTest too) */
.st-key-te_rail a{ display:flex; align-items:center; height:44px;
  width:236px; padding:0 0 0 21px; text-decoration:none; border:none;
  border-radius:0; white-space:nowrap; background:transparent;
  transition:background .14s ease; }
.st-key-te_rail a:hover{ background:var(--hover); }
/* phones: no hover-expand (touch keeps :hover stuck after a tap and the
   open rail would sit over the content) — a fixed icon rail instead */
@media (max-width: 680px){
  .st-key-te_rail, .st-key-te_rail:hover{ width:56px; box-shadow:none; }
  .st-key-te_rail:hover .tbl,
  .st-key-te_rail:hover a p, .st-key-te_rail:hover a span{ opacity:0; }
  [data-testid="stMain"]{ margin-left:56px; width:calc(100% - 56px); }
}
.st-key-te_rail a::before{ content:""; width:22px; height:22px;
  flex:0 0 22px; background-color:var(--ink);
  -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat;
  -webkit-mask-size:contain; mask-size:contain;
  -webkit-mask-position:center; mask-position:center; }
.st-key-te_rail a p, .st-key-te_rail a span{
  font-family:'Space Mono',monospace; font-size:.82rem; letter-spacing:.02em;
  margin:0 0 0 15px; color:var(--ink); opacity:0;
  transition:opacity .18s ease .02s; }
.st-key-te_rail:hover a p, .st-key-te_rail:hover a span{
  opacity:1; }
.st-key-te_rail_active a{ background:var(--paper);
  box-shadow:inset 3px 0 0 var(--accent); }

[data-testid="stMain"] .block-container{ padding-top:.4rem; }

/* sticky bar shell (needs st.container(key="te_topbar") in _render_topbar).
   Blends into the canvas: cream, no hairline — separation on scroll comes
   from a soft fade only. */
[class*="st-key-te_topbar"]{position:sticky;top:0;z-index:99;background:var(--cream);
  box-shadow:0 6px 12px -12px rgba(23,21,15,.15);padding:10px 0;margin-bottom:14px}
/* Streamlit's stMarkdownContainer has margin-bottom:-16px, which collapses the
   brand/chip boxes to ~2px — the column then centers that sliver and the text
   rides 8px low. Neutralise it inside the bar so all zones share a centerline. */
[class*="st-key-te_topbar"] [data-testid="stMarkdownContainer"]{margin-bottom:0!important}

/* zone 1 — brandmark + wordmark */
.te-brand{display:flex;align-items:center;gap:11px;white-space:nowrap}
/* thin divider closing the left group (brand · switcher) */
.te-brand::after{content:"";width:1px;height:26px;background:var(--line);margin-left:14px}
/* one control height across the bar — every zone shares top and bottom edges */
.te-brand .sq{width:44px;height:44px;border-radius:10px;background:var(--invert-bg);color:var(--invert-fg);flex:none;
  display:flex;align-items:center;justify-content:center;font-family:var(--display);font-weight:800;font-size:21px}
.te-brand .wm{font-family:var(--display);font-weight:800;font-size:12.5px;line-height:1.06;
  letter-spacing:.03em;color:var(--ink)}

/* zone 2 — rich tile switcher: an HTML face overlaid on a popover trigger.
   Streamlit can't put a 2-line tile (initial square + name + status) inside a
   native widget, so the visual face (pointer-events:none) is layered over the
   popover button that actually opens the client list. */
.st-key-te_switch{position:relative}
.st-key-te_switch [data-testid="stVerticalBlock"]{gap:0}
.st-key-te_switch [data-testid="stPopoverButton"]{width:100%!important;min-height:44px!important;height:44px!important;
  border:1px solid var(--line)!important;border-radius:10px!important;background:var(--paper)!important;padding:0!important}
.st-key-te_switch [data-testid="stPopoverButton"]:hover{border-color:var(--ink)!important}
.st-key-te_switch [data-testid="stPopoverButton"] [data-testid="stIconMaterial"],
.st-key-te_switch [data-testid="stPopoverButton"] svg{display:none!important}
/* Streamlit wraps each element in a positioned stElementContainer, so anchor the
   overlay at that wrapper (targeted by :has) rather than the inner div. */
.st-key-te_switch [data-testid="stElementContainer"]:has(.te-tileface){
  position:absolute;top:0;left:0;right:0;height:44px;pointer-events:none;z-index:3}
.te-tileface{display:flex;align-items:center;gap:10px;padding:0 11px;height:100%;pointer-events:none}
.te-tileface .sq{width:30px;height:30px;border-radius:7px;background:var(--sand);flex:none;
  display:flex;align-items:center;justify-content:center;font-family:var(--display);font-weight:800;font-size:14px;color:var(--ink)}
.te-tileface .meta{display:flex;flex-direction:column;line-height:1.14;min-width:0}
.te-tileface .nm{font-family:var(--body);font-weight:700;font-size:14px;color:var(--ink);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.te-tileface .sub{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:2px}
.te-tileface .sub .on{color:var(--good)}
.te-tileface .chev{margin-left:auto;color:var(--muted);flex:none;display:flex}
.te-tileface .chev svg{width:16px;height:16px}

/* zone 2b — the switcher's dropdown: a compact menu, not a dialog.
   Scoped by :has(te_create) so the help/avatar popovers stay untouched. */
[data-testid="stPopoverBody"]:has([class*="st-key-te_create"]){
  width:300px!important;min-width:300px!important;max-width:300px!important;
  padding:12px 14px!important}
[data-testid="stPopoverBody"]:has([class*="st-key-te_create"]) [data-testid="stVerticalBlock"]{gap:2px}
[data-testid="stPopoverBody"]:has([class*="st-key-te_create"]) hr{margin:8px 0;background:var(--line)}
/* client rows: slim, left-aligned, sand hover — not ink pills */
[data-testid="stPopoverBody"] [class*="st-key-pickc_"] button{
  background:transparent!important;border:none!important;box-shadow:none!important;
  color:var(--ink)!important;justify-content:flex-start!important;text-align:left!important;
  min-height:40px!important;padding:8px 10px!important;border-radius:6px!important;transform:none!important}
[data-testid="stPopoverBody"] [class*="st-key-pickc_"] button:hover{background:var(--sand)!important}
[data-testid="stPopoverBody"] [class*="st-key-pickc_"] button p{
  color:inherit!important;font-family:var(--body)!important;font-weight:600!important;
  font-size:14px!important;letter-spacing:0!important;text-transform:none!important;
  text-align:left!important}
[data-testid="stPopoverBody"] [class*="st-key-pickc_"] button [data-testid="stMarkdownContainer"]{
  width:100%!important;text-align:left!important}
/* the button's direct child is a flex wrapper that centers the label */
[data-testid="stPopoverBody"] [class*="st-key-pickc_"] button > div{
  justify-content:flex-start!important}
/* the active client: orange text + left accent bar. Selector outranks the
   base row rule above (both !important — specificity decides). */
[data-testid="stPopoverBody"] [class*="st-key-te_active_row"] [class*="st-key-pickc_"] button{
  color:var(--accent2)!important;
  box-shadow:inset 2.5px 0 0 var(--accent)!important;border-radius:4px!important}
/* compact create row */
[class*="st-key-te_create"] button{background:var(--accent)!important;
  border:1.5px solid var(--accent)!important;color:var(--invert-fg)!important;
  min-height:38px!important;padding:.35rem .7rem!important;font-size:.7rem!important}
[class*="st-key-te_create"] button:hover{background:var(--accent2)!important;border-color:var(--accent2)!important}
[class*="st-key-te_create"] button p{color:var(--invert-fg)!important}

/* zone 4 — coach identity chip (inline: COACH · ERIC) */
.te-coachchip{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);text-align:right;white-space:nowrap}
.te-coachchip b{color:var(--ink);font-weight:700}

/* avatar (popover trigger) — ink circle with orange ring.
   Right-align the circle in its column so it closes flush with the
   content edge below (the trigger is narrower than the column). */
[class*="st-key-tb_avatar"]{align-items:flex-end}
[class*="st-key-tb_help"]{align-items:flex-end}
[class*="st-key-tb_avatar"] [data-testid="stPopoverButton"]{
  width:44px!important;height:44px!important;border-radius:999px!important;background:var(--invert-bg)!important;
  color:var(--invert-fg)!important;font-family:var(--display)!important;font-weight:800!important;font-size:17px!important;
  padding:0!important;min-height:0!important;border:none!important;
  box-shadow:0 0 0 2px var(--paper),0 0 0 4px var(--accent)!important}
/* force paper on every descendant — `inherit` would pull ink from the wrapping
   markdown div (global div{color:ink}), hiding the initial on the ink circle */
[class*="st-key-tb_avatar"] [data-testid="stPopoverButton"] *{color:var(--invert-fg)!important}

/* help (popover trigger) — quiet outline circle */
[class*="st-key-tb_help"] [data-testid="stPopoverButton"]{
  width:44px!important;height:44px!important;border-radius:999px!important;background:transparent!important;
  color:var(--muted)!important;border:1px solid var(--line)!important;padding:0!important;min-height:0!important}
[class*="st-key-tb_help"] [data-testid="stPopoverButton"]:hover{border-color:var(--ink)!important;color:var(--ink)!important}
[class*="st-key-tb_help"] [data-testid="stPopoverButton"] p{color:inherit!important}

/* keep the round triggers clean: hide the popover dropdown chevron */
[class*="st-key-tb_avatar"] [data-testid="stPopoverButton"] [data-testid="stIconMaterial"],
[class*="st-key-tb_avatar"] [data-testid="stPopoverButton"] svg,
[class*="st-key-tb_help"] [data-testid="stPopoverButton"] [data-testid="stIconMaterial"],
[class*="st-key-tb_help"] [data-testid="stPopoverButton"] svg{display:none!important}
</style>
"""


def _svg(inner):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            + inner + '</svg>')


def _icon_mask_uri(paths):
    """A rail icon as a CSS mask data-URI (color comes from background-color,
    so active/ink states tint the same asset)."""
    from urllib.parse import quote
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
           "fill='none' stroke='black' stroke-width='2' stroke-linecap='round' "
           "stroke-linejoin='round'>" + paths + "</svg>")
    return "data:image/svg+xml," + quote(svg, safe="")


# href-keyed masks. page_link renders slash-less relative hrefs
# ("Meal_Planner"); Home's href is empty so it gets a keyed wrapper instead.
_RAIL_ICON_CSS = "<style>" + "".join(
    f'.st-key-te_rail a[href$="{href.lstrip("/")}"]::before{{'
    f'-webkit-mask-image:url("{_icon_mask_uri(_RAIL_ICONS[ic])}");'
    f'mask-image:url("{_icon_mask_uri(_RAIL_ICONS[ic])}")}}'
    for href, ic in (("/Clients", "users"), ("/Meal_Planner", "meal"),
                     ("/Weigh_Ins", "scale"), ("/Check_In", "check"),
                     ("/Supplements", "pill"), ("/Training", "dumbbell"),
                     ("/Applications", "inbox"))) + (
    f'.st-key-te_rail_home a::before{{'
    f'-webkit-mask-image:url("{_icon_mask_uri(_RAIL_ICONS["home"])}");'
    f'mask-image:url("{_icon_mask_uri(_RAIL_ICONS["home"])}")}}') + "</style>"


# nav labels -> i18n keys; the English label doubles as the fallback, so an
# unmapped entry renders as-is (t() returns the key it was given).
_NAV_T = {"Home": "nav_home", "Clients": "nav_clients",
          "Meal Planner": "nav_meal", "Weigh-ins": "nav_weigh",
          "Check-in": "nav_check", "Supplements": "nav_supp",
          "Training": "nav_train", "Applications": "nav_apps",
          "My Training": "nav_my_train", "My Plan": "nav_my_plan"}


def _rail_link(href, lbl):
    """One rail row. st.page_link = SPA nav, session survives. In AppTest a
    page file runs as its own single-page app (no page registry), so fall
    back to a plain anchor there — tests render the rail, they don't click it."""
    shown = t(_NAV_T.get(lbl, lbl))
    try:
        st.page_link(_PAGE_FILE[href], label=shown)
    except Exception:
        st.markdown(f'<a class="tfall" href="{href}" target="_self">'
                    f'<span>{shown}</span></a>', unsafe_allow_html=True)


def _render_rail(active_key):
    nav = _RAIL_NAV_CLIENT if current_role() == "client" else _RAIL_NAV
    st.markdown(_RAIL_CSS + _RAIL_ICON_CSS, unsafe_allow_html=True)
    with st.container(key="te_rail"):
        st.markdown('<div class="tbrand"><span class="tbi">T</span>'
                    '<span class="tbl">TRAIN&amp;EAT</span></div>',
                    unsafe_allow_html=True)
        for lbl, href, ic, key in nav:
            if lbl is None:
                st.markdown('<div class="tdiv"></div>', unsafe_allow_html=True)
            elif key == active_key:
                with st.container(key="te_rail_active"):
                    if href == "/":
                        with st.container(key="te_rail_home"):
                            _rail_link(href, lbl)
                    else:
                        _rail_link(href, lbl)
            elif href == "/":
                with st.container(key="te_rail_home"):
                    _rail_link(href, lbl)
            else:
                _rail_link(href, lbl)


def _pick_client(name):
    if current_role() == "client":     # defense in depth: clients never switch
        return
    st.session_state["client"] = name


def _create_client_cb():
    if current_role() == "client":
        return
    nm = (st.session_state.get("te_newname") or "").strip()
    if nm:
        cl.upsert_client(nm, {})
        st.session_state["client"] = nm
        st.session_state["te_newname"] = ""


_CHEV = _svg('<path d="m6 9 6 6 6-6"/>')


def _render_topbar_client():
    """Client top bar: brand · spacer · help · "Your coach" chip · avatar.
    No client switcher — a client's console is theirs alone. Reuses the
    tb_help / tb_logout keys so styling and tests carry over; the avatar
    container key extends tb_avatar (accent circle, ink ring)."""
    me = st.session_state.get("_client_self") or ""
    coach = ((cl.get_client(me) or {}).get("coach") or "").strip() if me else ""
    with st.container(key="te_topbar_client"):
        c_brand, _gap, c_prefs, c_help, c_chip, c_av = st.columns(
            [0.18, 0.38, 0.14, 0.07, 0.15, 0.08], vertical_alignment="center")
        with c_brand:
            st.markdown('<div class="te-brand"><div class="sq">T</div>'
                        '<div class="wm">TRAIN&nbsp;&amp;<br>EAT</div></div>',
                        unsafe_allow_html=True)
        with c_prefs:
            _pref_toggles()
        with c_help:
            with st.container(key="tb_help"):
                with st.popover("?"):
                    st.caption(t("tb_help_client"))
                    st.caption(f"T&E Coaching Console · v{APP_VERSION}")
        with c_chip:
            st.markdown(f'<div class="te-coachchip2">{t("tb_your_coach")}'
                        f'<b>{_html.escape(coach) or "T&amp;E"}</b></div>',
                        unsafe_allow_html=True)
        with c_av:
            with st.container(key="tb_avatar_client"):
                with st.popover((me[:1] or "C").upper()):
                    st.markdown(f"**{_html.escape(me) or t('tb_client')}**")
                    st.caption(t("tb_client_account"))
                    st.button(t("tb_logout"), key="tb_logout",
                              on_click=logout, use_container_width=True)


def _render_topbar():
    """Top bar, 4 zones: brandmark · rich tile client-switcher · Help · coach chip
    · avatar, as a sticky bar. The switcher is a CUSTOM popover — a native
    selectbox can't render the initial-square + name + status tile — so selection
    is driven by st.session_state['client']; external callers that set 'client'
    (app.py, Applications) still switch the active client. Uses on_click callbacks
    only (no st.rerun mid-form). Sets st.session_state['_active_client'].
    Clients get the switcher-less variant — their scope is locked to themselves."""
    if current_role() == "client":
        _render_topbar_client()
        return
    clients = cl.load_clients()
    names = sorted(clients.keys())
    active = st.session_state.get("client")
    if active not in names:
        active = names[0] if names else None
    st.session_state["client"] = active
    st.session_state["_active_client"] = active

    coach = (current_coach() or "").title()

    with st.container(key="te_topbar"):
        # Left group hugs the edge (brand · switcher), one flexible spacer
        # takes the slack, help/chip/avatar cluster right.
        c_brand, c_sw, _gap, c_prefs, c_help, c_chip, c_av = st.columns(
            [0.12, 0.24, 0.28, 0.13, 0.05, 0.12, 0.06],
            vertical_alignment="center")

        with c_brand:
            st.markdown('<div class="te-brand"><div class="sq">T</div>'
                        '<div class="wm">TRAIN&nbsp;&amp;<br>EAT</div></div>',
                        unsafe_allow_html=True)

        with c_sw:
            with st.container(key="te_switch"):
                with st.popover(" ", use_container_width=True):
                    st.markdown('<div class="mono" style="margin:0 0 6px">'
                                f'[ {t("tb_switch_client")} ]</div>',
                                unsafe_allow_html=True)
                    for nm in names:
                        if nm == active:
                            with st.container(key="te_active_row"):
                                st.button(f"✓ {nm}", key=f"pickc_{nm}",
                                          on_click=_pick_client, args=(nm,),
                                          use_container_width=True)
                        else:
                            st.button(nm, key=f"pickc_{nm}",
                                      on_click=_pick_client, args=(nm,),
                                      use_container_width=True)
                    if not names:
                        st.caption(t("tb_no_clients"))
                    st.divider()
                    ci, cb = st.columns([0.55, 0.45],
                                        vertical_alignment="center")
                    ci.text_input("New client name", key="te_newname",
                                  placeholder=t("tb_new_client_ph"),
                                  label_visibility="collapsed")
                    cb.button(t("tb_create_client"), key="te_create",
                              on_click=_create_client_cb,
                              use_container_width=True)
                if active:
                    st.markdown(
                        f'<div class="te-tileface"><div class="sq">'
                        f'{_html.escape(active[:1].upper())}</div><div class="meta">'
                        f'<div class="nm">{_html.escape(active)}</div>'
                        f'<div class="sub">{t("tb_client")}&nbsp;·&nbsp;'
                        f'<span class="on">{t("tb_active")}</span>'
                        f'</div></div><div class="chev">{_CHEV}</div></div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '<div class="te-tileface"><div class="meta">'
                        f'<div class="nm">{t("tb_no_client_sel")}</div>'
                        f'<div class="sub">{t("tb_add_to_begin")}</div></div>'
                        f'<div class="chev">{_CHEV}</div></div>',
                        unsafe_allow_html=True)

        with c_prefs:
            _pref_toggles()
        with c_help:
            with st.container(key="tb_help"):
                with st.popover("?"):
                    st.caption(t("tb_help_coach"))
                    st.caption(f"T&E Coaching Console · v{APP_VERSION}")

        with c_chip:
            st.markdown(f'<div class="te-coachchip">{t("tb_coach")}'
                        '&nbsp;·&nbsp;'
                        f'<b>{_html.escape(coach) or "—"}</b></div>',
                        unsafe_allow_html=True)

        with c_av:
            with st.container(key="tb_avatar"):
                with st.popover(coach[:1].upper() if coach else "C"):
                    st.markdown(f"**{t('tb_coach')} · "
                                f"{_html.escape(coach) or '—'}**")
                    if active:
                        st.caption(f"{t('tb_active_client')} — {active}")
                    st.button(t("tb_logout"), key="tb_logout",
                              on_click=logout, use_container_width=True)


def is_authed():
    """True when no gate is configured (local dev) or this session has
    already unlocked the console."""
    if not (_configured_users() or _configured_password()):
        return True
    return bool(st.session_state.get("_authed"))


def current_coach():
    """Name of the logged-in coach ('' when the gate is off / legacy mode)."""
    return st.session_state.get("_coach", "")


def current_role():
    """'coach' | 'client' for this session; None when locked out.
    Gate off (local dev) => coach. Authed legacy sessions that predate roles
    carry no _role — they count as coach (version-tolerant)."""
    if not (_configured_users() or _configured_password()):
        return "coach"
    if not st.session_state.get("_authed"):
        return None
    return st.session_state.get("_role", "coach")


def _force_client_scope():
    """A client session is ALWAYS scoped to itself. Runs on every page render
    so no poked session key or link can ever load another client's data."""
    me = st.session_state.get("_client_self")
    st.session_state["client"] = me
    st.session_state["_active_client"] = me
    st.session_state.pop("client_pick_pending", None)


def _reload_prefs():
    """Drop session lang/theme so load_prefs() re-reads the new identity's
    record on the next run (login and logout both change whose prefs apply)."""
    st.session_state.pop("_lang", None)
    st.session_state.pop("_theme", None)


def logout():
    for k in ("_authed", "_coach", "_role", "_client_self", "client",
              "_active_client"):
        st.session_state.pop(k, None)
    _reload_prefs()


def _any_client_logins():
    try:
        return any((r.get("login") or {}).get("active")
                   for r in cl.load_clients().values())
    except Exception:
        return False


def _any_coach_users():
    try:
        return any(r.get("active")
                   for r in cl.get_settings()["coach_users"].values())
    except Exception:
        return False


def login_form(key="auth_gate"):
    """One login for both roles. Username+password whenever coach users
    (APP_USERS or stored coach accounts) or client logins exist; else the
    legacy single password. Resolution order: coach (APP_USERS) -> stored
    coach account -> client login -> legacy password (any username), so the
    legacy coach password keeps working after named accounts appear.
    Reruns into an unlocked session on success."""
    users = _configured_users()
    two_field = bool(users) or _any_coach_users() or _any_client_logins()
    with st.form(key):
        if two_field:
            entered_u = st.text_input("Username")
            entered_p = st.text_input("Password", type="password")
            if st.form_submit_button("Log in", type="primary"):
                match = next((name for name, pw in users.items()
                              if name.lower() == entered_u.strip().lower()
                              and pw == entered_p), None)
                if not match:
                    match = cl.verify_coach_user(entered_u, entered_p)
                client_name = None if match else \
                    cl.verify_client_login(entered_u, entered_p)
                legacy = _configured_password()
                if match:
                    st.session_state["_authed"] = True
                    st.session_state["_coach"] = match
                    st.session_state["_role"] = "coach"
                    st.session_state.pop("_client_self", None)
                    _reload_prefs()
                    st.rerun()
                elif client_name:
                    st.session_state["_authed"] = True
                    st.session_state["_role"] = "client"
                    st.session_state["_client_self"] = client_name
                    st.session_state["_coach"] = ""
                    st.session_state["client"] = client_name
                    _reload_prefs()
                    st.rerun()
                elif legacy and entered_p == legacy:
                    st.session_state["_authed"] = True
                    st.session_state["_role"] = "coach"
                    _reload_prefs()
                    st.rerun()
                else:
                    st.error("Wrong username or password.")
        else:
            entered = st.text_input("Access password", type="password")
            if st.form_submit_button("Log in", type="primary"):
                if entered == _configured_password():
                    st.session_state["_authed"] = True
                    st.session_state["_role"] = "coach"
                    _reload_prefs()
                    st.rerun()
                else:
                    st.error("Incorrect password.")


def require_auth():
    """Hard-gate a console page whenever an access password is configured.
    Visitors get only the lock screen — nav hidden, page stopped.
    No-op locally (no password set), so `streamlit run` stays frictionless."""
    if is_authed():
        return
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)
    st.markdown(
        '<div class="hero"><div class="hero-top">'
        '<span class="mono acc">[ PRIVATE ]</span>'
        '<span class="mono">T&amp;E · COACHING CONSOLE</span></div>'
        '<h1>Train&amp;Eat<span class="ast">.</span></h1>'
        '<div class="hero-sub">This console is private. Enter the access '
        'password to continue.</div></div>', unsafe_allow_html=True)
    login_form()
    st.stop()


def require_role(*allowed):
    """Server-side page gate — call at the top of every page (after setup).
    Anonymous visitors hit the lock screen; an authed session with the wrong
    role gets a friendly stop, not hidden nav. Returns the session role."""
    require_auth()
    role = current_role()
    if role == "client":
        _force_client_scope()
    if role in allowed:
        return role
    st.markdown(
        '<div class="hero"><div class="hero-top">'
        '<span class="mono acc">[ COACH ONLY ]</span>'
        f'<span class="mono">T&amp;E · ©{YEAR}</span></div>'
        '<h1>Your coach handles this page<span class="ast">.</span></h1>'
        '<div class="hero-sub">Nothing for you to do here — your training, '
        'weigh-ins, check-in and plan live in the menu on the left.</div>'
        '</div>', unsafe_allow_html=True)
    st.stop()


def setup(page_title, icon="✳", public=False, soft=False):
    """Bootstrap a page. Returns True when the console is unlocked.

    `public=True` — applicant intake route: skips the password gate and hides
    the coach sidebar entirely (clean single-purpose page, no chrome).
    `soft=True` — the home page: visitors aren't blocked, but the chrome is
    hidden and False is returned so the page can render a public landing.
    Everything else hard-gates via `require_auth()`.
    """
    st.set_page_config(page_title=f"{page_title} · T&E", page_icon=icon,
                       layout="wide",
                       initial_sidebar_state=(
                           "collapsed" if (public or not is_authed())
                           else "expanded"))
    load_prefs()
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(theme_css(), unsafe_allow_html=True)
    if public:
        st.markdown(_HIDE_CHROME, unsafe_allow_html=True)
        return is_authed()
    if soft and not is_authed():
        st.markdown(_HIDE_CHROME, unsafe_allow_html=True)
        st.markdown(_WIDE_LANDING, unsafe_allow_html=True)
        return False
    require_auth()
    if current_role() == "client":
        _force_client_scope()
    _render_rail(_PAGE_KEY.get(page_title, ""))
    _render_topbar()
    return True


def hero(title, subtitle="", kicker="OVERVIEW"):
    sub = f'<div class="hero-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="hero"><div class="hero-top">'
        f'<span class="mono acc">[ {kicker} ]</span>'
        f'<span class="mono">T&amp;E · ©{YEAR}</span></div>'
        f'<h1>{title} <span class="ast">✳</span></h1>'
        f'{sub}</div>',
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


# ---------- styled tables --------------------------------------------------
# st.data_editor is canvas-rendered — CSS can't touch its cells — so editable
# tables are rebuilt as styled rows of real keyed inputs. Because the inputs
# are keyed session state, edits persist across day/tab switches (pair with a
# keep-alive loop for keys not rendered every run).

def _et_slug(key_base):
    return _re.sub(r"[^A-Za-z0-9_-]+", "-", str(key_base))


def _et_rows_key(key_base):
    return f"{key_base}::rows"


def _as_date(v):
    """Best-effort date coercion for date-kind cells (ISO strings, dates)."""
    if isinstance(v, _date):
        return v
    try:
        return _date.fromisoformat(str(v).strip()[:10])
    except (TypeError, ValueError):
        return None


def _et_seed(key_base, columns, initial_rows):
    """Seed cell state from the record ONCE per key_base; after that the
    session is the source of truth (that's what makes edits survive)."""
    rk = _et_rows_key(key_base)
    if rk in st.session_state:
        return
    rows = list(initial_rows) or [{}]
    st.session_state[rk] = list(range(len(rows)))
    for rid, row in enumerate(rows):
        for c in columns:
            v = row.get(c["field"], "")
            k = f"{key_base}::{rid}::{c['field']}"
            if c.get("kind") == "date":
                st.session_state[k] = _as_date(v) or _date.today()
            else:
                if isinstance(v, float):
                    v = f"{v:g}"      # 9000.0 -> "9000", 175.1 -> "175.1"
                st.session_state[k] = str(v if v is not None else "")


def _et_add_row(key_base, columns, defaults=None, prepend=False):
    rk = _et_rows_key(key_base)
    ids = st.session_state.get(rk, [])
    rid = (max(ids) + 1) if ids else 0
    for c in columns:
        dv = (defaults or {}).get(c["field"], "")
        k = f"{key_base}::{rid}::{c['field']}"
        if c.get("kind") == "date":
            st.session_state[k] = _as_date(dv) or _date.today()
        else:
            st.session_state[k] = str(dv or "")
    st.session_state[rk] = ([rid] + ids) if prepend else (ids + [rid])


def ensure_table(key_base, columns, initial_rows):
    """Seed an editable_table's state before it renders (e.g. when a chart
    above it needs the rows first)."""
    _et_seed(key_base, columns, initial_rows)


def add_table_row(key_base, columns, defaults=None, prepend=False):
    """Add a row (optionally pre-filled; prepend puts it on top) —
    callback-safe."""
    _et_add_row(key_base, columns, defaults, prepend)


def _et_del_row(key_base, rid):
    rk = _et_rows_key(key_base)
    st.session_state[rk] = [r for r in st.session_state.get(rk, []) if r != rid]


def read_table_rows(key_base, columns, require=None):
    """Harvest an editable_table's current rows from session state. Date-kind
    cells come back as ISO strings. Rows whose `require` field is blank are
    dropped. Safe to call from callbacks."""
    out = []
    for rid in st.session_state.get(_et_rows_key(key_base), []):
        row = {}
        for c in columns:
            v = st.session_state.get(f"{key_base}::{rid}::{c['field']}")
            if c.get("kind") == "date":
                row[c["field"]] = (v.isoformat()
                                   if hasattr(v, "isoformat")
                                   else str(v or "").strip())
            else:
                row[c["field"]] = (str(v) if v is not None else "").strip()
        if require and not row.get(require):
            continue
        out.append(row)
    return out


def editable_table(key_base, columns, initial_rows, add_label="＋ Add row"):
    """Editorial-styled editable table. columns = [{"field", "label",
    "width"?, "mono"?, "ph"?}]. Seeds from initial_rows once, then session
    state owns the data — read it back with read_table_rows(). All widgets
    keyed under key_base; add/delete run through callbacks."""
    _et_seed(key_base, columns, initial_rows)
    slug = _et_slug(key_base)
    widths = [c.get("width", 1.0) for c in columns] + [0.22]
    mono_css = "".join(
        f'.st-key-et_box_{slug} [data-testid="stColumn"]:nth-child({i + 1}) input'
        '{font-family:var(--mono)!important;font-size:13px!important;'
        'text-align:center!important}'
        for i, c in enumerate(columns) if c.get("mono"))
    if mono_css:
        st.markdown(f"<style>{mono_css}</style>", unsafe_allow_html=True)
    with st.container(key=f"et_box_{slug}"):
        hcols = st.columns(widths, gap="small")
        for i, c in enumerate(columns):
            hcols[i].markdown(f'<div class="eth">{_html.escape(c["label"])}'
                              '</div>', unsafe_allow_html=True)
        hcols[-1].markdown('<div class="eth">&nbsp;</div>',
                           unsafe_allow_html=True)
        for rid in st.session_state.get(_et_rows_key(key_base), []):
            rcols = st.columns(widths, gap="small",
                               vertical_alignment="center")
            for i, c in enumerate(columns):
                if c.get("kind") == "date":
                    rcols[i].date_input(
                        c["label"], key=f"{key_base}::{rid}::{c['field']}",
                        label_visibility="collapsed", format="YYYY-MM-DD")
                else:
                    rcols[i].text_input(
                        c["label"], key=f"{key_base}::{rid}::{c['field']}",
                        label_visibility="collapsed",
                        placeholder=c.get("ph", ""))
            rcols[-1].button("✕", key=f"{key_base}::{rid}::del",
                             on_click=_et_del_row, args=(key_base, rid),
                             help="Remove this row")
    if add_label:
        with st.container(key=f"et_add_{slug}"):
            st.button(add_label, key=f"{key_base}::addrow",
                      on_click=_et_add_row, args=(key_base, columns))
    return read_table_rows(key_base, columns)


def keep_table_alive(prefix):
    """Keep-alive for editable_table state across runs where a table isn't
    rendered (e.g. the other day tabs). Buttons can't be re-assigned, so
    action keys are skipped."""
    for k in list(st.session_state):
        ks = str(k)
        if not ks.startswith(prefix):
            continue
        if ks.endswith("::del") or ks.endswith("::addrow"):
            continue
        try:
            st.session_state[k] = st.session_state[k]
        except Exception:
            pass


def weight_chart(df, goal=None, height=280):
    """THE weight chart — identical on Weigh-ins and the client dashboard.
    Area (accent gradient fading down) + ink line + cream/accent points,
    latest point emphasized in solid ink. Optional goal: faint --good band
    + dashed rule; skipped cleanly when None. df needs Date + Weight.
    Returns False (rendering nothing) when there aren't 2 plottable rows."""
    import altair as alt
    import pandas as pd
    d = df.copy()
    d["Weight"] = pd.to_numeric(d["Weight"], errors="coerce")
    d = d.dropna(subset=["Weight"])
    if len(d) < 2:
        return False
    pal = chart_palette()
    lo, hi = float(d["Weight"].min()), float(d["Weight"].max())
    if goal is not None:
        lo, hi = min(lo, float(goal)), max(hi, float(goal))
    pad = max((hi - lo) * 0.25, 1.0)
    x = alt.X("Date:N", title=None, sort=None,
              axis=alt.Axis(labelAngle=0, labelColor=pal["fg-muted"],
                            domainColor=pal["border"],
                            tickColor=pal["border"],
                            labelFont="Space Mono", labelFontSize=10.5))
    y = alt.Y("Weight:Q", title=None,
              scale=alt.Scale(domain=[lo - pad, hi + pad]),
              axis=alt.Axis(labelColor=pal["fg-muted"],
                            gridColor=pal["border-soft"],
                            domainOpacity=0, tickColor=pal["border"],
                            labelFont="Space Mono", labelFontSize=10.5))
    base = alt.Chart(d).encode(x=x, y=y, tooltip=["Date", "Weight"])
    layers = []
    if goal is not None:
        g = float(goal)
        layers.append(alt.Chart(pd.DataFrame({"lo": [g - 1.5],
                                              "hi": [g + 1.5]}))
                      .mark_rect(color=pal["good"], opacity=0.08)
                      .encode(y="lo:Q", y2="hi:Q"))
        layers.append(alt.Chart(pd.DataFrame({"g": [g]}))
                      .mark_rule(color=pal["good"], strokeDash=[5, 5],
                                 strokeWidth=1.5)
                      .encode(y="g:Q"))
    # the area's implicit y2 is the ZERO baseline, which silently unions 0
    # into the y-scale and flattens the line — pin it to the domain floor
    layers.append(base.mark_area(
        line=False,
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color=_hex_rgba(pal["accent"], 0),
                                    offset=0),
                   alt.GradientStop(color=_hex_rgba(pal["accent"], 0.22),
                                    offset=1)],
            x1=1, x2=1, y1=1, y2=0)).encode(
        y2=alt.datum(float(lo - pad))))
    layers.append(base.mark_line(color=pal["fg"], strokeWidth=2.5,
                                 strokeJoin="round"))
    layers.append(base.mark_point(filled=True, color=pal["bg"],
                                  stroke=pal["accent"], strokeWidth=2.5,
                                  size=64))
    layers.append(alt.Chart(d.tail(1)).encode(x=x, y=y)
                  .mark_point(filled=True, color=pal["fg"], size=95))
    chart = (alt.layer(*layers)
             .properties(height=height, background="transparent")
             .configure_view(strokeWidth=0))
    st.altair_chart(chart, width="stretch")
    return True


def _index_tab_pick(key, opt):
    st.session_state[key] = opt


def index_tabs(key, options, numbered=True, labels=None):
    """Squared index-block switcher — replaces every pill/segmented radio.
    A row of st.buttons; the selected one is type='primary' (solid ink),
    the rest secondary (paper + hairline). Selection is keyed session state
    changed via on_click callbacks; returns the selected option. Buttons are
    keyed f"{key}::opt::{option}" (stable even when display labels — e.g.
    live counts — change via the `labels` map)."""
    if not options:
        return None
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    current = st.session_state[key]
    # the tabs__ container is a CSS hook: on phones the row WRAPS to a
    # second line instead of stacking one-tab-per-row (see the mobile block)
    with st.container(key=f"tabs__{key}"):
        cols = st.columns([1] * len(options) + [max(0.06, 5 - len(options))],
                          gap="small")
        for i, opt in enumerate(options):
            if labels and opt in labels:
                label = str(labels[opt])
            elif numbered:
                label = f"{i + 1:02d} · {opt}"
            else:
                label = str(opt)
            cols[i].button(
                label, key=f"{key}::opt::{opt}",
                type=("primary" if opt == current else "secondary"),
                on_click=_index_tab_pick, args=(key, opt),
                use_container_width=True)
    return current


def allergy_bar(allergy_text):
    """The slim allergy bar — renders only when real allergens exist.
    Free-text field; commas become a clean list. Returns True if shown."""
    t = str(allergy_text or "").strip()
    if not t or t.lower() in ("none", "n/a", "no", "-", "—", "nothing"):
        return False
    items = ", ".join(p.strip() for p in t.split(",") if p.strip())
    st.markdown(f'<div class="al-bar"><span class="lbl">⚠ Allergy</span>'
                f'<b>{_html.escape(items)}</b></div>',
                unsafe_allow_html=True)
    return True


def styled_table(headers, rows, mono_cols=()):
    """Read-only editorial table: sand header, mono uppercase labels, cream
    paper rows, hairline borders. rows = list of tuples/lists matching
    headers; mono_cols = indexes rendered centered in Space Mono."""
    th = "".join(f"<th>{_html.escape(str(h))}</th>" for h in headers)
    trs = []
    for row in rows:
        tds = "".join(
            f'<td class="mono">{_html.escape(str(v))}</td>'
            if i in mono_cols else f"<td>{_html.escape(str(v))}</td>"
            for i, v in enumerate(row))
        trs.append(f"<tr>{tds}</tr>")
    st.markdown(f'<div class="te-tblwrap"><table class="te-tbl">'
                f'<thead><tr>{th}</tr></thead>'
                f'<tbody>{"".join(trs)}</tbody></table></div>',
                unsafe_allow_html=True)


def client_panel(name, contact_line, metrics, status=None):
    """Active-client summary panel: big name, mono contact line, optional
    status chip, and a grid of metric cells.

    metrics = [{"label", "value", "unit"?, "delta"?: (text, tone)}, ...]
    status  = (text, tone) with tone in good|warn|over, or None for no chip.
    All strings are escaped — values come straight from client records."""
    status_html = ""
    if status:
        txt, tone = status
        status_html = (f'<span class="te-status {tone}">'
                       f'{_html.escape(str(txt))}</span>')
    cells = []
    for m in metrics:
        unit = m.get("unit")
        unit_html = f'<small>{_html.escape(str(unit))}</small>' if unit else ""
        delta_html = ""
        if m.get("delta"):
            dtxt, dtone = m["delta"]
            delta_html = (f'<div class="delta {dtone}">'
                          f'{_html.escape(str(dtxt))}</div>')
        cells.append('<div class="te-metric">'
                     f'<div class="l">{_html.escape(str(m["label"]))}</div>'
                     f'<div class="v">{_html.escape(str(m["value"]))}'
                     f'{unit_html}</div>'
                     f'{delta_html}</div>')
    st.markdown('<div class="te-panel"><div class="head">'
                f'<div><h2>{_html.escape(str(name))}</h2>'
                f'<div class="contact">{_html.escape(str(contact_line))}</div>'
                f'</div>{status_html}</div>'
                f'<div class="te-metrics">{"".join(cells)}</div></div>',
                unsafe_allow_html=True)


def empty_state(title, hint, kicker="NOTHING HERE YET"):
    """A branded empty state: what's missing and what to do about it."""
    st.markdown(
        f'<div class="empty"><span class="mono acc">[ {kicker} ]</span>'
        f'<h3>{title}</h3><p>{hint}</p></div>', unsafe_allow_html=True)


def marquee(word="TRAIN & EAT", n=8):
    unit = f'<span>{word}</span><span class="s">✳</span>'
    st.markdown(f'<div class="marquee"><div class="track">{unit*n}{unit*n}</div></div>',
                unsafe_allow_html=True)


def client_picker():
    """The active-client switcher now lives in the top bar (rendered by
    setup() -> _render_topbar). This returns the client it selected, so pages
    can keep calling `active = ui.client_picker()` unchanged."""
    return st.session_state.get("_active_client")
