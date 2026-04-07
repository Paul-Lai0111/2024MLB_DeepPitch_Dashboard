"""
pipeline.py

Responsible for fetching, cleaning, and storing Statcast pitch-by-pitch data.
Data source: Baseball Savant via the pybaseball library.

Design decisions:
- Fetch by month to avoid API timeouts (~70k pitches/month)
- Store as Parquet for fast I/O in downstream feature engineering
- Also persist to DuckDB for SQL-based queries in the dashboard
- Use pybaseball cache only during development (use_cache=True)
"""

import os
import time
import pandas as pd
import pybaseball as pb
from pathlib import Path
from tqdm import tqdm

from src.db import PitchDB


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# Columns we actually need — dropping the rest keeps file size manageable
REQUIRED_COLUMNS = [
    # Identifiers
    "game_date", "game_type", "player_name", "pitcher", "batter",
    "stand", "p_throws", "home_team", "away_team", "inning",

    # Pitch physical properties
    "pitch_type", "pitch_name", "release_speed", "release_spin_rate",
    "spin_axis", "release_extension", "release_pos_x", "release_pos_z",

    # Movement (pfx = movement in inches vs. spinless trajectory)
    "pfx_x", "pfx_z",

    # Plate location
    "plate_x", "plate_z",

    # Trajectory waypoints (used for spatiotemporal modeling)
    "vx0", "vy0", "vz0",   # initial velocity components
    "ax", "ay", "az",       # acceleration components

    # Outcome
    "description", "type", "bb_type",
    "launch_speed", "launch_angle",
    "estimated_woba_using_speedangle",  # xwOBA
    "woba_value",
    "delta_run_exp",
]

# Game types to EXCLUDE — we only want regular season and playoffs
EXCLUDED_GAME_TYPES = {"S", "E", "A"}  # S=Spring, E=Exhibition, A=All-Star

# Known bad pitch type labels to fix
PITCH_TYPE_MAP = {
    "FA": "FF",   # generic fastball → four-seam
    "IN": None,   # intentional ball — drop entirely
    "PO": None,   # pitchout — drop entirely
    "EP": None,   # eephus — extremely rare, drop
}


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_statcast_month(year: int, month: int) -> pd.DataFrame:
    """
    Fetch all Statcast pitch data for a given year/month.

    pybaseball's statcast() function pulls from Baseball Savant.
    We pass start/end date to keep each request small (~70k rows).

    Args:
        year: Season year (e.g. 2024).
        month: Month number (1-12).

    Returns:
        Raw DataFrame from Statcast, or empty DataFrame on failure.
    """
    # Build first and last day of the month
    start = f"{year}-{month:02d}-01"

    # Calculate last day (works for all months including Feb)
    last_day = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
    end = last_day.strftime("%Y-%m-%d")

    print(f"  Fetching {year}-{month:02d}  ({start} → {end})")

    try:
        df = pb.statcast(start_dt=start, end_dt=end, verbose=False)
        print(f"  ✓ {len(df):,} pitches fetched")
        return df
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return pd.DataFrame()


def fetch_season(year: int, months: list[int] | None = None) -> pd.DataFrame:
    """
    Fetch a full season of Statcast data, month by month.

    Regular season runs April–October (months 4–10).
    Postseason can bleed into November.

    Args:
        year: Season year.
        months: List of months to fetch. Defaults to April–October.

    Returns:
        Combined DataFrame for the full season.
    """
    if months is None:
        months = list(range(4, 11))  # April=4 through October=10

    frames = []

    for month in tqdm(months, desc=f"Fetching {year} season"):
        df = fetch_statcast_month(year, month)

        if df.empty:
            continue

        frames.append(df)

        # Be polite to the Baseball Savant API — pause between requests
        time.sleep(3)

    if not frames:
        print(f"[pipeline] No data fetched for {year}")
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    print(f"\n[pipeline] {year} total: {len(combined):,} pitches across {len(frames)} months")
    return combined


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def clean_statcast(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize raw Statcast data.

    Steps:
    1. Drop Spring Training, Exhibition, and All-Star game pitches
    2. Keep only the columns we need
    3. Fix known bad pitch_type labels
    4. Precise deduplication using sv_id
    5. Drop rows with missing critical physics columns
    6. Fix dtypes
    7. Sort by game_date and pitcher (required for Tunneling calculation)

    Args:
        df: Raw DataFrame from fetch_season().

    Returns:
        Cleaned DataFrame ready for feature engineering.
    """
    original_len = len(df)
    print(f"[clean] Starting with {original_len:,} rows")

    # --- Step 1: Remove non-regular-season games ---
    if "game_type" in df.columns:
        df = df[~df["game_type"].isin(EXCLUDED_GAME_TYPES)]
        print(f"[clean] After removing Spring/Exhibition/All-Star: {len(df):,} rows")

    # --- Step 2: Keep only relevant columns ---
    available = [c for c in REQUIRED_COLUMNS if c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        print(f"[clean] Warning — columns not found in data: {missing}")
    df = df[available].copy()

    # --- Step 3: Fix pitch type labels ---
    df["pitch_type"] = df["pitch_type"].replace(
        {k: v for k, v in PITCH_TYPE_MAP.items() if v is not None}
    )
    drop_types = {k for k, v in PITCH_TYPE_MAP.items() if v is None}
    df = df[~df["pitch_type"].isin(drop_types)]
    df = df[df["pitch_type"].notna() & (df["pitch_type"] != "")]

    # --- Step 4: Deduplication ---
    # sv_id is no longer populated by Baseball Savant as of 2024.
    # Instead, use a composite key that uniquely identifies each pitch.
    DEDUP_COLS = [
        "game_date", "pitcher", "batter",
        "inning", "pitch_type", "release_speed",
        "plate_x", "plate_z"
        ]

    available_dedup = [c for c in DEDUP_COLS if c in df.columns]
    before = len(df)
    df = df.drop_duplicates(subset=available_dedup)
    dupes = before - len(df)
    if dupes > 0:
        print(f"[clean] Removed {dupes:,} duplicate pitches (composite key)")
    else:
        print(f"[clean] No duplicates found")

    # --- Step 5: Drop rows missing critical physics columns ---
    # These are required for Big 6 feature engineering
    physics_cols = ["release_speed", "pfx_x", "pfx_z", "release_extension"]
    before = len(df)
    df = df.dropna(subset=physics_cols)
    dropped = before - len(df)
    if dropped > 0:
        print(f"[clean] Dropped {dropped:,} rows missing critical physics columns")

    # spin_axis has ~15% missing rate — keep rows but note it
    # SSW calculation will handle missing spin_axis separately
    spin_missing = df["spin_axis"].isna().sum() if "spin_axis" in df.columns else 0
    if spin_missing > 0:
        print(f"[clean] Note: {spin_missing:,} rows have missing spin_axis (kept, flagged)")

    # --- Step 6: Fix dtypes ---
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["release_speed"] = pd.to_numeric(df["release_speed"], errors="coerce")
    df["release_spin_rate"] = pd.to_numeric(df["release_spin_rate"], errors="coerce")

    # --- Step 7: Sort by date then pitcher ---
    # Critical for Pitch Tunneling: ensures pitch sequences are in
    # chronological order within each at-bat
    df = df.sort_values(["game_date", "pitcher"]).reset_index(drop=True)

    print(f"[clean] Final: {len(df):,} rows  (removed {original_len - len(df):,} total)")
    return df


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

def save_raw(df: pd.DataFrame, year: int) -> Path:
    """
    Save raw (uncleaned) Statcast data to Parquet.

    We save raw data before cleaning so we can always re-run
    the cleaning step without re-fetching from the API.

    Args:
        df: Raw DataFrame.
        year: Season year (used in filename).

    Returns:
        Path to the saved file.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"statcast_{year}_raw.parquet"
    df.to_parquet(path, index=False, compression="snappy")
    print(f"[pipeline] Raw data saved → {path}  ({path.stat().st_size / 1e6:.1f} MB)")
    return path


def save_processed(df: pd.DataFrame, year: int) -> Path:
    """
    Save cleaned Statcast data to Parquet and DuckDB.

    Args:
        df: Cleaned DataFrame.
        year: Season year (used in filename and table name).

    Returns:
        Path to the saved Parquet file.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Save as Parquet
    path = PROCESSED_DIR / f"statcast_{year}_clean.parquet"
    df.to_parquet(path, index=False, compression="snappy")
    print(f"[pipeline] Clean data saved → {path}  ({path.stat().st_size / 1e6:.1f} MB)")

    # Also persist to DuckDB for SQL queries
    db = PitchDB()
    db.save_dataframe(df, table_name=f"statcast_{year}", mode="replace")

    return path


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_pipeline(years: list[int], use_cache: bool = False) -> pd.DataFrame:
    """
    Full pipeline: fetch → clean → save for one or more seasons.

    Args:
        years: List of season years to process, e.g. [2024, 2025].
        use_cache: If True, enables pybaseball disk cache to speed up
                   repeated fetches during development. Disable for
                   production runs to always get fresh data.

    Returns:
        Combined cleaned DataFrame for all requested years.
    """
    # Control pybaseball cache explicitly
    if use_cache:
        pb.cache.enable()
        print("[pipeline] pybaseball cache ENABLED")
    else:
        pb.cache.disable()
        print("[pipeline] pybaseball cache DISABLED")

    all_frames = []

    for year in years:
        print(f"\n{'='*50}")
        print(f" Processing {year} season")
        print(f"{'='*50}")

        # 1. Fetch
        raw_df = fetch_season(year)
        if raw_df.empty:
            print(f"[pipeline] Skipping {year} — no data returned")
            continue

        # 2. Save raw (before any cleaning)
        save_raw(raw_df, year)

        # 3. Clean
        clean_df = clean_statcast(raw_df)

        # 4. Save processed
        save_processed(clean_df, year)

        all_frames.append(clean_df)

    if not all_frames:
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    print(f"\n[pipeline] All done. Total rows: {len(combined):,}")
    return combined


if __name__ == "__main__":
    # Full 2024 season fetch (April through October)
    # use_cache=True allows resuming if the connection drops mid-way
    run_pipeline(years=[2024], use_cache=True)