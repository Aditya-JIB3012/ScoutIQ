"""Regression models for Transfer Market Value and Performance Rating in ScoutIQ.
Includes multi-model comparison, evaluation metrics, and explainability breakdowns.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error

FEATURE_COLUMNS = [
    "age", "age_squared", "ovr", "pot", "pot_ovr_growth", "age_pot_synergy",
    "pace", "shooting", "passing", "dribbling", "defending", "physical",
    "athletic_index", "technical_index", "ball_progression_index",
    "goals_p90", "assists_p90", "xg_p90", "xa_p90",
    "goal_xg_diff", "assist_xa_diff", "goal_involvement_p90", "expected_involvement_p90",
    "key_passes_p90", "prog_passes_p90", "prog_carries_p90", "tackles_won_p90",
    "reputation", "weak_foot", "skill_moves", "contract_years_left", "contract_leverage",
    "league_tier_factor", "availability_rate"
]

FEATURE_DISPLAY_NAMES = {
    "ovr": "Overall Rating (OVR)",
    "pot": "Potential (POT)",
    "age": "Player Age",
    "age_squared": "Age Decline Curve",
    "pot_ovr_growth": "Development Upside",
    "age_pot_synergy": "Youth Potential Synergy",
    "reputation": "International Reputation",
    "league_tier_factor": "League Prestige",
    "technical_index": "Technical Quality",
    "athletic_index": "Athleticism & Pace",
    "ball_progression_index": "Ball Progression",
    "goal_involvement_p90": "Goal Involvement /90",
    "expected_involvement_p90": "Expected Impact (xG+xA)",
    "contract_leverage": "Contract Security",
    "contract_years_left": "Years on Contract",
    "goals_p90": "Goals / 90",
    "assists_p90": "Assists / 90",
    "shooting": "Finishing Ability",
    "passing": "Passing Vision",
    "dribbling": "Ball Control & Dribbling",
    "pace": "Top Speed & Acceleration",
    "physical": "Stamina & Strength",
    "defending": "Defensive Quality",
    "tackles_won_p90": "Tackles Won / 90",
    "availability_rate": "Injury Resistance"
}


class ScoutIQModelManager:
    """
    Manages regression models for Market Value and Performance Rating estimation.
    """

    def __init__(self):
        self.models: Dict[str, Any] = {
            "Random Forest": RandomForestRegressor(n_estimators=150, max_depth=14, random_state=42, n_jobs=-1),
            "Gradient Boosting": GradientBoostingRegressor(n_estimators=160, learning_rate=0.07, max_depth=5, random_state=42),
            "Ridge Regression": Pipeline([
                ("scaler", StandardScaler()),
                ("ridge", Ridge(alpha=30.0, random_state=42))
            ])
        }
        self.best_model_name = "Gradient Boosting"
        self.metrics: Dict[str, Dict[str, float]] = {}
        self.feature_cols = FEATURE_COLUMNS
        self.feature_importances: pd.DataFrame = pd.DataFrame()
        self.is_trained = False
        self.X_train = None
        self.X_test = None
        self.y_test = None
        self.y_test_m = None
        self.baseline_features = {}

    def train_and_evaluate(self, df_processed: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Train all candidate regression models and record performance metrics."""
        # Ensure all features exist
        available_features = [col for col in self.feature_cols if col in df_processed.columns]
        self.feature_cols = available_features

        X = df_processed[self.feature_cols].fillna(0)
        # Log-transformed target: log1p(market_val_m)
        y = df_processed["log_market_val"]
        y_original = df_processed["market_val_m"]

        X_train, X_test, y_train, y_test, y_train_orig, y_test_orig = train_test_split(
            X, y, y_original, test_size=0.20, random_state=42
        )

        self.X_train = X_train
        self.X_test = X_test
        self.y_test = y_test
        self.y_test_m = y_test_orig
        self.baseline_features = X_train.median().to_dict()

        for name, model in self.models.items():
            model.fit(X_train, y_train)
            pred_log = model.predict(X_test)
            pred_m = np.expm1(pred_log)
            pred_m = np.clip(pred_m, 0.1, None)

            r2 = float(r2_score(y_test_orig, pred_m))
            mae = float(mean_absolute_error(y_test_orig, pred_m))
            rmse = float(root_mean_squared_error(y_test_orig, pred_m))
            mape = float(np.mean(np.abs((y_test_orig - pred_m) / np.maximum(y_test_orig, 0.5))) * 100)

            self.metrics[name] = {
                "R2_Score": round(r2, 4),
                "MAE_EUR_M": round(mae, 2),
                "RMSE_EUR_M": round(rmse, 2),
                "MAPE_Pct": round(mape, 2)
            }

        # Select best model based on R2 on test set
        self.best_model_name = max(self.metrics.keys(), key=lambda k: self.metrics[k]["R2_Score"])

        # Extract feature importance from best tree model
        ref_model = self.models["Gradient Boosting"] if "Gradient Boosting" in self.models else self.models["Random Forest"]
        importances = ref_model.feature_importances_
        fi_df = pd.DataFrame({
            "feature": self.feature_cols,
            "display_name": [FEATURE_DISPLAY_NAMES.get(c, c) for c in self.feature_cols],
            "importance": importances
        }).sort_values(by="importance", ascending=False)
        self.feature_importances = fi_df

        self.is_trained = True
        return self.metrics

    def predict_value(self, player_features: pd.DataFrame, model_name: str | None = None) -> np.ndarray:
        """Predict market value in EUR Millions."""
        if not self.is_trained:
            raise ValueError("Models must be trained before predicting.")

        model_name = model_name or self.best_model_name
        model = self.models[model_name]

        X_input = player_features[self.feature_cols].fillna(0)
        pred_log = model.predict(X_input)
        pred_m = np.expm1(pred_log)
        return np.round(np.clip(pred_m, 0.2, 250.0), 2)

    def explain_player_valuation(self, player_row: pd.Series, model_name: str | None = None) -> List[Dict[str, Any]]:
        """
        Explain why a player's valuation is higher or lower than the median player,
        decomposing contributions across key value dimensions.
        """
        if not self.is_trained:
            return []

        # Compare player's key attributes with dataset baseline
        explanations = []

        # 1. Overall & Potential
        ovr_diff = player_row.get("ovr", 75) - self.baseline_features.get("ovr", 75)
        pot_diff = player_row.get("pot", 78) - self.baseline_features.get("pot", 78)
        rating_impact = (ovr_diff * 1.8) + (pot_diff * 1.2)
        explanations.append({
            "category": "Rating & Potential",
            "stat": f"OVR: {player_row.get('ovr', 0)} | POT: {player_row.get('pot', 0)}",
            "delta_eur_m": round(rating_impact, 1),
            "description": "Base skill and future development ceiling"
        })

        # 2. Age Factor
        age = player_row.get("age", 25)
        if age <= 21:
            age_impact = 15.0 + (22 - age) * 4.0
            age_desc = "Prime youth multiplier (high resale & growth window)"
        elif age <= 25:
            age_impact = 8.0
            age_desc = "Entering prime competitive years"
        elif age <= 28:
            age_impact = 2.0
            age_desc = "Peak performance window"
        elif age <= 31:
            age_impact = -8.0
            age_desc = "Approaching veteran stage; limited resale value"
        else:
            age_impact = -18.0
            age_desc = "Late career stage; steep depreciation"
        explanations.append({
            "category": "Age & Career Phase",
            "stat": f"{age} years old",
            "delta_eur_m": round(age_impact, 1),
            "description": age_desc
        })

        # 3. Attacking / Goal Output
        goals_p90 = player_row.get("goals_p90", 0.0)
        assists_p90 = player_row.get("assists_p90", 0.0)
        involvement = goals_p90 + assists_p90
        base_inv = self.baseline_features.get("goals_p90", 0.15) + self.baseline_features.get("assists_p90", 0.12)
        output_impact = (involvement - base_inv) * 22.0
        explanations.append({
            "category": "Offensive Output /90",
            "stat": f"{involvement:.2f} G+A/90",
            "delta_eur_m": round(output_impact, 1),
            "description": "Direct match scoring and playmaking impact"
        })

        # 4. League Tier & Global Prestige
        league = player_row.get("league", "Other")
        tier_factor = player_row.get("league_tier_factor", 0.7)
        reputation = player_row.get("reputation", 1)
        league_impact = (tier_factor - 0.75) * 20.0 + (reputation - 2) * 5.0
        explanations.append({
            "category": "League & Brand Prestige",
            "stat": f"{league} (Rep: {'★' * int(reputation)})",
            "delta_eur_m": round(league_impact, 1),
            "description": "Market exposure and financial strength of league"
        })

        # 5. Contract Leverage
        years_left = player_row.get("contract_years_left", 2.0)
        contract_impact = (years_left - 2.0) * 6.5
        explanations.append({
            "category": "Contract Security",
            "stat": f"{years_left:.1f} years left",
            "delta_eur_m": round(contract_impact, 1),
            "description": "Club transfer bargaining leverage"
        })

        return explanations

    def compute_performance_index(self, player_row: pd.Series) -> float:
        """
        Calculates an objective 0-100 Performance Rating based on per-90 metrics,
        efficiency ratios, and core attributes.
        """
        pos = player_row.get("position", "CM")
        ovr = player_row.get("ovr", 75)
        goals = player_row.get("goals_p90", 0.1)
        assists = player_row.get("assists_p90", 0.1)
        prog = player_row.get("ball_progression_index", 3.0)
        tackles = player_row.get("tackles_won_p90", 1.0)
        availability = player_row.get("availability_rate", 0.9)

        if any(p in pos for p in ["ST", "CF", "LW", "RW"]):
            score = (ovr * 0.45) + (goals * 25.0) + (assists * 15.0) + (prog * 1.5)
        elif any(p in pos for p in ["CAM", "CM"]):
            score = (ovr * 0.45) + (assists * 20.0) + (prog * 2.8) + (tackles * 3.5)
        elif any(p in pos for p in ["CB", "LB", "RB", "CDM"]):
            score = (ovr * 0.45) + (tackles * 8.0) + (prog * 2.0) + (player_row.get("defending", 70) * 0.20)
        else:  # GK
            score = (ovr * 0.70) + (player_row.get("physical", 70) * 0.30)

        # Scale by availability
        score = score * availability
        return round(float(np.clip(score, 50.0, 99.0)), 1)
