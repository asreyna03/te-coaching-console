"""Public 1-on-1 coaching application — Typeform-style wizard.

One question per screen. Choice steps are lettered option pills that
auto-advance on tap (no Continue click); height/weight are dropdowns with
unit toggles (ft-in/cm, lbs/kg); free-text questions are gated behind a
Yes/None choice so nobody is forced to type. Lives at /Apply — no password,
no sidebar (`ui.setup(..., public=True)`). Answers accumulate in
session_state and persist via `cl.save_application()` on the final answer,
landing in the coach-only Applications inbox.

All interaction runs through keyed widgets + on_click/on_change callbacks —
no mid-run st.rerun() (it breaks AppTest on fresh form widgets, and
callbacks are smoother anyway).
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import re
import streamlit as st
import ui
import coachlib as cl

ui.setup("Apply", public=True)

st.markdown("""<style>
.wizhead{display:flex;justify-content:space-between;align-items:center;
  margin:26px 0 8px}
/* progress bar as a measuring tape — the app's hero signature, filling in
   accent as the applicant advances; nub marks the current position */
.wizbar{position:relative;height:13px;margin:4px 0 34px}
.wizbar:before{content:"";position:absolute;inset:0;background:
  repeating-linear-gradient(90deg,var(--line) 0 1.5px,transparent 1.5px 9px),
  repeating-linear-gradient(90deg,var(--line) 0 1.5px,transparent 1.5px 45px);
  background-size:100% 55%,100% 100%;
  background-position:bottom left,bottom left;background-repeat:no-repeat}
.wizbar i{position:absolute;left:0;top:0;bottom:0;display:block;background:
  repeating-linear-gradient(90deg,var(--accent) 0 1.5px,transparent 1.5px 9px),
  repeating-linear-gradient(90deg,var(--accent) 0 1.5px,transparent 1.5px 45px),
  linear-gradient(var(--accent),var(--accent));
  background-size:100% 55%,100% 100%,100% 2px;
  background-position:bottom left,bottom left,bottom left;
  background-repeat:no-repeat;
  transition:width .5s cubic-bezier(.22,1,.36,1)}
.wizbar i:after{content:"";position:absolute;right:0;top:0;bottom:0;
  width:2.5px;background:var(--accent)}
.q{font-family:'Bricolage Grotesque','Archivo',sans-serif;font-weight:800;
  font-size:clamp(1.5rem,1.1rem + 2vw,2.2rem);letter-spacing:-.02em;
  line-height:1.05;margin:6px 0 6px}
.qhint{color:var(--muted);font-size:.95rem;margin:0 0 14px}
/* Typeform-style option pills (auto-advance buttons) */
[class*="st-key-aw_opt"] .stButton > button{
  width:100%;justify-content:flex-start !important;text-align:left;
  background:var(--paper);color:var(--ink);
  border:1.5px solid var(--line);border-radius:12px;
  padding:.72rem 1rem;
  transition:border-color .15s ease,transform .15s ease,box-shadow .15s ease}
[class*="st-key-aw_opt"] .stButton > button > div{
  width:100%;justify-content:flex-start}
[class*="st-key-aw_opt"] .stButton > button [data-testid="stMarkdownContainer"]{
  width:100%;text-align:left}
[class*="st-key-aw_opt"] .stButton > button p{
  font-family:'Archivo',sans-serif;font-weight:600;font-size:.95rem;
  letter-spacing:0;text-align:left}
/* lettered keycap — styles the leading A/B/C/D of the label */
[class*="st-key-aw_opt"] .stButton > button p::first-letter{
  font-family:'Space Mono',monospace;font-weight:700;color:var(--muted);
  background:var(--sand);border:1px solid var(--line);border-radius:5px;
  padding:.1em .38em;margin-right:.7em}
[class*="st-key-aw_opt"] .stButton > button:hover{
  background:var(--paper);border-color:var(--accent);color:var(--accent);
  transform:translateX(4px);box-shadow:0 10px 24px -18px rgba(0,0,0,.5)}
[class*="st-key-aw_opt"] .stButton > button:hover p::first-letter{
  color:#fff;background:var(--accent);border-color:var(--accent)}
[class*="st-key-aw_opt"] .stButton > button:active{
  transform:translateX(4px) scale(.99)}
/* staggered load-in: question, hint, then answers cascade like Typeform */
@media (prefers-reduced-motion: no-preference){
  .q{animation:fadeup .35s ease both}
  .qhint{animation:fadeup .35s ease .05s both}
  div[class*="st-key-aw_opt"]{animation:fadeup .35s ease .08s both}
  div[class*="st-key-aw_opt"] ~ div[class*="st-key-aw_opt"]{
    animation-delay:.14s}
  div[class*="st-key-aw_opt"] ~ div[class*="st-key-aw_opt"]
    ~ div[class*="st-key-aw_opt"]{animation-delay:.2s}
  div[class*="st-key-aw_opt"] ~ div[class*="st-key-aw_opt"]
    ~ div[class*="st-key-aw_opt"] ~ div[class*="st-key-aw_opt"]{
    animation-delay:.26s}
  [data-testid="stForm"]{animation:fadeup .35s ease .08s both}
  div[class*="st-key-aw_unit"]{animation:fadeup .35s ease .08s both}
  div[class*="st-key-aw_sel"]{animation:fadeup .35s ease .14s both}
  div[class*="st-key-aw_back"]{animation:fadein .4s ease .3s both}
  [data-testid="stAlert"]{
    animation:shake .4s cubic-bezier(.36,.07,.19,.97) both}
  .apply-done .hero:after{
    animation:tapedraw .9s cubic-bezier(.22,1,.36,1) .35s both}
}
@keyframes shake{10%,90%{transform:translateX(-1px)}
  20%,80%{transform:translateX(2px)}
  30%,50%,70%{transform:translateX(-3px)}40%,60%{transform:translateX(3px)}}
@keyframes tapedraw{from{clip-path:inset(0 100% 0 0)}
  to{clip-path:inset(0 0 0 0)}}
/* quiet back links — both the choice-step button and the in-form
   secondary submit render as muted text, not competing pills */
[class*="st-key-aw_back"] .stButton > button,
button[data-testid="stBaseButton-secondaryFormSubmit"]{
  background:transparent;border-color:transparent;color:var(--muted);
  box-shadow:none;padding:.3rem .6rem}
[class*="st-key-aw_back"] .stButton > button:hover,
button[data-testid="stBaseButton-secondaryFormSubmit"]:hover{
  background:transparent;border-color:transparent;color:var(--accent);
  transform:none;box-shadow:none}
</style>""", unsafe_allow_html=True)

SUBMITTED_KEY = "_apply_submitted"
ERR_KEY = "apply_error"
EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LETTERS = "ABCDEFGH"

# Post-submit confirmation. Refreshing returns to a blank form — intentional.
if st.session_state.get(SUBMITTED_KEY):
    st.markdown(
        '<div class="apply-done"><div class="hero"><div class="hero-top">'
        '<span class="mono acc">[ APPLICATION RECEIVED ]</span>'
        '<span class="mono">T&amp;E · COACHING</span></div>'
        '<h1>Thank you<span class="ast">.</span></h1>'
        '<div class="hero-sub">Your application has been submitted. '
        'I&rsquo;ll personally review it and reach out within 24&ndash;48 '
        'hours if I think we&rsquo;re a good fit.</div></div></div>',
        unsafe_allow_html=True)
    st.stop()

FT_IN = [f"{ft}'{i}\"" for ft in range(4, 8) for i in range(12)
         if (ft, i) >= (4, 10) and (ft, i) <= (7, 0)]
CM = [f"{n} cm" for n in range(147, 214, 1)]
LBS = [f"{n} lbs" for n in range(80, 401, 5)]
KG = [f"{n} kg" for n in range(36, 182, 2)]

STEPS = [
    {"key": "name", "kind": "text", "q": "What's your name?",
     "hint": "First and last.", "ph": "e.g. Eric Alvarez"},
    {"key": "age", "kind": "choice", "q": "How old are you?",
     "options": ["<18", "18–25", "25–35", "35–50+"]},
    {"key": "email", "kind": "text", "q": "What's your email?",
     "hint": "Where your application updates land.",
     "ph": "you@email.com"},
    {"key": "phone", "kind": "text", "q": "And your phone number?",
     "hint": "So we can actually reach you if it's a fit.",
     "ph": "555-010-0000"},
    {"key": "height", "kind": "select", "q": "How tall are you?",
     "units": {"ft / in": FT_IN, "cm": CM}, "ph": "Select your height"},
    {"key": "weight", "kind": "select", "q": "Current weight?",
     "units": {"lbs": LBS, "kg": KG}, "ph": "Select your weight"},
    {"key": "goal", "kind": "choice", "q": "What's your main fitness goal?",
     "options": ["Lose fat", "Build muscle", "Recomposition (both)",
                 "Performance / general health"]},
    {"key": "days", "kind": "choice",
     "q": "How many days per week do you currently train?",
     "options": ["0–2", "3–4", "5–6", "Every day"]},
    {"key": "injuries", "kind": "gated",
     "q": "Any injuries or limitations?",
     "gate": ["Yes", "None"], "none_val": "None",
     "hint": "If yes, you'll get a box to explain."},
    {"key": "allergies", "kind": "gated",
     "q": "Any food allergies or intolerances?",
     "gate": ["Yes", "None"], "none_val": "None",
     "hint": "Anything we need to know before building your meal plan."},
    {"key": "struggle", "kind": "gated",
     "q": "What are you struggling with most right now?",
     "gate": ["I'll type it out", "Nothing specific"],
     "none_val": "Nothing specific",
     "hint": "Honesty helps us actually help you."},
    {"key": "coached", "kind": "choice",
     "q": "Have you worked with a coach before?", "options": ["Yes", "No"]},
    {"key": "invest", "kind": "choice",
     "q": "Are you ready to invest in coaching if it's a good fit?",
     "options": ["Yes", "No"]},
]
GATE_KEYS = [f"apply_gate_{s['key']}" for s in STEPS if s["kind"] == "gated"]

# Guard 1 — schema drift: if the question set changes under an in-flight
# session (deploy / hot reload), reset the wizard cleanly instead of letting
# a half-old answers dict reach _finalize and crash on the last tap.
WIZARD_VERSION = "steps:" + "|".join(s["key"] for s in STEPS)
if st.session_state.get("apply_version") != WIZARD_VERSION:
    for k in ["apply_answers", "apply_step", ERR_KEY] + GATE_KEYS:
        st.session_state.pop(k, None)
    st.session_state["apply_version"] = WIZARD_VERSION

answers = st.session_state.setdefault("apply_answers", {})
step = st.session_state.setdefault("apply_step", 0)
s = STEPS[step]
total = len(STEPS)


# ---------- callbacks (run when a widget commits; no st.rerun anywhere) ----
def _finalize():
    # Guard 3 — .get() everywhere: a partial application in the inbox
    # always beats a stack trace that loses the applicant.
    a = st.session_state["apply_answers"]

    def val(key):
        return str(a.get(key, "") or "").strip()

    name_parts = val("name").split() or [""]
    cl.save_application({
        "first_name": name_parts[0],
        "last_name": " ".join(name_parts[1:]),
        "email": val("email"),
        "phone": val("phone"),
        "age": val("age"),
        "height": val("height"),
        "current_weight": val("weight"),
        "primary_goal": val("goal"),
        "days_per_week": val("days"),
        "injuries": val("injuries"),
        "allergies": val("allergies"),
        "biggest_struggle": val("struggle"),
        "coached_before": val("coached"),
        "ready_to_invest": val("invest"),
    })
    st.session_state[SUBMITTED_KEY] = True
    for k in ["apply_answers", "apply_step", ERR_KEY] + GATE_KEYS:
        st.session_state.pop(k, None)


def _record(key, value):
    """Store an answer and move on (or submit, on the last step)."""
    a = st.session_state["apply_answers"]
    a[key] = value
    st.session_state[ERR_KEY] = None
    if st.session_state["apply_step"] < len(STEPS) - 1:
        st.session_state["apply_step"] += 1
        return
    # Guard 2 — completeness: never submit with holes. If any answer is
    # missing (stale session, future bug), route back to the first missing
    # question instead of crashing — the applicant fixes it in one tap.
    missing = [i for i, sd in enumerate(STEPS)
               if not str(a.get(sd["key"], "") or "").strip()]
    if missing:
        st.session_state["apply_step"] = missing[0]
        st.session_state[ERR_KEY] = ("Almost done — this answer didn't save "
                                     "the first time, mind filling it in "
                                     "again?")
        return
    _finalize()


def _validate_text(key, val):
    if not val:
        return "This one's required."
    if key == "name" and len(val.split()) < 2:
        return "First and last name, please."
    if key == "email" and not EMAIL_RX.match(val):
        return "That doesn't look like an email address."
    if key == "phone" and len(re.sub(r"\D", "", val)) < 7:
        return "That doesn't look like a phone number."
    return None


def _text_continue(s):
    val = (st.session_state.get(f"aw_{s['key']}") or "").strip()
    err = _validate_text(s["key"], val)
    st.session_state[ERR_KEY] = err
    if not err:
        _record(s["key"], val)


def _area_continue(s):
    val = (st.session_state.get(f"aw_{s['key']}") or "").strip()
    if not val:
        st.session_state[ERR_KEY] = "A sentence or two helps us help you."
        return
    st.session_state[f"apply_gate_{s['key']}"] = None
    _record(s["key"], val)


def _select_changed(key, widget_key):
    val = st.session_state.get(widget_key)
    if val:
        _record(key, val)


def _gate_open(key):
    st.session_state[f"apply_gate_{key}"] = "yes"
    st.session_state[ERR_KEY] = None


def _go_back(s):
    st.session_state[ERR_KEY] = None
    gate_key = f"apply_gate_{s['key']}"
    if s["kind"] == "gated" and st.session_state.get(gate_key) == "yes":
        typed = st.session_state.get(f"aw_{s['key']}")
        if typed is not None:
            st.session_state["apply_answers"][s["key"]] = typed
        st.session_state[gate_key] = None
        return
    if s["kind"] == "text":
        typed = st.session_state.get(f"aw_{s['key']}")
        if typed is not None:
            st.session_state["apply_answers"][s["key"]] = typed
    st.session_state["apply_step"] -= 1


# ---------- render ---------------------------------------------------------
st.markdown(
    f'<div class="wizhead"><span class="mono acc">[ 1-ON-1 COACHING · '
    f'APPLICATION ]</span><span class="mono">QUESTION {step + 1} / {total}'
    f'</span></div>'
    f'<div class="wizbar"><i style="width:{int(100 * step / total)}%"></i>'
    f'</div>', unsafe_allow_html=True)

st.markdown(f'<div class="q">{s["q"]}</div>', unsafe_allow_html=True)
if s.get("hint"):
    st.markdown(f'<div class="qhint">{s["hint"]}</div>',
                unsafe_allow_html=True)


def _option_buttons(step_def, options, on_click):
    """Typeform-style lettered pills; a tap answers and advances."""
    for i, opt in enumerate(options):
        st.button(f"{LETTERS[i]}   {opt}", key=f"aw_opt_{step_def['key']}_{i}",
                  width="stretch", on_click=on_click, args=(opt,))


def _back_button(step_def):
    if st.session_state["apply_step"] > 0 or (
            step_def["kind"] == "gated"
            and st.session_state.get(f"apply_gate_{step_def['key']}") == "yes"):
        st.button("← Back", key="aw_back", on_click=_go_back, args=(step_def,))


if s["kind"] == "text":
    with st.form(f"apply_{s['key']}"):
        st.text_input(s["q"], value=answers.get(s["key"], ""),
                      placeholder=s.get("ph", ""), key=f"aw_{s['key']}",
                      label_visibility="collapsed")
        st.write("")
        back_col, cont_col = st.columns([1, 5])
        if step > 0:
            back_col.form_submit_button("← Back", on_click=_go_back, args=(s,))
        cont_col.form_submit_button("Continue →", type="primary",
                                    on_click=_text_continue, args=(s,))

elif s["kind"] == "choice":
    _option_buttons(s, s["options"], lambda opt, k=s["key"]: _record(k, opt))
    st.write("")
    _back_button(s)

elif s["kind"] == "select":
    unit_names = list(s["units"])
    unit = st.radio("Units", unit_names, horizontal=True,
                    key=f"aw_unit_{s['key']}", label_visibility="collapsed")
    opts = s["units"][unit]
    prev = answers.get(s["key"])
    widget_key = f"aw_sel_{s['key']}_{unit.replace(' ', '')}"
    st.selectbox(s["q"], opts,
                 index=opts.index(prev) if prev in opts else None,
                 placeholder=s["ph"], key=widget_key,
                 on_change=_select_changed, args=(s["key"], widget_key),
                 label_visibility="collapsed")
    st.write("")
    _back_button(s)

else:  # gated free text: Yes → textbox, None → straight through
    if st.session_state.get(f"apply_gate_{s['key']}") != "yes":
        yes_label, none_label = s["gate"]
        st.button(f"A   {yes_label}", key=f"aw_opt_{s['key']}_yes",
                  width="stretch", on_click=_gate_open, args=(s["key"],))
        st.button(f"B   {none_label}", key=f"aw_opt_{s['key']}_none",
                  width="stretch",
                  on_click=lambda k=s["key"], v=s["none_val"]: _record(k, v))
        st.write("")
        _back_button(s)
    else:
        prev = answers.get(s["key"], "")
        with st.form(f"apply_{s['key']}"):
            st.text_area(s["q"], value="" if prev == s["none_val"] else prev,
                         height=110, key=f"aw_{s['key']}",
                         label_visibility="collapsed")
            st.write("")
            back_col, cont_col = st.columns([1, 5])
            back_col.form_submit_button("← Back", on_click=_go_back, args=(s,))
            cont_col.form_submit_button("Continue →", type="primary",
                                        on_click=_area_continue, args=(s,))

if st.session_state.get(ERR_KEY):
    st.error(st.session_state[ERR_KEY])
