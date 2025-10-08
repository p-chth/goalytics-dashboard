# app.py — Goalytics Dashboard (dark theme + real data)
import os
import re
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────────────────────
# Page config & styling (dark main, readable sidebar widgets)
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Goalytics Dashboard", page_icon="⚽", layout="wide")

st.markdown(
    """
    <style>
      :root {
        --bg: #0d1218;
        --panel: #121821;
        --text: #eaf0f7;
        --muted: #9db0c3;
        --primary: #1e88e5;
        --green: #2bd374;
        --red: #ff5d5d;
        --border: #223145;
        --radius: 14px;

      }
      /* Main app area dark */
      html, body, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
      .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
      hr, .stDivider { border-color: var(--border) !important; }

      /* Metric cards */
      .metric-card { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 16px; }
      .metric-title { color: var(--muted); font-size: 13px; }
      .metric-value { color: var(--text); font-weight: 800; font-size: 28px; margin-top: 2px; }
      .metric-accent .metric-value { color: var(--primary); }
      .metric-green { color: var(--green) !important; }
      .metric-red { color: var(--red) !important; }

      /* Sidebar: dark pane, LIGHT controls with DARK text (universal selectors) */
      section[data-testid="stSidebar"] { background: #0a0f15; border-right: 1px solid var(--border); }
      section[data-testid="stSidebar"] * { color: #dbe6f3; }

      /* Inputs: force light background & dark text */
      section[data-testid="stSidebar"] input,
      section[data-testid="stSidebar"] select,
      section[data-testid="stSidebar"] textarea {
        background: #ffffff !important;
        color: #111 !important;
        border: 1px solid #d1d9e0 !important;
        border-radius: 10px !important;
      }
      section[data-testid="stSidebar"] label,
      section[data-testid="stSidebar"] .stMarkdown p { color: #dbe6f3 !important; }

      /* ---- BaseWeb Select (Streamlit Selectbox) — make EVERYTHING dark text ---- */
      /* Control (selected value & placeholder) */
      section[data-testid="stSidebar"] div[data-baseweb="select"] {
        background: #ffffff !important;
        color: #111 !important;
        border-radius: 10px !important;
      }
      section[data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #111 !important;   /* selected value, placeholder, tokens */
        fill: #111 !important;    /* dropdown chevron & clear icons */
      }
      /* Placeholder opacity */
      section[data-testid="stSidebar"] div[data-baseweb="select"] input::placeholder {
        color: #333 !important; opacity: 1 !important;
      }
      /* Dropdown menu portal (options) */
      /* menu portal can render OUTSIDE the sidebar, so use a global rule */
      div[data-baseweb="menu"] { background: #ffffff !important; }
      div[data-baseweb="menu"] * { color: #111 !important; }
      /* Option hover/active */
      div[data-baseweb="menu"] [role="option"]:hover,
      div[data-baseweb="menu"] [role="option"][aria-selected="true"] {
        background: #f0f3f7 !important; color: #111 !important;
      }

      /* Streamlit native charts background */
      .stPlotlyChart, .stVegaLiteChart, .stAltairChart, .stDeckGlJsonChart {
        background: var(--panel) !important; border-radius: var(--radius);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Secrets / Env
# ─────────────────────────────────────────────────────────────
def pick_secret(names, default=None):
    for n in names:
        try:
            if n in st.secrets and str(st.secrets[n]) != "":
                return str(st.secrets[n])
        except Exception:
            pass
        v = os.getenv(n)
        if v not in (None, ""):
            return str(v)
    return default

DB_HOST    = pick_secret(["PG_HOST","PGHOST"])
DB_PORT    = pick_secret(["PG_PORT","PGPORT"], "5432")
DB_NAME    = pick_secret(["PG_DB","PGDATABASE"], "postgres")
DB_USER    = pick_secret(["PG_USER","PGUSER"])
DB_PASS    = pick_secret(["PG_PASSWORD","PGPASSWORD"])
DB_SSLMODE = pick_secret(["PGSSLMODE","PG_SSLMODE"], "require")

if not (DB_HOST and DB_USER and DB_PASS):
    st.error("❌ Database credentials not provided. Set PG_HOST/PG_PORT/PG_DB/PG_USER/PG_PASSWORD (+PGSSLMODE).")
    st.stop()

engine_url   = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
connect_args = {"sslmode": DB_SSLMODE} if DB_SSLMODE else {}

@st.cache_resource(show_spinner=False)
def get_engine():
    return create_engine(engine_url, connect_args=connect_args, pool_pre_ping=True)

engine = get_engine()

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def col_pick(df, names_or_regex):
    if df is None: return None
    lc_map = {c.lower(): c for c in df.columns}
    for n in names_or_regex:
        if isinstance(n, str) and n.lower() in lc_map:
            return lc_map[n.lower()]
    for pat in names_or_regex:
        rx = re.compile(pat, re.IGNORECASE)
        for c in df.columns:
            if rx.fullmatch(c) or rx.search(c):
                return c
    return None

def to_num(df, cols):
    for c in cols:
        if c and c in df.columns and not pd.api.types.is_numeric_dtype(df[c]):
            df[c] = pd.to_numeric(df[c], errors="coerce")

def nz(x, d=0):
    try:
        if pd.isna(x): return d
        v = float(x)
        return int(v) if abs(v - int(v)) < 1e-9 else round(v, 2)
    except Exception:
        return d

def compute_home_away_stats(tm):
    """Return two dicts: home_stats, away_stats with keys: matches,wins,draws,losses,points,gf,ga,gd"""
    if tm is None or tm.empty:
        return None, None

    date_col = col_pick(tm, ["match_date", r".*date.*"])
    gf_col   = col_pick(tm, ["goals_for","gf", r".*goals.*for.*"])
    ga_col   = col_pick(tm, ["goals_against","ga", r".*goals.*against.*"])
    pts_col  = col_pick(tm, ["points","pts", r".*point.*"])
    res_col  = col_pick(tm, ["result", r".*\b(W|D|L)\b.*"])
    home_flag_col = col_pick(tm, ["is_home", "home_away", "venue", r".*home.*away.*"])

    if not home_flag_col or not gf_col or not ga_col:
        return None, None

    df = tm.copy()
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(date_col)
    to_num(df, [gf_col, ga_col])
    if pts_col: to_num(df, [pts_col])

    def to_is_home(x):
        if pd.isna(x): return None
        s = str(x).strip().lower()
        if s in {"home","h","host","บ้าน"}: return True
        if s in {"away","a","visitor","เยือน"}: return False
        if s in {"true","1","t","yes","y"}: return True
        if s in {"false","0","f","no","n"}: return False
        return None

    if df[home_flag_col].dtype == bool:
        is_home = df[home_flag_col]
    else:
        is_home = df[home_flag_col].map(to_is_home)

    home_df = df[is_home == True]
    away_df = df[is_home == False]

    def agg(side_df):
        if side_df is None or side_df.empty:
            return dict(matches=0,wins=0,draws=0,losses=0,points=0,gf=0,ga=0,gd=0)
        gf = int(pd.to_numeric(side_df[gf_col], errors="coerce").fillna(0).sum())
        ga = int(pd.to_numeric(side_df[ga_col], errors="coerce").fillna(0).sum())
        matches = int(len(side_df))
        if res_col and res_col in side_df.columns:
            s = side_df[res_col].astype(str).str.lower()
            wins  = int((s.str.startswith("w") | (s == "win")).sum())
            draws = int((s.str.startswith("d") | (s == "draw")).sum())
            losses= int((s.str.startswith("l") | (s == "loss")).sum())
        else:
            wins  = int((side_df[gf_col] > side_df[ga_col]).sum())
            draws = int((side_df[gf_col] == side_df[ga_col]).sum())
            losses= int((side_df[gf_col] < side_df[ga_col]).sum())
        if pts_col and pts_col in side_df.columns:
            points = int(pd.to_numeric(side_df[pts_col], errors="coerce").fillna(0).sum())
        else:
            points = 3*wins + 1*draws
        return dict(matches=matches,wins=wins,draws=draws,losses=losses,points=points,gf=gf,ga=ga,gd=gf-ga)

    return agg(home_df), agg(away_df)

@st.cache_data(ttl=120)
def load_summary():
    sql = text("SELECT * FROM dw.mv_male_team_summary")
    with engine.begin() as conn:
        return pd.read_sql(sql, conn)

@st.cache_data(ttl=120)
def load_team_match(competition=None, season=None, team=None):
    where = []
    params = {}
    if competition:
        where.append("(competition_name = :comp OR competition_id = :comp)")
        params["comp"] = str(competition)
    if season:
        where.append("(season_name = :season OR season_id = :season)")
        params["season"] = str(season)
    if team:
        where.append("(team_name = :team OR team_id = :team)")
        params["team"] = str(team)
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    sql = text(f"""
        SELECT *
        FROM dw.mv_team_match
        {clause}
        ORDER BY match_date NULLS LAST, match_id
    """)
    try:
        with engine.begin() as conn:
            return pd.read_sql(sql, conn, params=params)
    except Exception:
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────
# Load base data
# ─────────────────────────────────────────────────────────────
with st.spinner("Loading data…"):
    df = load_summary()

if df.empty:
    st.info("ℹ️ No data in dw.mv_male_team_summary yet. Run your ETL/refresh.")
    st.stop()

# Column mapping (flexible to naming)
comp_col   = col_pick(df, ["competition_name","competition","league",r".*competition.*id.*"])
season_col = col_pick(df, ["season_name","season",r".*season.*id.*"])
team_col   = col_pick(df, ["team_name","team","club",r".*team.*id.*"])

mp_col  = col_pick(df, ["matches","games","played","mp",r".*matches.*"])
w_col   = col_pick(df, ["wins","w",r".*wins.*"])
d_col   = col_pick(df, ["draws","d",r".*draws.*"])
l_col   = col_pick(df, ["losses","l",r".*loss.*"])
pts_col = col_pick(df, ["points","pts",r".*points.*"])
gf_col  = col_pick(df, ["goals_for","gf","goals_scored","goals",r".*goals.*for.*"])
ga_col  = col_pick(df, ["goals_against","ga","conceded",r".*goals.*against.*"])

home_cols = {
    "matches": col_pick(df, ["home_matches","matches_home",r".*home.*matches.*"]),
    "wins":    col_pick(df, ["home_wins","wins_home",r".*home.*wins.*"]),
    "draws":   col_pick(df, ["home_draws","draws_home",r".*home.*draw.*"]),
    "losses":  col_pick(df, ["home_losses","losses_home",r".*home.*loss.*"]),
    "points":  col_pick(df, ["home_points","points_home",r".*home.*points.*"]),
    "gf":      col_pick(df, ["home_goals_for","goals_for_home",r".*home.*goals.*for.*"]),
    "ga":      col_pick(df, ["home_goals_against","goals_against_home",r".*home.*goals.*against.*"]),
}
away_cols = {
    "matches": col_pick(df, ["away_matches","matches_away",r".*away.*matches.*"]),
    "wins":    col_pick(df, ["away_wins","wins_away",r".*away.*wins.*"]),
    "draws":   col_pick(df, ["away_draws","draws_away",r".*away.*draw.*"]),
    "losses":  col_pick(df, ["away_losses","losses_away",r".*away.*loss.*"]),
    "points":  col_pick(df, ["away_points","points_away",r".*away.*points.*"]),
    "gf":      col_pick(df, ["away_goals_for","goals_for_away",r".*away.*goals.*for.*"]),
    "ga":      col_pick(df, ["away_goals_against","goals_against_away",r".*away.*goals.*against.*"]),
}

# Ensure numeric
to_num(df, [mp_col,w_col,d_col,l_col,pts_col,gf_col,ga_col] + list(home_cols.values()) + list(away_cols.values()))

# ─────────────────────────────────────────────────────────────
# Cascading slicers (each dropdown shows only valid combos with others)
# ─────────────────────────────────────────────────────────────
def opts_for_comp(current_season, current_team):
    temp = df.copy()
    if current_season and current_season != "(All)" and season_col:
        temp = temp[temp[season_col].astype(str) == current_season]
    if current_team and current_team != "(All)" and team_col:
        temp = temp[temp[team_col].astype(str) == current_team]
    values = sorted(temp[comp_col].dropna().astype(str).unique().tolist()) if comp_col else []
    return ["(All)"] + values

def opts_for_season(current_comp, current_team):
    temp = df.copy()
    if current_comp and current_comp != "(All)" and comp_col:
        temp = temp[temp[comp_col].astype(str) == current_comp]
    if current_team and current_team != "(All)" and team_col:
        temp = temp[temp[team_col].astype(str) == current_team]
    values = sorted(temp[season_col].dropna().astype(str).unique().tolist()) if season_col else []
    return ["(All)"] + values

def opts_for_team(current_comp, current_season):
    temp = df.copy()
    if current_comp and current_comp != "(All)" and comp_col:
        temp = temp[temp[comp_col].astype(str) == current_comp]
    if current_season and current_season != "(All)" and season_col:
        temp = temp[temp[season_col].astype(str) == current_season]
    values = sorted(temp[team_col].dropna().astype(str).unique().tolist()) if team_col else []
    return ["(All)"] + values

# Keep selections stable while options shrink/expand
for k, default in [("sel_comp","(All)"), ("sel_season","(All)"), ("sel_team","(All)")]:
    if k not in st.session_state: st.session_state[k] = default

# Compute options conditioned on the other two selections
comp_options   = opts_for_comp(st.session_state.get("sel_season"), st.session_state.get("sel_team"))
season_options = opts_for_season(st.session_state.get("sel_comp"), st.session_state.get("sel_team"))
team_options   = opts_for_team(st.session_state.get("sel_comp"), st.session_state.get("sel_season"))

# Coerce invalid selections back to "(All)"
if st.session_state.sel_comp not in comp_options: st.session_state.sel_comp = "(All)"
if st.session_state.sel_season not in season_options: st.session_state.sel_season = "(All)"
if st.session_state.sel_team not in team_options: st.session_state.sel_team = "(All)"

with st.sidebar:
    st.markdown("## ⚽ Goalytics Dashboard")

    sel_comp   = st.selectbox("Competition", comp_options, index=comp_options.index(st.session_state.sel_comp), key="sel_comp")
    # Recompute others after a change
    season_options = opts_for_season(sel_comp, st.session_state.get("sel_team"))
    if st.session_state.sel_season not in season_options: st.session_state.sel_season = "(All)"

    sel_season = st.selectbox("Season", season_options, index=season_options.index(st.session_state.sel_season), key="sel_season")
    # Recompute teams after season change
    team_options = opts_for_team(sel_comp, sel_season)
    if st.session_state.sel_team not in team_options: st.session_state.sel_team = "(All)"

    sel_team   = st.selectbox("Team", team_options, index=team_options.index(st.session_state.sel_team), key="sel_team")

# Apply filters (respect "(All)")
fdf = df.copy()
if sel_season != "(All)" and season_col:
    fdf = fdf[fdf[season_col].astype(str) == sel_season]
if sel_comp != "(All)" and comp_col:
    fdf = fdf[fdf[comp_col].astype(str) == sel_comp]
if sel_team != "(All)" and team_col:
    fdf = fdf[fdf[team_col].astype(str) == sel_team]

if fdf.empty:
    st.info("No rows after filtering.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# Title / subtitle
# ─────────────────────────────────────────────────────────────
st.title("Team Analytics Dashboard")
st.markdown("Competition → season → team insights.")
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# OVERALL STATS
# ─────────────────────────────────────────────────────────────
st.header("Overall Stats")

totals = {
    "matches": nz(fdf[mp_col].sum()) if mp_col else 0,
    "wins":    nz(fdf[w_col].sum()) if w_col else 0,
    "draws":   nz(fdf[d_col].sum()) if d_col else 0,
    "losses":  nz(fdf[l_col].sum()) if l_col else 0,
    "points":  nz(fdf[pts_col].sum()) if pts_col else 0,
    "gf":      nz(fdf[gf_col].sum()) if gf_col else 0,
    "ga":      nz(fdf[ga_col].sum()) if ga_col else 0,
}

m1, m2, m3, m4, m5 = st.columns(5)
for c, title in zip([m1,m2,m3,m4,m5], ["Matches","Wins","Draws","Losses","Points"]):
    key = title.lower()
    val = totals["matches" if key=="matches" else key]
    accent = " metric-accent" if key == "points" else ""
    c.markdown(f"""
      <div class="metric-card{accent}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{val}</div>
      </div>
    """, unsafe_allow_html=True)

# Bigger mini trends row
tm = load_team_match(
    competition=None if sel_comp=="(All)" else sel_comp,
    season=None if sel_season=="(All)" else sel_season,
    team=None if sel_team=="(All)" else sel_team,
)
if tm is not None and not tm.empty:
    date_col = col_pick(tm, ["match_date", r".*date.*"])
    gf_m_col = col_pick(tm, ["goals_for","gf", r".*goals.*for.*"])
    ga_m_col = col_pick(tm, ["goals_against","ga", r".*goals.*against.*"])
    g1, g2 = st.columns(2, gap="large")
    if date_col and (gf_m_col or ga_m_col):
        tm2 = tm.copy()
        tm2[date_col] = pd.to_datetime(tm2[date_col], errors="coerce")
        tm2 = tm2.sort_values(date_col)
        if gf_m_col: to_num(tm2, [gf_m_col])
        if ga_m_col: to_num(tm2, [ga_m_col])
        if gf_m_col:
            g1.markdown('<div class="metric-card"><div class="metric-title">Goals Scored</div>', unsafe_allow_html=True)
            g1.line_chart(tm2.set_index(date_col)[gf_m_col], height=220, use_container_width=True)
            g1.markdown('</div>', unsafe_allow_html=True)
        if ga_m_col:
            g2.markdown('<div class="metric-card"><div class="metric-title">Goals Conceded</div>', unsafe_allow_html=True)
            g2.line_chart(tm2.set_index(date_col)[ga_m_col], height=220, use_container_width=True)
            g2.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="metric-card"><div class="metric-title">Goals Scored / Conceded</div>'
        '<div class="metric-value">—</div></div>',
        unsafe_allow_html=True
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# HOME & AWAY (with Goal Diff)
# ─────────────────────────────────────────────────────────────
def section_block(title, cols_map):
    st.subheader(title)
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)

    def sum_or_zero(col):
        return nz(fdf[col].sum()) if col and col in fdf.columns else 0

    matches = sum_or_zero(cols_map.get("matches"))
    wins    = sum_or_zero(cols_map.get("wins"))
    draws   = sum_or_zero(cols_map.get("draws"))
    losses  = sum_or_zero(cols_map.get("losses"))
    points  = sum_or_zero(cols_map.get("points"))
    gf_val  = sum_or_zero(cols_map.get("gf"))
    ga_val  = sum_or_zero(cols_map.get("ga"))
    gd_val  = nz(gf_val - ga_val)

    r1c1.markdown(f'<div class="metric-card"><div class="metric-title">Matches</div><div class="metric-value">{matches}</div></div>', unsafe_allow_html=True)
    r1c2.markdown(f'<div class="metric-card"><div class="metric-title">Wins</div><div class="metric-value">{wins}</div></div>', unsafe_allow_html=True)
    r1c3.markdown(f'<div class="metric-card"><div class="metric-title">Draws</div><div class="metric-value">{draws}</div></div>', unsafe_allow_html=True)
    r1c4.markdown(f'<div class="metric-card"><div class="metric-title">Losses</div><div class="metric-value">{losses}</div></div>', unsafe_allow_html=True)

    r2c1.markdown(f'<div class="metric-card metric-accent"><div class="metric-title">Points</div><div class="metric-value">{points}</div></div>', unsafe_allow_html=True)
    r2c2.markdown(f'<div class="metric-card"><div class="metric-title">Goals For</div><div class="metric-value metric-green">{gf_val}</div></div>', unsafe_allow_html=True)
    r2c3.markdown(f'<div class="metric-card"><div class="metric-title">Goals Against</div><div class="metric-value metric-red">{ga_val}</div></div>', unsafe_allow_html=True)
    r2c4.markdown(f'<div class="metric-card"><div class="metric-title">Goal Diff</div><div class="metric-value">{gd_val}</div></div>', unsafe_allow_html=True)

def render_side(title, stats):
    st.subheader(title)
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)

    r1c1.markdown(f'<div class="metric-card"><div class="metric-title">Matches</div><div class="metric-value">{nz(stats["matches"])}</div></div>', unsafe_allow_html=True)
    r1c2.markdown(f'<div class="metric-card"><div class="metric-title">Wins</div><div class="metric-value">{nz(stats["wins"])}</div></div>', unsafe_allow_html=True)
    r1c3.markdown(f'<div class="metric-card"><div class="metric-title">Draws</div><div class="metric-value">{nz(stats["draws"])}</div></div>', unsafe_allow_html=True)
    r1c4.markdown(f'<div class="metric-card"><div class="metric-title">Losses</div><div class="metric-value">{nz(stats["losses"])}</div></div>', unsafe_allow_html=True)

    r2c1.markdown(f'<div class="metric-card metric-accent"><div class="metric-title">Points</div><div class="metric-value">{nz(stats["points"])}</div></div>', unsafe_allow_html=True)
    r2c2.markdown(f'<div class="metric-card"><div class="metric-title">Goals For</div><div class="metric-value metric-green">{nz(stats["gf"])}</div></div>', unsafe_allow_html=True)
    r2c3.markdown(f'<div class="metric-card"><div class="metric-title">Goals Against</div><div class="metric-value metric-red">{nz(stats["ga"])}</div></div>', unsafe_allow_html=True)
    r2c4.markdown(f'<div class="metric-card"><div class="metric-title">Goal Diff</div><div class="metric-value">{nz(stats.get("gd", nz(stats["gf"]) - nz(stats["ga"])) )}</div></div>', unsafe_allow_html=True)

home_stats, away_stats = (None, None)
if tm is not None and not tm.empty:
    home_stats, away_stats = compute_home_away_stats(tm)

if home_stats and home_stats["matches"] > 0:
    render_side("🏠 Home Stats", home_stats)
elif any(home_cols.values()):
    section_block("🏠 Home Stats", home_cols)

if away_stats and away_stats["matches"] > 0:
    render_side("✈️ Away Stats", away_stats)
elif any(away_cols.values()):
    section_block("✈️ Away Stats", away_cols)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# HISTORICAL TRENDS — Points per Season (for current selection)
# ─────────────────────────────────────────────────────────────
st.header("📈 Historical Trends")

hist = df.copy()
if sel_comp != "(All)" and comp_col:
    hist = hist[hist[comp_col].astype(str) == sel_comp]
if sel_team != "(All)" and team_col:
    hist = hist[hist[team_col].astype(str) == sel_team]

if not hist.empty and season_col and pts_col:
    to_num(hist, [pts_col])
    points_by_season = (
        hist[[season_col, pts_col]]
        .groupby(season_col, as_index=False)
        .sum(numeric_only=True)
        .sort_values(season_col)
        .rename(columns={season_col: "Season", pts_col: "Points"})
    ).set_index("Season")

    if not points_by_season.empty:
        last_season = points_by_season.index[-1]
        last_val = int(points_by_season.iloc[-1]["Points"])
        delta = 0
        if len(points_by_season) >= 2:
            prev_val = int(points_by_season.iloc[-2]["Points"])
            delta = last_val - prev_val
        st.metric(label=f"Points per Season ({last_season})", value=str(last_val),
                  delta=f"{delta} vs prev season" if len(points_by_season) >= 2 else None)

        st.area_chart(points_by_season, y="Points", use_container_width=True, height=260)
else:
    st.info("No seasonal points found for the current selection.")

# ─────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────
st.caption(f"Connected to {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER} (sslmode={DB_SSLMODE}). "
           f"Sources: dw.mv_male_team_summary (+ dw.mv_team_match if present).")
