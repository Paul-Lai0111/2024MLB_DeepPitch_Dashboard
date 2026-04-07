import streamlit as st
import pandas as pd
import plotly.express as px
from src.db import PitchDB
from src.engine import compute_big6

# --- 1. 球種完整名稱對照表 ---
PITCH_NAMES = {
    'FF': '四縫線速球 (Four-Seam Fastball)',
    'SI': '伸卡球/二縫線 (Sinker)',
    'FC': '切球 (Cutter)',
    'SL': '滑球 (Slider)',
    'ST': '橫掃球 (Sweeper)',
    'SV': '曲滑球 (Slurve)',
    'CU': '曲球 (Curveball)',
    'KC': '彈指曲球 (Knuckle Curve)',
    'CH': '變速球 (Changeup)',
    'FS': '指叉球 (Splitter)',
    'FO': '叉指變速球 (Forkball)',
    'KN': '彈指球 (Knuckleball)',
    'EP': '小便球 (Eephus)',
    'PO': '牽制投球 (Pitch Out)'
}

# --- 2. 頁面基本設定 ---
st.set_page_config(page_title="DeepPitch | 2024 MLB投手物理分析儀表板", layout="wide")

@st.cache_data
def load_data():
    db = PitchDB()
    df_raw = db.query_to_df("SELECT * FROM statcast_2024")
    df = compute_big6(df_raw)
    df['pitch_name_full'] = df['pitch_type'].map(PITCH_NAMES).fillna(df['pitch_type'])
    return df

df_all = load_data()

# --- 3. 側邊欄：個人資訊 ---
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 10px; border-bottom: 1px solid #ddd; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.2em;">Paul Lai</h1>
            <p style="margin: 5px 0; font-weight: bold; font-size: 1.1em;">加州大學聖地牙哥分校 (UCSD)</p>
            <p style="margin: 5px 0; font-size: 1.0em;">資料科學碩士 (MS in Data Science)</p>
            <p style="margin: 10px 0 5px 0; font-size: 0.95em;">📧 <a href="mailto:paul262935@gmail.com">paul262935@gmail.com</a></p>
            <p style="margin: 5px 0; font-size: 0.95em;">🔗 <a href="https://www.linkedin.com/in/paullai0111/" target="_blank">LinkedIn Profile</a></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.header("🔍 投手分析篩選") 
    pitcher_list = sorted(df_all['player_name'].unique())
    selected_pitchers = st.multiselect("選擇投手 (可複選對比)", pitcher_list, default=["Yamamoto, Yoshinobu"])
    
    if selected_pitchers:
        st.write("**選手 MLB 官網連結**")
        for p in selected_pitchers:
            p_id = df_all[df_all['player_name'] == p]['pitcher'].iloc[0]
            st.markdown(f"- [{p}](https://www.mlb.com/player/{int(p_id)})")

    available_pitches = sorted(df_all[df_all['player_name'].isin(selected_pitchers)]['pitch_name_full'].unique())
    selected_pitch_types = st.multiselect("篩選特定球種", available_pitches, default=available_pitches)
    
    st.divider()
    # 在 app_mandarin.py 中
    import streamlit as st

    def display_view_counter():
        # 顯示小標題
        st.caption("數據來源: 2024 MLB Statcast | 物理引擎: DeepPitch v3.0")
    
        repo = "Paul-Lai0111/2024MLB_DeepPitch_Dashboard"
        st.markdown(f"""
        [![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/{repo})
        ![Python](https://img.shields.io/badge/Python-3.12-blue)
        """)
    


    # 直接在側邊欄呼叫
    display_view_counter()

# --- 4. 主頁面：建立 Tabs ---
tab1, tab2 = st.tabs(["👤 投手分析報告", "🏆 聯盟球員球質Top 10"])

# ==========================================
# TAB 1: 投手深度報告
# ==========================================
with tab1:
    st.title("DeepPitch Analytics: 2024 大聯盟投手物理分析儀表板")

    # --- 使用 st.info 建立導讀區 ---
    st.info("**歡迎使用 Big 6 進階物理指標系統**：本儀表板透過六大核心數據，拆解大聯盟投手的壓制力來源。")

    # --- 利用 Columns 或是清單樣式美化指南 ---
    st.markdown("### Big 6 進階數據指南 (核心定義)")
    
 # 使用卡片式排版，並將「核心」獨立成行以利快速閱讀
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #4A90E2;">
            <h4 style="margin-top: 0; color: #1f2937; font-weight: 800;">1. IVB <span style="font-size: 0.7em; color: #4b5563;">(Induced Vertical Break, 誘發性垂直位移)</span></h4>
            <p style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">核心：&nbsp;&nbsp;抗重力能力。</p>
            <p style="color: #374151; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                視覺上產生「上竄」效果。高 IVB (18-20"+) 因馬格努斯力抵消更多重力，使球掉落比預期少，誘使打者在球下方揮空。
            </p>
        </div>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #4A90E2;">
            <h4 style="margin-top: 0; color: #1f2937; font-weight: 800;">2. VAA <span style="font-size: 0.7em; color: #4b5563;">(Vertical Approach Angle, 垂直進壘角度)</span></h4>
            <p style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">核心：&nbsp;&nbsp;下墜坡度。</p>
            <p style="color: #374151; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                越接近 0° 代表路徑越平直。當「平直 VAA」搭配「好球帶頂端」速球時，角度落差會讓打者產生球在「向上噴」的視覺錯覺。
            </p>
        </div>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #4A90E2;">
            <h4 style="margin-top: 0; color: #1f2937; font-weight: 800;">3. HAA <span style="font-size: 0.7em; color: #4b5563;">(Horizontal Approach Angle, 水平進壘角度)</span></h4>
            <p style="color: #1f2937; font-weight: 700; margin-bottom: 5px;">核心：&nbsp;&nbsp;斜向切入感。</p>
            <p style="color: #374151; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                數值越遠離 0° 代表球路越斜向切入。搭配大幅度橫移(HB)能橫跨好球帶，造成打者判斷混亂。
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="background-color: #eef2ff; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #6366f1;">
            <h4 style="margin-top: 0; color: #1e1b4b; font-weight: 800;">4. Spin Efficiency <span style="font-size: 0.7em; color: #4338ca;">(旋轉效率)</span></h4>
            <p style="color: #1e1b4b; font-weight: 700; margin-bottom: 5px;">核心：&nbsp;&nbsp;位移轉化率。</p>
            <p style="color: #1e1b4b; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                當效率高，能創造極大 IVB 或 HB；若效率低，則帶有大量 <b>Gyro Spin (螺旋旋轉)</b>。這解釋了轉速相同但球路竄勁不同的原因。
            </p>
        </div>
        <div style="background-color: #eef2ff; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #6366f1;">
            <h4 style="margin-top: 0; color: #1e1b4b; font-weight: 800;">5. SSW <span style="font-size: 0.7em; color: #4338ca;">(Seam-Shifted Wake Deviation, 縫線引發位移)</span></h4>
            <p style="color: #1e1b4b; font-weight: 700; margin-bottom: 5px;">核心：&nbsp;&nbsp;不規則位移。</p>
            <p style="color: #1e1b4b; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                純因縫線位置擾流產生的額外位移。高 SSW 會產生大腦難以預測的<b>「晚期竄動」</b>，是伸卡球與變速球的主要殺招。
            </p>
        </div>
        <div style="background-color: #eef2ff; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #6366f1;">
            <h4 style="margin-top: 0; color: #1e1b4b; font-weight: 800;">6. Tunneling <span style="font-size: 0.7em; color: #4338ca;">(Pitch Tunneling, 球路共軌效應)</span></h4>
            <p style="color: #1e1b4b; font-weight: 700; margin-bottom: 5px;">核心：&nbsp;&nbsp;隱蔽欺敵性。</p>
            <p style="color: #1e1b4b; font-size: 0.95em; line-height: 1.6; margin-top: 0;">
                不同球路在路徑中高度重疊直到隧道點。共軌距離越長，隱蔽效果越好，打者將難以辨識球種。
            </p>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("點擊展開：更詳盡的物理原理與進階數據深探"):
        st.markdown("### 物理能量解析：棒球上所受到的力")

        # --- 1. 放置圖片 (置頂置中) ---

        img_spacer1, img_center, img_spacer2 = st.columns([1, 3, 1])
        with img_center:
            st.image("image/forces_baseball.jpg", caption="棒球物理受力向量圖 (Forces on a baseball)", use_column_width=True) 

        # 加上分隔線
        st.divider()

        # --- 2. 放置文字  ---
        st.markdown("""
        #### 核心原理：馬格努斯效應 (Magnus Effect)

        這是棒球位移的物理基石。當球體在空氣中旋轉飛行時，旋轉會帶動周圍空氣流動，導致球體兩側產生**壓力差**，進而將球推向壓力較小的一方。

        * **流體力學機制**：
            * **壓力差與白努利定律**：球旋轉時，一側空氣流速加快（壓力降低），另一側減慢（壓力升高），球會向壓力低的一側偏移。
            * **後旋 (Backspin)**：產生向上的力，對抗重力（**IVB** 的來源）。
            * **上旋 (Topspin)**：產生向下的力，加速下墜（**Curveball** 的原理）。
            * **側旋 (Sidespin)**：產生向左或向右的水平偏移（**HB** 的來源）。

        * **關鍵指標：有效轉速 (Active Spin)**
            * 並非所有旋轉都能產生位移。只有**與飛行路徑垂直**的旋轉軸（如純後旋）才能完整觸發馬格努斯效應。
            * **螺旋旋轉 (Gyro Spin)**：像子彈一樣順著飛行路徑旋轉，幾乎不產生馬格努斯位移。

        * **環境影響因子**：
            * **空氣密度**：在高海拔球場（如科羅拉多 Coors Field），空氣稀薄導致馬格努斯效應減弱，球的位移會明顯縮水。
            * **球速**：球速越快，單位時間內空氣流動的作用力越顯著。

        > **總結**：馬格努斯效應決定了球「**預期下墜**」與「**實際路徑**」之間的差距。

        #### 物理底層：白努利定律 (Bernoulli's Principle)

        這是流體力學中的金科玉律，解釋了為什麼流動的空氣能產生「力量」來移動棒球。

        * **核心定義**：
            在一個流體系統中，**流速越快的地方，壓力就越小；流速越慢的地方，壓力就越大。**
            > 公式簡化概念：$P + \\frac{1}{2}\\rho v^2 = \\text{常數}$ (壓力與速度成反比)

        * **在棒球旋轉中的應用**：
            1.  **帶動氣流**：當球旋轉時，球體表面的縫線會摩擦並「抓取」周圍的空氣跟著旋轉。
            2.  **速度差異**：
                * 在球旋轉方向與飛行氣流方向**相同**的一側，空氣流速會被「加速」（流速快 $\\rightarrow$ 低壓）。
                * 在旋轉方向與氣流方向**相反**的一側，空氣流速會被「抵消/減慢」（流速慢 $\\rightarrow$ 高壓）。
            3.  **產生位移**：高壓側的空氣會將球推向低壓側，這股推力就是**馬格努斯力**。

        * **生活中的類比**：
            * **飛機機翼**：機翼上方弧度大導致流速快、壓力小，產生向上的升力。
            * **快速道路**：兩輛大車併行開太快時，中間流速快壓力小，車輛會感覺被互相「吸」過去。

        > **總結**：沒有白努利定律造成的壓力差，就沒有任何位移變化（IVB/HB）。
        
        #### 縫線引發尾流效應 (Seam-Shifted Wake, SSW)

        這是除了馬格努斯效應之外，現代棒球最重要的發現。它解釋了為何有些球能產生「轉速數據」預測以外的位移。

        * **核心機制：非對稱尾流**
            * 球體表面的**縫線**會干擾氣流層。當縫線不對稱地切過空氣時，會導致球體後方的氣流（Wake）發生偏移，進而產生推力。
            * 這是一種「非旋轉產生」的力量，主要發生在 **Sinker (伸卡球)** 與 **Changeup (變速球)** 上。
        * **實戰指標：觀測軸與推算軸的落差**
            * 透過數據儀器（如 Statcast）比對「轉速預期路徑」與「實際飛行路徑」的偏差值。偏差越大，代表 SSW 貢獻的「球路生命力」越強，打者越難精準擊中球心。

        #### 進場幾何學：VAA 與 垂直位移的加乘

        單有強大的位移（IVB）是不夠的，必須配合**進壘幾何角度**才能發揮最大殺傷力。

        * **放球高度 (Release Height) 的影響**：
            * 同樣的 18 英吋 IVB，若從**低放球點**投出，會產生更平的 **VAA**。
            * 這種「低起點、高終點」的軌跡，會讓打者視覺上覺得球在「向上噴」，即便球速普通也極難被擊中。
        * **延伸長度 (Extension)**：
            * 投手放球點越靠近本壘，球在空中受重力影響的時間越短，這會進一步優化 VAA 的平直度，並增加打者的體感球速。

        #### 腦科學與隧道效應 (Tunneling)

        這部分討論的是打者的**感知極限**。

        * **判斷點 (Commit Point)**：
            * 打者在球離手約 24 英尺（約 7 公尺）處，大腦就必須決定是否揮棒。
        * **共軌效應的威力**：
            * 若不同球種在抵達判斷點前的軌跡誤差（Tunnel Differential）極小，打者的大腦會將其歸類為同一球種。
            * 當球通過判斷點後才產生位移（位移發生得越晚越好），打者已經無法修正揮棒動作。這就是為什麼「共軌距離」越長，壓制力越強。

        > **最終核心總結**：優秀的投手是透過 **馬格努斯力** 創造位移，利用 **SSW** 增加不確定性，並藉由 **幾何角度 (VAA)** 與 **隧道共軌 (Tunneling)** 讓這一切在打者眼裡變得不可辨識。

        #### HB (Horizontal Break, 橫向位移)

        這是衡量球路「左右偏離」能力的指標。與 IVB 不同，HB 描述的是球在水平面上的橫向竄動。

        * **物理來源：側旋 (Side Spin)**
            * 當球的旋轉軸向左右偏移（例如 3:00 或 9:00 方向），馬格努斯力就會在水平方向產生推力。
            * **正負值定義 (以右投手為準)**：
                * **正值 (+)**：球向右打者**外角**（一壘側）偏轉，代表球種如：滑球 (Slider)、橫掃球 (Sweeper)。
                * **負值 (-)**：球向右打者**內角**（三壘側）竄入，代表球種如：伸卡球 (Sinker)、二縫線 (2-Seam)。

        * **關鍵趨勢：橫向分離度 (Horizontal Separation)**
            * 現代棒球極度強調「Sweeper (橫掃球)」，這類球種追求極致的 HB（通常超過 15 英吋），讓球橫跨整個好球帶，增加打者判斷進壘點的難度。

        * **與 HAA (水平進壘角度) 的聯動**：
            * 極大的 HB 會直接導致極端的 **HAA**。當球從打者視野外「切」回好球帶，或從好球帶「滑」出視野，會造成打者對邊界判斷的絕望感。

        > **總結**：HB 決定了球路在水平面上的「橫向覆蓋率」，是製造弱擊球與凍結打者的關鍵。
        """)

    st.divider()

    if not selected_pitchers:
        st.warning("請選擇至少一位投手。")
    else:
        comparison_df = df_all[(df_all['player_name'].isin(selected_pitchers)) & (df_all['pitch_name_full'].isin(selected_pitch_types))].copy()
        comparison_df['HB_in'] = comparison_df['pfx_x'] * 12

        st.subheader("關鍵物理數據對比")
        cols = st.columns(len(selected_pitchers))
        for i, p_name in enumerate(selected_pitchers):
            p_df = comparison_df[comparison_df['player_name'] == p_name]
            p_id = p_df['pitcher'].iloc[0]
            ff_df = p_df[p_df['pitch_type'] == 'FF']
            with cols[i]:
                st.markdown(f"#### **[{p_name}](https://www.mlb.com/player/{int(p_id)})**")
                st.metric("四縫線 VAA", f"{ff_df['vaa'].mean():.2f}°" if not ff_df.empty else "N/A")
                st.metric("平均共軌隧道距離", f"{p_df['tunneling'].mean():.2f} in")

        st.divider()

        st.subheader("⚾ 投手位移圖對比 (Movement Profile)")
        fig = px.scatter(
            comparison_df, x='HB_in', y='ivb', 
            color='player_name' if len(selected_pitchers) > 1 else 'pitch_name_full', 
            symbol='pitch_name_full',
            hover_data={'player_name':True, 'pitch_name_full':True, 'release_speed':':.1f', 'vaa':':.2f', 'haa':':.2f'},
            labels={'HB_in': '水平位移 (in)', 'ivb': '誘導垂直位移 IVB (in)'},
            template="plotly_white", height=750
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.3)
        fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.3)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("詳細數據分解 (滑動鼠標可查看解釋)")
        summary_table = comparison_df.groupby(['player_name', 'pitch_name_full']).agg({
            'release_speed': 'mean', 'ivb': 'mean', 'vaa': 'mean', 'haa': 'mean',
            'spin_efficiency': 'mean', 'ssw_deviation': 'mean', 'tunneling': 'mean'
        }).round(3).reset_index()
        summary_table.rename(columns={'player_name': '球員姓名', 'pitch_name_full': '球種'}, inplace=True)

        st.dataframe(
            summary_table, use_container_width=True, hide_index=True,
            column_config={
                "球員姓名": st.column_config.TextColumn("球員姓名", help="投手名稱"),
                "球種": st.column_config.TextColumn("球種", help="完整球種名稱"),
                "release_speed": st.column_config.NumberColumn("均速 (mph)", help="球速"),
                "ivb": st.column_config.NumberColumn("IVB (in)", help="誘導垂直位移：球抗重力上竄的能力"),
                "vaa": st.column_config.NumberColumn("VAA (deg)", help="垂直進壘角：越接近 0 代表軌跡越平直"),
                "haa": st.column_config.NumberColumn("HAA (deg)", help="水平進壘角：橫向切入角度"),
                "spin_efficiency": st.column_config.NumberColumn("旋轉效率", help="轉速轉化為實際位移的效率"),
                "ssw_deviation": st.column_config.NumberColumn("SSW 偏差 (in)", help="縫線效應位移：球路末端詭譎變化的主因"),
                "tunneling": st.column_config.NumberColumn("隧道共軌距離 (in)", help="欺敵性：共軌效果越強距離越短")
            }
        )

# ==========================================
# TAB 2: 聯盟球路特質領導者 
# ==========================================
with tab2:
    st.title(" 🏆 2024 聯盟球員球質Top 10 ")
    st.markdown("針對全賽季投球數達 **500 顆** 以上之投手，篩選出各項投球物理指標最頂尖的球員。點擊球員名字可跳轉至MLB球員官網。")

    pitcher_counts = df_all['player_name'].value_counts()
    qualified_pitchers = pitcher_counts[pitcher_counts >= 500].index
    df_qual = df_all[df_all['player_name'].isin(qualified_pitchers)]

    def get_rank_md(df_input, column, ascending=False, title=""):
        res = df_input.groupby('player_name')[column].mean().sort_values(ascending=ascending).head(10).reset_index()
        res['球員姓名'] = res['player_name'].apply(lambda x: f"[{x}](https://www.mlb.com/player/{int(df_all[df_all['player_name']==x]['pitcher'].iloc[0])})")
        res = res[['球員姓名', column]].rename(columns={column: title})
        return res.to_markdown(index=False)

    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        st.subheader("視覺上竄王者 (Extreme VAA)")
        # 強調「入射角度」與「放球點」
        st.caption("【進壘角度】數值越接近 0°，球路越像「直線射入」而非斜向掉落。這讓高角度速球完美切入揮棒路徑上方，無視球速也能製造大量揮空。")
        st.markdown(get_rank_md(df_qual[df_qual['pitch_type'] == 'FF'], 'vaa', False, "平均 VAA (deg)"), unsafe_allow_html=True)

    with r1_c2:
        st.subheader("垂直位移天賦 (Elite IVB)")
        # 強調「對抗重力」與「旋轉力量」
        st.caption("【抗重力能力】指球因後旋產生的向上位移。當 IVB > 18 吋，球掉落幅度比大腦預期更少，產生球在進壘前「突然上竄」的視覺錯覺。")
        st.markdown(get_rank_md(df_qual[df_qual['pitch_type'] == 'FF'], 'ivb', False, "平均 IVB (in)"), unsafe_allow_html=True)

    st.info("優質速球通常同時具備 **平直 VAA**（切入角平）與 **高 IVB**（抗重力強）。當這兩者結合，就是打者最難應付的『上升感速球』。")

    with r1_c3:
            st.subheader("縫線位移大師 (SSW Master)")
            st.caption("""
            【非對稱尾流】指球路位移中，排除馬格努斯力後，純粹因「縫線位置」產生的額外位移。這項指標越高，代表球在進壘前會產生大腦難以預期的「晚期竄動」，是伸卡球與變速球誘使弱擊球的核心。
            """)
            # 修正點：'ssw' -> 'ssw_deviation'，單位改為 (in) 較符合物理直覺
            md_content = get_rank_md(
                df_qual[df_qual['pitch_type'].isin(['SI', 'CH'])], 
                'ssw_deviation', 
                False, 
                "SSW 偏差值 (in)"
            )
            st.markdown(md_content, unsafe_allow_html=True)

    st.divider()

    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        st.subheader("極致切入角度 (HAA Specialist)")
        st.caption("【水平進壘角】數值（絕對值）越高，代表球路越是「從兩側斜向切入」而非直線前進。這讓球能從打者視野外切回好球帶邊角，是橫掃球 (Sweeper) 凍結打者的核心秘密。")
        # 先計算絕對值再排名
        df_qual['haa_abs'] = df_qual['haa'].abs()
        st.markdown(get_rank_md(df_qual[df_qual['pitch_type'].isin(['SL', 'ST'])], 'haa_abs', False, "平均 HAA (deg)"), unsafe_allow_html=True)


    with r2_c2:
        st.subheader("高效能轉速 (Spin Efficiency)")
        st.caption("【有效轉速比】指總轉速中轉化為「實際位移」的比例。數值越高（接近 100%），代表旋轉越能完整驅動馬格努斯力，這解釋了為何有些投手轉速不快，球路卻極具「竄勁」與生命力。")
        st.markdown(get_rank_md(df_qual, 'spin_efficiency', False, "平均旋轉效率 (%)"), unsafe_allow_html=True)


    with r2_c3:
        st.subheader("球路共軌 (Tunneling Elite)")
        st.caption("【視覺重疊】指不同球種在判斷點前路徑一致的能力。共軌距離越長，代表打者辨識球種的時間越短，是製造誘使追打壞球與揮空的終極欺敵戰術。")
        st.markdown(get_rank_md(df_qual, 'tunneling', False, "隧道距離 (in)"), unsafe_allow_html=True)


st.divider()
st.caption("🔒 安全防護：採用唯讀架構與參數化查詢。")