# Project Notes — T&E Coaching Console

Standalone fitness-coaching web app. **Independent of SOLARos** — self-contained in
this folder (own credentials in `.secrets/`, own data in `data/`).

## Origin
Built 2026-07-01 from a friend's coaching Google Sheet ("T&E Sheet") that Sam copied
and blanked into a reusable template.
- Source sheet (blanked copy, Sam's Drive): `<redacted — private Sheet ID kept out of public repo>`
- Full-data backup (pre-blanking): `<redacted — private Sheet ID kept out of public repo>`

## Layout
- `app.py` — home / client picker
- `pages/` — Meal Planner, Weigh-ins, Check-in, Supplements, Training, Sync
- `coachlib.py` — data layer (food DB + local client store)
- `ui.py` — theme + shared UI (hero, client picker)
- `sync.py` — Google Sheets sync (uses `.secrets/`, NOT SOLARos's Desktop creds)
- `data/fooddb.json` — food + supplement DB cached from the sheet
- `data/clients.json` — local client entries (gitignored)
- `.secrets/` — own copy of `token.pickle` + `credentials.json` (gitignored)

## Run
```bash
cd ~/Desktop/coaching_app && python3 -m streamlit run app.py   # -> localhost:8600
```

## Auth / independence
The app authenticates with its **own** copy of Sam's Google OAuth token in
`.secrets/` — it never reads `~/Desktop/token.pickle` (the SOLARos one). Same Google
identity (the sheet is Sam's), but no file dependency on SOLARos.

## Status
v1 done: Meal Planner (live macros), Weigh-ins (log + trend), Check-in, Supplements.
Training page = program viewer TODO. Sync = pull food DB + push meal plans/weigh-ins.
