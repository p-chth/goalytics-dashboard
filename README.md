# Goalytics Dashboard (Streamlit)

Streamlit app that reads your DW (Postgres/Supabase) — especially `dw.mv_male_team_summary`.

## Deploy (Streamlit Cloud)

1. Push this folder to a new public repo (e.g. `goalytics-dashboard`).
2. In Streamlit Cloud:
   - Main file: `streamlit_app.py`
   - Add Secrets:
     ```toml
     PGHOST = "YOUR-SUPABASE-HOST.supabase.co"
     PGPORT = "5432"
     PGDATABASE = "postgres"  # or 'football'
     PGUSER = "postgres"
     PGPASSWORD = "YOUR-PASSWORD"
     PGSSLMODE = "require"
     ```

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PGHOST=localhost PGPORT=5432 PGDATABASE=football PGUSER=goalytics PGPASSWORD=goalytics PGSSLMODE=prefer
streamlit run streamlit_app.py
```

## Notes
- App auto-detects common column names; tweak as needed.
- Keep ETL repo separate from this dashboard repo.
