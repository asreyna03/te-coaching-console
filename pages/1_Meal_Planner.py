import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import pandas as pd
import ui
import coachlib as cl

ui.setup("Meal Planner", "🍽")
active = ui.client_picker()
cats, lookup = cl.load_fooddb()
FOODS = cl.all_food_names(cats)
MEALS = ["Pre", "Intra", "Post", "Meal 1", "Meal 2", "Meal 3", "Meal 4", "Meal 5"]

ui.hero("Meal Planner.",
        "Build each meal from your database — several foods per meal, amounts "
        "in grams, macros totalling live against target.",
        kicker="NUTRITION")

if not active:
    st.info("👈 Pick or create a client in the sidebar first.")
    st.stop()

rec = cl.get_client(active)
daytype = st.radio("Day type", ["Training Day", "Non-Training Day"],
                   horizontal=True)
plan_key = f"meal::{active}::{daytype}"

# ---- saved plan, grouped by meal (back-compat with old {Meal,Food,Servings}) ----
saved_rows = rec.get("meal_plans", {}).get(daytype) or []
saved_by_meal = {}
for r in saved_rows:
    food = str(r.get("Food") or "").strip()
    if not food or food not in lookup:
        continue
    saved_by_meal.setdefault(r.get("Meal") or "Meal 1", []).append(r)


def _saved_amount(meal, food):
    """Previous amount for this food, whatever format it was saved in."""
    for r in saved_by_meal.get(meal, []):
        if str(r.get("Food")) == food:
            if r.get("Amount") not in (None, ""):
                return cl._f(r["Amount"])
            sv = cl._f(r.get("Servings", 1)) or 1.0
            kind, qty, _ = cl.serving_info(lookup[food].get("serving", ""))
            return sv * qty if kind in ("g", "ml") else sv
    return None


# ---- targets ----
ui.label("DAILY TARGETS")
tgt = rec.get("targets", {}).get(daytype, {})
d = 2500 if daytype == "Training Day" else 2200
t1, t2, t3, t4 = st.columns(4)
t_cal = t1.number_input("Calories", 0, value=int(tgt.get("cal", d)), step=10)
t_pro = t2.number_input("Protein (g)", 0, value=int(tgt.get("protein", 200)), step=5)
t_fat = t3.number_input("Fats (g)", 0, value=int(tgt.get("fats", 60)), step=5)
t_carb = t4.number_input("Carbs (g)", 0, value=int(tgt.get("carbs", 280)), step=5)

# ---- meals in this day ----
ui.label("MEALS IN THIS DAY")
meal_options = MEALS + [m for m in saved_by_meal if m not in MEALS]
default_meals = [m for m in meal_options if m in saved_by_meal] or ["Meal 1"]
meals_sel = st.multiselect("Meals", meal_options, default=default_meals,
                           key=f"{plan_key}::meals",
                           label_visibility="collapsed")

# ---- per-meal builders ----
rows = []
for meal in [m for m in meal_options if m in meals_sel]:
    st.markdown(f'<div class="mono ink" style="margin:18px 0 4px">'
                f'[ {meal.upper()} ]</div>', unsafe_allow_html=True)
    prev_foods = list(dict.fromkeys(
        str(r.get("Food")) for r in saved_by_meal.get(meal, [])))
    sel = st.multiselect(f"Foods in {meal}", FOODS, default=prev_foods,
                         key=f"{plan_key}::{meal}::foods",
                         placeholder="Add foods to this meal…",
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
        st.caption(f"**{meal} subtotal** — {round(m_cal)} cal · "
                   f"P {m_pro:.1f} · F {m_fat:.1f} · C {m_carb:.1f}")
    else:
        st.caption("No foods yet — pick some in the box above.")

res = pd.DataFrame(rows)

# ---- day totals vs target ----
tc = int(res["Cal"].sum()) if not res.empty else 0
tp = round(res["Protein"].sum(), 1) if not res.empty else 0
tf = round(res["Fats"].sum(), 1) if not res.empty else 0
tk = round(res["Carbs"].sum(), 1) if not res.empty else 0

ui.label("DAY TOTALS VS TARGET")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Calories", f"{tc} / {t_cal}", f"{t_cal - tc} left")
m2.metric("Protein", f"{tp:g} / {t_pro}g", f"{round(t_pro - tp, 1):g} left")
m3.metric("Fats", f"{tf:g} / {t_fat}g", f"{round(t_fat - tf, 1):g} left")
m4.metric("Carbs", f"{tk:g} / {t_carb}g", f"{round(t_carb - tk, 1):g} left")
if t_cal:
    st.progress(min(tc / t_cal, 1.0), text=f"{round(100*tc/t_cal)}% of calorie target")

if tc > 0:
    pc, fc, cc = tp * 4, tf * 9, tk * 4
    st.caption(f"**Calorie split** — 🥩 Protein {round(100*pc/tc)}%  ·  "
               f"🥑 Fats {round(100*fc/tc)}%  ·  🍚 Carbs {round(100*cc/tc)}%")

# ---- by-meal summary (foods with grams in parentheses) ----
if not res.empty:
    ui.label("BY MEAL")
    grp = (res.groupby("Meal", sort=False)
           .agg(Foods=("Label", lambda s: "  +  ".join(s)),
                Cal=("Cal", "sum"), Protein=("Protein", "sum"),
                Fats=("Fats", "sum"), Carbs=("Carbs", "sum"))
           .reset_index())
    st.dataframe(grp, width="stretch", hide_index=True)

# ---- save / reset ----
st.divider()
b1, b2, _ = st.columns([2, 2, 5])
if b1.button("💾 Save this plan to client", type="primary"):
    plan_rows = ([{"Meal": r["Meal"], "Food": r["Food"],
                   "Servings": r["Servings"], "Amount": r["Amount"]}
                  for r in rows]
                 or [{"Meal": "Meal 1", "Food": "", "Servings": 1.0}])
    mp = rec.get("meal_plans", {}); mp[daytype] = plan_rows
    tg = rec.get("targets", {})
    tg[daytype] = {"cal": t_cal, "protein": t_pro, "fats": t_fat, "carbs": t_carb}
    cl.upsert_client(active, {"meal_plans": mp, "targets": tg})
    st.toast(f"Saved {daytype} plan for {active} ✓")
    st.success(f"Saved {daytype} plan for {active}.")

if b2.button("↺ Reset to last saved"):
    for k in [k for k in st.session_state if str(k).startswith(plan_key)]:
        del st.session_state[k]
    st.rerun()

with st.expander("🔎 Browse the food database"):
    cat = st.selectbox("Category", cl.FOOD_CATS,
                       format_func=lambda c: f"{cl.CAT_ICON[c]} {cl.CAT_LABEL[c]}")
    df = pd.DataFrame(cats[cat])[["name", "serving", "calories", "protein",
                                  "fats", "carbs"]]
    df.columns = ["Food", "Serving", "Cal", "Protein", "Fats", "Carbs"]
    st.dataframe(df, width="stretch", hide_index=True)
