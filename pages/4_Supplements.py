"""Supplements — the SAME editorial reference grid for coach and client
(Supplement · Reason · Dose/timing · Essential? · Buy). The earlier
coach-only cost/pricing grid is parked (per Sam) — its data stays in
`_settings.supp_costs` untouched in case it comes back.

Buy links: the food-DB "link" column mostly holds prose ("Order here…"),
so real product URLs live as coach-set overrides in `_settings.supp_links`
{name: url}. Only http(s) URLs ever render; no URL -> no Buy link at all.
"""
import html as _html
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl
from i18n import t

ui.setup("Supplements", "✳")
role = ui.require_role("coach", "client")
ui.client_picker()
supps = cl.load_supplements()
links = cl.get_settings()["supp_links"]


def _buy_url(s):
    """Coach override first, then the food-DB link if it's a real URL."""
    u = str(links.get(str(s["name"]).strip(), "") or "").strip()
    if u.startswith(("http://", "https://")):
        return u
    raw = str(s.get("link", "") or "").strip()
    return raw if raw.startswith(("http://", "https://")) else ""


ui.hero(t("sc_title"), t("sc_sub", n=len(supps)), kicker=t("sc_kicker"))

# ---- coach-only: buy-link editor (Sam pastes real product URLs here) -------
if role == "coach":
    def _save_links():
        out = {}
        for s in supps:
            nm = str(s["name"]).strip()
            if not nm:
                continue
            u = (st.session_state.get(f"slink::{nm}") or "").strip()
            if u:
                out[nm] = u
        cl.save_settings({"supp_links": out})
        st.session_state["sl_msg"] = t("sl_saved")

    if st.session_state.get("sl_msg"):
        st.success(st.session_state.pop("sl_msg"))
    with st.expander(t("sl_expander")):
        st.caption(t("sl_cap"))
        for s in supps:
            nm = str(s["name"]).strip()
            if not nm:
                continue
            st.text_input(nm, value=links.get(nm, ""),
                          placeholder="https://…", key=f"slink::{nm}")
        st.button(t("sl_save"), key="slink_save", type="primary",
                  on_click=_save_links)

q = st.text_input(t("sc_search"), placeholder=t("sc_search_ph"),
                  key="supp_search").strip().lower()

rows = []
for s in supps:
    if not str(s["name"]).strip():
        continue
    blob = f'{s["name"]} {s["reason"]}'.lower()
    if q and q not in blob:
        continue
    rows.append(s)

if not rows:
    st.info(t("sc_no_match"))
else:
    trs = []
    for s in rows:
        reason = str(s.get("reason", "") or "").strip() or "—"
        dose = str(s.get("directions", "") or "").strip() or "—"
        essential = "essential" in reason.lower()
        ess_cell = (f'<span class="cs-chip done">{t("sc_essential")}</span>'
                    if essential else
                    f'<span class="cs-chip none">{t("sc_optional")}</span>')
        url = _buy_url(s)
        buy_cell = ""      # no URL -> no Buy link at all (never a dead one)
        if url:
            buy_cell = (f'<a class="buy" '
                        f'href="{_html.escape(url, quote=True)}" '
                        f'target="_blank" rel="noopener">'
                        f'{t("sc_buy_link")}</a>')
        trs.append(
            f'<tr><td class="sup">{_html.escape(str(s["name"]))}</td>'
            f'<td class="rsn">{_html.escape(reason)}</td>'
            f'<td class="dose">➜ {_html.escape(dose)}</td>'
            f'<td class="ctr">{ess_cell}</td>'
            f'<td class="ctr">{buy_cell}</td></tr>')
    st.markdown(
        '<div class="sc-wrap"><div class="sc-gbar">'
        f'<span>{t("sc_your_stack")}</span>'
        f'<span class="mt">{t("sc_grid_sub", n=len(rows))}</span></div>'
        '<div class="sc-scroll"><table class="sc-tbl" '
        'style="min-width:760px"><thead><tr>'
        f'<th class="l">{t("sc_supplement")}</th>'
        f'<th class="l">{t("sc_reason")}</th>'
        f'<th class="l">{t("sc_dose")}</th><th>{t("sc_essential_q")}</th>'
        f'<th>{t("sc_buy")}</th>'
        f'</tr></thead><tbody>{"".join(trs)}</tbody></table></div></div>',
        unsafe_allow_html=True)
