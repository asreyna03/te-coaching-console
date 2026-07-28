"""Coach-only inbox for inbound coaching applications.

Auth-gated like the rest of the console. One inbox: review each application,
mark reviewed / decline / delete — or "Convert to client →", which creates
the client profile (start date today, goals composed from their answers) AND
their client login in one click, showing the temp credentials once. Details
are edited afterwards on Home.

All actions run through on_click callbacks (no mid-run st.rerun).
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from datetime import date
import streamlit as st
import ui
import coachlib as cl
from i18n import t

ui.setup("Applications")
ui.require_role("coach")
ui.client_picker()

ui.hero(f'{t("nav_apps")}.', t("ap_sub"), kicker=t("ap_kicker"))

STATUS_LABELS = {"new": t("ap_new"), "reviewed": t("ap_reviewed"),
                 "converted": t("ap_converted"),
                 "declined": t("ap_declined")}
STATUS_ORDER = ["new", "reviewed", "converted", "declined"]
MSG_KEY = "apps_msg"


def _set_status(app_id, status):
    cl.set_application_status(app_id, status)


def _delete(app_id):
    cl.delete_application(app_id)


def _full_name(a):
    return (f"{a.get('first_name', '').strip()} "
            f"{a.get('last_name', '').strip()}").strip() or "(no name)"


def _compose_goals(a):
    """Fold the application answers into a first-draft goals note."""
    bits = [a.get("primary_goal", "").strip()]
    struggle = a.get("biggest_struggle", "").strip()
    if struggle and struggle.lower() != "nothing specific":
        bits.append(f"Struggles with: {struggle}")
    injuries = a.get("injuries", "").strip()
    if injuries and injuries.lower() != "none":
        bits.append(f"Injuries/limitations: {injuries}")
    allergies = a.get("allergies", "").strip()
    if allergies and allergies.lower() != "none":
        bits.append(f"Food allergies/intolerances: {allergies}")
    bits.append(f"Currently trains {a.get('days_per_week', '?')} days/week; "
                f"coached before: {a.get('coached_before', '?')}")
    return ". ".join(b for b in bits if b)


def _convert(a):
    """One click: application -> client profile + client login. Start date is
    today, goals are composed from their answers; the temp credentials are
    shown to the coach exactly once (no email is sent — that's queued work).
    Details get edited afterwards on Home."""
    aid = a["id"]
    name = _full_name(a)
    if name == "(no name)":
        st.session_state[MSG_KEY] = ("error", t("ap_no_name"))
        return
    stats = " — ".join(x for x in (a.get("height", "").strip(),
                                   a.get("current_weight", "").strip()) if x)
    cl.upsert_client(name, {
        "start_date": date.today().isoformat(),
        "bodyweight": (a.get("current_weight") or "").strip(),
        "stats": stats,
        "goals": _compose_goals(a),
        "contact_email": (a.get("email") or "").strip(),
        "contact_phone": (a.get("phone") or "").strip(),
        "age": a.get("age", ""),
        "allergies": ("" if (a.get("allergies") or "").strip().lower()
                      in ("", "none") else a.get("allergies", "").strip()),
    })
    email = (a.get("email") or "").strip().lower()
    username = email or name.lower().replace(" ", ".")
    temp_pw = cl.generate_temp_password()
    cl.set_client_login(name, username, temp_pw)
    st.session_state["_onb_creds"] = {"name": name, "username": username,
                                      "password": temp_pw}
    cl.set_application_status(aid, "converted")
    st.session_state["client_pick_pending"] = name
    st.session_state["client"] = name
    st.session_state[MSG_KEY] = (
        "success", t("ap_now_client", name=name))


apps = cl.load_applications()
if st.session_state.get(MSG_KEY):
    kind, text = st.session_state.pop(MSG_KEY)
    (st.success if kind == "success" else st.error)(text)
if st.session_state.get("_onb_creds"):
    creds = st.session_state.pop("_onb_creds")
    st.warning(t("onb_creds", name=creds["name"], u=creds["username"],
                 p=creds["password"]))

# ---------------- the inbox -------------------------------------------------
if not apps:
    ui.empty_state(t("ap_none"), t("ap_none_sub"),
                   kicker=t("ap_empty_kicker"))
else:
    counts = {k: sum(1 for a in apps if a.get("status", "new") == k)
              for k in STATUS_ORDER}
    ui.stat_row([(counts["new"], t("ap_new")),
                 (counts["reviewed"], t("ap_reviewed")),
                 (counts["converted"], t("ap_converted")),
                 (counts["declined"], t("ap_declined"))])
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

    _tab_labels = {"all": t("ap_all", n=len(apps))}
    _tab_labels.update({k: f"{STATUS_LABELS[k].title()} {counts[k]}"
                        for k in STATUS_ORDER})
    filt = ui.index_tabs("apps_filter", ["all"] + STATUS_ORDER,
                         numbered=False, labels=_tab_labels)
    shown = (apps if filt == "all"
             else [a for a in apps if a.get("status", "new") == filt])

    if not shown:
        ui.empty_state(t("ap_bucket_empty"), t("ap_bucket_sub"),
                       kicker=t("ap_empty_kicker"))

    for a in shown:
        full = _full_name(a)
        submitted = (a.get("submitted_at") or "").split("T")[0] or "—"
        status = a.get("status", "new")
        header = (f"{full}  ·  {submitted}  ·  "
                  f"{STATUS_LABELS.get(status, status.upper())}")
        with st.expander(header, expanded=(status == "new")):
            c1, c2 = st.columns(2)
            c1.markdown(f"**{t('ap_email')}**  \n"
                        f"{a.get('email', '—') or '—'}")
            c1.markdown(f"**{t('ap_phone')}**  \n"
                        f"{a.get('phone', '—') or '—'}")
            c1.markdown(f"**{t('ap_age')}**  \n"
                        f"{a.get('age', '—') or '—'}")
            c2.markdown(f"**{t('ap_height')}**  \n"
                        f"{a.get('height', '—') or '—'}")
            c2.markdown(f"**{t('ap_weight')}**  \n"
                        f"{a.get('current_weight', '—') or '—'}")
            c2.markdown(f"**{t('ap_days')}**  \n"
                        f"{a.get('days_per_week', '—') or '—'}")

            ui.label(t("ap_goal"))
            st.write(a.get("primary_goal", "—") or "—")
            ui.label(t("ap_injuries"))
            st.write(a.get("injuries", "—") or "—")
            ui.label(t("ap_allergies"))
            st.write(a.get("allergies", "—") or "—")
            ui.label(t("ap_struggle"))
            st.write(a.get("biggest_struggle", "—") or "—")
            ui.label(t("ap_coached"))
            st.write(f"{a.get('coached_before', '—') or '—'}  ·  "
                     f"{a.get('ready_to_invest', '—') or '—'}")

            st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
            aid = a["id"]
            b0, b1, b2, b3 = st.columns([0.34, 0.25, 0.19, 0.22])
            if status != "converted":
                b0.button(t("ap_convert"), key=f"conv_{aid}",
                          on_click=_convert, args=(a,))
            b1.button(t("ap_review"), key=f"rev_{aid}",
                      on_click=_set_status, args=(aid, "reviewed"))
            b2.button(t("ap_decline"), key=f"dec_{aid}",
                      on_click=_set_status, args=(aid, "declined"))
            b3.button(t("ap_delete"), key=f"del_{aid}",
                      on_click=_delete, args=(aid,))
