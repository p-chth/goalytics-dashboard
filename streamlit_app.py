
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Goalytics — Team Dashboard", layout="wide")

def _get_secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

DB_HOST = _get_secret("PGHOST")
DB_PORT = _get_secret("PGPORT", "5432")
DB_NAME = _get_secret("PGDATABASE", "football")
DB_USER = _get_secret("PGUSER", "postgres")
DB_PASS = _get_secret("PGPASSWORD")
DB_SSLMODE = _get_secret("PGSSLMODE", "prefer")  # 'require' on Supabase

if not DB_HOST or not DB_PASS:
    st.error("Database credentials not provided. Set them in Streamlit Secrets or env vars.")
    st.stop()

engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
connect_args = {"sslmode": DB_SSLMODE} if DB_SSLMODE else {}

@st.cache_resource(show_spinner=False)
def get_engine():
    return create_engine(engine_url, connect_args=connect_args, pool_pre_ping=True)

engine = get_engine()

def first_col(df, *cands):
    for c in cands:
        if c in df.columns:
            return c
    return None

@st.cache_data(ttl=60)
def list_views():
    with engine.begin() as conn:
        q = text("""
            SELECT schemaname, matviewname
            FROM pg_matviews
            WHERE schemaname IN ('dw','public','analytics')
            ORDER BY schemaname, matviewname
        """)
        return pd.read_sql(q, conn)

@st.cache_data(ttl=60)
def read_mv(mv_fq):
    with engine.begin() as conn:
        return pd.read_sql(text(f"SELECT * FROM {mv_fq}"), conn)

st.title("⚽️ Goalytics — Male Team Summary")

mvs = list_views()
options = [f"{r.schemaname}.{r.matviewname}" for _, r in mvs.iterrows()] if not mvs.empty else []
default_mv = "dw.mv_male_team_summary"
mv_fq = st.sidebar.selectbox("Materialized view", options or [default_mv],
                             index=(options.index(default_mv) if default_mv in options else 0))

df = read_mv(mv_fq)

if df.empty:
    st.info("The MV returned no rows.")
    st.stop()

comp_col   = first_col(df, "competition_name", "competition", "league", "competition_id")
season_col = first_col(df, "season_name", "season", "season_id")
team_col   = first_col(df, "team_name", "team", "team_id", "club")
gf_col     = first_col(df, "goals_for", "gf", "goals_scored", "goals")
ga_col     = first_col(df, "goals_against", "ga", "conceded")
pts_col    = first_col(df, "points", "pts")
mp_col     = first_col(df, "matches", "games", "played", "mp")

with st.sidebar:
    st.subheader("Filters")
    if comp_col:
        comps = ["(All)"] + sorted(df[comp_col].dropna().unique().tolist())
        sel = st.selectbox("Competition", comps, index=0)
        if sel != "(All)":
            df = df[df[comp_col] == sel]
    if season_col:
        seasons = ["(All)"] + sorted(df[season_col].dropna().unique().tolist())
        sel = st.selectbox("Season", seasons, index=0)
        if sel != "(All)":
            df = df[df[season_col] == sel]
    if team_col:
        teams = ["(All)"] + sorted(df[team_col].dropna().unique().tolist())
        sel = st.selectbox("Team", teams, index=0)
        if sel != "(All)":
            df = df[df[team_col] == sel]

c1,c2,c3,c4 = st.columns(4)
with c1: st.metric("Teams", df[team_col].nunique() if team_col else len(df))
with c2: st.metric("Matches", int(df[mp_col].sum()) if mp_col else len(df))
with c3: st.metric("Goals For", int(df[gf_col].sum()) if gf_col else 0)
with c4: st.metric("Goals Against", int(df[ga_col].sum()) if ga_col else 0)

st.divider()

try:
    import plotly.express as px
    if team_col and gf_col:
        top = (df[[team_col, gf_col]].groupby(team_col, as_index=False).sum()
               .sort_values(gf_col, ascending=False).head(15))
        fig = px.bar(top, x=team_col, y=gf_col, title="Top teams — Goals For")
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Chart skipped: {e}")

st.subheader("Data")
st.dataframe(df, use_container_width=True)

st.caption(f"Connected to {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER} (sslmode={DB_SSLMODE}). Source MV: {mv_fq}")
