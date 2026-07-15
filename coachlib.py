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
