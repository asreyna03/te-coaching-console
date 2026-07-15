"""Shared data layer for the T&E coaching app."""
import json
from pathlib import Path

import db  # Postgres persistence when DATABASE_URL is set; JSON fallback otherwise

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FOODDB_PATH = DATA / "fooddb.json"
CLIENTS_PATH = DATA / "clients.json"

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
def load_clients():
    if db.enabled():
        return db.load_all()
    if CLIENTS_PATH.exists():
        with open(CLIENTS_PATH) as f:
            return json.load(f)
    return {}


def save_clients(d):
    if db.enabled():
        for name, rec in d.items():
            db.save_one(name, rec)
        return
    CLIENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CLIENTS_PATH, "w") as f:
        json.dump(d, f, indent=2)


def get_client(name):
    if db.enabled():
        return db.get_one(name)
    return load_clients().get(name, {})


def upsert_client(name, patch):
    rec = get_client(name)
    rec.update(patch)
    rec.setdefault("name", name)
    if db.enabled():
        db.save_one(name, rec)
    else:
        clients = load_clients()
        clients[name] = rec
        save_clients(clients)
    return rec


def delete_client(name):
    if db.enabled():
        db.delete_one(name)
        return
    clients = load_clients()
    clients.pop(name, None)
    save_clients(clients)
