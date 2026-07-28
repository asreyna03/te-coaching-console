"""Shared data layer for the T&E coaching app.

Caching: Streamlit re-runs the whole script on every interaction, so the
pure readers below are wrapped in @st.cache_data — repeated reads within a
session cost nothing instead of a Supabase round-trip each. Every write
path clears the client-store caches (`_clear_store_caches`), so a save is
visible on the very next rerun; the TTLs only bound staleness from writes
that happen OUTSIDE this process (e.g. direct DB edits).

Scope note: caches are keyed by the readers' arguments (get_client by
name), and return copies — they hold exactly what the uncached call would
return, so role isolation is unchanged (verified by the auth suite)."""
import hashlib
import hmac
import json
import secrets
from pathlib import Path

import streamlit as st

import db  # Postgres persistence when DATABASE_URL is set; JSON fallback otherwise

DATA_TTL = 120      # client store + applications (writes clear these anyway)
STATIC_TTL = 3600   # the committed food-DB file

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FOODDB_PATH = DATA / "fooddb.json"
CLIENTS_PATH = DATA / "clients.json"
APPLICATIONS_PATH = DATA / "applications.json"

FOOD_CATS = ["Proteins", "Carbohydrates", "Fats",
             "FruitsVegetables", "DrinksCondiments"]
CAT_LABEL = {
    "Proteins": "Proteins", "Carbohydrates": "Carbs", "Fats": "Fats",
    "FruitsVegetables": "Fruits/Veg", "DrinksCondiments": "Drinks/Condiments",
}
CAT_ICON = {
    "Proteins": "🥩", "Carbohydrates": "🍚", "Fats": "🥑",
    "FruitsVegetables": "🥦", "DrinksCondiments": "🥤",
}


def _f(x):
    try:
        return float(str(x).replace(",", "").strip())
    except Exception:
        return 0.0


@st.cache_data(ttl=STATIC_TTL, show_spinner=False)
def load_fooddb():
    """Return (cats, lookup) where cats[cat]=[item...] and lookup[name]=item."""
    with open(FOODDB_PATH) as f:
        raw = json.load(f)
    cats, lookup = {}, {}
    for cat in FOOD_CATS:
        items = []
        for r in raw.get(cat, {}).get("rows", []):
            name = str(r[0]).strip()
            if not name:
                continue
            item = {
                "name": name,
                "category": cat,
                "serving": str(r[1]) if len(r) > 1 else "",
                "calories": _f(r[2] if len(r) > 2 else 0),
                "protein": _f(r[3] if len(r) > 3 else 0),
                "fats": _f(r[4] if len(r) > 4 else 0),
                "carbs": _f(r[5] if len(r) > 5 else 0),
            }
            items.append(item)
            lookup[name] = item
        cats[cat] = items
    return cats, lookup


def all_food_names(cats):
    names = []
    for cat in FOOD_CATS:
        for it in cats.get(cat, []):
            names.append(it["name"])
    return sorted(set(names))


def macros_for(lookup, food, servings):
    it = lookup.get(str(food).strip())
    s = _f(servings)
    if not it:
        return (0.0, 0.0, 0.0, 0.0)
    return (it["calories"] * s, it["protein"] * s, it["fats"] * s, it["carbs"] * s)


# ---------------- serving interpretation (grams / ml / units) ----------------
def serving_info(serving_str):
    """Interpret a serving descriptor from the food DB.

    Returns (kind, qty, unit):
      '100' or '100g'  -> ('g', 100.0, 'g')     # sheet convention: bare number = grams
      '500ml'          -> ('ml', 500.0, 'ml')
      '1 Slice'        -> ('unit', 1.0, 'Slice')
      '1'              -> ('unit', 1.0, '')      # ambiguous '1' = one item
      ''               -> ('unit', 1.0, '')
    """
    import re
    s = str(serving_str or "").strip()
    if not s:
        return ("unit", 1.0, "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)", s)
    if m:
        q = float(m.group(1))
        # a bare '1' is "one item" (e.g. an egg), larger bare numbers are grams
        return ("g", q, "g") if q > 1 else ("unit", q, "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*g(?:rams?)?\b", s, re.I)
    if m:
        return ("g", float(m.group(1)), "g")
    m = re.search(r"(\d+(?:\.\d+)?)\s*ml\b", s, re.I)
    if m:
        return ("ml", float(m.group(1)), "ml")
    m = re.match(r"(\d+(?:\.\d+)?)\s*(.+)$", s)
    if m:
        return ("unit", float(m.group(1)) or 1.0, m.group(2).strip())
    return ("unit", 1.0, s)


def amount_label(item, amount):
    """Human label for a chosen amount: '(300g)', '(500ml)', '(3 Slices)', '(x2)'."""
    kind, qty, unit = serving_info(item.get("serving", ""))
    a = _f(amount)
    fmt = f"{a:g}"
    if kind in ("g", "ml"):
        return f"({fmt}{kind})"
    if qty != 1:                      # e.g. serving '2 Crackers' -> multiples of it
        return f"({fmt} × {item.get('serving', '').strip()})"
    if not unit:
        return f"(x{fmt})"
    u = unit if (a == 1 or unit.lower().endswith("s")) else unit + "s"
    return f"({fmt} {u})"


def servings_from_amount(item, amount):
    """Convert an entered amount (grams / ml / qty) into DB 'servings' for macros."""
    kind, qty, unit = serving_info(item.get("serving", ""))
    a = _f(amount)
    if kind in ("g", "ml") and qty > 0:
        return a / qty
    return a


def default_amount(item):
    """Sensible starting amount for a food: one full serving."""
    kind, qty, unit = serving_info(item.get("serving", ""))
    return qty if kind in ("g", "ml") else 1.0


@st.cache_data(ttl=STATIC_TTL, show_spinner=False)
def load_supplements():
    with open(FOODDB_PATH) as f:
        raw = json.load(f)
    out = []
    for r in raw.get("Supplements", {}).get("rows", []):
        out.append({
            "name": r[0] if len(r) > 0 else "",
            "reason": r[1] if len(r) > 1 else "",
            "directions": r[2] if len(r) > 2 else "",
            "link": r[3] if len(r) > 3 else "",
        })
    return out


# ---------------- client store (Postgres when configured, else local JSON) ----
@st.cache_data(ttl=DATA_TTL, show_spinner=False)
def _load_clients_raw():
    """Every record in the store, including reserved '_'-prefixed ones."""
    if db.enabled():
        return db.load_all()
    if CLIENTS_PATH.exists():
        with open(CLIENTS_PATH) as f:
            return json.load(f)
    return {}


def _clear_store_caches():
    """Every client-store write funnels through here so the next read —
    same rerun or next — sees the saved state, never a cached one."""
    _load_clients_raw.clear()
    get_client.clear()


def load_clients():
    """Real clients only — reserved records (e.g. '_settings') never show
    up in rosters, pickers or dashboards."""
    return {k: v for k, v in _load_clients_raw().items()
            if not str(k).startswith("_")}


def save_clients(d):
    try:
        if db.enabled():
            for name, rec in d.items():
                db.save_one(name, rec)
            return
        CLIENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CLIENTS_PATH, "w") as f:
            json.dump(d, f, indent=2)
    finally:
        _clear_store_caches()


@st.cache_data(ttl=DATA_TTL, show_spinner=False)
def get_client(name):
    if db.enabled():
        return db.get_one(name)
    return _load_clients_raw().get(name, {})


def upsert_client(name, patch):
    rec = get_client(name)
    rec.update(patch)
    rec.setdefault("name", name)
    try:
        if db.enabled():
            db.save_one(name, rec)
        else:
            clients = _load_clients_raw()
            clients[name] = rec
            save_clients(clients)   # clears the caches
            return rec
    finally:
        _clear_store_caches()
    return rec


def delete_client(name):
    try:
        if db.enabled():
            db.delete_one(name)
            return
        clients = _load_clients_raw()
        clients.pop(name, None)
        save_clients(clients)       # clears the caches
    finally:
        _clear_store_caches()


# ---------------- app settings (reserved record, version-stamped) --------------
SETTINGS_KEY = "_settings"
SETTINGS_VERSION = 1


def get_settings():
    """Coach/app-level settings — currency + supplement costs. Tolerant of a
    missing or older-shaped record."""
    rec = get_client(SETTINGS_KEY) or {}
    return {"version": SETTINGS_VERSION,
            "currency": str(rec.get("currency") or "S/"),
            "supp_costs": (rec.get("supp_costs")
                           if isinstance(rec.get("supp_costs"), dict)
                           else {}),
            "coach_prefs": (rec.get("coach_prefs")
                            if isinstance(rec.get("coach_prefs"), dict)
                            else {})}


def save_settings(patch):
    patch = dict(patch)
    patch["version"] = SETTINGS_VERSION
    return upsert_client(SETTINGS_KEY, patch)


# ---------------- computed plan grid + shopping list ---------------------------
def plan_grid(name):
    """The client's meal plan, fully computed: for each day type with rows,
    meals in order with per-row serving/amount/macros, per-meal totals and a
    day total. Foods missing from the DB degrade to zero-macro rows."""
    rec = get_client(name) or {}
    cats, lookup = load_fooddb()
    out = {}
    for daytype in ("Training Day", "Non-Training Day"):
        rows = (rec.get("meal_plans") or {}).get(daytype) or []
        if not rows:
            continue
        meals = {}
        order = []
        for r in rows:
            meal = str(r.get("Meal", "") or "Meal")
            if meal not in meals:
                meals[meal] = []
                order.append(meal)
            food = str(r.get("Food", ""))
            try:
                amt = float(r.get("Amount") or 0)
            except (TypeError, ValueError):
                amt = 0.0
            item = lookup.get(food)
            if item:
                kind, qty, unit = serving_info(item.get("serving", ""))
                servings = servings_from_amount(item, amt)
                cal, p, f, c = macros_for(lookup, food, servings)
                meals[meal].append({
                    "category": item.get("category", ""), "food": food,
                    "serving": (f"{qty:g} {unit}".strip()
                                if unit else f"{qty:g}"),
                    "n": round(servings, 2),
                    "amount": amount_label(item, amt),
                    "cal": cal, "p": p, "f": f, "c": c})
            else:
                meals[meal].append({"category": "", "food": food,
                                    "serving": "—", "n": 0, "amount": "—",
                                    "cal": 0.0, "p": 0.0, "f": 0.0,
                                    "c": 0.0})
        day = {"meals": [], "targets": (rec.get("targets") or {})
               .get(daytype) or {}}
        d_cal = d_p = d_f = d_c = 0.0
        for meal in order:
            mrows = meals[meal]
            t = (sum(x["cal"] for x in mrows), sum(x["p"] for x in mrows),
                 sum(x["f"] for x in mrows), sum(x["c"] for x in mrows))
            d_cal += t[0]; d_p += t[1]; d_f += t[2]; d_c += t[3]
            day["meals"].append({"meal": meal, "rows": mrows, "totals": t})
        day["totals"] = (d_cal, d_p, d_f, d_c)
        out[daytype] = day
    return out


def shopping_list(name):
    """One line per food across the whole plan (both day types, every meal —
    the same chicken adds up), grouped by DB category. Amounts are grams/ml/
    qty per one training + one rest day; the client scales to their week."""
    rec = get_client(name) or {}
    cats, lookup = load_fooddb()
    agg = {}
    for daytype in ("Training Day", "Non-Training Day"):
        for r in (rec.get("meal_plans") or {}).get(daytype) or []:
            food = str(r.get("Food", "")).strip()
            if not food:
                continue
            try:
                amt = float(r.get("Amount") or 0)
            except (TypeError, ValueError):
                amt = 0.0
            item = lookup.get(food)
            kind, unit, cat = "g", "g", "Other"
            if item:
                k, q, u = serving_info(item.get("serving", ""))
                kind = k
                unit = u or ("g" if k == "g" else "×")
                cat = item.get("category", "Other")
            e = agg.setdefault(food, {"amount": 0.0, "kind": kind,
                                      "unit": unit, "category": cat})
            e["amount"] += amt
    grouped = {}
    for food in sorted(agg):
        e = agg[food]
        if e["kind"] in ("g", "ml"):
            label = f'{e["amount"]:g} {e["unit"]}'
        elif e["unit"] and e["unit"] != "×":
            label = f'{e["amount"]:g} × {e["unit"]}'
        else:
            label = f'{e["amount"]:g}'
        grouped.setdefault(e["category"], []).append(
            {"food": food, "amount": e["amount"], "label": label})
    ordered = {c: grouped[c] for c in FOOD_CATS if c in grouped}
    for c in grouped:
        if c not in ordered:
            ordered[c] = grouped[c]
    return ordered


# ---------------- training programs -------------------------------------------
# Version-stamped so older/partial records are tolerated everywhere:
#   training = {"version": 1, "block", "week", "weeks_total",
#               "days": [{"name", "exercises": [{"exercise", "sets", "reps",
#                                                "rir", "cue", "video"}]}]}
TRAINING_VERSION = 1
_EX_FIELDS = ("exercise", "sets", "reps", "rir", "cue", "video")


def _int_or(v, default):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def default_training():
    return {"version": TRAINING_VERSION, "block": 1, "week": 1,
            "weeks_total": 6,
            "days": [{"name": n, "exercises": []}
                     for n in ("Push", "Pull", "Legs")]}


def get_training(name):
    """The client's program, normalized — any missing field, old shape or
    junk value comes back as a well-formed dict (never raises)."""
    raw = (get_client(name) or {}).get("training")
    if not isinstance(raw, dict) or not raw.get("days"):
        base = default_training()
        if isinstance(raw, dict):
            for k in ("block", "week", "weeks_total"):
                if k in raw:
                    base[k] = _int_or(raw[k], base[k])
        return base
    days = []
    for d in raw.get("days", []):
        if not isinstance(d, dict):
            continue
        exercises = []
        for e in (d.get("exercises") or []):
            if isinstance(e, dict):
                exercises.append({f: str(e.get(f, "") or "")
                                  for f in _EX_FIELDS})
        days.append({"name": str(d.get("name") or "Day"),
                     "exercises": exercises})
    return {"version": TRAINING_VERSION,
            "block": _int_or(raw.get("block"), 1),
            "week": _int_or(raw.get("week"), 1),
            "weeks_total": _int_or(raw.get("weeks_total"), 6),
            "days": days or default_training()["days"]}


def save_training(name, training):
    """Write a program back onto the client record, version-stamped."""
    t = dict(training)
    t["version"] = TRAINING_VERSION
    return upsert_client(name, {"training": t})


def has_program(name):
    """True when the client has a saved program with actual exercises (a
    default empty skeleton doesn't count — used by duplicate-overwrite guard)."""
    raw = (get_client(name) or {}).get("training") or {}
    return any(d.get("exercises")
               for d in raw.get("days", []) if isinstance(d, dict))


# Per-week completion, version-stamped:
#   training_log = {"version": 1, "log": {"<block>-<week>": {"<day>": [i,...]}}}
TRAINING_LOG_VERSION = 1


def get_training_log(name):
    """{week_key: {day: sorted [exercise indexes]}} — junk-tolerant."""
    raw = (get_client(name) or {}).get("training_log") or {}
    log = raw.get("log") if isinstance(raw, dict) else {}
    out = {}
    if isinstance(log, dict):
        for wk, days in log.items():
            if not isinstance(days, dict):
                continue
            out[str(wk)] = {
                str(d): sorted({_int_or(i, -1) for i in v
                                if _int_or(i, -1) >= 0})
                for d, v in days.items() if isinstance(v, (list, tuple))}
    return out


def set_training_done(name, week_key, day, indexes):
    """Record which exercise indexes are done for one day of one week."""
    log = get_training_log(name)
    log.setdefault(str(week_key), {})[str(day)] = \
        sorted({int(i) for i in indexes})
    return upsert_client(name, {"training_log":
                                {"version": TRAINING_LOG_VERSION,
                                 "log": log}})


# ---------------- client logins (the "client" role) ---------------------------
# Stored on the client record, version-stamped so records without a login (or
# with a future shape) are tolerated everywhere:
#   login = {"version": 1, "username", "salt", "pw_hash", "active"}
# PBKDF2-HMAC-SHA256 with a per-record random salt — plaintext is never stored.
LOGIN_VERSION = 1
_PW_ITERATIONS = 200_000


def _hash_pw(password, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", str(password).encode(),
                               bytes.fromhex(salt_hex), _PW_ITERATIONS).hex()


def generate_temp_password():
    """Short, shareable one-time password the coach reads out to the client."""
    return "te-" + secrets.token_hex(3)


def set_client_login(name, username, password, active=True):
    """Create or replace the login on a client record."""
    salt = secrets.token_hex(16)
    login = {"version": LOGIN_VERSION,
             "username": str(username or "").strip().lower(),
             "salt": salt,
             "pw_hash": _hash_pw(password, salt),
             "active": bool(active)}
    return upsert_client(name, {"login": login})


def verify_client_login(username, password):
    """Resolve credentials to a client name, or None. Constant-time compare;
    inactive logins and clients without one never match."""
    u = str(username or "").strip().lower()
    if not u or not password:
        return None
    for name, rec in load_clients().items():
        lg = rec.get("login") or {}
        if not lg.get("active") or lg.get("username", "") != u:
            continue
        salt, expected = lg.get("salt", ""), lg.get("pw_hash", "")
        if salt and expected and hmac.compare_digest(
                _hash_pw(password, salt), expected):
            return name
    return None


# ---------------- applications (Postgres when configured, else local JSON) ----
def _load_apps_json():
    if APPLICATIONS_PATH.exists():
        with open(APPLICATIONS_PATH) as f:
            return json.load(f)
    return []


def _save_apps_json(apps):
    APPLICATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(APPLICATIONS_PATH, "w") as f:
        json.dump(apps, f, indent=2)


def save_application(payload):
    """Persist a new coaching application; returns the assigned id."""
    try:
        if db.enabled():
            return db.save_application(payload)
        from datetime import datetime, timezone
        apps = _load_apps_json()
        new_id = max((a.get("id", 0) for a in apps), default=0) + 1
        apps.append({"id": new_id, "status": "new",
                     "submitted_at": datetime.now(timezone.utc).isoformat(),
                     **payload})
        _save_apps_json(apps)
        return new_id
    finally:
        load_applications.clear()


@st.cache_data(ttl=DATA_TTL, show_spinner=False)
def load_applications():
    """Newest first."""
    if db.enabled():
        return db.load_applications()
    return sorted(_load_apps_json(),
                  key=lambda a: a.get("submitted_at", ""), reverse=True)


def set_application_status(app_id, status):
    try:
        if db.enabled():
            db.set_application_status(app_id, status)
            return
        apps = _load_apps_json()
        for a in apps:
            if a.get("id") == app_id:
                a["status"] = status
        _save_apps_json(apps)
    finally:
        load_applications.clear()


def delete_application(app_id):
    try:
        if db.enabled():
            db.delete_application(app_id)
            return
        _save_apps_json([a for a in _load_apps_json()
                         if a.get("id") != app_id])
    finally:
        load_applications.clear()
