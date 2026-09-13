# ⚽ ScoutIQ — Player Performance & Market Value Estimator

**ScoutIQ** is a football analytics and transfer market intelligence platform powered by multi-model machine learning. It models complex, non-linear player valuations and performance ratings by synthesizing EA FC/FIFA attributes, FBref advanced per-90 metrics (xG, xA, progressive actions, defensive duels), and Transfermarkt contract/financial metadata.

---

## 🌟 Key Features

1. **🔍 Global Scouting Hub**:
   - Filter and explore 1,400+ top-flight footballers across Europe's top leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1, and emerging competitions).
   - Search by player name, club, position, age, or budget range with side-by-side actual vs. predicted valuations.

2. **⚡ In-Depth Player Valuation & Scouting Report**:
   - Search real superstar profiles (*Erling Haaland, Kylian Mbappé, Jude Bellingham, Bukayo Saka, Lamine Yamal, Florian Wirtz, Rodri, William Saliba, etc.*).
   - Hexagonal attribute radar chart (*Pace, Shooting, Passing, Dribbling, Defending, Physical*).
   - **Explainable AI Valuation Driver Breakdown**: Directional attribution showing how Age, Output (G+A/90), International Reputation, Potential upside, and Contract length drive the player's market price.
   - Comprehensive FBref per-90 metrics strip (*xG, xA, key passes, progressive carries, tackles won*).

3. **🎛️ Interactive "What-If" Market Simulator & Player Builder**:
   - Tweak attributes, goals/90, assists/90, league tiers, and contract length in real-time.
   - Watch the machine learning regression model recalculate expected transfer fee and fair value range dynamically.

4. **💎 Moneyball Deal Finder (Undervalued Gems)**:
   - Identifies market inefficiencies where `Predicted Value > Actual Value`.
   - Filter by transfer budget and age to isolate high-ROI diamonds in the rough.

5. **⚔️ Head-to-Head Comparison**:
   - Dual-player overlay radar charts and head-to-head metric matchup table.

6. **📊 ML Diagnostics & Data Science Lab**:
   - Multi-model evaluation benchmark comparing **Gradient Boosting**, **Random Forest**, and **Ridge (Regularized Linear)** regression.
   - Residual distribution plot ($y_{\text{true}}$ vs. $y_{\text{pred}}$).
   - Tree-based Gini feature importance ranking.
   - Correlation heatmap for athletic, technical, and match output metrics.

---

## 🔬 Data Science & Machine Learning Architecture

### 1. Handling Messy Real-World Football Data
- **String Currency Parsing**: Robust parsing of messy formats (`€180.00m`, `€900k`, ` € 25.5 M `, `£`, `$`, `N/A`).
- **Wage Conversion**: Unifies weekly and annual wage strings (`€375,000 / week`, `€35k p/w`).
- **Contract Expiration Decay**: Computes remaining contract duration relative to current season date.
- **Position-Based Median Imputation**: Automatically imputes missing advanced metrics based on tactical role medians (ATT, WNG, MID, DEF, GK).

### 2. Feature Engineering
- **Quadratic Age Curves**: $Age^2$ feature models the non-linear appreciation curve (peaks around age 24–27, followed by accelerated depreciation).
- **Growth Headroom & Synergy**: $POT - OVR$ upside and $(POT - OVR) / (Age - 14)$ youth ceiling factor.
- **Offensive & Playmaking Efficiency**: $(Goals - xG)$ and $(Assists - xA)$ finishing efficiency.
- **Progression Index**: Composite score from progressive passing and progressive carries per 90.
- **League Tier Multipliers**: Reflects commercial exposure and financial buying power across domestic leagues.
- **Contract Leverage**: Incorporates bargaining power decay when entering the final 12–18 months of a contract.

### 3. Log Target Transformation
Football transfer valuations have extreme right skew (a small elite tier commands €100M+ while the median sits at €5M–€12M). ScoutIQ models $\log(1 + y)$ and inverse-transforms predictions with $\exp(y) - 1$, preventing severe underestimation of superstars and stabilizing error variance across the entire distribution.

---

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run Automated Unit & Pipeline Tests
```bash
python -m unittest tests/test_pipeline.py
```

### Launch the Streamlit App
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Project Structure

```text
ScoutIQ/
├── app.py                         # Main Streamlit application
├── requirements.txt               # Dependencies
├── README.md                      # Documentation
├── scoutiq/
│   ├── data/
│   │   ├── dataset_generator.py   # Realistic football data synthesizer
│   │   └── preprocessor.py        # Messy data cleaning & feature engineering
│   ├── models/
│   │   └── regressor.py           # Multi-model regression, evaluation, explainability
│   └── ui/
│       ├── components.py          # Plotly radar, waterfall, residuals, heatmap
│       └── styles.py              # Custom dark-theme CSS and cards
└── tests/
    └── test_pipeline.py           # Automated unit tests for pipeline & ML models
```
