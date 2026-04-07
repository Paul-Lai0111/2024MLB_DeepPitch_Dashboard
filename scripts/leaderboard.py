import pandas as pd
from src.db import PitchDB
from src.engine import compute_big6

def generate_leaderboards():
    db = PitchDB()
    
    # Load all processed data for 2024
    print("[leaderboard] Fetching 2024 season data from DuckDB...")
    df_raw = db.query_to_df("SELECT * FROM statcast_2024")
    df = compute_big6(df_raw)
    # Filter: Minimum 500 pitches to ensure statistical significance
    pitcher_counts = df['player_name'].value_counts()
    qualified_pitchers = pitcher_counts[pitcher_counts >= 500].index
    df_qual = df[df['player_name'].isin(qualified_pitchers)].copy()

    print(f"[leaderboard] Analyzing {len(qualified_pitchers)} qualified pitchers...")

    # ---------------------------------------------------------------------------
    # 1. THE VAA KINGS (Four-Seam Fastballs only)
    # Goal: Shallowest (closest to 0) VAA. Elite range is > -4.5 deg.
    # ---------------------------------------------------------------------------
    ff_df = df_qual[df_qual['pitch_type'] == 'FF'].copy()
    vaa_leaderboard = ff_df.groupby('player_name')['vaa'].agg(['mean', 'count']).reset_index()
    vaa_leaderboard = vaa_leaderboard[vaa_leaderboard['count'] >= 200] # Min 200 fastballs
    vaa_leaderboard = vaa_leaderboard.sort_values(by='mean', ascending=False).head(10)

    # ---------------------------------------------------------------------------
    # 2. THE SSW WIZARDS (Sinkers / 2-Seam only)
    # Goal: Highest deviation between Magnus model and actual break.
    # ---------------------------------------------------------------------------
    si_df = df_qual[df_qual['pitch_type'] == 'SI'].copy()
    ssw_leaderboard = si_df.groupby('player_name')['ssw_deviation'].agg(['mean', 'count']).reset_index()
    ssw_leaderboard = ssw_leaderboard[ssw_leaderboard['count'] >= 100] # Min 100 sinkers
    ssw_leaderboard = ssw_leaderboard.sort_values(by='mean', ascending=False).head(10)

    # ---------------------------------------------------------------------------
    # 3. THE TUNNELING MASTERS (All pitch types)
    # Goal: Smallest average distance between consecutive pitches at decision point.
    # ---------------------------------------------------------------------------
    tunnel_leaderboard = df_qual.groupby('player_name')['tunneling'].agg(['mean', 'count']).reset_index()
    tunnel_leaderboard = tunnel_leaderboard.sort_values(by='mean', ascending=True).head(10)

    # --- PRINT RESULTS ---
    print("\n" + "="*60)
    print("  TOP 10 VAA KINGS (Rising Fastball Effect)")
    print("  Higher mean (closer to 0) = Flatter approach")
    print("="*60)
    print(vaa_leaderboard.to_string(index=False))

    print("\n" + "="*60)
    print("  TOP 10 SSW WIZARDS (Seam-Shifted Wake Movement)")
    print("  Higher mean = More 'unnatural' sinker movement")
    print("="*60)
    print(ssw_leaderboard.to_string(index=False))

    print("\n" + "="*60)
    print("  TOP 10 TUNNELING MASTERS (Pitch Deception)")
    print("  Lower mean = Harder for batters to distinguish pitches")
    print("="*50)
    print(tunnel_leaderboard.to_string(index=False))

if __name__ == "__main__":
    generate_leaderboards()