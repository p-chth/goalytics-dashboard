# ⚽ Goalytics Dashboard

A Streamlit-based analytics dashboard for visualizing football team performance from your **Goalytics Data Warehouse**.  
It connects directly to your Postgres (local or Supabase) instance, supporting dynamic filters, trend charts, and detailed Home/Away performance stats.

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
- 🔐 **Secure connection** using `.streamlit/secrets.toml` or environment variables

---

## 🧠 Tech Stack

| Layer | Tool / Library | Description |
|-------|----------------|-------------|
| Backend | **PostgreSQL** | Data Warehouse (`dw.mv_male_team_summary`, `dw.mv_team_match`) |
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

You can use **either** of the following methods:

#### 🧩 Option A — `.streamlit/secrets.toml`
Create the file:
```toml
# .streamlit/secrets.toml
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "football"
PG_USER = "airflow"
PG_PASSWORD = "airflow"
PGSSLMODE = "prefer"  # or "require" for Supabase
```

#### 🧩 Option B — Environment variables
```bash
export PG_HOST=localhost
export PG_PORT=5432
export PG_DB=football
export PG_USER=airflow
export PGPASSWORD=airflow
export PGSSLMODE=prefer
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

## 🧑‍💻 Author

**Goalytics Project**  
Developed as part of a Data Platform Engineering portfolio — integrating ETL (Airflow + Spark), Postgres DW, and Streamlit analytics.
