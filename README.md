# DeepPitch Analytics: 2024 MLB Pitch Physics Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Data](https://img.shields.io/badge/Data-MLB_Statcast_2024-red.svg)](https://baseballsavant.mlb.com/)

---

### Project Overview
In modern baseball, traditional metrics like ERA or K/9 fall short in evaluating a pitcher's true dominance. This project is an interactive data science dashboard built on **2024 MLB Statcast** data. Moving away from outcome-based statistics, this dashboard adopts a strictly **Fluid Dynamics and Physics Engine** perspective to deeply deconstruct the spatial trajectory, anti-gravity properties, and visual deception of Major League pitches.

### What Can You Discover?
This dashboard is designed for data analysts, scouts, and baseball enthusiasts. Through interactive exploration, it addresses advanced analytical questions:
* **"Why is this 92 mph fastball harder to hit than a 98 mph one?"**
  By analyzing **IVB** and **VAA**, discover how pitchers leverage the Magnus effect to create a "rising" optical illusion.
* **"How is late-movement generated?"**
  By deconstructing **SSW (Seam-Shifted Wake)**, uncover the aerodynamic secrets behind heavy sinkers that consistently generate groundballs.
* **"Why do elite batters swing at pitches in the dirt?"**
  By evaluating **Pitch Tunneling**, quantify how pitchers mask their pitch trajectories before the commit point to maximize deception.

### The "Big 6" Advanced Metrics
This product accurately calculates and visualizes six cutting-edge physics metrics:
1. **IVB (Induced Vertical Break)**: Measures a pitch's ability to "defy gravity."
2. **VAA (Vertical Approach Angle)**: The steepness of the ball entering the strike zone. Flat VAAs are lethal for high fastballs.
3. **HAA (Horizontal Approach Angle)**: The lateral entry angle, crucial for evaluating sweepers and sliders.
4. **Spin Efficiency**: The percentage of raw spin converted into actual movement (differentiating Magnus vs. Gyro spin).
5. **SSW (Seam-Shifted Wake)**: Captures non-Magnus movement caused by seam orientation.
6. **Pitch Tunneling**: Measures the visual overlap of different pitch types during the early flight phase.

### Key Features & UI
* **Interactive Leaderboard**: Multi-dimensional sorting by pitch type, velocity, and specific movement metrics.
* **Player Profiling**: Interactive radar charts and 2D/3D trajectory plots visualizing a pitcher's arsenal via Plotly.
* **Physics Encyclopedia**: Built-in guides with force vector diagrams (Lift, Drag, Gravity) for fluid dynamics education.

### Tech Stack & Architecture
* **Frontend**: Streamlit
* **Data Processing**: Pandas, NumPy
* **Database**: DuckDB, SQLite
* **Visualization**: Plotly
* **Data Source**: pybaseball (MLB Statcast API)

---

## 中文介紹

### 專案簡介
在現代棒球中，傳統的防禦率 (ERA) 或三振率 (K/9) 已不足以評估投手的真正宰制力。本專案為基於 **2024 MLB Statcast** 數據開發之互動式資料科學產品。本儀表板捨棄傳統的「結果論」數據，轉而採用**流體力學與物理引擎**視角，深度解構大聯盟級別球路的空間軌跡、抗重力能力與視覺欺騙性。

### 分析視角與應用場景
本工具專為資料分析師與進階棒球研究者設計，旨在解答以下核心問題：
* **解析速球品質**：透過觀察 **IVB (誘發性垂直位移)** 與 **VAA (垂直進壘角)**，量化投手如何利用馬格努斯效應創造「上竄」的視覺錯覺。
* **解構尾勁成因**：透過解析 **SSW (縫線偏移效應)**，揭開無法單靠原始轉速解釋的「晚期竄動 (Late-life)」，了解伸卡球狂造滾地球的物理機制。
* **量化視覺欺騙**：透過 **Pitch Tunneling (球路隧穿效應)** 模型，評估投手不同球種在出手初期的軌跡重合度。

### 六大核心物理指標
1. **IVB (誘發性垂直位移)**: 衡量球路「抗重力」能力。
2. **VAA (垂直進壘角度)**: 球進入好球帶的陡峭程度。
3. **HAA (水平進壘角度)**: 球路橫向竄動的視覺切入角。
4. **Spin Efficiency (旋轉效率)**: 原始轉速轉化為有效位移之百分比。
5. **SSW (縫線偏移效應)**: 捕捉非馬格努斯力造成的位移，為當今大聯盟最前沿的空氣動力學指標。
6. **Pitch Tunneling (球路隧穿效應)**: 計算不同球種在共軌點前的視覺重合度。

### 核心功能與技術架構
* **動態實時排行榜**: 支援多維度篩選與參數排序。
* **投手專項報告**: 利用 Plotly 渲染高品質 2D/3D 空間軌跡圖。
* **高速資料處理**: 採用 DuckDB 與 Pandas 實現巨量 Statcast 數據的毫秒級查詢。

---

## Repository Structure (專案架構)
```text
2024MLB_DeepPitch_Dashboard/
├── src/                    # Core algorithm and database logic
├── data/                   # 2024 Statcast SQLite Database
├── image/                  # Static assets and physics diagrams
├── app_mandarin.py         # Production App (Traditional Chinese)
├── app_en.py               # Development App (English)
├── requirements.txt        # Cloud deployment dependencies
└── README.md               # Project documentation

# About the Author (關於作者)

### Paul Lai (Hong-Min Lai)

* **Education**: M.S. in Data Science, University of California, San Diego (UCSD)