"""Google Sheets sync for the coaching app.

Uses the app's OWN credentials in .secrets/ — never SOLARos's Desktop token.
Two-way: pull the food database from the sheet, and push/pull a client's full
record to a dedicated 'APP · <name>' tab (human-readable rows + an exact JSON
blob in Z1 for lossless round-trip).
"""
import json
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import coachlib as cl

ROOT = Path(__file__).resolve().parent
SECRETS = ROOT / ".secrets"
TOKEN = SECRETS / "token.pickle"
# Sheet ID is loaded from the env var TE_SHEET_ID or a gitignored
# .secrets/sheet_id.txt, so it never lands in the public repo.
def _load_sheet_id():
    import os
    v = os.environ.get("TE_SHEET_ID", "").strip()
    if v:
        return v
    try:  # Streamlit Cloud secret, if deployed
        import streamlit as st
        s = str(st.secrets.get("te_sheet_id", "") or "").strip()
        if s:
            return s
    except Exception:
        pass
    f = SECRETS / "sheet_id.txt"
    return f.read_text().strip() if f.exists() else ""


def _secret_google():
    """Google OAuth fields from st.secrets['google'] on a deploy, else None."""
    try:
        import streamlit as st
        g = st.secrets.get("google")
        return dict(g) if g else None
    except Exception:
        return None


SHEET_ID = _load_sheet_id()

FOOD_RANGES = ["Proteins", "Carbohydrates", "Fats", "FruitsVegetables",
               "DrinksCondiments", "Recipes"]


def _creds():
    # Deployed (Streamlit Cloud): build creds from st.secrets['google'] if set.
    g = _secret_google()
    if g:
        from google.oauth2.credentials import Credentials
        c = Credentials(
            token=g.get("token"), refresh_token=g.get("refresh_token"),
            token_uri=g.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=g.get("client_id"), client_secret=g.get("client_secret"),
            scopes=list(g.get("scopes", [])) or None)
        if getattr(c, "expired", False) and c.refresh_token:
            c.refresh(Request())
        return c
    # Local: the app's own pickled token in .secrets/.
    if TOKEN.exists():
        with open(TOKEN, "rb") as f:
            c = pickle.load(f)
        if c and getattr(c, "expired", False) and getattr(c, "refresh_token", None):
            c.refresh(Request())
            with open(TOKEN, "wb") as f:
                pickle.dump(c, f)
        return c
    raise RuntimeError(
        "Google Sheets sync isn't set up on this instance. The app works "
        "without it — add credentials to enable syncing.")


def _svc():
    return build("sheets", "v4", credentials=_creds())


# ---------------- food DB (sheet -> app) ----------------
def pull_fooddb():
    svc = _svc()
    resp = svc.spreadsheets().values().batchGet(
        spreadsheetId=SHEET_ID, ranges=FOOD_RANGES + ["Supplements"],
        valueRenderOption="FORMATTED_VALUE").execute()
    out = {}
    for name, vr in zip(FOOD_RANGES + ["Supplements"], resp["valueRanges"]):
        rows = vr.get("values", [])
        hdr = rows[0] if rows else []
        items = [r for r in rows[1:] if r and str(r[0]).strip()]
        out[name] = {"header": hdr, "rows": items}
    cl.FOODDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(cl.FOODDB_PATH, "w") as f:
        json.dump(out, f, indent=2)
    return {k: len(v["rows"]) for k, v in out.items()}


# ---------------- client (app <-> sheet) ----------------
def _tab_titles(svc):
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    return [s["properties"]["title"] for s in meta["sheets"]]


def _ensure_tab(svc, title):
    if title not in _tab_titles(svc):
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": title}}}]}
        ).execute()


def _tab_for(name):
    return f"APP · {name}"


def list_app_clients():
    svc = _svc()
    return sorted(t[len("APP · "):] for t in _tab_titles(svc)
                  if t.startswith("APP · "))


def push_client(name):
    rec = cl.get_client(name)
    svc = _svc()
    tab = _tab_for(name)
    _ensure_tab(svc, tab)

    rows = [["T&E COACHING — CLIENT EXPORT"], ["Client", name],
            ["Start date", rec.get("start_date", "")],
            ["Bodyweight", rec.get("bodyweight", "")],
            ["Goals", rec.get("goals", "")], []]
    rows.append(["TARGETS", "Calories", "Protein", "Fats", "Carbs"])
    for dt, t in rec.get("targets", {}).items():
        rows.append([dt, t.get("cal", ""), t.get("protein", ""),
                     t.get("fats", ""), t.get("carbs", "")])
    rows.append([])
    for dt, plan in rec.get("meal_plans", {}).items():
        rows.append([f"MEAL PLAN — {dt}", "Meal", "Food", "Amount", "Servings"])
        for r in plan:
            rows.append(["", r.get("Meal", ""), r.get("Food", ""),
                         r.get("Amount", ""), r.get("Servings", "")])
        rows.append([])
    wi = rec.get("weighins", [])
    if wi:
        rows.append(["WEIGH-INS", "Date", "Weight", "Steps", "Sleep", "Notes"])
        for r in wi:
            rows.append(["", r.get("Date", ""), r.get("Weight", ""),
                         r.get("Steps", ""), r.get("Sleep (hrs)", ""),
                         r.get("Notes", "")])
        rows.append([])
    ci = rec.get("checkins", {})
    if ci:
        rows.append(["CHECK-INS"])
        for wk, c in sorted(ci.items(), key=lambda x: int(x[0])):
            rows.append([f"Week {wk}", "Weight avg", c.get("weight_avg", "")])
            for q, a in c.get("answers", {}).items():
                rows.append(["", q, a])
            rows.append([])

    svc.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID, range=f"'{tab}'").execute()
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID, range=f"'{tab}'!A1",
        valueInputOption="RAW", body={"values": rows}).execute()
    # lossless machine blob for pull-back
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID, range=f"'{tab}'!Z1",
        valueInputOption="RAW", body={"values": [[json.dumps(rec)]]}).execute()
    return tab, len(rows)


def pull_client(name):
    svc = _svc()
    tab = _tab_for(name)
    v = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{tab}'!Z1").execute().get("values", [])
    if not v or not v[0] or not str(v[0][0]).strip():
        raise ValueError(f"No app data found on tab '{tab}'.")
    rec = json.loads(v[0][0])
    cl.upsert_client(name, rec)
    return rec
