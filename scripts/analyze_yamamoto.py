import pandas as pd
from src.db import PitchDB
from src.engine import compute_big6
from src.visualizer import PitchVisualizer

# ---------------------------------------------------------------------------
# 1. Data Retrieval
# ---------------------------------------------------------------------------
db = PitchDB()
query = "SELECT * FROM statcast_2024 WHERE player_name LIKE '%Yamamoto%'"
df_yamamoto = db.query_to_df(query)

# ---------------------------------------------------------------------------
# 2. Data Cleaning (Move this BEFORE compute_big6)
# ---------------------------------------------------------------------------
# Yamamoto's average extension is around 6.6ft. 
# Let's use a tighter professional range: 5.5ft to 7.2ft
df_yamamoto = df_yamamoto[
    (df_yamamoto['release_extension'] >= 5.5) & 
    (df_yamamoto['release_extension'] <= 7.2)
].copy()

# ---------------------------------------------------------------------------
# 3. Physics Calculation
# ---------------------------------------------------------------------------
# Now compute metrics based on CLEANED raw data
df_features = compute_big6(df_yamamoto)

# ---------------------------------------------------------------------------
# 4. Fastball Profile Analysis
# ---------------------------------------------------------------------------
ff_stats = df_features[df_features['pitch_type'] == 'FF'].copy()

# Correcting the Perceived Velo if it's systematically high
# Typical PV is Release Speed + (Extension - 6.0) * 1.5
ff_stats['perceived_velo'] = ff_stats['release_speed'] + (ff_stats['release_extension'] - 6.0) * 1.5
print("\n" + "="*55)
print("  YOSHINOBU YAMAMOTO: 2024 FASTBALL PHYSICS REPORT")
print("="*55)
print(f"  Sample Size         : {len(ff_stats)} pitches")
print(f"  Avg. VAA            : {ff_stats['vaa'].mean():.2f}° (Target: < -5.5°)")
print(f"  Avg. IVB            : {ff_stats['ivb'].mean():.2f} inches")
print(f"  Avg. Perceived Velo : {ff_stats['perceived_velo'].mean():.1f} mph")
print(f"  Spin Efficiency     : {ff_stats['spin_efficiency'].mean() * 100:.1f}%")
print("-" * 55)
print("  PRO SCOUTING NOTE:")
print("  Yamamoto's high spin efficiency and elite extension create a 'rising' effect, making his 95mph feel like high 90s.")
print("="*55)


# --- Visualization ---
viz = PitchVisualizer()
viz.plot_movement(df_features, "Yoshinobu Yamamoto")