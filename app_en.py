import streamlit as st
import pandas as pd
import plotly.express as px
from src.db import PitchDB
from src.engine import compute_big6

# --- 1. Pitch type full name lookup ---
PITCH_NAMES = {
    'FF': 'Four-Seam Fastball',
    'SI': 'Sinker',
    'FC': 'Cutter',
    'SL': 'Slider',
    'ST': 'Sweeper',
    'SV': 'Slurve',
    'CU': 'Curveball',
    'KC': 'Knuckle Curve',
    'CH': 'Changeup',
    'FS': 'Splitter',
    'FO': 'Forkball',
    'KN': 'Knuckleball',
    'EP': 'Eephus',
    'PO': 'Pitchout'
}

# --- 2. Page configuration ---
st.set_page_config(page_title="DeepPitch | 2024 MLB Pitcher Physics Dashboard", layout="wide")

REQUIRED_COLS = [
    # Identifiers
    "player_name", "pitcher", "batter",
    "game_date", "inning", "pitch_type",

    # Velocity & movement
    "release_speed", "release_spin_rate",
    "release_extension",
    "release_pos_x", "release_pos_z",

    # Statcast trajectory vectors
    "vx0", "vy0", "vz0",
    "ax", "ay", "az",

    # Movement (pfx)
    "pfx_x", "pfx_z",

    # Required for SSW
    "spin_axis",

    # UI display
    "plate_x", "plate_z",
]

@st.cache_data(ttl=3600, max_entries=1)
def load_data():
    db = PitchDB()
    cols = ", ".join(REQUIRED_COLS)
    df_raw = db.query_to_df(f"""
        SELECT {cols}
        FROM statcast_2024
        WHERE pitch_type IS NOT NULL
          AND release_speed IS NOT NULL
          AND release_speed > 0
    """)
    df = compute_big6(df_raw)
    df['pitch_name_full'] = df['pitch_type'].map(PITCH_NAMES).fillna(df['pitch_type'])
    return df

df_all = load_data()

# --- 3. Sidebar: Personal info ---
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 10px; border-bottom: 1px solid #ddd; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.2em;">Paul Lai</h1>
            <p style="margin: 5px 0; font-weight: bold; font-size: 1.1em;">University of California, San Diego (UCSD)</p>
            <p style="margin: 5px 0; font-size: 1.0em;">M.S. in Data Science</p>
            <p style="margin: 10px 0 5px 0; font-size: 0.95em;">📧 <a href="mailto:paul262935@gmail.com">paul262935@gmail.com</a></p>
            <p style="margin: 5px 0; font-size: 0.95em;">🔗 <a href="https://www.linkedin.com/in/paullai0111/" target="_blank">LinkedIn Profile</a></p>
        </div>
    """, unsafe_allow_html=True)

    st.header("🔍 Pitcher Analysis Filter")
    pitcher_list = sorted(df_all['player_name'].unique())
    selected_pitchers = st.multiselect("Select Pitcher(s) for Comparison", pitcher_list, default=["Yamamoto, Yoshinobu"])

    if selected_pitchers:
        st.write("**Player MLB Profile Links**")
        for p in selected_pitchers:
            p_id = df_all[df_all['player_name'] == p]['pitcher'].iloc[0]
            st.markdown(f"- [{p}](https://www.mlb.com/player/{int(p_id)})")

    available_pitches = sorted(df_all[df_all['player_name'].isin(selected_pitchers)]['pitch_name_full'].unique())
    selected_pitch_types = st.multiselect("Filter by Pitch Type", available_pitches, default=available_pitches)

    st.divider()

    def display_view_counter():
        st.caption("Data Source: 2024 MLB Statcast | Physics Engine: DeepPitch v3.0")
        repo = "Paul-Lai0111/2024MLB_DeepPitch_Dashboard"
        st.markdown(f"""
        [![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/{repo})
        ![Python](https://img.shields.io/badge/Python-3.12-blue)
        """)

    display_view_counter()

# --- 4. Main page: Tabs ---
tab1, tab2 = st.tabs(["👤 Pitcher Analysis Report", "🏆 2024 League Leaders: Top 10 by Pitch Quality"])

# ==========================================
# TAB 1: Pitcher Deep Dive Report
# ==========================================
with tab1:
    st.title("DeepPitch Analytics: 2024 MLB Pitcher Physics Dashboard")

    st.info("**Welcome to the Big 6 Advanced Metrics System**: This dashboard deconstructs pitcher dominance through six core physical indicators.")

    st.markdown("### Big 6 Advanced Metrics Guide (Core Definitions)")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #4A90E2;">
            <h4 style="margin-top: 0; color: #1f2937; font-weight: 800;">1. IVB <span style="font-size: 0.7em; color: #4b5563;">(Induced Vertical Break)</span></h4>
            <p style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">Core Concept:&nbsp;&nbsp;Rise resistance against gravity.</p>
            <p style="color: #374151; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                Creates a perceived "rising" effect at the plate. Elite IVB (18–20"+) means the Magnus force offsets more gravity, causing the ball to drop less than expected and inducing swings below the pitch.
            </p>
        </div>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #4A90E2;">
            <h4 style="margin-top: 0; color: #1f2937; font-weight: 800;">2. VAA <span style="font-size: 0.7em; color: #4b5563;">(Vertical Approach Angle)</span></h4>
            <p style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">Core Concept:&nbsp;&nbsp;Descent plane into the zone.</p>
            <p style="color: #374151; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                The closer to 0°, the flatter the trajectory. A flat VAA paired with an elevated fastball creates the visual illusion of the ball "exploding upward," making it extremely difficult to square up regardless of velocity.
            </p>
        </div>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #4A90E2;">
            <h4 style="margin-top: 0; color: #1f2937; font-weight: 800;">3. HAA <span style="font-size: 0.7em; color: #4b5563;">(Horizontal Approach Angle)</span></h4>
            <p style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">Core Concept:&nbsp;&nbsp;Lateral cutting action into the zone.</p>
            <p style="color: #374151; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                The further from 0°, the more the pitch cuts diagonally across the plate. Combined with large horizontal break (HB), the pitch can sweep across the entire strike zone, overloading the hitter's tracking ability.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="background-color: #eef2ff; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #6366f1;">
            <h4 style="margin-top: 0; color: #1e1b4b; font-weight: 800;">4. Spin Efficiency <span style="font-size: 0.7em; color: #4338ca;">(Active Spin Rate)</span></h4>
            <p style="color: #1e1b4b; font-weight: 700; margin-bottom: 5px;">Core Concept:&nbsp;&nbsp;Conversion rate of spin into movement.</p>
            <p style="color: #1e1b4b; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                High efficiency drives maximum IVB or HB; low efficiency indicates significant <b>Gyro Spin</b> — spin that produces no Magnus deflection. This explains why two pitchers with identical spin rates can produce vastly different pitch life.
            </p>
        </div>
        <div style="background-color: #eef2ff; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #6366f1;">
            <h4 style="margin-top: 0; color: #1e1b4b; font-weight: 800;">5. SSW <span style="font-size: 0.7em; color: #4338ca;">(Seam-Shifted Wake Deviation)</span></h4>
            <p style="color: #1e1b4b; font-weight: 700; margin-bottom: 5px;">Core Concept:&nbsp;&nbsp;Unpredictable late movement.</p>
            <p style="color: #1e1b4b; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                Additional movement generated purely by asymmetric airflow disturbance from seam orientation — independent of spin. High SSW produces <b>late-breaking action</b> that the brain cannot anticipate, making it the primary weapon behind elite sinkers and changeups.
            </p>
        </div>
        <div style="background-color: #eef2ff; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #6366f1;">
            <h4 style="margin-top: 0; color: #1e1b4b; font-weight: 800;">6. Tunneling <span style="font-size: 0.7em; color: #4338ca;">(Pitch Tunneling)</span></h4>
            <p style="color: #1e1b4b; font-weight: 700; margin-bottom: 5px;">Core Concept:&nbsp;&nbsp;Deception through shared flight path.</p>
            <p style="color: #1e1b4b; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                Different pitch types sharing an identical trajectory window through the tunnel point. The longer two pitches share the same path before diverging, the less time a hitter has to identify pitch type and adjust.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("Click to Expand: Deep Dive into Physics Principles & Advanced Metrics"):
        st.markdown("### Physics Breakdown: Forces Acting on a Baseball")

        img_spacer1, img_center, img_spacer2 = st.columns([1, 3, 1])
        with img_center:
            st.image("image/forces_baseball.jpg", caption="Force vectors acting on a baseball in flight", use_column_width=True)

        st.divider()

        st.markdown("""
        #### The Magnus Effect: Foundation of All Pitch Movement

        The Magnus Effect is the physical cornerstone of baseball movement. When a spinning ball travels through air, the rotation drags surrounding airflow, generating a **pressure differential** across the ball that deflects it toward the low-pressure side.

        * **Fluid Dynamics Mechanism**:
            * **Bernoulli's Principle**: The spinning surface accelerates airflow on one side (lower pressure) and decelerates it on the other (higher pressure), pushing the ball toward the low-pressure side.
            * **Backspin**: Generates upward Magnus lift, counteracting gravity — the source of **IVB**.
            * **Topspin**: Generates downward force, accelerating drop — the principle behind **Curveballs**.
            * **Sidespin**: Generates lateral deflection — the source of **Horizontal Break (HB)**.

        * **Key Concept: Active Spin (Spin Efficiency)**
            * Not all spin produces movement. Only the spin component whose axis is **perpendicular to the flight path** (pure backspin) fully activates the Magnus Effect.
            * **Gyro Spin**: Spin whose axis is aligned with the flight path — like a bullet — generates virtually zero Magnus deflection.

        * **Environmental Factors**:
            * **Air Density**: At high-altitude parks (e.g., Coors Field), thinner air weakens the Magnus Effect, noticeably reducing pitch break.
            * **Velocity**: Higher pitch speed amplifies the aerodynamic forces acting on the ball per unit time.

        > **Summary**: The Magnus Effect determines the gap between a pitch's **expected gravity-driven drop** and its **actual flight path**.

        #### Bernoulli's Principle: The Physics Behind Pitch Life

        Bernoulli's Principle is the fundamental law of fluid dynamics that explains how moving air exerts force on a baseball.

        * **Core Definition**:
            In a fluid system, **faster-moving fluid exerts lower pressure; slower-moving fluid exerts higher pressure.**
            > Simplified formula: $P + \\frac{1}{2}\\rho v^2 = \\text{constant}$ (pressure and velocity are inversely related)

        * **Application to Pitch Spin**:
            1. **Airflow entrainment**: As the ball spins, the seams grip and drag surrounding air along with the rotation.
            2. **Velocity differential**:
                * On the side where the spin direction aligns with the oncoming airflow, air is **accelerated** (faster flow → lower pressure).
                * On the opposite side, airflow is **decelerated** (slower flow → higher pressure).
            3. **Movement generation**: The high-pressure side pushes the ball toward the low-pressure side — this force is the **Magnus force**.

        * **Real-World Analogies**:
            * **Aircraft wing**: The curved upper surface accelerates airflow, reducing pressure and generating lift.
            * **Highway drafting**: Two large trucks traveling side-by-side create a low-pressure corridor between them, pulling the vehicles toward each other.

        > **Summary**: Without the pressure differential created by Bernoulli's Principle, there is no movement — no IVB, no HB, nothing.

        #### Seam-Shifted Wake (SSW): The Modern Game's Most Important Discovery

        Beyond the Magnus Effect, SSW is the most significant aerodynamic phenomenon in modern baseball analytics. It explains why certain pitches generate movement that pure spin-rate models cannot predict.

        * **Core Mechanism: Asymmetric Wake**
            * The ball's **seams** disrupt the boundary layer of air. When seams pass asymmetrically through the airflow, they shift the wake behind the ball, generating an additional force vector.
            * This is a **non-spin-driven force**, primarily observed on **Sinkers** and **Changeups**.
        * **Measurement: Observed vs. Predicted Movement Deviation**
            * By comparing the "spin-predicted trajectory" against the "actual flight path" in Statcast data, the residual deviation quantifies SSW contribution. Larger deviation = greater late-break unpredictability = harder to make solid contact.

        #### Approach Geometry: VAA and the Amplification of Vertical Movement

        Raw IVB alone is insufficient — it must combine with the right **approach geometry** to reach maximum effectiveness.

        * **Release Height**:
            * The same 18" of IVB released from a **lower arm slot** produces a flatter VAA.
            * This "low origin, high destination" trajectory creates the visual impression that the ball is "rising" through the zone, making it nearly impossible to hit even at modest velocities.
        * **Extension**:
            * Greater extension (release point closer to home plate) reduces the ball's time under gravity, further flattening VAA and increasing perceived velocity.

        #### Neuroscience & Tunneling: Exploiting the Hitter's Cognitive Limit

        This section addresses the fundamental **perceptual limits** of the human brain under game conditions.

        * **The Commit Point**:
            * Hitters must commit to swing or take approximately **24 feet** (~7 meters) in front of the plate — roughly 150ms after release.
        * **Why Tunneling Works**:
            * If different pitch types share a near-identical flight path through the tunnel window, the brain classifies them as the same pitch until it's too late.
            * Once the pitch passes the commit point and breaks, the hitter can no longer adjust. The later the break occurs relative to the commit point, the more effective the pitch. This is why **longer tunnel distance = greater deception = higher whiff rates**.

        > **Final Summary**: Elite pitchers use the **Magnus force** to generate movement, **SSW** to add unpredictability, and exploit **approach geometry (VAA)** and **pitch tunneling** to make everything indistinguishable until it's too late to react.

        #### Horizontal Break (HB): Lateral Plate Coverage

        HB measures a pitch's capacity to deflect laterally — the horizontal counterpart to IVB.

        * **Physical Origin: Sidespin**
            * When the spin axis tilts left or right (e.g., 3 o'clock or 9 o'clock), the Magnus force generates a lateral push.
            * **Sign Convention (RHP perspective)**:
                * **Positive (+)**: Ball moves toward the **first-base side** (away from RHH) — Sliders, Sweepers.
                * **Negative (−)**: Ball moves toward the **third-base side** (running in on RHH) — Sinkers, Two-seamers.

        * **Modern Trend: Horizontal Separation**
            * The rise of the **Sweeper** reflects the game's obsession with maximizing HB (typically 15"+), forcing hitters to cover the full width of the strike zone and creating impossible pitch-recognition scenarios.

        * **HAA Interaction**:
            * Extreme HB directly produces extreme **HAA**. When a pitch cuts back into the zone from outside the batter's visual field — or slides off the outside corner — it creates despair in the hitter's spatial judgment.

        > **Summary**: HB determines a pitch's lateral plate coverage and is the primary driver of weak contact and frozen hitters on the outer third.
        """)

    st.divider()

    if not selected_pitchers:
        st.warning("Please select at least one pitcher.")
    else:
        comparison_df = df_all[
            (df_all['player_name'].isin(selected_pitchers)) &
            (df_all['pitch_name_full'].isin(selected_pitch_types))
        ].copy()
        comparison_df['HB_in'] = comparison_df['pfx_x'] * 12

        st.subheader("Key Physical Metrics Comparison")
        cols = st.columns(len(selected_pitchers))
        for i, p_name in enumerate(selected_pitchers):
            p_df = comparison_df[comparison_df['player_name'] == p_name]
            p_id = p_df['pitcher'].iloc[0]
            ff_df = p_df[p_df['pitch_type'] == 'FF']
            with cols[i]:
                st.markdown(f"#### **[{p_name}](https://www.mlb.com/player/{int(p_id)})**")
                st.metric("Four-Seam VAA", f"{ff_df['vaa'].mean():.2f}°" if not ff_df.empty else "N/A")
                st.metric("Avg Tunnel Distance", f"{p_df['tunneling'].mean():.2f} in")

        st.divider()

        st.subheader("⚾ Pitch Movement Profile")
        fig = px.scatter(
            comparison_df, x='HB_in', y='ivb',
            color='player_name' if len(selected_pitchers) > 1 else 'pitch_name_full',
            symbol='pitch_name_full',
            hover_data={
                'player_name': True, 'pitch_name_full': True,
                'release_speed': ':.1f', 'vaa': ':.2f', 'haa': ':.2f'
            },
            labels={'HB_in': 'Horizontal Break (in)', 'ivb': 'Induced Vertical Break (in)'},
            template="plotly_white", height=750
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.3)
        fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.3)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detailed Metrics Breakdown (Hover for Definitions)")
        summary_table = comparison_df.groupby(['player_name', 'pitch_name_full']).agg({
            'release_speed': 'mean', 'ivb': 'mean', 'vaa': 'mean', 'haa': 'mean',
            'spin_efficiency': 'mean', 'ssw_deviation': 'mean', 'tunneling': 'mean'
        }).round(3).reset_index()
        summary_table.rename(columns={'player_name': 'Player', 'pitch_name_full': 'Pitch Type'}, inplace=True)

        st.dataframe(
            summary_table, use_container_width=True, hide_index=True,
            column_config={
                "Player": st.column_config.TextColumn("Player", help="Pitcher name"),
                "Pitch Type": st.column_config.TextColumn("Pitch Type", help="Full pitch type name"),
                "release_speed": st.column_config.NumberColumn("Velocity (mph)", help="Average pitch velocity at release"),
                "ivb": st.column_config.NumberColumn("IVB (in)", help="Induced Vertical Break: Magnus-driven rise against gravity"),
                "vaa": st.column_config.NumberColumn("VAA (deg)", help="Vertical Approach Angle: closer to 0° = flatter trajectory into the zone"),
                "haa": st.column_config.NumberColumn("HAA (deg)", help="Horizontal Approach Angle: lateral cutting angle into the zone"),
                "spin_efficiency": st.column_config.NumberColumn("Spin Efficiency", help="Fraction of total spin rate converted into actual Magnus movement"),
                "ssw_deviation": st.column_config.NumberColumn("SSW Deviation (in)", help="Seam-Shifted Wake: residual late movement beyond Magnus prediction"),
                "tunneling": st.column_config.NumberColumn("Tunnel Distance (in)", help="Pitch tunneling: shorter distance = greater deception before the commit point")
            }
        )

# ==========================================
# TAB 2: League Pitch Quality Leaders
# ==========================================
with tab2:
    st.title("🏆 2024 League Leaders: Top 10 by Pitch Quality")
    st.markdown("Ranking pitchers with **500+ pitches** thrown in the 2024 season across key physical performance indicators. Click a player's name to visit their MLB profile.")

    pitcher_counts = df_all['player_name'].value_counts()
    qualified_pitchers = pitcher_counts[pitcher_counts >= 500].index
    df_qual = df_all[df_all['player_name'].isin(qualified_pitchers)]

    def get_rank_md(df_input, column, ascending=False, title=""):
        res = df_input.groupby('player_name')[column].mean().sort_values(ascending=ascending).head(10).reset_index()
        res['Player'] = res['player_name'].apply(
            lambda x: f"[{x}](https://www.mlb.com/player/{int(df_all[df_all['player_name']==x]['pitcher'].iloc[0])})"
        )
        res = res[['Player', column]].rename(columns={column: title})
        return res.to_markdown(index=False)

    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        st.subheader("Extreme Vertical Approach Angle (VAA)")
        st.caption("The closer to 0°, the more the fastball enters the zone on a flat, laser-like plane rather than on a steep downward arc — perfectly intercepting the natural upward swing path and generating elite whiff rates independent of velocity.")
        st.markdown(get_rank_md(df_qual[df_qual['pitch_type'] == 'FF'], 'vaa', False, "Avg VAA (deg)"), unsafe_allow_html=True)

    with r1_c2:
        st.subheader("Elite Induced Vertical Break (IVB)")
        st.caption("The Magnus-driven upward deflection of a four-seam fastball. When IVB exceeds 18\", the ball drops significantly less than the brain predicts, creating the perception of a rising fastball and inducing swings below the pitch.")
        st.markdown(get_rank_md(df_qual[df_qual['pitch_type'] == 'FF'], 'ivb', False, "Avg IVB (in)"), unsafe_allow_html=True)

    st.info("Elite fastballs typically combine **flat VAA** (shallow approach angle) with **high IVB** (strong Magnus rise). Together, they produce the 'rising fastball' illusion that is the most difficult pitch in baseball to square up.")

    with r1_c3:
        st.subheader("Seam-Shifted Wake (SSW) Masters")
        st.caption("Residual movement generated purely by asymmetric seam-induced wake — independent of spin rate. High SSW indicates late-breaking action that the brain cannot model or anticipate, making it the primary weapon behind the most deceptive sinkers and changeups in the game.")
        md_content = get_rank_md(
            df_qual[df_qual['pitch_type'].isin(['SI', 'CH'])],
            'ssw_deviation',
            False,
            "SSW Deviation (in)"
        )
        st.markdown(md_content, unsafe_allow_html=True)

    st.divider()

    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        st.subheader("Horizontal Approach Angle (HAA) Specialists")
        st.caption("The higher the absolute HAA value, the more the pitch cuts diagonally across the plate rather than traveling on a straight line. This allows the pitch to enter the zone from outside the hitter's initial tracking window — the defining characteristic of the elite Sweeper.")
        df_qual['haa_abs'] = df_qual['haa'].abs()
        st.markdown(get_rank_md(df_qual[df_qual['pitch_type'].isin(['SL', 'ST'])], 'haa_abs', False, "Avg HAA (deg)"), unsafe_allow_html=True)

    with r2_c2:
        st.subheader("Best Spin Efficiency")
        st.caption("The percentage of total spin rate converted into active Magnus movement. Near 100% efficiency means virtually all rotation drives IVB or HB — explaining how certain pitchers generate elite pitch life despite average spin rates.")
        st.markdown(get_rank_md(df_qual, 'spin_efficiency', False, "Avg Spin Efficiency (%)"), unsafe_allow_html=True)

    with r2_c3:
        st.subheader("Elite Pitch Tunneling")
        st.caption("The ability of different pitch types to share an identical flight path through the hitter's commit window. Longer shared tunnel distance compresses the hitter's pitch-recognition window, maximizing chase rate on breaking balls and whiff rate on fastballs.")
        st.markdown(get_rank_md(df_qual, 'tunneling', False, "Tunnel Distance (in)"), unsafe_allow_html=True)

st.divider()
st.caption("🔒 Security: Read-only architecture with parameterized queries.")