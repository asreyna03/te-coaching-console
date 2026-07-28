import json
import sys
from datetime import date
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl
from i18n import t
# pandas + pdfexport (fpdf) are heavy and branch-specific — imported lazily
# in the coach section / PDF builder so the other branch never pays for them

ui.setup("Meal Planner", "✳")
role = ui.require_role("coach", "client")
active = ui.client_picker()
cats, lookup = cl.load_fooddb()
FOODS = cl.all_food_names(cats)
MEALS = ["Pre", "Intra", "Post", "Meal 1", "Meal 2", "Meal 3", "Meal 4", "Meal 5"]

# Instruction-bar defaults (coach-editable per client, version-stamped).
PLAN_INST_DEFAULTS = {
    "weighing": "Rice and meat weighed cooked, everything else raw",
    "sodium": "Sodium — ¼ tsp pink + ⅛ tsp low",
    "water": "Water — 1.5–2 gal daily",
}
CAT_PRETTY = {"Proteins": "Proteins", "Carbohydrates": "Carbohydrates",
              "Fats": "Fats", "FruitsVegetables": "Fruits / Veg",
              "DrinksCondiments": "Drinks / Cond", "Recipes": "Recipes"}


def _plan_inst(rec):
    inst = rec.get("plan_instructions") or {}
    return {k: (str(inst.get(k) or "").strip() or v)
            for k, v in PLAN_INST_DEFAULTS.items()}


def _e(x):
    import html
    return html.escape(str(x))


def _grid_row(r):
    """One plan row -> computed grid cells (Amount = serving × n-servings,
    macros from the food DB; foods gone from the DB degrade to dashes)."""
    food = str(r.get("Food", ""))
    try:
        amt = float(r.get("Amount") or 0)
    except (TypeError, ValueError):
        amt = 0.0
    item = lookup.get(food)
    if not item:
        return {"cat": "—", "food": food, "serv": "—", "n": "—",
                "amount": "—", "cal": 0.0, "p": 0.0, "f": 0.0, "c": 0.0,
                "ok": False}
    kind, qty, unit = cl.serving_info(item.get("serving", ""))
    servings = cl.servings_from_amount(item, amt)
    serv_lbl = (f"{qty:g} {unit}".strip() if kind in ("g", "ml")
                else (f"{qty:g} {unit}".strip() if unit else f"{qty:g} ×"))
    cal, p, f, c = cl.macros_for(lookup, food, servings)
    _cat = item.get("category", "")
    return {"cat": (t(f"cat_{_cat}") if _cat in CAT_PRETTY
                    else (_cat or "—")),
            "food": food, "serv": serv_lbl, "n": f"{round(servings, 2):g}",
            "amount": cl.amount_label(item, amt),
            "cal": cal, "p": p, "f": f, "c": c, "ok": True}


# ---- client view: the locked full-grid layout, read-only -------------------
if role == "client":
    rec = cl.get_client(active) if active else {}
    DAY_LABELS = {"Training day": "Training Day", "Rest day": "Non-Training Day"}
    has_any = active and any(
        (rec.get("meal_plans", {}).get(dt) or rec.get("targets", {}).get(dt))
        for dt in DAY_LABELS.values())
    if not has_any:
        ui.hero(f'{t("nav_my_plan")}.', t("mg_hero_sub"),
                kicker=t("mg_kicker"))
        ui.empty_state(t("mg_no_plan"), t("mg_no_plan_sub"),
                       kicker=t("nav_my_plan").upper())
        st.stop()

    tkey = f"myplan_day::{active}"
    if st.session_state.get(tkey) not in DAY_LABELS:
        st.session_state[tkey] = "Training day"
    sel_label = st.session_state[tkey]
    daytype = DAY_LABELS[sel_label]
    TAB_T = {"Training day": t("mg_tab_training"),
             "Rest day": t("mg_tab_rest")}

    bw = (rec.get("bodyweight") or "").strip()
    ui.hero(f"{TAB_T[sel_label]}.",
            " · ".join(x for x in (active, bw) if x), kicker=t("mg_kicker"))
    ui.allergy_bar(rec.get("allergies"))

    tgt = rec.get("targets", {}).get(daytype) or {}

    def _tv(key):
        try:
            return f"{int(float(tgt.get(key))):,}"
        except (TypeError, ValueError):
            return "—"

    st.markdown(
        '<div class="mg-targets">'
        f'<div><div class="l">{t("mg_targets_cal")}</div>'
        f'<div class="v acc">{_tv("cal")}</div></div>'
        f'<div><div class="l">{t("mg_proteina")}</div>'
        f'<div class="v">{_tv("protein")}<small> g</small></div></div>'
        f'<div><div class="l">{t("mg_grasas")}</div>'
        f'<div class="v">{_tv("fats")}<small> g</small></div></div>'
        f'<div><div class="l">{t("mg_carbos")}</div>'
        f'<div class="v">{_tv("carbs")}<small> g</small></div></div>'
        '</div>', unsafe_allow_html=True)

    inst = _plan_inst(rec)
    st.markdown(
        f'<div class="mg-inst"><div class="h">{_e(inst["weighing"])}</div>'
        f'<div class="r"><span>{_e(inst["sodium"])}</span>'
        f'<span>{_e(inst["water"])}</span></div></div>',
        unsafe_allow_html=True)

    ui.index_tabs(tkey, list(DAY_LABELS), numbered=False, labels=TAB_T)

    rows = rec.get("meal_plans", {}).get(daytype) or []
    if not rows:
        ui.empty_state(t("mg_empty_day"), t("mg_empty_day_sub"),
                       kicker=t("nav_my_plan").upper())
        st.stop()

    meal_order = ([m for m in MEALS
                   if any(str(r.get("Meal")) == m for r in rows)]
                  + [m for m in dict.fromkeys(str(r.get("Meal"))
                                              for r in rows)
                     if m not in MEALS])
    HEAD = (f'<thead><tr><th class="l">{t("mg_categoria")}</th>'
            f'<th class="l">{t("mg_alimento")}</th><th>{t("mg_racion")}</th>'
            f'<th>{t("mg_num_raciones")}</th><th>{t("mg_cantidad")}</th>'
            f'<th>{t("mg_cal")}</th><th>{t("mg_proteina")}</th>'
            f'<th>{t("mg_grasas")}</th><th>{t("mg_carbos")}</th>'
            '</tr></thead>')
    day_cal = day_p = day_f = day_c = 0.0
    for meal in meal_order:
        mrows = [_grid_row(r) for r in rows
                 if str(r.get("Meal")) == meal]
        m_cal = sum(x["cal"] for x in mrows)
        m_p = sum(x["p"] for x in mrows)
        m_f = sum(x["f"] for x in mrows)
        m_c = sum(x["c"] for x in mrows)
        day_cal += m_cal; day_p += m_p; day_f += m_f; day_c += m_c
        trs = []
        for x in mrows:
            trs.append(
                f'<tr><td class="cat">{_e(x["cat"])}</td>'
                f'<td class="food">{_e(x["food"])}</td>'
                f'<td class="q">{_e(x["serv"])}</td>'
                f'<td class="q">{_e(x["n"])}</td>'
                f'<td class="q">{_e(x["amount"])}</td>'
                f'<td class="num cal">{round(x["cal"])}</td>'
                f'<td class="num">{x["p"]:.1f}</td>'
                f'<td class="num">{x["f"]:.1f}</td>'
                f'<td class="num">{x["c"]:.1f}</td></tr>')
        trs.append(
            f'<tr class="tot"><td class="lbl" colspan="5">'
            f'{_e(t("mg_meal_totals", meal=meal))}'
            f'</td><td>{round(m_cal)}</td><td>{m_p:.1f}</td>'
            f'<td>{m_f:.1f}</td><td>{m_c:.1f}</td></tr>')
        st.markdown(
            f'<div class="mg-mealwrap"><div class="mg-mbar">'
            f'<span>{_e(meal)}</span>'
            f'<span class="mt">{round(m_cal)} cal · P{m_p:.1f} · '
            f'F{m_f:.1f} · C{m_c:.1f}</span></div>'
            f'<div class="mg-scroll"><table class="mg-tbl">{HEAD}'
            f'<tbody>{"".join(trs)}</tbody></table></div></div>',
            unsafe_allow_html=True)

    tgt_cal = None
    try:
        tgt_cal = float(tgt.get("cal"))
    except (TypeError, ValueError):
        pass
    if tgt_cal:
        diff = day_cal - tgt_cal
        ok_txt = (t("mg_on_target") if abs(diff) <= tgt_cal * 0.03 else
                  t("mg_over" if diff > 0 else "mg_under",
                    n=abs(round(diff))))
    else:
        ok_txt = ""
    st.markdown(
        f'<div class="mg-daytot"><span>{t("mg_total_dia").upper()} &nbsp;'
        f'<b>{round(day_cal)}</b> cal &nbsp;·&nbsp; '
        f'P <b>{day_p:.0f}</b> · F <b>{day_f:.0f}</b> · '
        f'C <b>{day_c:.0f}</b></span>'
        f'<span class="ok">{_e(ok_txt)}</span></div>',
        unsafe_allow_html=True)

    # ---- shopping list — collapsed on screen; the PDF always prints it
    # in full (it builds from cl.shopping_list directly, never UI state)
    shopping = cl.shopping_list(active)
    if shopping:
        ui.label(t("mg_shopping").upper())
        with st.expander(t("mg_shopping"), expanded=False):
            st.caption(t("mg_shopping_cap"))
            iso = date.today().isocalendar()
            wkid = f"{iso[0]}-{iso[1]}"
            for cat, items in shopping.items():
                cat_lbl = (t(f"cat_{cat}") if cat in CAT_PRETTY else cat)
                st.markdown('<div class="mono acc" '
                            'style="margin:10px 0 2px">'
                            f'[ {_e(cat_lbl.upper())} ]'
                            '</div>', unsafe_allow_html=True)
                for it in items:
                    st.checkbox(f'{it["food"]} — {it["label"]}',
                                key=f"sl::{active}::{wkid}::{it['food']}")

    # ---- PDF bundle (plan + training + shopping list) -------------------
    # Building the PDF on every rerun is the page's single dearest step, so
    # it's cached against a fingerprint of everything that prints: a saved
    # change makes a new fingerprint -> fresh build; otherwise it's instant.
    @st.cache_data(ttl=600, show_spinner=False)
    def _plan_pdf(name, fingerprint):
        import pdfexport
        return pdfexport.build_plan_pdf(name)

    _fp = json.dumps(
        [rec.get(k) for k in ("meal_plans", "targets", "training",
                              "plan_instructions", "bodyweight")],
        sort_keys=True, default=str)
    pdf_bytes = _plan_pdf(active, _fp)
    if pdf_bytes:
        st.download_button(
            t("mg_pdf"), data=pdf_bytes,
            file_name=f"TE_{active.replace(' ', '_')}_plan.pdf",
            mime="application/pdf", key=f"pdf_dl::{active}")
    else:
        st.caption(t("mg_pdf_na"))
    st.stop()

import pandas as pd   # coach-only from here down (client branch st.stop()s)

ui.hero(f'{t("nav_meal")}.', t("cp_sub"), kicker=t("cp_kicker"))

if not active:
    ui.empty_state(t("co_no_client"), t("cp_no_client_sub"),
                   kicker=t("nav_meal").upper())
    st.stop()

rec = cl.get_client(active)
daytype = ui.index_tabs(f"mp_day::{active}",
                        ["Training Day", "Non-Training Day"],
                        numbered=False,
                        labels={"Training Day": t("dia_entreno"),
                                "Non-Training Day": t("dia_no_entreno")})
plan_key = f"meal::{active}::{daytype}"

# Keep drafts alive: Streamlit drops widget state for widgets that skip a run
# (e.g. flipping day type unmounts the other day's inputs). Re-asserting the
# keys of the non-rendered scopes preserves unsaved edits until Save/Reset.
for _k in list(st.session_state.keys()):
    _ks = str(_k)
    if _ks.startswith("meal::") and not _ks.startswith(plan_key):
        st.session_state[_k] = st.session_state[_k]

# ---- saved plan, grouped by meal (back-compat with old {Meal,Food,Servings}) ----
saved_rows = rec.get("meal_plans", {}).get(daytype) or []
saved_by_meal = {}
_missing_foods = []
for r in saved_rows:
    food = str(r.get("Food") or "").strip()
    if not food:
        continue
    if food not in lookup:
        _missing_foods.append(food)
        continue
    saved_by_meal.setdefault(r.get("Meal") or "Meal 1", []).append(r)


def _row_amount(r, food):
    """Amount for one saved row, converting old Servings-only rows."""
    if r.get("Amount") not in (None, ""):
        return cl._f(r["Amount"])
    sv = (cl._f(r.get("Servings"))
          if r.get("Servings") not in (None, "") else 1.0)
    kind, qty, _ = cl.serving_info(lookup[food].get("serving", ""))
    return sv * qty if kind in ("g", "ml") else sv


def _saved_amount(meal, food):
    """Previous amount for this food in this meal; duplicates are summed so
    old plans with the same food twice in one meal keep their true total."""
    matches = [r for r in saved_by_meal.get(meal, [])
               if str(r.get("Food")) == food]
    if not matches:
        return None
    return sum(_row_amount(r, food) for r in matches)


# ---- targets (keyed per client+daytype so edits never leak across records) ----
ui.allergy_bar(rec.get("allergies"))
ui.label(t("cp_daily_targets"))
tgt = rec.get("targets", {}).get(daytype, {})
d = 2500 if daytype == "Training Day" else 2200
t1, t2, t3, t4 = st.columns(4)
t_cal = t1.number_input(t("cp_calories"), 0, value=int(tgt.get("cal", d)),
                        step=10, key=f"{plan_key}::t::cal")
t_pro = t2.number_input(t("cp_protein_g"), 0,
                        value=int(tgt.get("protein", 200)),
                        step=5, key=f"{plan_key}::t::protein")
t_fat = t3.number_input(t("cp_fats_g"), 0, value=int(tgt.get("fats", 60)),
                        step=5, key=f"{plan_key}::t::fats")
t_carb = t4.number_input(t("cp_carbs_g"), 0,
                         value=int(tgt.get("carbs", 280)),
                         step=5, key=f"{plan_key}::t::carbs")


def _save_instructions():
    cl.upsert_client(active, {"plan_instructions": {
        "version": 1,
        "weighing": (st.session_state.get(f"pi::{active}::weighing")
                     or "").strip(),
        "sodium": (st.session_state.get(f"pi::{active}::sodium")
                   or "").strip(),
        "water": (st.session_state.get(f"pi::{active}::water")
                  or "").strip(),
    }})
    st.toast(t("cp_inst_saved"))


with st.expander(t("cp_inst_expander")):
    _cur_inst = _plan_inst(rec)
    st.text_input(t("cp_inst_weighing"), value=_cur_inst["weighing"],
                  key=f"pi::{active}::weighing")
    c_i1, c_i2 = st.columns(2)
    c_i1.text_input(t("cp_inst_sodium"), value=_cur_inst["sodium"],
                    key=f"pi::{active}::sodium")
    c_i2.text_input(t("cp_inst_water"), value=_cur_inst["water"],
                    key=f"pi::{active}::water")
    st.button(t("cp_inst_save"), key=f"pi_save::{active}",
              on_click=_save_instructions)

if _missing_foods:
    st.caption(t("cp_missing") + ", ".join(sorted(set(_missing_foods))))

# ---- meals in this day ----
ui.label(t("cp_meals_label"))
meal_options = MEALS + [m for m in saved_by_meal if m not in MEALS]
default_meals = [m for m in meal_options if m in saved_by_meal] or ["Meal 1"]
with st.container(key="mp_meals_box"):     # CSS hook: bigger meal chips
    meals_sel = st.multiselect("Meals", meal_options, default=default_meals,
                               key=f"{plan_key}::meals",
                               label_visibility="collapsed")

# ---- per-meal builders ----
rows = []
for meal in [m for m in meal_options if m in meals_sel]:
    st.markdown(f'<div class="mp-meal-h"><span class="br">[</span> '
                f'{meal.upper()} <span class="br">]</span></div>',
                unsafe_allow_html=True)
    prev_foods = list(dict.fromkeys(
        str(r.get("Food")) for r in saved_by_meal.get(meal, [])))
    sel = st.multiselect(f"Foods in {meal}", FOODS, default=prev_foods,
                         key=f"{plan_key}::{meal}::foods",
                         placeholder=t("cp_add_foods_ph"),
                         label_visibility="collapsed")

    m_cal = m_pro = m_fat = m_carb = 0.0
    for food in sel:
        item = lookup[food]
        kind, qty, unit = cl.serving_info(item.get("serving", ""))
        prev_amt = _saved_amount(meal, food)
        start = float(prev_amt) if prev_amt is not None else cl.default_amount(item)
        c1, c2, c3 = st.columns([5, 2, 4])
        amt = c2.number_input(
            {"g": "grams", "ml": "ml"}.get(kind, "quantity"),
            min_value=0.0, value=float(start),
            step=5.0 if kind in ("g", "ml") else 0.5,
            key=f"{plan_key}::{meal}::{food}::amt",
            format="%g", label_visibility="collapsed")
        servings = cl.servings_from_amount(item, amt)
        cal, pro, fat, carb = cl.macros_for(lookup, food, servings)
        c1.markdown(f'**{food}** <span class="mono acc">'
                    f'{cl.amount_label(item, amt)}</span>',
                    unsafe_allow_html=True)
        c3.caption(f"{round(cal)} cal · P {pro:.1f} · F {fat:.1f} · C {carb:.1f}")
        rows.append({"Meal": meal, "Food": food, "Amount": amt,
                     "Servings": round(servings, 4),
                     "Label": f"{food} {cl.amount_label(item, amt)}",
                     "Cal": round(cal), "Protein": round(pro, 1),
                     "Fats": round(fat, 1), "Carbs": round(carb, 1)})
        m_cal += cal; m_pro += pro; m_fat += fat; m_carb += carb
    if sel:
        st.caption(f"**{t('cp_subtotal', meal=meal)}** — {round(m_cal)} cal "
                   f"· P {m_pro:.1f} · F {m_fat:.1f} · C {m_carb:.1f}")
    else:
        st.caption(t("cp_no_foods"))

res = pd.DataFrame(rows)

# ---- day totals vs target ----
tc = int(res["Cal"].sum()) if not res.empty else 0
tp = round(res["Protein"].sum(), 1) if not res.empty else 0
tf = round(res["Fats"].sum(), 1) if not res.empty else 0
tk = round(res["Carbs"].sum(), 1) if not res.empty else 0

ui.label(t("cp_totals_label"))
m1, m2, m3, m4 = st.columns(4)
# delta_color="off": "left" is a remaining amount, not a trend — keep it neutral
# rather than let Streamlit paint a misleading green up-arrow. Over/under target
# is shown honestly by the progress bar below.
m1.metric(t("cp_calories"), f"{tc} / {t_cal}",
          t("cp_left", n=t_cal - tc), delta_color="off")
m2.metric(t("cp_protein"), f"{tp:g} / {t_pro}g",
          t("cp_left", n=f"{round(t_pro - tp, 1):g}"), delta_color="off")
m3.metric(t("cp_fats"), f"{tf:g} / {t_fat}g",
          t("cp_left", n=f"{round(t_fat - tf, 1):g}"), delta_color="off")
m4.metric(t("cp_carbs"), f"{tk:g} / {t_carb}g",
          t("cp_left", n=f"{round(t_carb - tk, 1):g}"), delta_color="off")
if t_cal:
    st.progress(min(tc / t_cal, 1.0),
                text=t("mg_calorie_pct", p=round(100 * tc / t_cal)))

if tc > 0:
    pc, fc, cc = tp * 4, tf * 9, tk * 4
    st.caption(f"**{t('cp_split')}** — {t('cp_protein')} "
               f"{round(100*pc/tc)}%  ·  {t('cp_fats')} {round(100*fc/tc)}%"
               f"  ·  {t('cp_carbs')} {round(100*cc/tc)}%")

# ---- by-meal summary (foods with grams in parentheses) ----
if not res.empty:
    ui.label(t("cp_by_meal"))
    grp = (res.groupby("Meal", sort=False)
           .agg(Foods=("Label", lambda s: "  +  ".join(s)),
                Cal=("Cal", "sum"), Protein=("Protein", "sum"),
                Fats=("Fats", "sum"), Carbs=("Carbs", "sum"))
           .reset_index())
    st.dataframe(grp, width="stretch", hide_index=True)

# ---- save / reset ----
st.divider()
b1, b2, _ = st.columns([2, 2, 5])
if b1.button(t("cp_save_plan"), type="primary"):
    plan_rows = ([{"Meal": r["Meal"], "Food": r["Food"],
                   "Servings": r["Servings"], "Amount": r["Amount"]}
                  for r in rows]
                 or [{"Meal": "Meal 1", "Food": "", "Servings": 1.0}])
    mp = rec.get("meal_plans", {}); mp[daytype] = plan_rows
    tg = rec.get("targets", {})
    tg[daytype] = {"cal": t_cal, "protein": t_pro, "fats": t_fat, "carbs": t_carb}
    cl.upsert_client(active, {"meal_plans": mp, "targets": tg})
    st.toast(t("cp_saved_toast", daytype=t(
        "dia_entreno" if daytype == "Training Day" else "dia_no_entreno"),
        name=active))

if b2.button(t("cp_reset")):
    for k in [k for k in st.session_state if str(k).startswith(plan_key)]:
        del st.session_state[k]
    st.rerun()

with st.expander(t("cp_browse")):
    cat = st.selectbox(t("cp_category"), cl.FOOD_CATS,
                       format_func=lambda c: f"{cl.CAT_ICON[c]} {cl.CAT_LABEL[c]}")
    df = pd.DataFrame(cats[cat])[["name", "serving", "calories", "protein",
                                  "fats", "carbs"]]
    df.columns = ["Food", "Serving", "Cal", "Protein", "Fats", "Carbs"]
    st.dataframe(df, width="stretch", hide_index=True)
