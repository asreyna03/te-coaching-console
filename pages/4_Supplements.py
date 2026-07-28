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


def _fnum(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


# ---- coach view: the cost sheet (client view stays the reference cards) ----
if role == "coach":
    settings = cl.get_settings()
    cur = settings["currency"]
    ui.hero(t("scc_title"), t("scc_sub"), kicker=t("scc_kicker"))

    def _save_currency():
        cl.save_settings({"currency": (st.session_state.get("sup_cur")
                                       or "S/").strip() or "S/"})

    SUP_COLS = [
        {"field": "name", "label": t("sc_supplement"), "width": 1.5,
         "ph": "e.g. Creatina"},
        {"field": "brand", "label": t("scc_brand"), "width": 1.0},
        {"field": "qty", "label": t("scc_qty"), "width": 0.5, "mono": True},
        {"field": "daily", "label": t("scc_daily"), "width": 0.5, "mono": True},
        {"field": "price", "label": t("scc_price"), "width": 0.6, "mono": True},
    ]
    costs = settings["supp_costs"]
    names_db = [str(s["name"]).strip() for s in supps
                if str(s["name"]).strip()]
    initial = [{"name": n,
                **{f: str((costs.get(n) or {}).get(f, "") or "")
                   for f in ("brand", "qty", "daily", "price")}}
               for n in names_db]
    initial += [{"name": n,
                 **{f: str((costs.get(n) or {}).get(f, "") or "")
                    for f in ("brand", "qty", "daily", "price")}}
                for n in costs if n not in names_db]

    def _save_costs():
        rows_ = ui.read_table_rows("supcost", SUP_COLS, require="name")
        cl.save_settings({"supp_costs": {
            r["name"]: {f: r[f] for f in ("brand", "qty", "daily", "price")}
            for r in rows_}})
        st.session_state["sup_msg"] = t("scc_saved")

    if st.session_state.get("sup_msg"):
        st.success(st.session_state.pop("sup_msg"))

    with st.expander(t("scc_edit_costs")):
        st.text_input(t("scc_currency"), value=cur, key="sup_cur",
                      on_change=_save_currency, max_chars=4)
        ui.editable_table("supcost", SUP_COLS, initial,
                          add_label=t("scc_add"))
        st.button(t("scc_save"), key="supcost_save", type="primary",
                  on_click=_save_costs)

    rows = ui.read_table_rows("supcost", SUP_COLS, require="name")
    comp = []
    for r in rows:
        qty, daily, price = (_fnum(r["qty"]), _fnum(r["daily"]),
                             _fnum(r["price"]))
        lasts = (qty / daily) if qty and daily else None
        per = (price / qty) if price and qty else None
        cday = (price / lasts) if price and lasts else None
        comp.append({**r, "qty_n": qty, "daily_n": daily, "price_n": price,
                     "lasts": lasts, "per": per, "cday": cday})

    priced = [c for c in comp if c["price_n"]]
    total = sum(c["price_n"] for c in priced)
    cday_sum = sum(c["cday"] for c in comp if c["cday"])
    longest = max((c for c in comp if c["lasts"]),
                  key=lambda c: c["lasts"], default=None)
    best = min((c for c in comp if c["per"]),
               key=lambda c: c["per"], default=None)

    def _m(v, dec=2):
        return f"{v:,.{dec}f}" if v is not None else "—"

    st.markdown(
        '<div class="sc-band">'
        f'<div><div class="l">{t("scc_total")}</div>'
        f'<div class="v acc">{cur} {_m(total)}</div>'
        f'<div class="vs">{t("scc_priced", n=len(priced))}</div></div>'
        f'<div><div class="l">{t("scc_cpd")}</div>'
        f'<div class="v">{cur} {_m(cday_sum)}</div>'
        f'<div class="vs">{t("scc_month", cur=cur, n=_m(cday_sum * 30, 0))}</div></div>'
        f'<div><div class="l">{t("scc_longest")}</div>'
        f'<div class="v" style="font-size:19px">'
        f'{round(longest["lasts"]) if longest else "—"}'
        f'<small style="font-size:12px;color:var(--invert-muted)"> {t("scc_days")}</small></div>'
        f'<div class="vs">{_html.escape(longest["name"]) if longest else "—"}'
        '</div></div>'
        f'<div><div class="l">{t("scc_best")}</div>'
        f'<div class="v" style="font-size:19px">'
        f'{cur} {_m(best["per"]) if best else "—"}</div>'
        f'<div class="vs">{_html.escape(best["name"]) if best else "—"}'
        '</div></div></div>', unsafe_allow_html=True)

    ui.label(t("scc_label"))
    trs = []
    for c in comp:
        brand = str(c["brand"]).strip()
        brand_td = (f'<td class="brand">{_html.escape(brand)}</td>' if brand
                    else '<td class="brand none">—</td>')
        lasts_td = (f'{round(c["lasts"])} <small>{t("scc_days")}</small>'
                    if c["lasts"] else "—")
        trs.append(
            f'<tr><td class="sup">{_html.escape(c["name"])}</td>{brand_td}'
            f'<td class="num">{_m(c["qty_n"], 0)}</td>'
            f'<td class="num">{_m(c["daily_n"], 0)}</td>'
            f'<td class="num">{lasts_td}</td>'
            f'<td class="num price">'
            f'{cur + " " + _m(c["price_n"]) if c["price_n"] else "—"}</td>'
            f'<td class="num unit">'
            f'{cur + " " + _m(c["per"]) if c["per"] else "—"}</td></tr>')
    trs.append(
        f'<tr class="tot"><td class="lbl" colspan="5">{t("scc_total")}</td>'
        f'<td><span class="big">{cur} {_m(total)}</span></td><td></td></tr>')
    st.markdown(
        '<div class="sc-wrap"><div class="sc-gbar">'
        f'<span>{t("scc_bar")}</span>'
        f'<span class="mt">{t("scc_bar_sub")}</span></div>'
        '<div class="sc-scroll"><table class="sc-tbl"><thead><tr>'
        f'<th class="l">{t("sc_supplement")}</th>'
        f'<th class="l">{t("scc_brand")}</th><th>{t("scc_qty")}</th>'
        f'<th>{t("scc_daily")}</th><th>{t("scc_lasts")}</th>'
        f'<th>{t("scc_price")}</th><th>{t("scc_unit")}</th>'
        f'</tr></thead><tbody>{"".join(trs)}</tbody></table></div></div>',
        unsafe_allow_html=True)
    st.caption(t("scc_note"))
    st.stop()

# ---- client view: the same editorial grid as the coach — read-only, and
# never any pricing (Qty/Daily/Lasts/Price/Per-unit are coach-only) ----------
ui.hero(t("sc_title"), t("sc_sub", n=len(supps)), kicker=t("sc_kicker"))

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
        link = str(s.get("link", "") or "")
        buy_cell = "—"
        if link.startswith("http"):
            buy_cell = (f'<a class="buy" '
                        f'href="{_html.escape(link, quote=True)}" '
                        f'target="_blank" rel="noopener">{t("sc_buy_link")}</a>')
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
