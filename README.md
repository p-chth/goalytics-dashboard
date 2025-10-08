# ⚽ Goalytics Dashboard

A Streamlit-based analytics dashboard for visualizing football team performance from your **Goalytics Data Warehouse**.  
It connects directly to your Postgres (local Docker) or Supabase instance, supporting dynamic filters, trend charts, and detailed Home/Away performance stats.

---

## 🚀 Features

- 🕶️ **Dark UI** with modern layout and responsive design  
- 🔁 **Cascading filters** — each slicer updates automatically based on related selections  
- 📊 **Dynamic Overview** section:
  - Matches, Wins, Draws, Losses, Points
  - Goals Scored / Conceded trends (side-by-side large charts)
- 🏠 **Home & Away Analysis** — computed automatically from match data  
  - Includes matches, wins/draws/losses, points, goals for/against, and goal difference
- 📈 **Historical Trends** — season-over-season points visualization  
- 🔐 **Secure connection** supporting both **local Postgres** and **Supabase** setups

---

## 🧠 Tech Stack

| Layer | Tool / Library | Description |
|-------|----------------|-------------|
| Backend | **PostgreSQL / Supabase** | Data Warehouse (`dw.mv_male_team_summary`, `dw.mv_team_match`) |
| Frontend | **Streamlit** | Interactive web dashboard |
| Data Access | **SQLAlchemy + psycopg2** | Query and cache data |
| Visualization | **Streamlit native charts** | Line & Area charts for team stats |
| Styling | **Custom CSS (dark theme)** | Clean, modern interface |

---

## ⚙️ Setup Instructions

### 1️⃣ Install dependencies
```bash
pip install streamlit sqlalchemy psycopg2-binary pandas
```

### 2️⃣ Configure database credentials

You can connect **either** to your **local Postgres** or **Supabase** instance.  
Use `.streamlit/secrets.toml` (recommended) or environment variables.

#### 🧩 Option A — `.streamlit/secrets.toml`

Create the file:

```toml
# .streamlit/secrets.toml

# --- Local Postgres (Docker or localhost) ---
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "football"
PG_USER = "airflow"
PG_PASSWORD = "airflow"
PGSSLMODE = "prefer"  # use "disable" if SSL not enabled

# --- Supabase (cloud-hosted Postgres) ---
# Uncomment and fill these if connecting to Supabase instead
# PG_HOST = "db.<your-supabase-project>.supabase.co"
# PG_PORT = "5432"
# PG_DB = "postgres"
# PG_USER = "postgres"
# PG_PASSWORD = "<YOUR_SUPABASE_DB_PASSWORD>"
# PGSSLMODE = "require"   # required for Supabase SSL
```

#### 🧩 Option B — Environment variables

```bash
# Local Postgres example
export PG_HOST=localhost
export PG_PORT=5432
export PG_DB=football
export PG_USER=airflow
export PGPASSWORD=airflow
export PGSSLMODE=prefer

# Supabase example
export PG_HOST=db.<your-supabase-project>.supabase.co
export PG_PORT=5432
export PG_DB=postgres
export PG_USER=postgres
export PGPASSWORD=<YOUR_SUPABASE_DB_PASSWORD>
export PGSSLMODE=require
```

---

## 🧩 Running the App

### ▶️ Local run
```bash
streamlit run app.py
```

### 🐳 Run via Docker
Add the environment variables in your `docker-compose.yml`:
```yaml
services:
  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      PG_HOST: postgres
      PG_PORT: 5432
      PG_DB: football
      PG_USER: airflow
      PGPASSWORD: airflow
      PGSSLMODE: prefer
```

---

## 🧱 Data Requirements

The dashboard expects these **views/tables** in your `dw` schema:

- `dw.mv_male_team_summary` — aggregated per-season, per-team performance  
- `dw.mv_team_match` — match-level data with at least:
  - `match_date`
  - `team_name`
  - `goals_for`, `goals_against`
  - `is_home` or `home_away`
  - (optional) `points`, `result`

---

## 🧭 Layout Overview

```
Goalytics Dashboard
├── Sidebar
│   ├── Competition (dynamic)
│   ├── Season (dynamic)
│   └── Team (dynamic)
│
├── Overall Stats
│   ├── Metric cards (Matches, Wins, Draws, Losses, Points)
│   └── Goals Scored / Conceded line charts
│
├── Home & Away Analysis
│   ├── Home Stats
│   └── Away Stats
│
└── Historical Trends
    └── Points per Season area chart
```

---

## 🎨 Customization

You can modify the dark theme via the `<style>` block in `app.py`:

```css
--bg: #0d1218;        /* background */
--panel: #121821;     /* card panel */
--text: #eaf0f7;      /* main text */
--primary: #1e88e5;   /* highlight blue */
```

---

## 🛡️ Troubleshooting

| Issue | Likely Cause | Fix |
|-------|---------------|-----|
| ❌ Database credentials not provided | `.streamlit/secrets.toml` missing or incorrect | Add valid credentials |
| ⚪ Empty dashboard / no data | ETL not loaded into `dw.mv_male_team_summary` | Re-run your pipeline |
| ⚠️ Charts blank | Missing columns (`goals_for`, `match_date`, etc.) | Check your view definitions |
| 🎨 Dropdown text too light | Cached styles | **Shift+Reload** the browser |

---

## 🏁 Example

Run it locally:
```bash
streamlit run app.py
```
Then open → [http://localhost:8501](http://localhost:8501)

---

## ☁️ Streamlit Cloud Deployment

If deploying on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push your project to GitHub  
2. Add the following **App secrets** in the Streamlit Cloud UI under **Settings → Secrets**:

```toml
PG_HOST = "db.<your-supabase-project>.supabase.co"
PG_PORT = "5432"
PG_DB = "postgres"
PG_USER = "postgres"
PG_PASSWORD = "<YOUR_SUPABASE_DB_PASSWORD>"
PGSSLMODE = "require"
```

3. Run the app — Streamlit will automatically load your secrets.

---

## 🧑‍💻 Author

**Goalytics Project**  
Developed as part of a Data Platform Engineering portfolio — integrating ETL (Airflow + Spark), Postgres DW, and Streamlit analytics.
