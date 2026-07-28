"""EN/ES strings for every piece of chrome in the console.

Rules (from the Phase-2 brief):
- Keys are semantic (peso_actual), never English-text-as-key.
- t() falls back lang -> en -> the key itself: never crashes, never blank.
- USER DATA is never routed through here — food, supplement and exercise
  names, cues, coach notes and plan instructions render exactly as typed.
- Storage keys ("Training Day", meal names, check-in question keys) never
  change; pages translate their *display* only (index_tabs labels=...).
"""
import streamlit as st

VERSION = 1

STRINGS = {
    "en": {
        # -- nav rail ------------------------------------------------------
        "nav_home": "Home",
        "nav_clients": "Clients",
        "nav_meal": "Meal Planner",
        "nav_weigh": "Weigh-ins",
        "nav_check": "Check-in",
        "nav_supp": "Supplements",
        "nav_train": "Training",
        "nav_apps": "Applications",
        "nav_my_train": "My Training",
        "nav_my_plan": "My Plan",
        # -- top bar -------------------------------------------------------
        "tb_switch_client": "SWITCH CLIENT",
        "tb_new_client_ph": "New client name…",
        "tb_create_client": "＋ Create client",
        "tb_no_clients": "No clients yet — add your first below.",
        "tb_no_client_sel": "No client selected",
        "tb_add_to_begin": "Add one to begin",
        "tb_client": "Client",
        "tb_active": "Active",
        "tb_help_coach": ("Pick a client to load their console — everything "
                          "on the page scopes to them."),
        "tb_help_client": ("Your console — everything here is yours alone. "
                           "Questions? Message your coach."),
        "tb_your_coach": "Your coach",
        "tb_coach": "Coach",
        "tb_client_account": "Client account",
        "tb_logout": "Log out",
        "tb_theme_help": "Theme: system / light / dark",
        "tb_active_client": "Active client",
        # -- client dashboard (app.py) ------------------------------------
        "td_kicker_week": "YOUR PROGRESS · WEEK {n}",
        "td_kicker": "YOUR PROGRESS",
        "td_hey": "Hey,",
        "td_goal": "GOAL",
        "td_coach": "COACH",
        "td_started": "STARTED",
        "td_streak": "⚡ {n}-WEEK LOGGING STREAK",
        "peso_actual": "Current weight",
        "meta_semana": "This week's target",
        "registros": "Weigh-ins logged",
        "checkin_semanal": "This week's check-in",
        "td_since_start": "since start",
        "td_protein_g": "{n}g protein",
        "td_up_to_date": "✓ up to date",
        "td_log_due": "log due",
        "td_done": "Done",
        "td_due": "Due",
        "td_do_it": "Do it →",
        "td_this_week_chk": "✓ this week",
        "td_weekly_avg": "WEEKLY AVG",
        "td_rate": "RATE",
        "td_steps7": "AVG STEPS 7D",
        "td_sleep7": "AVG SLEEP 7D",
        "td_where": "WHERE YOU'RE AT",
        "td_weight_trend": "Weight trend",
        "td_two_logs": "Log two weigh-ins and your trend draws itself here.",
        "td_this_week": "This week",
        "td_log_today": "Log today's weigh-in",
        "td_last": "Last: {w} lb · {d}d ago",
        "td_no_logs": "No logs yet",
        "td_log_btn": "Log",
        "td_weekly_checkin": "Weekly check-in",
        "td_ci_done": "Done for this week",
        "td_ci_due": "Due — takes ~3 min",
        "td_start_btn": "Start",
        "td_meal_plan": "Meal plan",
        "td_macros_set": "Training-day macros set",
        "td_not_set": "Not set yet",
        "td_view_btn": "View",
        "td_done_chip": "✓ done",
        "td_your_plan": "YOUR PLAN",
        "mi_plan": "My meal plan",
        "mi_plan_sub": "Your targets and meals for training &amp; rest days.",
        "mi_entreno": "My training",
        "mi_entreno_sub": "This block&rsquo;s workouts — sets, reps, and cues.",
        "mis_suplementos": "My supplements",
        "mis_suplementos_sub": "What to take, when, and why.",
        "abrir": "Open →",
        "abrir_a": "Open {x}",
        "td_note_from": "Note from {who}",
        "td_your_coach_lc": "your coach",
        "td_not_linked": "Account not linked",
        "td_not_linked_sub": ("Your login isn't linked to a client record "
                              "yet — message your coach."),
        "td_your_console": "YOUR CONSOLE",
        # -- shared day types / meals (display only; storage keys fixed) ---
        "dia_entreno": "Training Day",
        "dia_descanso": "Rest Day",
        "dia_no_entreno": "Non-Training Day",
        "comida": "Meal",
        # -- meal grid (client My Plan) ------------------------------------
        "mg_kicker": "YOUR PLAN",
        "mg_categoria": "Category",
        "mg_alimento": "Selection",
        "mg_racion": "Serving size",
        "mg_num_raciones": "No. of servings",
        "mg_cantidad": "Amount",
        "mg_cal": "Cal",
        "mg_proteina": "Protein",
        "mg_grasas": "Fats",
        "mg_carbos": "Carbs",
        "mg_total_dia": "Day total",
        "mg_en_plan": "on plan",
        "mg_targets_cal": "Calorie target",
        "mg_shopping": "Shopping list",
        "mg_shopping_sub": "everything on your plan, totalled for the week",
        "mg_pdf": "Download PDF",
        "mg_no_plan": "No plan yet",
        "mg_no_plan_sub": ("Your coach hasn't published a meal plan for you "
                           "yet — it'll appear here as soon as they do."),
        "mg_calorie_pct": "{p}% of calorie target",
        # -- weigh-ins -----------------------------------------------------
        "wi_kicker": "TRACKING",
        "wi_title": "Weigh-ins.",
        "wi_sub": ("Daily weight, steps and sleep — charted as a trend "
                   "that actually reads."),
        "wi_latest": "Latest",
        "wi_change": "Change since start",
        "wi_average": "Average",
        "wi_add_day": "＋ Add day",
        "wi_daily_log": "DAILY LOG",
        "wi_date": "Date",
        "wi_weight": "Weight (lbs)",
        "wi_steps": "Steps",
        "wi_sleep": "Sleep (hrs)",
        "wi_notes": "Notes",
        "wi_save": "Save log",
        "wi_saved": "Weigh-ins saved.",
        "wi_trend": "WEIGHT TREND",
        "wi_no_data": "No weigh-ins yet",
        "wi_no_data_sub": "Add your first day above and it charts here.",
        # -- check-in ------------------------------------------------------
        "ci_kicker": "ACCOUNTABILITY",
        "ci_title": "Check-in.",
        "ci_week": "Week",
        "ci_save": "Save check-in",
        "ci_saved": "Check-in saved.",
        # -- training (client) --------------------------------------------
        # -- supplements (client) -----------------------------------------
        "sc_kicker": "STACK",
        "sc_title": "Supplements.",
        "sc_sub": ("{n} supplements from your database — reason for use, "
                   "dose and timing, where to buy."),
        "sc_search_ph": "Filter by name or reason…",
        "sc_search": "Search",
        "sc_no_match": "No supplements match that search.",
        "sc_your_stack": "Your stack",
        "sc_grid_sub": "{n} supplements · reason · dose · where to buy",
        "sc_supplement": "Supplement",
        "sc_reason": "Reason",
        "sc_dose": "Dose / timing",
        "sc_essential_q": "Essential?",
        "sc_buy": "Buy",
        "sc_essential": "Essential",
        "sc_optional": "Optional",
        "sc_buy_link": "Buy →",
        # -- coach console (app.py) ---------------------------------------
        "co_kicker": "COACHING CONSOLE",
        "co_foods_db": "FOODS · DATABASE",
        "co_categories": "CATEGORIES",
        "co_supplements": "SUPPLEMENTS",
        "co_clients_on_file": "CLIENTS ON FILE",
        "co_active_client": "ACTIVE CLIENT",
        "co_started": "started {d}",
        "co_edit_info": "Edit client info",
        "co_name": "Client name",
        "co_start_date": "Start date",
        "co_email": "Email",
        "co_phone": "Phone",
        "co_age": "Age",
        "co_bodyweight": "Bodyweight",
        "co_stats": "Stats",
        "co_allergies": "Allergies (comma-separated — powers the red alerts)",
        "co_goals": "Goals",
        "co_coach_field": "Coach (shown on the client's dashboard)",
        "co_note_field": ("Note to client (their dashboard's dark block — "
                          "leave empty to hide it)"),
        "co_save_info": "Save client info",
        "co_saved": "Client info saved.",
        "co_renamed": "Saved — renamed to '{name}'.",
        "co_name_taken": ("There's already a client named '{name}' — pick a "
                          "different name."),
        "co_no_client": "No client selected",
        "co_no_client_sub": ("Pick or create a client in the sidebar to "
                             "begin — their details, targets and history "
                             "will show up here."),
        "co_whats_inside": "WHAT'S INSIDE",
        "pm_bodyweight": "Bodyweight",
        "pm_td_cal": "TD cal target",
        "pm_td_protein": "TD protein",
        "pm_weighins": "Weigh-ins",
        "pm_since_start": "{arrow} {n} lbs since start",
        "co_card_meal": ("Pick foods, set servings — calories &amp; macros "
                         "total live against target, training day or rest "
                         "day."),
        "co_card_weigh": ("Daily weight, steps &amp; sleep, charted as a "
                          "trend that actually reads at scale."),
        "co_card_check": ("The weekly check-in, prompt for prompt — "
                          "captured per week, per client."),
        "co_card_supp": ("{n} supplements. Reason for use, directions, "
                         "buy links. Searchable."),
        "co_card_train": ("Program builder — day tabs, sets, reps, RIR and "
                          "cues, duplicated to any client in a click."),
        "co_card_apps": ("Public apply form at /Apply, coach-only inbox "
                         "here. Review inbound leads and convert them "
                         "straight into your roster."),
        # -- meal planner: client grid extras ------------------------------
        "mg_hero_sub": "Your daily targets and meals, set by your coach.",
        "mg_tab_training": "Training day",
        "mg_tab_rest": "Rest day",
        "mg_empty_day": "Nothing on this day yet",
        "mg_empty_day_sub": ("Your coach hasn't built this day — flip the "
                             "toggle or check back soon."),
        "mg_meal_totals": "{meal} totals",
        "mg_on_target": "✓ on target",
        "mg_over": "{n} over target",
        "mg_under": "{n} under target",
        "mg_shopping_cap": ("Every food across your plan, added together — "
                            "covers one training + one rest day, so scale "
                            "to your week. Ticks reset each week."),
        "mg_pdf_na": ("PDF export isn't available here — no PDF engine "
                      "installed in this environment."),
        "cat_Proteins": "Proteins",
        "cat_Carbohydrates": "Carbohydrates",
        "cat_Fats": "Fats",
        "cat_FruitsVegetables": "Fruits / Veg",
        "cat_DrinksCondiments": "Drinks / Cond",
        "cat_Recipes": "Recipes",
        # -- meal planner: coach builder -----------------------------------
        "cp_sub": ("Build each meal from your database — several foods per "
                   "meal, amounts in grams, macros totalling live against "
                   "target."),
        "cp_kicker": "NUTRITION",
        "cp_no_client_sub": ("Pick or create a client in the sidebar to "
                             "start planning their meals."),
        "cp_daily_targets": "DAILY TARGETS",
        "cp_calories": "Calories",
        "cp_protein_g": "Protein (g)",
        "cp_fats_g": "Fats (g)",
        "cp_carbs_g": "Carbs (g)",
        "cp_inst_expander": ("Client-view instructions (the red bar on "
                             "their plan)"),
        "cp_inst_weighing": "Weighing note",
        "cp_inst_sodium": "Sodium",
        "cp_inst_water": "Water",
        "cp_inst_save": "Save instructions",
        "cp_inst_saved": "Client-view instructions saved.",
        "cp_missing": "Not in the food database anymore (excluded): ",
        "cp_meals_label": "MEALS IN THIS DAY",
        "cp_add_foods_ph": "Add foods to this meal…",
        "cp_subtotal": "{meal} subtotal",
        "cp_no_foods": "No foods yet — pick some in the box above.",
        "cp_totals_label": "DAY TOTALS VS TARGET",
        "cp_left": "{n} left",
        "cp_split": "Calorie split",
        "cp_protein": "Protein",
        "cp_fats": "Fats",
        "cp_carbs": "Carbs",
        "cp_by_meal": "BY MEAL",
        "cp_save_plan": "Save this plan to client",
        "cp_reset": "Reset to last saved",
        "cp_saved_toast": "Saved {daytype} plan for {name}",
        "cp_browse": "Browse the food database",
        "cp_category": "Category",
        # -- weigh-ins extras ----------------------------------------------
        "wi_no_client_sub": ("Pick or create a client in the sidebar to "
                             "log their weigh-ins."),
        "wi_no_trend": "No trend yet",
        "wi_no_trend_sub": ("Log at least two weigh-ins with a weight and "
                            "the trend chart will draw itself here."),
        "wi_save_btn": "Save log to client",
        "wi_saved_n": "Saved {n} entries for {name}.",
        # -- check-in extras -----------------------------------------------
        "ci_sub": ("The weekly check-in — prompt for prompt, captured per "
                   "week, per client."),
        "ci_no_client_sub": ("Pick or create a client in the sidebar to "
                             "run their weekly check-in."),
        "ci_week_num": "Week #",
        "ci_wavg": "Date — Weight Average",
        "ci_saved_wk": "Saved Week {w} check-in for {name}.",
        "ci_weeks_saved": "Weeks with saved check-ins: ",
        "ci_sec_training": "Training",
        "ci_sec_nutrition": "Nutrition & Body",
        "ci_sec_recovery": "Recovery & Lifestyle",
        "ci_sec_notes": "Week & Notes",
        # -- training: client view -----------------------------------------
        "tc_hero_sub": ("Your program lives here — day by day: exercises, "
                        "sets, reps and your coach's cues."),
        "tc_almost": "Almost ready",
        "tc_almost_sub": ("Your coach is putting your program together — "
                          "it shows up here the moment it's published."),
        "tc_day_title": "{day} day.",
        "tc_day_sub": "Today's session — tick each exercise off as you go.",
        "tc_kicker": "YOUR TRAINING · BLOCK {b}",
        "tc_week_of": "Week {w} of {t}",
        "tc_rest": "Rest day (for now)",
        "tc_rest_sub": ("Nothing programmed under this day yet — check the "
                        "other tabs or ask your coach."),
        "tc_watch": "Watch demo",
        "tc_progress": ("{done} of {n} done · {day} · Week {w} — progress "
                        "resets each week"),
        "tc_complete": "Workout complete ✓",
        "tc_mark": "Mark workout done",
        "tc_sets_word": "sets",
        "tc_reps_word": "reps",
        # -- training: coach builder ---------------------------------------
        "ct_sub": ("Build each day as a simple table — add exercises, set "
                   "the numbers, drop in a cue and a video. Reuse a whole "
                   "program on another client in one click."),
        "ct_kicker": "PROGRAMMING",
        "ct_no_client_sub": ("Pick or create a client in the top bar to "
                             "build their program."),
        "ct_day_name_req": "Give the new day a name.",
        "ct_day_exists": "There's already a day called “{name}”.",
        "ct_added": "Added day “{name}”.",
        "ct_renamed": "Renamed “{old}” to “{name}”.",
        "ct_need_one": "A program needs at least one day.",
        "ct_deleted": "Deleted “{name}”.",
        "ct_saved": ("Saved — {days} · Block {b}, Week {w} of {t}."),
        "ct_program_word": "program",
        "ct_copied": "Program copied to {name} — {n} days.",
        "ct_building": "BUILDING FOR",
        "ct_block_up": "BLOCK",
        "ct_week_up": "WEEK",
        "ct_of_up": "OF",
        "ct_block": "Block",
        "ct_week": "Week",
        "ct_weeks_total": "Weeks total",
        "ct_add_day": "＋ Add day",
        "ct_day_name": "Day name",
        "ct_tip": ("Tip: name a day “Cardio” and its table "
                   "relabels to Duration / Interval automatically."),
        "ct_add_day_btn": "Add day",
        "ct_manage": "Manage “{day}”",
        "ct_rename_to": "Rename to",
        "ct_rename_btn": "Rename day",
        "ct_delete_day": "Delete “{day}” and its exercises",
        "ct_exercises": "{day} — EXERCISES",
        "ct_add_ex": "＋ Add exercise",
        "ct_edits_note": ("Edits stick as you switch days — **Save "
                          "program** writes every edited day back to the "
                          "client."),
        "ct_save": "Save program",
        "ct_dup_label": "DUPLICATE PROGRAM",
        "ct_dup_none": ("Add another client and you can copy this whole "
                        "program onto them in one click."),
        "ct_dup_to": "Copy the saved program to",
        "ct_dup_btn": "Duplicate to client",
        "ct_dup_note": ("Copies what's saved — unsaved table edits aren't "
                        "included."),
        "ct_overwrite": ("**{name} already has a program.** Overwrite it "
                         "with {src}'s? This replaces all of their days "
                         "and exercises."),
        "ct_yes": "Yes, overwrite {name}'s program",
        "ct_cancel": "Cancel",
        "ct_col_exercise": "Exercise",
        "ct_col_sets": "Sets",
        "ct_col_reps": "Reps",
        "ct_col_rir": "RIR",
        "ct_col_cue": "Cue / notes",
        "ct_col_video": "Video",
        "ct_col_duration": "Duration",
        "ct_col_interval": "Interval",
        # -- supplements: coach cost sheet ---------------------------------
        "scc_title": "Your stack, costed.",
        "scc_sub": ("Every supplement with quantity, how long a tub lasts "
                    "at the daily dose, price, and price per serving."),
        "scc_kicker": "SUPPLEMENTS · COST",
        "scc_currency": "Currency symbol",
        "scc_edit_costs": "Edit costs (qty · daily dose · price · currency)",
        "scc_add": "＋ Add supplement",
        "scc_save": "Save costs",
        "scc_saved": "Costs saved.",
        "scc_total": "Total stack",
        "scc_cpd": "Cost per day",
        "scc_month": "≈ {cur} {n} / month",
        "scc_longest": "Longest lasting",
        "scc_best": "Best value / unit",
        "scc_days": "days",
        "scc_priced": "{n} priced",
        "scc_label": "COST BREAKDOWN",
        "scc_bar": "Supplement stack",
        "scc_bar_sub": "price · duration · per-serving",
        "scc_brand": "Brand",
        "scc_qty": "Qty",
        "scc_daily": "Daily",
        "scc_lasts": "Lasts",
        "scc_price": "Price",
        "scc_unit": "Per unit",
        "scc_note": ("Lasts = Qty ÷ Daily · Per unit = Price ÷ Qty · "
                     "Cost/day spreads each price over the days it lasts. "
                     "Clients never see pricing."),
        # -- clients sheet -------------------------------------------------
        "cs_sub": ("Your whole roster at a glance — click a row to open "
                   "someone's console."),
        "cs_name_req": "Give the client a name.",
        "cs_exists": "There's already a client named “{name}”.",
        "cs_created": "{name} created — fill in their details on Home.",
        "onb_creds": ("**{name}'s login — shown only this once.** Share it "
                      "with them now:\n\nusername `{u}` · temp password "
                      "`{p}`"),
        "cs_active": "ACTIVE CLIENTS",
        "cs_ci_due": "CHECK-INS DUE",
        "cs_to_build": "PROGRAMS TO BUILD",
        "cs_new_apps": "NEW APPLICATIONS",
        "cs_your_clients": "YOUR CLIENTS",
        "cs_new_client": "＋ New client",
        "cs_client_name": "Client name",
        "cs_create": "Create client",
        "cs_none": "No clients yet",
        "cs_none_sub": ("Create your first client, or convert an "
                        "application from the inbox."),
        "cs_bar": "Clients",
        "cs_bar_sub": "{n} active · click a row to open",
        "cs_col_client": "Client",
        "cs_col_goal": "Goal",
        "cs_col_week": "Week",
        "cs_col_weight": "Weight",
        "cs_col_weighins": "Weigh-ins",
        "cs_col_checkin": "Check-in",
        "cs_col_program": "Program",
        "cs_col_allergy": "Allergy",
        "cs_col_todo": "To-do",
        "cs_col_open": "Open",
        "cs_done": "Done",
        "cs_due": "Due",
        "cs_set": "Set",
        "cs_missing": "Missing",
        "cs_none_chip": "None",
        "cs_build": "Build program",
        "cs_checkin_todo": "Check-in",
        "cs_all_good": "All good",
        "cs_open_arrow": "Open →",
        # -- applications --------------------------------------------------
        "ap_sub": ("Inbound leads from the public apply form — review them "
                   "here, then one click converts the good ones straight "
                   "into clients."),
        "ap_kicker": "APPLICATIONS",
        "ap_new": "NEW",
        "ap_reviewed": "REVIEWED",
        "ap_converted": "CONVERTED",
        "ap_declined": "DECLINED",
        "ap_all": "All {n}",
        "ap_none": "No applications yet.",
        "ap_none_sub": ("Share your <b>/Apply</b> link with prospective "
                        "clients — their submissions land here for "
                        "review."),
        "ap_empty_kicker": "EMPTY INBOX",
        "ap_bucket_empty": "Nothing in this bucket.",
        "ap_bucket_sub": "Switch filters to see the rest.",
        "ap_no_name": ("This application has no name — can't create a "
                       "client."),
        "ap_now_client": "{name} is now a client — edit details on Home.",
        "ap_email": "Email",
        "ap_phone": "Phone",
        "ap_age": "Age",
        "ap_height": "Height",
        "ap_weight": "Current weight",
        "ap_days": "Trains (days/week)",
        "ap_goal": "PRIMARY GOAL",
        "ap_injuries": "INJURIES / LIMITATIONS",
        "ap_allergies": "FOOD ALLERGIES / INTOLERANCES",
        "ap_struggle": "BIGGEST STRUGGLE",
        "ap_coached": "COACHED BEFORE · READY TO INVEST",
        "ap_convert": "Convert to client →",
        "ap_review": "Mark reviewed",
        "ap_decline": "Decline",
        "ap_delete": "Delete",
    },
    "es": {
        # -- nav rail ------------------------------------------------------
        "nav_home": "Inicio",
        "nav_clients": "Clientes",
        "nav_meal": "Planificador",
        "nav_weigh": "Registros",
        "nav_check": "Check-in",
        "nav_supp": "Suplementos",
        "nav_train": "Entreno",
        "nav_apps": "Solicitudes",
        "nav_my_train": "Mi entreno",
        "nav_my_plan": "Mi plan",
        # -- top bar -------------------------------------------------------
        "tb_switch_client": "CAMBIAR CLIENTE",
        "tb_new_client_ph": "Nombre del cliente…",
        "tb_create_client": "＋ Crear cliente",
        "tb_no_clients": "Aún no hay clientes — crea el primero abajo.",
        "tb_no_client_sel": "Ningún cliente seleccionado",
        "tb_add_to_begin": "Crea uno para empezar",
        "tb_client": "Cliente",
        "tb_active": "Activo",
        "tb_help_coach": ("Elige un cliente para cargar su consola — toda "
                          "la página se ajusta a él."),
        "tb_help_client": ("Tu consola — todo lo que ves aquí es solo tuyo. "
                           "¿Dudas? Escríbele a tu coach."),
        "tb_your_coach": "Tu coach",
        "tb_coach": "Coach",
        "tb_client_account": "Cuenta de cliente",
        "tb_logout": "Cerrar sesión",
        "tb_theme_help": "Tema: sistema / claro / oscuro",
        "tb_active_client": "Cliente activo",
        # -- client dashboard ---------------------------------------------
        "td_kicker_week": "TU PROGRESO · SEMANA {n}",
        "td_kicker": "TU PROGRESO",
        "td_hey": "Hola,",
        "td_goal": "OBJETIVO",
        "td_coach": "COACH",
        "td_started": "INICIO",
        "td_streak": "⚡ RACHA DE {n} SEMANAS",
        "peso_actual": "Peso actual",
        "meta_semana": "Meta de la semana",
        "registros": "Registros",
        "checkin_semanal": "Check-in semanal",
        "td_since_start": "desde el inicio",
        "td_protein_g": "{n}g de proteína",
        "td_up_to_date": "✓ al día",
        "td_log_due": "registro pendiente",
        "td_done": "Hecho",
        "td_due": "Pendiente",
        "td_do_it": "Hazlo →",
        "td_this_week_chk": "✓ esta semana",
        "td_weekly_avg": "MEDIA SEMANAL",
        "td_rate": "RITMO",
        "td_steps7": "PASOS MEDIA 7D",
        "td_sleep7": "SUEÑO MEDIA 7D",
        "td_where": "DÓNDE ESTÁS",
        "td_weight_trend": "Tendencia de peso",
        "td_two_logs": "Registra dos pesajes y tu tendencia aparecerá aquí.",
        "td_this_week": "Esta semana",
        "td_log_today": "Registra tu peso de hoy",
        "td_last": "Último: {w} lb · hace {d}d",
        "td_no_logs": "Sin registros aún",
        "td_log_btn": "Registrar",
        "td_weekly_checkin": "Check-in semanal",
        "td_ci_done": "Hecho esta semana",
        "td_ci_due": "Pendiente — toma ~3 min",
        "td_start_btn": "Empezar",
        "td_meal_plan": "Plan de comidas",
        "td_macros_set": "Macros de día de entreno listos",
        "td_not_set": "Aún sin definir",
        "td_view_btn": "Ver",
        "td_done_chip": "✓ hecho",
        "td_your_plan": "TU PLAN",
        "mi_plan": "Mi plan",
        "mi_plan_sub": "Tus metas y comidas para días de entreno y descanso.",
        "mi_entreno": "Mi entreno",
        "mi_entreno_sub": "Los entrenos de este bloque — series, reps y "
                          "técnica.",
        "mis_suplementos": "Mis suplementos",
        "mis_suplementos_sub": "Qué tomar, cuándo y por qué.",
        "abrir": "Abrir →",
        "abrir_a": "Abrir {x}",
        "td_note_from": "Nota de {who}",
        "td_your_coach_lc": "tu coach",
        "td_not_linked": "Cuenta sin vincular",
        "td_not_linked_sub": ("Tu acceso aún no está vinculado a una ficha "
                              "de cliente — escríbele a tu coach."),
        "td_your_console": "TU CONSOLA",
        # -- day types / meals --------------------------------------------
        "dia_entreno": "Día de entreno",
        "dia_descanso": "Día de descanso",
        "dia_no_entreno": "Día de descanso",
        "comida": "Comida",
        # -- meal grid -----------------------------------------------------
        "mg_kicker": "TU PLAN",
        "mg_categoria": "Categoría",
        "mg_alimento": "Alimento",
        "mg_racion": "Ración",
        "mg_num_raciones": "N.º de raciones",
        "mg_cantidad": "Cantidad",
        "mg_cal": "Cal",
        "mg_proteina": "Proteína",
        "mg_grasas": "Grasas",
        "mg_carbos": "Carbos",
        "mg_total_dia": "Total del día",
        "mg_en_plan": "en plan",
        "mg_targets_cal": "Meta de calorías",
        "mg_shopping": "Lista de la compra",
        "mg_shopping_sub": "todo tu plan, sumado para la semana",
        "mg_pdf": "⤓ Descargar plan (PDF)",
        "mg_no_plan": "Aún no hay plan",
        "mg_no_plan_sub": ("Tu coach todavía no ha publicado tu plan de "
                           "comidas — vuelve pronto."),
        "mg_calorie_pct": "{p}% de la meta de calorías",
        # -- weigh-ins -----------------------------------------------------
        "wi_kicker": "SEGUIMIENTO",
        "wi_title": "Registros.",
        "wi_sub": ("Peso diario, pasos y sueño — en una tendencia que "
                   "de verdad se lee."),
        "wi_latest": "Último",
        "wi_change": "Cambio desde el inicio",
        "wi_average": "Media",
        "wi_add_day": "＋ Añadir día",
        "wi_daily_log": "REGISTRO DIARIO",
        "wi_date": "Fecha",
        "wi_weight": "Peso (lbs)",
        "wi_steps": "Pasos",
        "wi_sleep": "Sueño (hrs)",
        "wi_notes": "Notas",
        "wi_save": "Guardar registro",
        "wi_saved": "Registros guardados.",
        "wi_trend": "TENDENCIA DE PESO",
        "wi_no_data": "Aún no hay registros",
        "wi_no_data_sub": "Añade tu primer día arriba y aparecerá aquí.",
        # -- check-in ------------------------------------------------------
        "ci_kicker": "COMPROMISO",
        "ci_title": "Check-in.",
        "ci_week": "Semana",
        "ci_save": "Guardar check-in",
        "ci_saved": "Check-in guardado.",
        # -- training (client) --------------------------------------------
        # -- supplements (client) -----------------------------------------
        "sc_kicker": "STACK",
        "sc_title": "Suplementos.",
        "sc_sub": ("{n} suplementos de tu base de datos — motivo de uso, "
                   "dosis y horario, dónde comprar."),
        "sc_search_ph": "Filtra por nombre o motivo…",
        "sc_search": "Buscar",
        "sc_no_match": "Ningún suplemento coincide con esa búsqueda.",
        "sc_your_stack": "Tu stack",
        "sc_grid_sub": "{n} suplementos · motivo · dosis · dónde comprar",
        "sc_supplement": "Suplemento",
        "sc_reason": "Motivo",
        "sc_dose": "Dosis / horario",
        "sc_essential_q": "¿Esencial?",
        "sc_buy": "Comprar",
        "sc_essential": "Esencial",
        "sc_optional": "Opcional",
        "sc_buy_link": "Comprar →",
        # -- coach console -------------------------------------------------
        "co_kicker": "CONSOLA DE COACHING",
        "co_foods_db": "ALIMENTOS · BASE DE DATOS",
        "co_categories": "CATEGORÍAS",
        "co_supplements": "SUPLEMENTOS",
        "co_clients_on_file": "CLIENTES REGISTRADOS",
        "co_active_client": "CLIENTE ACTIVO",
        "co_started": "inicio {d}",
        "co_edit_info": "Editar ficha del cliente",
        "co_name": "Nombre del cliente",
        "co_start_date": "Fecha de inicio",
        "co_email": "Email",
        "co_phone": "Teléfono",
        "co_age": "Edad",
        "co_bodyweight": "Peso corporal",
        "co_stats": "Medidas",
        "co_allergies": ("Alergias (separadas por comas — activan las "
                         "alertas rojas)"),
        "co_goals": "Objetivos",
        "co_coach_field": "Coach (se muestra en el panel del cliente)",
        "co_note_field": ("Nota para el cliente (el bloque oscuro de su "
                          "panel — déjalo vacío para ocultarlo)"),
        "co_save_info": "Guardar ficha",
        "co_saved": "Ficha guardada.",
        "co_renamed": "Guardado — renombrado a '{name}'.",
        "co_name_taken": ("Ya existe un cliente llamado '{name}' — elige "
                          "otro nombre."),
        "co_no_client": "Ningún cliente seleccionado",
        "co_no_client_sub": ("Elige o crea un cliente en la barra lateral "
                             "para empezar — sus datos, metas e historial "
                             "aparecerán aquí."),
        "co_whats_inside": "QUÉ HAY DENTRO",
        "pm_bodyweight": "Peso corporal",
        "pm_td_cal": "Meta cal DE",
        "pm_td_protein": "Proteína DE",
        "pm_weighins": "Registros",
        "pm_since_start": "{arrow} {n} lbs desde el inicio",
        "co_card_meal": ("Elige alimentos y raciones — calorías y macros "
                         "suman en vivo contra la meta, día de entreno o "
                         "descanso."),
        "co_card_weigh": ("Peso diario, pasos y sueño, en una tendencia "
                          "que de verdad se lee a escala."),
        "co_card_check": ("El check-in semanal, pregunta a pregunta — "
                          "guardado por semana y por cliente."),
        "co_card_supp": ("{n} suplementos. Motivo de uso, indicaciones, "
                         "enlaces de compra. Con buscador."),
        "co_card_train": ("Creador de programas — días en pestañas, series, "
                          "reps, RIR y técnica, duplicado a cualquier "
                          "cliente en un clic."),
        "co_card_apps": ("Formulario público en /Apply, bandeja solo para "
                         "coaches aquí. Revisa solicitudes y conviértelas "
                         "directo en clientes."),
        # -- meal planner: client grid extras ------------------------------
        "mg_hero_sub": "Tus metas diarias y comidas, definidas por tu coach.",
        "mg_tab_training": "Día de entreno",
        "mg_tab_rest": "Día de descanso",
        "mg_empty_day": "Aún no hay nada en este día",
        "mg_empty_day_sub": ("Tu coach todavía no ha armado este día — "
                             "cambia de pestaña o vuelve pronto."),
        "mg_meal_totals": "Totales {meal}",
        "mg_on_target": "✓ en meta",
        "mg_over": "{n} por encima de la meta",
        "mg_under": "{n} por debajo de la meta",
        "mg_shopping_cap": ("Cada alimento de tu plan, sumado — cubre un "
                            "día de entreno + uno de descanso, escálalo a "
                            "tu semana. Las marcas se reinician cada "
                            "semana."),
        "mg_pdf_na": ("La exportación a PDF no está disponible aquí — no "
                      "hay motor de PDF instalado."),
        "cat_Proteins": "Proteínas",
        "cat_Carbohydrates": "Carbohidratos",
        "cat_Fats": "Grasas",
        "cat_FruitsVegetables": "Frutas / Verd",
        "cat_DrinksCondiments": "Bebidas / Cond",
        "cat_Recipes": "Recetas",
        # -- meal planner: coach builder -----------------------------------
        "cp_sub": ("Arma cada comida desde tu base de datos — varios "
                   "alimentos por comida, cantidades en gramos, macros "
                   "sumando en vivo contra la meta."),
        "cp_kicker": "NUTRICIÓN",
        "cp_no_client_sub": ("Elige o crea un cliente en la barra lateral "
                             "para planificar sus comidas."),
        "cp_daily_targets": "METAS DIARIAS",
        "cp_calories": "Calorías",
        "cp_protein_g": "Proteína (g)",
        "cp_fats_g": "Grasas (g)",
        "cp_carbs_g": "Carbos (g)",
        "cp_inst_expander": ("Instrucciones para el cliente (la barra roja "
                             "de su plan)"),
        "cp_inst_weighing": "Nota de pesaje",
        "cp_inst_sodium": "Sodio",
        "cp_inst_water": "Agua",
        "cp_inst_save": "Guardar instrucciones",
        "cp_inst_saved": "Instrucciones guardadas.",
        "cp_missing": "Ya no están en la base de datos (excluidos): ",
        "cp_meals_label": "COMIDAS DE ESTE DÍA",
        "cp_add_foods_ph": "Añade alimentos a esta comida…",
        "cp_subtotal": "Subtotal {meal}",
        "cp_no_foods": "Sin alimentos aún — elige algunos arriba.",
        "cp_totals_label": "TOTALES DEL DÍA VS META",
        "cp_left": "quedan {n}",
        "cp_split": "Reparto calórico",
        "cp_protein": "Proteína",
        "cp_fats": "Grasas",
        "cp_carbs": "Carbos",
        "cp_by_meal": "POR COMIDA",
        "cp_save_plan": "Guardar este plan al cliente",
        "cp_reset": "Volver a lo guardado",
        "cp_saved_toast": "Plan de {daytype} guardado para {name}",
        "cp_browse": "Explorar la base de alimentos",
        "cp_category": "Categoría",
        # -- weigh-ins extras ----------------------------------------------
        "wi_no_client_sub": ("Elige o crea un cliente en la barra lateral "
                             "para registrar sus pesajes."),
        "wi_no_trend": "Aún no hay tendencia",
        "wi_no_trend_sub": ("Registra al menos dos pesajes con peso y la "
                            "gráfica aparecerá aquí."),
        "wi_save_btn": "Guardar registro al cliente",
        "wi_saved_n": "{n} entradas guardadas para {name}.",
        # -- check-in extras -----------------------------------------------
        "ci_sub": ("El check-in semanal — pregunta a pregunta, guardado "
                   "por semana y por cliente."),
        "ci_no_client_sub": ("Elige o crea un cliente en la barra lateral "
                             "para hacer su check-in semanal."),
        "ci_week_num": "Semana n.º",
        "ci_wavg": "Fecha — Peso promedio",
        "ci_saved_wk": "Check-in de la semana {w} guardado para {name}.",
        "ci_weeks_saved": "Semanas con check-in guardado: ",
        "ci_sec_training": "Entreno",
        "ci_sec_nutrition": "Nutrición y cuerpo",
        "ci_sec_recovery": "Recuperación y estilo de vida",
        "ci_sec_notes": "Semana y notas",
        # -- training: client view -----------------------------------------
        "tc_hero_sub": ("Tu programa vive aquí — día a día: ejercicios, "
                        "series, reps y las notas de tu coach."),
        "tc_almost": "Casi listo",
        "tc_almost_sub": ("Tu coach está armando tu programa — aparecerá "
                          "aquí en cuanto lo publique."),
        "tc_day_title": "Día de {day}.",
        "tc_day_sub": "La sesión de hoy — marca cada ejercicio al terminar.",
        "tc_kicker": "TU ENTRENO · BLOQUE {b}",
        "tc_week_of": "Semana {w} de {t}",
        "tc_rest": "Día de descanso (por ahora)",
        "tc_rest_sub": ("Nada programado en este día todavía — revisa las "
                        "otras pestañas o pregúntale a tu coach."),
        "tc_watch": "Ver demo",
        "tc_progress": ("{done} de {n} hechos · {day} · Semana {w} — el "
                        "progreso se reinicia cada semana"),
        "tc_complete": "Entreno completado ✓",
        "tc_mark": "Marcar entreno hecho",
        "tc_sets_word": "series",
        "tc_reps_word": "reps",
        # -- training: coach builder ---------------------------------------
        "ct_sub": ("Arma cada día como una tabla simple — añade "
                   "ejercicios, pon los números, suma una nota y un "
                   "video. Reutiliza un programa completo en otro cliente "
                   "con un clic."),
        "ct_kicker": "PROGRAMACIÓN",
        "ct_no_client_sub": ("Elige o crea un cliente en la barra superior "
                             "para armar su programa."),
        "ct_day_name_req": "Ponle nombre al nuevo día.",
        "ct_day_exists": "Ya existe un día llamado “{name}”.",
        "ct_added": "Día “{name}” añadido.",
        "ct_renamed": "“{old}” renombrado a “{name}”.",
        "ct_need_one": "Un programa necesita al menos un día.",
        "ct_deleted": "“{name}” eliminado.",
        "ct_saved": ("Guardado — {days} · Bloque {b}, semana {w} de {t}."),
        "ct_program_word": "programa",
        "ct_copied": "Programa copiado a {name} — {n} días.",
        "ct_building": "ARMANDO PARA",
        "ct_block_up": "BLOQUE",
        "ct_week_up": "SEMANA",
        "ct_of_up": "DE",
        "ct_block": "Bloque",
        "ct_week": "Semana",
        "ct_weeks_total": "Semanas totales",
        "ct_add_day": "＋ Añadir día",
        "ct_day_name": "Nombre del día",
        "ct_tip": ("Tip: llama a un día “Cardio” y su tabla cambia a "
                   "Duración / Intervalo automáticamente."),
        "ct_add_day_btn": "Añadir día",
        "ct_manage": "Gestionar “{day}”",
        "ct_rename_to": "Renombrar a",
        "ct_rename_btn": "Renombrar día",
        "ct_delete_day": "Eliminar “{day}” y sus ejercicios",
        "ct_exercises": "{day} — EJERCICIOS",
        "ct_add_ex": "＋ Añadir ejercicio",
        "ct_edits_note": ("Los cambios se conservan al cambiar de día — "
                          "**Guardar programa** escribe cada día editado "
                          "al cliente."),
        "ct_save": "Guardar programa",
        "ct_dup_label": "DUPLICAR PROGRAMA",
        "ct_dup_none": ("Añade otro cliente y podrás copiarle este "
                        "programa completo con un clic."),
        "ct_dup_to": "Copiar el programa guardado a",
        "ct_dup_btn": "Duplicar al cliente",
        "ct_dup_note": ("Copia lo guardado — los cambios sin guardar no "
                        "se incluyen."),
        "ct_overwrite": ("**{name} ya tiene un programa.** ¿Sobrescribirlo "
                         "con el de {src}? Esto reemplaza todos sus días y "
                         "ejercicios."),
        "ct_yes": "Sí, sobrescribir el programa de {name}",
        "ct_cancel": "Cancelar",
        "ct_col_exercise": "Ejercicio",
        "ct_col_sets": "Series",
        "ct_col_reps": "Reps",
        "ct_col_rir": "RIR",
        "ct_col_cue": "Nota / técnica",
        "ct_col_video": "Video",
        "ct_col_duration": "Duración",
        "ct_col_interval": "Intervalo",
        # -- supplements: coach cost sheet ---------------------------------
        "scc_title": "Tu stack, costeado.",
        "scc_sub": ("Cada suplemento con cantidad, cuánto dura un bote a "
                    "la dosis diaria, precio y precio por ración."),
        "scc_kicker": "SUPLEMENTOS · COSTO",
        "scc_currency": "Símbolo de moneda",
        "scc_edit_costs": ("Editar costos (cantidad · dosis diaria · "
                           "precio · moneda)"),
        "scc_add": "＋ Añadir suplemento",
        "scc_save": "Guardar costos",
        "scc_saved": "Costos guardados.",
        "scc_total": "Stack total",
        "scc_cpd": "Costo por día",
        "scc_month": "≈ {cur} {n} / mes",
        "scc_longest": "El que más dura",
        "scc_best": "Mejor valor / unidad",
        "scc_days": "días",
        "scc_priced": "{n} con precio",
        "scc_label": "DESGLOSE DE COSTOS",
        "scc_bar": "Stack de suplementos",
        "scc_bar_sub": "precio · duración · por ración",
        "scc_brand": "Marca",
        "scc_qty": "Cant.",
        "scc_daily": "Diario",
        "scc_lasts": "Dura",
        "scc_price": "Precio",
        "scc_unit": "Por unidad",
        "scc_note": ("Dura = Cant. ÷ Diario · Por unidad = Precio ÷ Cant. "
                     "· El costo/día reparte cada precio entre los días "
                     "que dura. Los clientes nunca ven precios."),
        # -- clients sheet -------------------------------------------------
        "cs_sub": ("Todo tu roster de un vistazo — haz clic en una fila "
                   "para abrir su consola."),
        "cs_name_req": "Ponle nombre al cliente.",
        "cs_exists": "Ya existe un cliente llamado “{name}”.",
        "cs_created": "{name} creado — completa sus datos en Inicio.",
        "onb_creds": ("**El acceso de {name} — se muestra solo esta vez.** "
                      "Compárteselo ahora:\n\nusuario `{u}` · contraseña "
                      "temporal `{p}`"),
        "cs_active": "CLIENTES ACTIVOS",
        "cs_ci_due": "CHECK-INS PENDIENTES",
        "cs_to_build": "PROGRAMAS POR ARMAR",
        "cs_new_apps": "SOLICITUDES NUEVAS",
        "cs_your_clients": "TUS CLIENTES",
        "cs_new_client": "＋ Nuevo cliente",
        "cs_client_name": "Nombre del cliente",
        "cs_create": "Crear cliente",
        "cs_none": "Aún no hay clientes",
        "cs_none_sub": ("Crea tu primer cliente o convierte una solicitud "
                        "desde la bandeja."),
        "cs_bar": "Clientes",
        "cs_bar_sub": "{n} activos · clic en una fila para abrir",
        "cs_col_client": "Cliente",
        "cs_col_goal": "Objetivo",
        "cs_col_week": "Semana",
        "cs_col_weight": "Peso",
        "cs_col_weighins": "Registros",
        "cs_col_checkin": "Check-in",
        "cs_col_program": "Programa",
        "cs_col_allergy": "Alergia",
        "cs_col_todo": "Pendiente",
        "cs_col_open": "Abrir",
        "cs_done": "Hecho",
        "cs_due": "Pendiente",
        "cs_set": "Listo",
        "cs_missing": "Falta",
        "cs_none_chip": "Ninguna",
        "cs_build": "Armar programa",
        "cs_checkin_todo": "Check-in",
        "cs_all_good": "Todo bien",
        "cs_open_arrow": "Abrir →",
        # -- applications --------------------------------------------------
        "ap_sub": ("Solicitudes del formulario público — revísalas aquí y "
                   "con un clic convierte las buenas directo en clientes."),
        "ap_kicker": "SOLICITUDES",
        "ap_new": "NUEVAS",
        "ap_reviewed": "REVISADAS",
        "ap_converted": "CONVERTIDAS",
        "ap_declined": "RECHAZADAS",
        "ap_all": "Todas {n}",
        "ap_none": "Aún no hay solicitudes.",
        "ap_none_sub": ("Comparte tu enlace <b>/Apply</b> con clientes "
                        "potenciales — sus solicitudes llegan aquí para "
                        "revisión."),
        "ap_empty_kicker": "BANDEJA VACÍA",
        "ap_bucket_empty": "Nada en este filtro.",
        "ap_bucket_sub": "Cambia de filtro para ver el resto.",
        "ap_no_name": ("Esta solicitud no tiene nombre — no se puede crear "
                       "el cliente."),
        "ap_now_client": "{name} ya es cliente — edita sus datos en Inicio.",
        "ap_email": "Email",
        "ap_phone": "Teléfono",
        "ap_age": "Edad",
        "ap_height": "Estatura",
        "ap_weight": "Peso actual",
        "ap_days": "Entrena (días/semana)",
        "ap_goal": "OBJETIVO PRINCIPAL",
        "ap_injuries": "LESIONES / LIMITACIONES",
        "ap_allergies": "ALERGIAS / INTOLERANCIAS",
        "ap_struggle": "MAYOR DIFICULTAD",
        "ap_coached": "TUVO COACH ANTES · LISTO PARA INVERTIR",
        "ap_convert": "Convertir en cliente →",
        "ap_review": "Marcar revisada",
        "ap_decline": "Rechazar",
        "ap_delete": "Eliminar",
    },
}


def t(key, **fmt):
    """Translate `key` for the session language. Fallback chain:
    session lang -> English -> the key itself. With kwargs, .format()s the
    result; a bad placeholder degrades to the raw string, never a crash."""
    lang = st.session_state.get("_lang", "en")
    table = STRINGS.get(lang) or STRINGS["en"]
    s = table.get(key)
    if s is None:
        s = STRINGS["en"].get(key, key)
    if fmt:
        try:
            return s.format(**fmt)
        except (KeyError, IndexError, ValueError):
            return s
    return s


def daytype_label(dt):
    """Display label for a plan day-type. 'Training Day'/'Non-Training Day'
    are STORAGE keys — they translate for display only; any custom day-type
    name the coach invented renders as typed."""
    m = {"Training Day": "dia_entreno", "Non-Training Day": "dia_no_entreno",
         "Rest Day": "dia_descanso"}
    key = m.get(str(dt).strip())
    return t(key) if key else str(dt)
