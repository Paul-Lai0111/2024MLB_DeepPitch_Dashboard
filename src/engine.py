"""
engine.py

Feature engineering for the Big 6 advanced pitching metrics.
All calculations use vectorized NumPy/pandas operations for performance.

Physical constants and formulas are based on:
- Statcast Research (baseballsavant.mlb.com)
- Alan Nathan's physics of baseball (baseball.physics.illinois.edu)
- Driveline Baseball R&D publications

Unit conventions (following MLB Statcast standard):
- Distances: feet (except IVB/break which is reported in inches)
- Velocities: mph for release_speed, ft/s for internal calculations
- Angles: degrees (output), radians (internal)
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

GRAVITY_FT_S2 = 32.174        # gravitational acceleration (ft/s²)
MPH_TO_FT_S = 1.46667         # conversion factor: 1 mph = 1.46667 ft/s
HOME_PLATE_DISTANCE = 60.5    # pitcher's rubber to home plate (feet)
DECISION_POINT = 23.0         # approximate batter decision point from plate (feet)
INCHES_PER_FOOT = 12.0

# Magnus force scaling constant — empirically derived from 2024 Statcast data.
# k = observed_break_magnitude / (spin_rate / speed_ft_s)
# We use the 95th percentile so that spin_efficiency=1.0 corresponds to
# near-perfect spin efficiency, not the average pitch.
MAGNUS_K = 0.111600

# ---------------------------------------------------------------------------
# 1. IVB — Induced Vertical Break
# ---------------------------------------------------------------------------

def calc_ivb(pfx_z: pd.Series) -> pd.Series:
    """
    Calculate Induced Vertical Break (IVB).

    IVB measures the vertical movement caused purely by spin (Magnus force),
    with gravity's contribution already removed by Statcast's pfx_z.

    Statcast pfx_z is in feet — we convert to inches (industry standard).
    Positive IVB = ball rises relative to spinless trajectory (e.g. 4-seam FB)
    Negative IVB = ball drops faster than gravity alone (e.g. curveball)

    Args:
        pfx_z: Vertical movement vs. spinless trajectory (feet), from Statcast.

    Returns:
        IVB in inches.
    """
    return pfx_z * INCHES_PER_FOOT


# ---------------------------------------------------------------------------
# 2 & 3. VAA & HAA — Vertical and Horizontal Approach Angle
# ---------------------------------------------------------------------------

def _calc_velocity_at_plate(
    v0: pd.Series,
    a: pd.Series,
    vy0: pd.Series,
) -> pd.Series:
    """
    Calculate a velocity component at the moment the pitch crosses home plate.

    Statcast provides initial velocity (v0) and acceleration (a) at the
    release point (y=50 ft from plate). We integrate forward to y=0 (plate)
    using constant-acceleration kinematics:

        v_plate = sqrt(v0² + 2a × Δy)

    where Δy is the distance from release point reference to plate.

    Args:
        v0: Initial velocity component at y=50 ft reference point (ft/s).
        a:  Constant acceleration component (ft/s²).
        vy0: Initial y-velocity (ft/s), used to determine time of flight.

    Returns:
        Velocity component at home plate (ft/s).
    """
    # Statcast y-reference is 50 ft from home plate
    # Time to travel from y=50 to y=0 (plate):
    # y(t) = vy0*t + 0.5*ay*t² = 0  →  solve for t
    # We use the kinematic shortcut: v² = v0² + 2aΔy
    delta_y = 50.0  # feet from Statcast reference to plate
    return np.sqrt(np.maximum(v0**2 + 2 * a * delta_y, 0))


def calc_vaa(
    vz0: pd.Series,
    vy0: pd.Series,
    az: pd.Series,
    ay: pd.Series,
) -> pd.Series:
    """
    Calculate Vertical Approach Angle (VAA) at home plate.

    VAA is the vertical angle of the pitch trajectory as it crosses the plate.
    More negative VAA = steeper downward angle = harder to hit.

    Dodgers research: FF with VAA < -5.5° generates significantly higher
    whiff rates than shallower fastballs.

    Formula:
        VAA = arctan(vz_plate / |vy_plate|) × (180 / π)

    Args:
        vz0: Initial vertical velocity at release (ft/s).
        vy0: Initial y-velocity at release (ft/s), negative (toward plate).
        az:  Vertical acceleration (ft/s²).
        ay:  Y-axis acceleration (ft/s²).

    Returns:
        VAA in degrees. Typical range: -10° to -3°.
    """
    vz_plate = vz0 + az * _time_to_plate(vy0, ay)
    vy_plate = vy0 + ay * _time_to_plate(vy0, ay)

    # arctan(vz / |vy|) — vy is negative (moving toward plate), take absolute
    vaa = np.degrees(np.arctan2(vz_plate, np.abs(vy_plate)))
    return vaa


def calc_haa(
    vx0: pd.Series,
    vy0: pd.Series,
    ax: pd.Series,
    ay: pd.Series,
) -> pd.Series:
    """
    Calculate Horizontal Approach Angle (HAA) at home plate.

    HAA is the lateral angle of the pitch as it crosses the plate.
    Larger absolute HAA = more horizontal sweep = harder to track laterally.

    Args:
        vx0: Initial horizontal velocity at release (ft/s).
        vy0: Initial y-velocity at release (ft/s).
        ax:  Horizontal acceleration (ft/s²).
        ay:  Y-axis acceleration (ft/s²).

    Returns:
        HAA in degrees. Positive = arm-side run, negative = glove-side.
    """
    t = _time_to_plate(vy0, ay)
    vx_plate = vx0 + ax * t
    vy_plate = vy0 + ay * t

    haa = np.degrees(np.arctan2(vx_plate, np.abs(vy_plate)))
    return haa


def _time_to_plate(vy0: pd.Series, ay: pd.Series) -> pd.Series:
    """
    Calculate time of flight from Statcast reference point (y=50ft) to plate.

    Uses quadratic formula on y(t) = vy0*t + 0.5*ay*t² = -50
    (negative because we're moving 50 ft in the -y direction)

    Args:
        vy0: Initial y-velocity (ft/s), typically negative (~-130 ft/s).
        ay:  Y-axis acceleration (ft/s²).

    Returns:
        Time of flight in seconds. Typical range: 0.37–0.42s.
    """
    # Solve: 0.5*ay*t² + vy0*t + 50 = 0
    # t = (-vy0 - sqrt(vy0² - 4*(0.5*ay)*50)) / (2*0.5*ay)
    discriminant = vy0**2 - 2 * ay * 50
    discriminant = np.maximum(discriminant, 0)  # guard against floating point
    t = (-vy0 - np.sqrt(discriminant)) / ay
    return t


# ---------------------------------------------------------------------------
# 4. Spin Efficiency
# ---------------------------------------------------------------------------

def calc_spin_efficiency(
    release_speed: pd.Series,
    release_spin_rate: pd.Series,
    pfx_x: pd.Series,
    pfx_z: pd.Series,
) -> pd.Series:
    """
    Calculate Spin Efficiency — the fraction of spin that produces
    useful Magnus force (i.e. actual movement).

    Method: compare observed total break magnitude to the theoretical
    maximum break a pitch could generate given its spin rate and velocity.
    The ratio gives us efficiency.

    k is empirically derived from 2024 Statcast data (95th percentile
    of observed_break / (spin_rate / speed)), ensuring that efficiency=1.0
    represents near-perfect spin efficiency rather than the average pitch.

    Args:
        release_speed:    Pitch velocity at release (mph).
        release_spin_rate: Spin rate (rpm).
        pfx_x:            Horizontal movement vs spinless (feet).
        pfx_z:            Vertical movement vs spinless (feet).

    Returns:
        Spin efficiency as a ratio (0.0 to 1.0).
        NaN where spin_rate is missing.
    """
    # Observed break magnitude (feet)
    observed_break = np.sqrt(pfx_x**2 + pfx_z**2)

    # Convert speed to ft/s for consistent units
    speed_ft_s = release_speed * MPH_TO_FT_S

    # Theoretical maximum break using empirically calibrated k
    theoretical_max = MAGNUS_K * release_spin_rate / speed_ft_s

    # Guard against division by zero
    theoretical_max = theoretical_max.replace(0, np.nan)

    efficiency = (observed_break / theoretical_max).clip(0, 1)
    return efficiency


# ---------------------------------------------------------------------------
# 5. SSW Deviation — Seam-Shifted Wake
# ---------------------------------------------------------------------------

def calc_ssw_deviation(
    pfx_x: pd.Series,
    pfx_z: pd.Series,
    release_speed: pd.Series,
    release_spin_rate: pd.Series,
    spin_axis: pd.Series,
) -> pd.Series:
    """
    Calculate Seam-Shifted Wake (SSW) deviation in inches.

    SSW measures the distance between the actual observed movement and 
    the theoretical movement predicted by the Magnus force model.

    CRITICAL COORDINATE ALIGNMENT:
    - Statcast 0° (12 o'clock) = Pure Topspin -> Should result in negative pfx_z.
    - Statcast 180° (6 o'clock) = Pure Backspin -> Should result in positive pfx_z.
    - Statcast 90° (3 o'clock) = Pure Sidespin -> Should result in positive pfx_x.

    To align with math functions (sin/cos):
    - pred_pfx_x = sin(axis)
    - pred_pfx_z = -cos(axis)  <-- The negative sign corrects the vertical direction.
    """
    # Convert spin_axis to radians
    axis_rad = np.radians(spin_axis)

    # Calculate theoretical Magnus magnitude using calibrated MAGNUS_K
    speed_ft_s = release_speed * MPH_TO_FT_S
    theoretical_mag = MAGNUS_K * release_spin_rate / speed_ft_s
    
    # Project theoretical components onto X and Z axes
    # We use -cos for Z because 0° (Topspin) must push the ball DOWN.
    pred_pfx_x = theoretical_mag * np.sin(axis_rad)
    pred_pfx_z = -theoretical_mag * np.cos(axis_rad)

    # Compute Euclidean distance (deviation) between predicted and actual vectors
    deviation_ft = np.sqrt(
        (pfx_x - pred_pfx_x)**2 +
        (pfx_z - pred_pfx_z)**2
    )

    # Convert from feet to inches for industry standard reporting
    return deviation_ft * INCHES_PER_FOOT


# ---------------------------------------------------------------------------
# 6. Pitch Tunneling
# ---------------------------------------------------------------------------

def calc_tunneling(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Pitch Tunneling distance for each pitch.

    Tunneling measures how similar two consecutive pitches look to the batter
    at their decision point (~23 feet from the plate, ~0.15s after release).

    A pitch that passes through nearly the same window as the previous pitch
    before diverging is said to "tunnel" well — the batter commits before
    seeing the true break.

    Method:
    1. Project each pitch's position at the decision point using kinematics
    2. For each pitch, compute 3D Euclidean distance to the previous pitch
       in the same at-bat
    3. First pitch of each at-bat gets NaN (no previous pitch)

    Position at decision point (y = decision_point from plate):
        t_decision = time when y_from_release = total_distance - decision_point
        x(t) = release_pos_x + vx0*t + 0.5*ax*t²
        z(t) = release_pos_z + vz0*t + 0.5*az*t² - 0.5*g*t²

    Args:
        df: Cleaned DataFrame with columns:
            pitcher, batter, game_date, inning,
            vx0, vy0, vz0, ax, ay, az,
            release_pos_x, release_pos_z

    Returns:
        Series of tunneling distances in inches (NaN for first pitch of at-bat).
    """
    # --- Project position at decision point ---
    # Time for pitch to travel from release to decision_point distance from plate
    # release reference is at y=50ft from plate, so we travel to y=decision_point
    y_target = 50.0 - DECISION_POINT  # feet traveled from Statcast reference

    # Solve y(t) = vy0*t + 0.5*ay*t² = y_target
    # 0.5*ay*t² + vy0*t - y_target = 0
    discriminant = df["vy0"]**2 + 2 * df["ay"] * y_target
    t_decision = (-df["vy0"] - np.sqrt(discriminant.clip(0))) / df["ay"]

    # X position at decision point (horizontal)
    x_at_decision = (
        df["release_pos_x"]
        + df["vx0"] * t_decision
        + 0.5 * df["ax"] * t_decision**2
    )

    # Z position at decision point (vertical, include gravity)
    z_at_decision = (
        df["release_pos_z"]
        + df["vz0"] * t_decision
        + 0.5 * (df["az"] - GRAVITY_FT_S2) * t_decision**2
    )

    # --- Compute distance to previous pitch in same at-bat ---
    # Group by at-bat: same pitcher + batter + game_date + inning
    at_bat_key = (
        df["pitcher"].astype(str)
        + "_" + df["batter"].astype(str)
        + "_" + df["game_date"].astype(str)
        + "_" + df["inning"].astype(str)
    )

    # Shift within each at-bat to get previous pitch position
    prev_x = x_at_decision.groupby(at_bat_key).shift(1)
    prev_z = z_at_decision.groupby(at_bat_key).shift(1)

    # Euclidean distance in the x-z plane at decision point
    tunnel_distance_ft = np.sqrt(
        (x_at_decision - prev_x)**2 +
        (z_at_decision - prev_z)**2
    )

    # Convert to inches
    return tunnel_distance_ft * INCHES_PER_FOOT


# ---------------------------------------------------------------------------
# 7. Perceived Velocity
# ---------------------------------------------------------------------------

def calc_perceived_velocity(
    release_speed: pd.Series,
    release_extension: pd.Series,
) -> pd.Series:
    """
    Calculate Perceived Velocity (PV).

    A pitch released closer to the batter gives less reaction time,
    making it feel faster than its actual velocity.

    Formula (standard MLB calculation):
        PV = release_speed × (HOME_PLATE_DISTANCE / effective_distance)
    where:
        effective_distance = HOME_PLATE_DISTANCE - release_extension

    Example: 95 mph with 6.5 ft extension
        PV = 95 × (60.5 / 54.0) = 106.4 mph perceived

    Args:
        release_speed:     Actual velocity at release (mph).
        release_extension: How far in front of rubber pitcher releases (feet).
                           Typical range: 5.0–7.5 feet.

    Returns:
        Perceived velocity in mph.
    """
    effective_distance = HOME_PLATE_DISTANCE - release_extension

    # Guard against zero or negative effective distance
    effective_distance = effective_distance.clip(lower=1.0)

    return release_speed * (HOME_PLATE_DISTANCE / effective_distance)


# ---------------------------------------------------------------------------
# Master function — compute all Big 6 features at once
# ---------------------------------------------------------------------------

def compute_big6(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all Big 6 features and append them to the DataFrame.

    This is the main entry point for feature engineering.
    Input DataFrame must be the cleaned output from pipeline.py.

    New columns added:
        ivb             - Induced Vertical Break (inches)
        vaa             - Vertical Approach Angle (degrees)
        haa             - Horizontal Approach Angle (degrees)
        spin_efficiency - Spin Efficiency (0.0 to 1.0)
        ssw_deviation   - SSW Deviation (inches)
        tunneling       - Pitch Tunneling distance (inches)
        perceived_velo  - Perceived Velocity (mph)

    Args:
        df: Cleaned Statcast DataFrame from pipeline.py.

    Returns:
        Original DataFrame with 7 new feature columns appended.
    """
    print("[engine] Computing Big 6 features...")
    result = df.copy()

    # 1. IVB
    result["ivb"] = calc_ivb(df["pfx_z"])
    print(f"  ✓ IVB          | mean={result['ivb'].mean():.2f} in  | "
          f"range=[{result['ivb'].min():.1f}, {result['ivb'].max():.1f}]")

    # 2 & 3. VAA and HAA
    result["vaa"] = calc_vaa(df["vz0"], df["vy0"], df["az"], df["ay"])
    result["haa"] = calc_haa(df["vx0"], df["vy0"], df["ax"], df["ay"])
    print(f"  ✓ VAA          | mean={result['vaa'].mean():.2f}°  | "
          f"range=[{result['vaa'].min():.1f}, {result['vaa'].max():.1f}]")
    print(f"  ✓ HAA          | mean={result['haa'].mean():.2f}°  | "
          f"range=[{result['haa'].min():.1f}, {result['haa'].max():.1f}]")

    # 4. Spin Efficiency
    result["spin_efficiency"] = calc_spin_efficiency(
        df["release_speed"], df["release_spin_rate"], df["pfx_x"], df["pfx_z"]
    )
    print(f"  ✓ Spin Eff     | mean={result['spin_efficiency'].mean():.3f}  | "
          f"NaN={result['spin_efficiency'].isna().sum():,}")

    # 5. SSW Deviation
    result["ssw_deviation"] = calc_ssw_deviation(
        df["pfx_x"], df["pfx_z"], df["release_speed"],
        df["release_spin_rate"], df["spin_axis"]
    )
    print(f"  ✓ SSW Dev      | mean={result['ssw_deviation'].mean():.2f} in  | "
          f"NaN={result['ssw_deviation'].isna().sum():,}")

    # 6. Pitch Tunneling
    result["tunneling"] = calc_tunneling(df)
    print(f"  ✓ Tunneling    | mean={result['tunneling'].mean():.2f} in  | "
          f"NaN={result['tunneling'].isna().sum():,} (first pitch of each at-bat)")

    # 7. Perceived Velocity
    result["perceived_velo"] = calc_perceived_velocity(
        df["release_speed"], df["release_extension"]
    )
    print(f"  ✓ Perceived V  | mean={result['perceived_velo'].mean():.1f} mph | "
          f"range=[{result['perceived_velo'].min():.1f}, {result['perceived_velo'].max():.1f}]")

    print(f"\n[engine] Done. Shape: {result.shape}")
    return result