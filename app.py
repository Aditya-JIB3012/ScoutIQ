"""ScoutIQ: Football Player Performance & Market Value Estimator.
An end-to-end Machine Learning web application demonstrating data engineering,
multi-model regression, explainable AI, and football scouting analytics.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

# Ensure root repository directory is on Python search path for Streamlit Cloud
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Tuple, List, Dict, Any
import streamlit as st
import pandas as pd
import numpy as np

try:
    from scoutiq.data.dataset_generator import get_all_real_players, generate_player_dataset
    from scoutiq.data.preprocessor import FootballDataCleaner, FootballFeatureEngineer, LEAGUE_TIER_MAP
    from scoutiq.models.regressor import ScoutIQModelManager, FEATURE_COLUMNS
    from scoutiq.ui.styles import CUSTOM_CSS
    from scoutiq.ui.components import (
        render_player_radar,
        render_valuation_drivers_bar,
        render_feature_importance_chart,
        render_residuals_plot,
        render_correlation_heatmap
    )
except (ImportError, ModuleNotFoundError):
    # Fallback for flat repository structure (all files in root directory)
    from dataset_generator import get_all_real_players, generate_player_dataset
    from preprocessor import FootballDataCleaner, FootballFeatureEngineer, LEAGUE_TIER_MAP
    from regressor import ScoutIQModelManager, FEATURE_COLUMNS
    from styles import CUSTOM_CSS
    from components import (
        render_player_radar,
        render_valuation_drivers_bar,
        render_feature_importance_chart,
        render_residuals_plot,
        render_correlation_heatmap
    )

# Page Configuration
st.set_page_config(
    page_title="ScoutIQ | Player Valuation & Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Premium Dark Theme CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading football database & processing features...")
def load_and_process_data(real_only: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load authentic real players or expanded scouting pool, clean data, and engineer features."""
    if real_only:
        raw_df = get_all_real_players()
    else:
        raw_df = generate_player_dataset(1200, use_real_only=False)

    cleaner = FootballDataCleaner()
    df_clean = cleaner.fit_transform(raw_df)
    fe = FootballFeatureEngineer()
    df_processed = fe.transform(df_clean)
    return raw_df, df_processed


@st.cache_resource(show_spinner="Training predictive regression algorithms...")
def get_trained_model_manager(df_processed: pd.DataFrame) -> ScoutIQModelManager:
    """Train candidate models and return fitted manager."""
    mgr = ScoutIQModelManager()
    mgr.train_and_evaluate(df_processed)
    return mgr


# Sidebar: Database & Model Settings
st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
        <span style="font-size: 1.5rem;">⚽</span>
        <span style="font-size: 1.3rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">ScoutIQ Pro</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("### ⚙️ Database & ML Configuration")
use_real_only = st.sidebar.toggle(
    "🌟 100% Real Star Players",
    value=True,
    help="When active, strictly loads authentic world-famous footballers from top clubs."
)

raw_df, df_processed = load_and_process_data(real_only=use_real_only)
model_mgr = get_trained_model_manager(df_processed)

# Append predictions if not present
if "pred_val_m" not in df_processed.columns:
    df_processed["pred_val_m"] = model_mgr.predict_value(df_processed)
    df_processed["val_delta_m"] = df_processed["pred_val_m"] - df_processed["market_val_m"]
    df_processed["val_ratio"] = df_processed["pred_val_m"] / df_processed["market_val_m"].clip(lower=0.5)
    df_processed["performance_score"] = df_processed.apply(model_mgr.compute_performance_index, axis=1)

selected_model = st.sidebar.selectbox(
    "Active ML Regression Model",
    options=list(model_mgr.models.keys()),
    index=list(model_mgr.models.keys()).index(model_mgr.best_model_name)
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Scouting Filters")
available_leagues = sorted(df_processed["league"].unique())
selected_leagues = st.sidebar.multiselect(
    "Leagues",
    options=available_leagues,
    default=[]
)

selected_roles = st.sidebar.multiselect(
    "Tactical Role",
    options=["ATT", "WNG", "MID", "DEF", "GK"],
    default=[]
)

min_age, max_age = int(df_processed["age"].min()), int(df_processed["age"].max())
age_range = st.sidebar.slider("Age Bracket", min_age, max_age, (min_age, max_age))
max_price = st.sidebar.slider("Max Transfer Fee (€M)", 5, 220, 220, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-size: 0.8rem; color: #64748b; line-height: 1.5;">
        <strong style="color: #94a3b8;">ScoutIQ Engine v1.2</strong><br>
        • EA FC / FIFA Attributes<br>
        • FBref Per-90 Analytics<br>
        • Transfermarkt Valuation Models
    </div>
    """,
    unsafe_allow_html=True
)

# Header Banner
db_badge_text = "100% Real Footballers" if use_real_only else "Expanded Scouting Pool"
st.markdown(
    f"""
    <div class="scoutiq-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.8rem;">
            <div>
                <h1 class="scoutiq-title">
                    <span>ScoutIQ</span>
                </h1>
                <div class="scoutiq-subtitle">
                    Intelligent Football Player Performance & Market Value Estimator • Powered by Multi-Model ML
                </div>
            </div>
            <div style="display: flex; gap: 0.6rem; align-items: center;">
                <div class="live-indicator">
                    <span class="pulse-dot"></span>
                    <span>{db_badge_text}</span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Apply Filters
filtered_df = df_processed.copy()
if selected_leagues:
    filtered_df = filtered_df[filtered_df["league"].isin(selected_leagues)]
if selected_roles:
    filtered_df = filtered_df[filtered_df["pos_role"].isin(selected_roles)]
filtered_df = filtered_df[
    (filtered_df["age"] >= age_range[0]) &
    (filtered_df["age"] <= age_range[1]) &
    (filtered_df["market_val_m"] <= max_price)
]

# Top KPI Stat Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(
        f"""
        <div class="stat-card-pro">
            <div class="stat-label-pro">Filtered Cohort</div>
            <div class="stat-value-pro">{len(filtered_df):,} <span style="font-size: 1rem; color: #64748b; font-weight: 500;">/ {len(df_processed):,}</span></div>
            <div class="stat-meta-pro" style="color: #38bdf8;">Active scouting targets</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with kpi2:
    r2_val = model_mgr.metrics[selected_model]["R2_Score"]
    st.markdown(
        f"""
        <div class="stat-card-pro">
            <div class="stat-label-pro">{selected_model} R²</div>
            <div class="stat-value-pro" style="color: #10b981;">{r2_val:.3f}</div>
            <div class="stat-meta-pro" style="color: #10b981;">High variance explained</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with kpi3:
    mae_val = model_mgr.metrics[selected_model]["MAE_EUR_M"]
    st.markdown(
        f"""
        <div class="stat-card-pro">
            <div class="stat-label-pro">Mean Absolute Error</div>
            <div class="stat-value-pro">€{mae_val:.2f}M</div>
            <div class="stat-meta-pro" style="color: #94a3b8;">Average valuation residual</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with kpi4:
    avg_mv = filtered_df["market_val_m"].mean() if len(filtered_df) > 0 else 0
    st.markdown(
        f"""
        <div class="stat-card-pro">
            <div class="stat-label-pro">Cohort Mean Value</div>
            <div class="stat-value-pro" style="color: #f59e0b;">€{avg_mv:.1f}M</div>
            <div class="stat-meta-pro" style="color: #94a3b8;">Transfermarkt benchmark</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Main Multi-Tab Workspace
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Scouting Hub",
    "⚡ Player Valuation & Report",
    "🎛️ 'What-If' Market Simulator",
    "💎 Moneyball Deal Finder",
    "⚔️ Head-to-Head Comparison",
    "📊 ML Diagnostics & Data Lab"
])


def get_role_badge_html(role: str) -> str:
    role = str(role).upper()
    if role == "ATT":
        return f'<span class="badge-role-att">{role}</span>'
    elif role == "WNG":
        return f'<span class="badge-role-wng">{role}</span>'
    elif role == "MID":
        return f'<span class="badge-role-mid">{role}</span>'
    elif role == "DEF":
        return f'<span class="badge-role-def">{role}</span>'
    else:
        return f'<span class="badge-role-gk">{role}</span>'


# -------------------------------------------------------------
# TAB 1: Scouting Hub
# -------------------------------------------------------------
with tab1:
    st.markdown("### 🔍 Global Player Scouting Database")
    st.markdown("Explore authentic footballers across Europe with Transfermarkt valuations and ML fair-value predictions.")

    search_term = st.text_input(
        "🔎 Search by Player Name, Club, or Nationality:",
        placeholder="e.g., Erling Haaland, Bellingham, Real Madrid, Arsenal, Spain..."
    )

    tbl_df = filtered_df.copy()
    if search_term:
        tbl_df = tbl_df[
            tbl_df["name"].str.contains(search_term, case=False, na=False) |
            tbl_df["club"].str.contains(search_term, case=False, na=False) |
            tbl_df["nationality"].str.contains(search_term, case=False, na=False)
        ]

    cols_view = [
        "name", "club", "league", "position", "pos_role", "age",
        "ovr", "pot", "market_val_m", "pred_val_m", "val_delta_m", "performance_score"
    ]
    tbl_display = tbl_df[cols_view].copy()
    tbl_display["Actual Val"] = tbl_display["market_val_m"].apply(lambda v: f"€{v:.1f}M")
    tbl_display["Predicted Val"] = tbl_display["pred_val_m"].apply(lambda v: f"€{v:.1f}M")
    tbl_display["Delta (€M)"] = tbl_display["val_delta_m"].apply(lambda v: f"{v:+.1f}M")
    tbl_display["Perf. Score"] = tbl_display["performance_score"].apply(lambda v: f"{v:.1f}")

    rename_map = {
        "name": "Player",
        "club": "Club",
        "league": "League",
        "position": "Pos",
        "pos_role": "Role",
        "age": "Age",
        "ovr": "OVR",
        "pot": "POT"
    }
    final_table = tbl_display[["name", "club", "league", "position", "pos_role", "age", "ovr", "pot", "Actual Val", "Predicted Val", "Delta (€M)", "Perf. Score"]].rename(columns=rename_map)

    st.dataframe(
        final_table,
        use_container_width=True,
        height=480
    )


# -------------------------------------------------------------
# TAB 2: Player Valuation & Report
# -------------------------------------------------------------
with tab2:
    st.markdown("### ⚡ In-Depth Player Valuation & Scouting Report")

    all_player_names = sorted(df_processed["name"].unique())
    col_sel1, col_sel2 = st.columns([1.5, 1.0])
    with col_sel1:
        default_pick = "Erling Haaland" if "Erling Haaland" in all_player_names else all_player_names[0]
        selected_player_name = st.selectbox(
            "Select Real Player to Inspect:",
            options=all_player_names,
            index=all_player_names.index(default_pick)
        )
    with col_sel2:
        quick_star = st.selectbox(
            "Quick Star Jump:",
            options=["-- Select Marquee Star --"] + [p for p in ["Kylian Mbappé", "Jude Bellingham", "Bukayo Saka", "Lamine Yamal", "Florian Wirtz", "Rodri", "William Saliba", "Cole Palmer", "Harry Kane", "Vinícius Jr."] if p in all_player_names],
            index=0
        )
        if quick_star != "-- Select Marquee Star --":
            selected_player_name = quick_star

    player = df_processed[df_processed["name"] == selected_player_name].iloc[0]

    # Predict using selected ML model
    player_df = pd.DataFrame([player])
    pred_val = model_mgr.predict_value(player_df, model_name=selected_model)[0]
    actual_val = player["market_val_m"]
    delta_val = pred_val - actual_val
    perf_rating = model_mgr.compute_performance_index(player)

    # Broadcast Player Showcase Card
    role_badge = get_role_badge_html(player["pos_role"])
    delta_color = "#10b981" if delta_val >= 0 else "#f43f5e"
    delta_label = "Undervalued (Bargain)" if delta_val > 5 else ("Overvalued (Premium)" if delta_val < -5 else "Fair Valuation")

    st.markdown(
        f"""
        <div class="player-hero-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div style="display: flex; align-items: center; gap: 1.2rem;">
                    <div class="ovr-shield">{player['ovr']}</div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.6rem;">
                            <h2 style="margin: 0; font-size: 2rem; font-weight: 800; color: #ffffff;">{player['name']}</h2>
                            {role_badge}
                        </div>
                        <div style="margin-top: 0.4rem; color: #94a3b8; font-size: 0.92rem;">
                            <strong style="color: #f8fafc;">{player['club']}</strong> • {player['league']} • <span style="color: #cbd5e1;">{player['nationality']}</span> • Age {player['age']}
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 1rem; align-items: center;">
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Potential Ceiling</div>
                        <div class="pot-shield" style="margin-left: auto;">{player['pot']}</div>
                    </div>
                    <div style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 1rem; text-align: right;">
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Contract Expiry</div>
                        <div style="color: #e2e8f0; font-weight: 700; font-size: 1.05rem;">{player['contract_expiry']}</div>
                        <div style="font-size: 0.78rem; color: #94a3b8;">({player['contract_years_left']:.1f} yrs remaining)</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4 Valuation KPI Cards
    vc1, vc2, vc3, vc4 = st.columns(4)
    with vc1:
        st.markdown(
            f"""
            <div class="stat-card-pro">
                <div class="stat-label-pro">ScoutIQ Predicted Value</div>
                <div class="stat-value-pro" style="color: #10b981;">€{pred_val:.1f}M</div>
                <div class="stat-meta-pro" style="color: #38bdf8;">Est. Range: €{pred_val*0.9:.1f}M – €{pred_val*1.1:.1f}M</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with vc2:
        st.markdown(
            f"""
            <div class="stat-card-pro">
                <div class="stat-label-pro">Actual Transfer Value</div>
                <div class="stat-value-pro">€{actual_val:.1f}M</div>
                <div class="stat-meta-pro" style="color: #94a3b8;">Transfermarkt listing</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with vc3:
        st.markdown(
            f"""
            <div class="stat-card-pro">
                <div class="stat-label-pro">Valuation Delta</div>
                <div class="stat-value-pro" style="color: {delta_color};">{delta_val:+.1f}M €</div>
                <div class="stat-meta-pro" style="color: {delta_color}; font-weight: 700;">{delta_label}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with vc4:
        st.markdown(
            f"""
            <div class="stat-card-pro">
                <div class="stat-label-pro">Performance Index</div>
                <div class="stat-value-pro" style="color: #f59e0b;">{perf_rating:.1f} <span style="font-size: 0.9rem; color: #64748b;">/ 100</span></div>
                <div class="stat-meta-pro" style="color: #94a3b8;">Composite match impact</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Radar Chart & Explainable AI Breakdown
    col_chart_left, col_chart_right = st.columns([1, 1])
    with col_chart_left:
        st.markdown("##### 📐 EA FC Hexagonal Attribute Radar")
        radar_fig = render_player_radar(player)
        st.plotly_chart(radar_fig, use_container_width=True)

    with col_chart_right:
        st.markdown("##### 💡 Explainable AI: Valuation Drivers vs. Market Baseline")
        explanations = model_mgr.explain_player_valuation(player, model_name=selected_model)
        drivers_fig = render_valuation_drivers_bar(explanations)
        st.plotly_chart(drivers_fig, use_container_width=True)

    # Advanced Match Analytics Strip
    st.markdown("##### 📊 Advanced FBref Analytics & Match Performance (Per 90)")
    fb1, fb2, fb3, fb4, fb5, fb6 = st.columns(6)
    fb1.metric("Goals / 90", f"{player.get('goals_p90', 0):.2f}", delta=f"xG: {player.get('xg_p90', 0):.2f}")
    fb2.metric("Assists / 90", f"{player.get('assists_p90', 0):.2f}", delta=f"xA: {player.get('xa_p90', 0):.2f}")
    fb3.metric("Key Passes / 90", f"{player.get('key_passes_p90', 0):.2f}")
    fb4.metric("Prog. Passes / 90", f"{player.get('prog_passes_p90', 0):.2f}")
    fb5.metric("Prog. Carries / 90", f"{player.get('prog_carries_p90', 0):.2f}")
    fb6.metric("Tackles Won / 90", f"{player.get('tackles_won_p90', 0):.2f}")


# -------------------------------------------------------------
# TAB 3: "What-If" Market Simulator
# -------------------------------------------------------------
with tab3:
    st.markdown("### 🎛️ Interactive 'What-If' Market Value Simulator")
    st.markdown("Adjust player stats, extend contracts, or simulate transfers between leagues to observe how the ML model recalculates transfer fees in real-time.")

    col_sim_in, col_sim_out = st.columns([1.2, 1.0])

    with col_sim_in:
        template_choice = st.selectbox(
            "Load Player as Base Template:",
            options=["[Custom Scratch Player]"] + all_player_names,
            index=1 if "Erling Haaland" in all_player_names else 0
        )

        if template_choice != "[Custom Scratch Player]":
            tpl = df_processed[df_processed["name"] == template_choice].iloc[0]
            d_age = int(tpl["age"])
            d_ovr = int(tpl["ovr"])
            d_pot = int(tpl["pot"])
            d_pace = int(tpl["pace"])
            d_shooting = int(tpl["shooting"])
            d_passing = int(tpl["passing"])
            d_dribbling = int(tpl["dribbling"])
            d_defending = int(tpl["defending"])
            d_physical = int(tpl["physical"])
            d_goals = float(tpl["goals_p90"])
            d_assists = float(tpl["assists_p90"])
            d_league = str(tpl["league"])
            d_contract = float(tpl["contract_years_left"])
            d_rep = int(tpl["reputation"])
        else:
            d_age, d_ovr, d_pot = 22, 82, 88
            d_pace, d_shooting, d_passing = 84, 78, 80
            d_dribbling, d_defending, d_physical = 82, 55, 74
            d_goals, d_assists = 0.35, 0.25
            d_league = "Premier League"
            d_contract = 3.5
            d_rep = 2

        s1, s2, s3 = st.columns(3)
        with s1:
            sim_age = st.slider("Age", 16, 38, d_age)
            sim_ovr = st.slider("Overall Rating (OVR)", 60, 95, d_ovr)
            sim_pot = st.slider("Potential Ceiling (POT)", max(sim_ovr, 60), 96, max(sim_ovr, d_pot))
        with s2:
            sim_pace = st.slider("Pace", 40, 99, d_pace)
            sim_shooting = st.slider("Shooting", 30, 99, d_shooting)
            sim_passing = st.slider("Passing", 30, 99, d_passing)
        with s3:
            sim_dribbling = st.slider("Dribbling", 30, 99, d_dribbling)
            sim_defending = st.slider("Defending", 20, 95, d_defending)
            sim_physical = st.slider("Physical", 40, 99, d_physical)

        s4, s5 = st.columns(2)
        with s4:
            sim_goals = st.number_input("Goals / 90", 0.0, 1.5, d_goals, step=0.05)
            sim_assists = st.number_input("Assists / 90", 0.0, 1.0, d_assists, step=0.05)
            sim_league = st.selectbox("League Tier", options=list(LEAGUE_TIER_MAP.keys()), index=list(LEAGUE_TIER_MAP.keys()).index(d_league) if d_league in LEAGUE_TIER_MAP else 0)
        with s5:
            sim_contract = st.slider("Contract Remaining (Years)", 0.5, 6.0, d_contract, step=0.5)
            sim_rep = st.slider("International Reputation (1-5)", 1, 5, d_rep)

    with col_sim_out:
        sim_data = {
            "age": sim_age,
            "age_squared": sim_age ** 2,
            "ovr": sim_ovr,
            "pot": sim_pot,
            "pot_ovr_growth": max(0, sim_pot - sim_ovr),
            "age_pot_synergy": max(0, sim_pot - sim_ovr) / max(1, sim_age - 14),
            "pace": sim_pace,
            "shooting": sim_shooting,
            "passing": sim_passing,
            "dribbling": sim_dribbling,
            "defending": sim_defending,
            "physical": sim_physical,
            "athletic_index": sim_pace * 0.55 + sim_physical * 0.45,
            "technical_index": sim_shooting * 0.35 + sim_passing * 0.35 + sim_dribbling * 0.30,
            "ball_progression_index": 4.2,
            "goals_p90": sim_goals,
            "assists_p90": sim_assists,
            "xg_p90": sim_goals * 0.95,
            "xa_p90": sim_assists * 0.95,
            "goal_xg_diff": sim_goals * 0.05,
            "assist_xa_diff": sim_assists * 0.05,
            "goal_involvement_p90": sim_goals + sim_assists,
            "expected_involvement_p90": (sim_goals + sim_assists) * 0.95,
            "key_passes_p90": 1.9,
            "prog_passes_p90": 4.8,
            "prog_carries_p90": 3.8,
            "tackles_won_p90": 1.2,
            "reputation": sim_rep,
            "weak_foot": 4,
            "skill_moves": 4,
            "contract_years_left": sim_contract,
            "contract_leverage": np.clip(sim_contract / 4.0, 0.25, 1.25),
            "league_tier_factor": LEAGUE_TIER_MAP.get(sim_league, 0.60),
            "availability_rate": 0.95
        }

        sim_df = pd.DataFrame([sim_data])
        sim_pred_m = model_mgr.predict_value(sim_df, model_name=selected_model)[0]
        sim_perf = model_mgr.compute_performance_index(pd.Series(sim_data))

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(16, 36, 56, 0.9) 0%, rgba(6, 78, 59, 0.8) 100%); border: 1px solid #10b981; border-radius: 18px; padding: 1.8rem; text-align: center; margin-top: 1.2rem; box-shadow: 0 15px 35px -10px rgba(16, 185, 129, 0.3);">
                <div style="color: #94a3b8; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">Recalculated Market Valuation</div>
                <div style="font-size: 3.2rem; font-weight: 900; color: #10b981; margin: 0.3rem 0; letter-spacing: -0.03em;">€{sim_pred_m:.1f}M</div>
                <div style="color: #e2e8f0; font-size: 0.9rem;">Fair Value Band: €{sim_pred_m*0.88:.1f}M – €{sim_pred_m*1.12:.1f}M</div>
                <hr style="border-color: rgba(255,255,255,0.1); margin: 1.2rem 0;">
                <div style="display: flex; justify-content: space-around;">
                    <div>
                        <div style="color: #94a3b8; font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">Performance Score</div>
                        <div style="font-size: 1.6rem; font-weight: 800; color: #f59e0b;">{sim_perf:.1f}</div>
                    </div>
                    <div>
                        <div style="color: #94a3b8; font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">Development Growth</div>
                        <div style="font-size: 1.6rem; font-weight: 800; color: #38bdf8;">+{sim_pot - sim_ovr} OVR</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        sim_radar_series = pd.Series({
            "name": "Simulated Profile",
            "pace": sim_pace, "shooting": sim_shooting, "passing": sim_passing,
            "dribbling": sim_dribbling, "defending": sim_defending, "physical": sim_physical
        })
        st.plotly_chart(render_player_radar(sim_radar_series), use_container_width=True)


# -------------------------------------------------------------
# TAB 4: Moneyball Deal Finder
# -------------------------------------------------------------
with tab4:
    st.markdown("### 💎 Moneyball Deal Finder (Undervalued Targets)")
    st.markdown("Uncover market inefficiencies where machine learning predicts a player's intrinsic performance value is substantially higher than their current transfer fee.")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        budget = st.slider("Maximum Transfer Budget (€M)", 10, 80, 45, step=5)
    with col_b2:
        u23_toggle = st.checkbox("Focus on Young Prospects (Age ≤ 23)", value=True)

    deals = df_processed.copy()
    deals = deals[deals["market_val_m"] <= budget]
    if u23_toggle:
        deals = deals[deals["age"] <= 23]

    deals = deals.sort_values(by="val_delta_m", ascending=False).head(12)

    st.markdown(f"Discovered **{len(deals)} premier value opportunities** within budget:")

    d_cols = st.columns(3)
    for i, (_, r) in enumerate(deals.iterrows()):
        with d_cols[i % 3]:
            roi = ((r["pred_val_m"] - r["market_val_m"]) / max(1.0, r["market_val_m"])) * 100
            st.markdown(
                f"""
                <div class="deal-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h4 style="margin: 0; font-size: 1.15rem; color: #ffffff; font-weight: 800;">{r['name']}</h4>
                            <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 0.2rem;">
                                {r['club']} • {r['league']}
                            </div>
                        </div>
                        <span class="live-indicator" style="font-size: 0.7rem;">+{roi:.0f}% ROI</span>
                    </div>
                    <div style="margin: 0.7rem 0;">
                        {get_role_badge_html(r['pos_role'])}
                        <span style="font-size: 0.82rem; color: #cbd5e1; margin-left: 0.4rem;">Age {r['age']} • OVR: <strong>{r['ovr']}</strong> (POT: <strong style="color:#38bdf8;">{r['pot']}</strong>)</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 0.8rem; padding-top: 0.6rem; border-top: 1px solid rgba(255,255,255,0.08);">
                        <div>
                            <div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Listed Value</div>
                            <div style="font-size: 1.15rem; font-weight: 800; color: #cbd5e1;">€{r['market_val_m']:.1f}M</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 0.72rem; color: #10b981; font-weight: 700; text-transform: uppercase;">ScoutIQ Fair Value</div>
                            <div style="font-size: 1.25rem; font-weight: 900; color: #10b981;">€{r['pred_val_m']:.1f}M</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# -------------------------------------------------------------
# TAB 5: Head-to-Head Comparison
# -------------------------------------------------------------
with tab5:
    st.markdown("### ⚔️ Head-to-Head Player Comparison")
    st.markdown("Direct side-by-side metric battle and attribute overlay between two real footballers.")

    hc1, hc2 = st.columns(2)
    with hc1:
        p1_choice = st.selectbox("Player A:", options=all_player_names, index=all_player_names.index("Erling Haaland") if "Erling Haaland" in all_player_names else 0)
    with hc2:
        p2_default = all_player_names.index("Kylian Mbappé") if "Kylian Mbappé" in all_player_names else (1 if len(all_player_names) > 1 else 0)
        p2_choice = st.selectbox("Player B:", options=all_player_names, index=p2_default)

    p1 = df_processed[df_processed["name"] == p1_choice].iloc[0]
    p2 = df_processed[df_processed["name"] == p2_choice].iloc[0]

    h_left, h_right = st.columns([1, 1])
    with h_left:
        st.markdown("##### 📐 Dual-Player Overlay Radar")
        st.plotly_chart(render_player_radar(p1, p2), use_container_width=True)

    with h_right:
        st.markdown("##### 📋 Head-to-Head Metric Showdown")
        h2h_rows = [
            ("Overall Rating (OVR)", str(p1["ovr"]), str(p2["ovr"])),
            ("Potential Ceiling (POT)", str(p1["pot"]), str(p2["pot"])),
            ("Age", str(p1["age"]), str(p2["age"])),
            ("Pace", str(p1["pace"]), str(p2["pace"])),
            ("Shooting", str(p1["shooting"]), str(p2["shooting"])),
            ("Passing", str(p1["passing"]), str(p2["passing"])),
            ("Dribbling", str(p1["dribbling"]), str(p2["dribbling"])),
            ("Defending", str(p1["defending"]), str(p2["defending"])),
            ("Physical", str(p1["physical"]), str(p2["physical"])),
            ("Goals / 90", f"{p1['goals_p90']:.2f}", f"{p2['goals_p90']:.2f}"),
            ("Assists / 90", f"{p1['assists_p90']:.2f}", f"{p2['assists_p90']:.2f}"),
            ("Actual Transfer Value", f"€{p1['market_val_m']:.1f}M", f"€{p2['market_val_m']:.1f}M"),
            ("ScoutIQ Predicted Value", f"€{p1['pred_val_m']:.1f}M", f"€{p2['pred_val_m']:.1f}M"),
            ("Performance Index", f"{p1['performance_score']:.1f}", f"{p2['performance_score']:.1f}")
        ]
        comp_df = pd.DataFrame(h2h_rows, columns=["Metric", str(p1["name"]), str(p2["name"])])
        st.table(comp_df)


# -------------------------------------------------------------
# TAB 6: ML Model & Regression Diagnostics
# -------------------------------------------------------------
with tab6:
    st.markdown("### 📊 Data Science & ML Model Diagnostics")
    st.markdown("Full transparency into candidate regression algorithms, residual distributions, and feature importance rankings.")

    diag_summary = []
    for model_k, model_v in model_mgr.metrics.items():
        diag_summary.append({
            "Regression Algorithm": model_k,
            "R² Score (Test Split)": model_v["R2_Score"],
            "MAE (€ Millions)": f"€{model_v['MAE_EUR_M']:.2f}M",
            "RMSE (€ Millions)": f"€{model_v['RMSE_EUR_M']:.2f}M",
            "MAPE (%)": f"{model_v['MAPE_Pct']:.1f}%"
        })
    st.table(pd.DataFrame(diag_summary))

    dc1, dc2 = st.columns(2)
    with dc1:
        y_pred_log = model_mgr.models[selected_model].predict(model_mgr.X_test)
        y_pred_m = np.expm1(y_pred_log)
        st.plotly_chart(render_residuals_plot(model_mgr.y_test_m.values, y_pred_m), use_container_width=True)

    with dc2:
        st.plotly_chart(render_feature_importance_chart(model_mgr.feature_importances), use_container_width=True)

    st.markdown("##### 🧬 Feature Engineering Correlation Matrix")
    c_cols = [
        "market_val_m", "ovr", "pot", "age", "goals_p90", "assists_p90",
        "xg_p90", "prog_passes_p90", "prog_carries_p90", "athletic_index", "technical_index"
    ]
    st.plotly_chart(render_correlation_heatmap(df_processed, c_cols), use_container_width=True)

st.markdown(
    """
    <hr style="border-color: rgba(255,255,255,0.08); margin-top: 3.5rem;">
    <div style="text-align: center; color: #64748b; font-size: 0.85rem; padding-bottom: 1rem;">
        ScoutIQ Pro • Football Analytics & Transfer Intelligence Engine
    </div>
    """,
    unsafe_allow_html=True
)
