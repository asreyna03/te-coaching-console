# T&E Coaching Console

An interactive web app version of the "T&E Sheet" coaching template — built with
Streamlit. Build meal plans, track weigh-ins, run weekly check-ins and browse
your supplement guide, all powered by the food database from your Google Sheet.

## Run it

```bash
cd ~/Desktop/coaching_app
python3 -m streamlit run app.py
```

Then open http://localhost:8600

## Pages
- **Home** – client picker + overview
- **Meal Planner** – pick foods, set servings, live calories/macros vs target (TD & NTD)
- **Weigh-ins** – daily weight/steps/sleep log + weight-trend chart
- **Check-in** – weekly check-in form (same prompts as the sheet)
- **Supplements** – searchable supplement guide
- **Training** – program viewer (stub — wiring up next)

## Data
- `data/fooddb.json` – food + supplement database, pulled from the Google Sheet.
  Re-sync anytime with the fetch script (uses `~/Desktop/token.pickle`).
- `data/clients.json` – client entries (info, meal plans, weigh-ins, check-ins),
  stored locally on this machine.

## Deploy a shareable live app (Streamlit Community Cloud — free)

This turns the repo into a public URL people can actually use. Because the app
touches real client data, it ships with a **password gate**: set an
`app_password` secret and only people you give it to can get in.

1. Go to **https://share.streamlit.io** → sign in with GitHub → **Create app**.
2. Pick repo **asreyna03/te-coaching-console**, branch **main**, main file **app.py**.
3. Open **Advanced settings → Secrets** and paste:
   ```toml
   app_password = "choose-a-strong-password"
   ```
4. **Deploy.** You get a `…streamlit.app` link. Share the link **and** the
   password with the people you want to have access.

**Security notes**
- Without `app_password` set, the app is **open to anyone with the link** — always set it before sharing.
- Google Sheet sync is **off** on the hosted app by default (your Google login
  never leaves your machine). The app runs fully without it. To enable sync on
  the deploy, add a `te_sheet_id` and a `[google]` secret block (token,
  refresh_token, client_id, client_secret, scopes) — only do this if you accept
  that the hosted app then acts as your Google identity.
- Hosted client data is **shared among everyone with the password** and is not
  persistent across restarts. For real per-client privacy, keep it local or add
  proper per-user accounts.

## Notes
Port is set to **8600** in `.streamlit/config.toml` to avoid clashing with the
SOLARos dashboard on 8501. The `app_password` gate lives in `ui.setup()`, so it
protects every page; locally (no password set) it's a no-op.
