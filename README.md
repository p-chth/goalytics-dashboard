# Goalytics Dashboard (Streamlit)

A lightweight Streamlit app that visualizes team analytics from your Data Warehouse (Postgres or Supabase), reading the materialized view **`dw.mv_male_team_summary`**.

---

## 🚀 Deploy on Streamlit Cloud

1. Put this folder in a **separate public GitHub repo** (e.g., `goalytics-dashboard`).
2. In Streamlit Cloud:
   - **Main file:** `streamlit_app.py`
   - **Python version:** 3.11 (recommended)
   - **Add Secrets** → paste one of the blocks below.

### 🔐 Secrets (Supabase — *Transaction Pooler*)
Use this if you’re connecting via the Supabase pooler (IPv4 friendly, good for Streamlit Cloud). Get values from **Project → Database → Connection Info**.

```toml
# Streamlit Cloud → Settings → Secrets
PGHOST = "aws-<region>.pooler.supabase.com"   # e.g. aws-1-ap-southeast-1.pooler.supabase.com
PGPORT = "5432"                               # pooler port is usually 5432 (session) or 6543 (transaction)
PGDATABASE = "postgres"                       # or 'football' if you created one
PGUSER = "postgres.<PROJECT_REF>"             # e.g. postgres.abcxyz...
PGPASSWORD = "YOUR_DB_PASSWORD"
PGSSLMODE = "require"
```

### 🔐 Secrets (Supabase — *Direct*)
Use only if your environment supports IPv6 and you connect directly to the DB (not the pooler).

```toml
PGHOST = "db.<PROJECT_REF>.supabase.co"
PGPORT = "5432"
PGDATABASE = "postgres"      
PGUSER = "postgres"
PGPASSWORD = "YOUR_DB_PASSWORD"
PGSSLMODE = "require"
```

### 🔐 Secrets (Local Postgres)
If you want the dashboard to hit your local Postgres (from your ETL stack):

```toml
PGHOST = "localhost"
PGPORT = "5432"
PGDATABASE = "football"
PGUSER = "goalytics"
PGPASSWORD = "goalytics"
PGSSLMODE = "prefer"
```

> The app automatically accepts either `PG_*` or `PG*` names (e.g., `PG_HOST` or `PGHOST`).

---

## 🧑‍💻 Run Locally

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Example: local Postgres
export PGHOST=localhost PGPORT=5432 PGDATABASE=football PGUSER=goalytics PGPASSWORD=goalytics PGSSLMODE=prefer

# OR Example: Supabase (pooler)
export PGHOST=aws-1-ap-southeast-1.pooler.supabase.com PGPORT=5432 PGDATABASE=postgres PGUSER=postgres.<REF> PGPASSWORD=YOUR_PASS PGSSLMODE=require

streamlit run streamlit_app.py
```

---

## 📂 Expected DW Objects

This app expects **`dw.mv_male_team_summary`** to exist and be populated. It’s created by your ETL migrations and refreshed by your Airflow DAG. If you see zero rows:

- Ensure you ran DB migrations (001..003).
- Trigger the ETL and the MV refresh tasks.
- Verify with:
  ```sql
  SELECT COUNT(*) FROM dw.mv_male_team_summary;
  ```

---

## 🧩 App Behavior

- Auto-detects common column names for: competition, season, team, matches, wins, draws, losses, points, goals for/against.
- Sidebar filters: Competition / Season / Team.
- KPI cards: Overview, Home, Away.
- Dark main content with **light sidebar inputs** for readability.

> We intentionally keep the layout focused (no extra charts) to match the design brief.

---

## 🛠 Troubleshooting

**“❌ Database credentials not provided”**  
→ Add the **Secrets** in Streamlit Cloud (or export env vars locally). The app reads from `st.secrets` first.

**“relation \"dw.mv_male_team_summary\" does not exist”**  
→ Run migrations and/or the DAG, or point the app to the correct database/schema.

**Pooler vs Direct**  
- If you see `MaxClientsInSessionMode` or SSL termination errors, use the **Transaction Pooler** host + port from Supabase and keep `PGSSLMODE=require`.

---

## 📜 License
MIT
