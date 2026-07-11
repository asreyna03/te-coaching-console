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

## Notes
Port is set to **8600** in `.streamlit/config.toml` to avoid clashing with the
SOLARos dashboard on 8501.
