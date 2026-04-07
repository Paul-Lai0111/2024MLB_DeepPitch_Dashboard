import streamlit as st
import pandas as pd
import plotly.express as px
from src.db import PitchDB
from src.engine import compute_big6

# --- Page Configuration ---
st.set_page_config(page_title="DeepPitch Analytics | MLB Physics", layout="wide")

@st.cache_data
def load_data():
    db = PitchDB()
    df = db.query_to_df("SELECT * FROM statcast_2024")
    # Using our calibrated physics engine
    return compute_big6(df)

# --- Title & Header ---
st.title("⚾ DeepPitch Analytics")
st.subheader("2024 MLB Advanced Physics & Scouting Dashboard")
st.markdown("""
Explore elite pitching metrics including **Vertical Approach Angle (VAA)**, 
**Induced Vertical Break (IVB)**, and **Seam-Shifted Wake (SSW)** deviation.
""")

df_all = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Scouting Filters")
pitcher_list = sorted(df_all['player_name'].unique())
selected_pitcher = st.sidebar.selectbox(
    "Select Pitcher", 
    pitcher_list, 
    index=pitcher_list.index("Yamamoto, Yoshinobu") if "Yamamoto, Yoshinobu" in pitcher_list else 0
)

# Filter Data
pitcher_df = df_all[df_all['player_name'] == selected_pitcher].copy()

# --- KPI Metrics Row ---
col1, col2, col3, col4 = st.columns(4)

# Calculations for metrics
ff_df = pitcher_df[pitcher_df['pitch_type'] == 'FF']
avg_vaa = ff_df['vaa'].mean() if not ff_df.empty else 0
avg_velo = pitcher_df['release_speed'].mean()

col1.metric("Avg Velocity", f"{avg_velo:.1f} mph")
col2.metric("4-Seam VAA", f"{avg_vaa:.2f}°", help="Vertical Approach Angle at Home Plate")
col3.metric("Avg Extension", f"{pitcher_df['release_extension'].mean():.2f} ft")
col4.metric("Scouted Pitches", len(pitcher_df))

st.divider()

# --- Interactive Visuals ---
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader(f"Movement Profile: {selected_pitcher}")
    # Convert movement to inches for the plot
    pitcher_df['HB_in'] = pitcher_df['pfx_x'] * 12
    
    fig = px.scatter(
        pitcher_df, 
        x='HB_in', y='ivb', 
        color='pitch_type',
        hover_data=['release_speed', 'release_spin_rate', 'vaa', 'spin_efficiency'],
        labels={'HB_in': 'Horizontal Break (in)', 'ivb': 'Induced Vertical Break (in)'},
        template="plotly_white",
        height=600
    )
    # Add Strike Zone Crosshairs
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.3)
    fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.3)
    
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("Physical Profile")
    # Show a radar or simple bar chart for pitch mix
    pitch_mix = pitcher_df['pitch_type'].value_counts(normalize=True) * 100
    fig_mix = px.pie(values=pitch_mix.values, names=pitch_mix.index, hole=.4, title="Pitch Mix %")
    st.plotly_chart(fig_mix, use_container_width=True)

# --- Detailed Analytics Table ---
st.subheader("Advanced Pitch Metrics Breakdown")
summary = pitcher_df.groupby('pitch_type').agg({
    'release_speed': 'mean',
    'ivb': 'mean',
    'vaa': 'mean',
    'spin_efficiency': 'mean',
    'ssw_deviation': 'mean'
}).round(3).rename(columns={
    'release_speed': 'Velo (mph)',
    'ivb': 'IVB (in)',
    'vaa': 'VAA (deg)',
    'spin_efficiency': 'Spin Eff.',
    'ssw_deviation': 'SSW Dev (in)'
})
st.table(summary)

st.info("Metrics are calculated using the DeepPitch Calibrated Magnus Model (k=0.1116).")