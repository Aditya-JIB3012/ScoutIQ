"""Data Preprocessor & Feature Engineering Pipeline for ScoutIQ.
Demonstrates handling messy real-world football data:
- String currency & wage parsing
- Date & contract remaining calculations
- Multi-position normalization
- Missing value imputation by position
- Domain-specific feature engineering (Age curves, finishing efficiency, progression indices)
- Target log transformations
"""

from __future__ import annotations
import re
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

LEAGUE_TIER_MAP = {
    "Premier League": 1.0,
    "La Liga": 0.90,
    "LaLiga": 0.90,
    "Bundesliga": 0.85,
    "Serie A": 0.85,
    "Ligue 1": 0.75,
    "Eredivisie / Liga Portugal": 0.65,
    "Other": 0.50
}

POSITION_ROLES = {
    "ST": "ATT", "CF": "ATT",
    "LW": "WNG", "RW": "WNG", "LM": "WNG", "RM": "WNG",
    "CAM": "MID", "CM": "MID", "CDM": "MID",
    "CB": "DEF", "LB": "DEF", "RB": "DEF", "LWB": "DEF", "RWB": "DEF",
    "GK": "GK"
}


def parse_currency_to_millions(val: any) -> float:
    """Parse raw string currency (e.g. '€180.00m', '€900k', ' € 25.5 M ') to float millions."""
    if pd.isna(val) or val is None:
        return np.nan

    val_str = str(val).strip().replace(",", "")
    if val_str in ["N/A", "-", "", "nan", "None"]:
        return np.nan

    # Extract digits and potential multiplier
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([mMkK])?", val_str)
    if not match:
        return np.nan

    num = float(match.group(1))
    unit = match.group(2)

    if unit:
        unit = unit.lower()
        if unit == "m":
            return round(num, 3)
        elif unit == "k":
            return round(num / 1000.0, 4)
    # If no unit specified and number is small, assume millions; if > 100,000 assume exact EUR
    if num > 100000:
        return round(num / 1_000_000.0, 3)
    return round(num, 3)


def parse_wage_to_weekly_eur(val: any) -> float:
    """Parse messy wage string to weekly wage in EUR integer."""
    if pd.isna(val) or val is None:
        return np.nan

    val_str = str(val).strip().replace(",", "")
    if val_str in ["N/A", "-", "", "nan", "None"]:
        return np.nan

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([kK])?", val_str)
    if not match:
        return np.nan

    num = float(match.group(1))
    unit = match.group(2)

    if unit and unit.lower() == "k":
        return int(num * 1000)
    return int(num)


def parse_contract_years(val: any, reference_year: float | None = None) -> float:
    """Calculate remaining contract years relative to reference season."""
    if reference_year is None:
        today = datetime.now()
        reference_year = today.year + (today.month - 1) / 12.0
    if pd.isna(val) or val is None:
        return 2.0  # default assumption

    val_str = str(val).strip()
    # Try YYYY-MM-DD
    try:
        dt = datetime.strptime(val_str[:10], "%Y-%m-%d")
        remaining = (dt.year + (dt.month / 12.0)) - reference_year
        return max(0.2, round(remaining, 1))
    except Exception:
        pass

    # Try extracting 4-digit year
    year_match = re.search(r"(202[4-9]|203[0-5])", val_str)
    if year_match:
        exp_year = float(year_match.group(1)) + 0.5
        return max(0.2, round(exp_year - reference_year, 1))

    return 2.0


def clean_primary_position(val: any) -> str:
    """Extract primary position code from multi-position strings."""
    if pd.isna(val) or val is None:
        return "CM"
    val_str = str(val).split(",")[0].strip().upper()
    return val_str if val_str in POSITION_ROLES else "CM"


class FootballDataCleaner:
    """
    Cleans messy raw football player data and imputes missing statistics.
    """

    def __init__(self):
        self.position_medians = {}

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()

        # 1. Clean primary identifiers and categories
        df_clean["primary_pos"] = df_clean["position"].apply(clean_primary_position)
        df_clean["pos_role"] = df_clean["primary_pos"].map(POSITION_ROLES).fillna("MID")

        # 2. Parse currency, wage, and contract
        df_clean["market_val_m"] = df_clean["market_val_raw"].apply(parse_currency_to_millions)
        df_clean["wage_eur_wk"] = df_clean["wage_raw"].apply(parse_wage_to_weekly_eur)
        df_clean["contract_years_left"] = df_clean["contract_expiry"].apply(parse_contract_years)

        # 3. Numeric conversions
        numeric_cols = [
            "age", "ovr", "pot", "pace", "shooting", "passing", "dribbling", "defending",
            "physical", "goals_p90", "assists_p90", "xg_p90", "xa_p90", "key_passes_p90",
            "prog_passes_p90", "prog_carries_p90", "tackles_won_p90", "reputation",
            "weak_foot", "skill_moves", "minutes", "injury_days"
        ]
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

        # 4. Position-based median imputation for missing FBref stats
        stats_to_impute = ["xg_p90", "xa_p90", "goals_p90", "assists_p90", "key_passes_p90", "prog_passes_p90", "prog_carries_p90"]
        for stat in stats_to_impute:
            if stat in df_clean.columns:
                medians = df_clean.groupby("pos_role")[stat].median()
                self.position_medians[stat] = medians
                df_clean[stat] = df_clean.apply(
                    lambda row: medians.get(row["pos_role"], 0.1) if pd.isna(row[stat]) else row[stat],
                    axis=1
                )

        # Impute missing market values with OVR-based heuristic if completely missing
        if df_clean["market_val_m"].isna().any():
            median_val_by_ovr = df_clean.groupby("ovr")["market_val_m"].transform("median")
            df_clean["market_val_m"] = df_clean["market_val_m"].fillna(median_val_by_ovr).fillna(5.0)

        if df_clean["wage_eur_wk"].isna().any():
            median_wage_by_ovr = df_clean.groupby("ovr")["wage_eur_wk"].transform("median")
            df_clean["wage_eur_wk"] = df_clean["wage_eur_wk"].fillna(median_wage_by_ovr).fillna(25000)

        # Floor market values to at least €0.1M
        df_clean["market_val_m"] = df_clean["market_val_m"].clip(lower=0.1)

        return df_clean


class FootballFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Constructs domain-specific features for predicting market value and overall impact.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_feats = df.copy()

        # Age dynamics: Peak age in football is typically 24-27
        # Quadratic feature captures the parabolic appreciation & depreciation
        df_feats["age_squared"] = df_feats["age"] ** 2
        df_feats["pot_ovr_growth"] = np.maximum(0, df_feats["pot"] - df_feats["ovr"])
        df_feats["age_pot_synergy"] = df_feats["pot_ovr_growth"] / (df_feats["age"] - 14).clip(lower=1)

        # Finishing & Playmaking Efficiency (handling zero division safely)
        df_feats["goal_xg_diff"] = df_feats["goals_p90"] - df_feats["xg_p90"]
        df_feats["assist_xa_diff"] = df_feats["assists_p90"] - df_feats["xa_p90"]
        df_feats["goal_involvement_p90"] = df_feats["goals_p90"] + df_feats["assists_p90"]
        df_feats["expected_involvement_p90"] = df_feats["xg_p90"] + df_feats["xa_p90"]

        # Composite technical and athletic indices
        df_feats["ball_progression_index"] = (
            df_feats["prog_passes_p90"] * 0.45 + df_feats["prog_carries_p90"] * 0.55
        )
        df_feats["athletic_index"] = (df_feats["pace"] * 0.55 + df_feats["physical"] * 0.45)
        df_feats["technical_index"] = (
            df_feats["shooting"] * 0.35 + df_feats["passing"] * 0.35 + df_feats["dribbling"] * 0.30
        )

        # League prestige tier
        df_feats["league_tier_factor"] = df_feats["league"].map(LEAGUE_TIER_MAP).fillna(0.60)

        # Contract leverage (clubs have less transfer leverage when < 1.5 years remain)
        df_feats["contract_leverage"] = np.clip(df_feats["contract_years_left"] / 4.0, 0.25, 1.25)

        # Injury availability rate
        df_feats["availability_rate"] = np.clip((365 - df_feats["injury_days"]) / 365.0, 0.4, 1.0)

        # Target variable log transform (crucial for skewed market values)
        if "market_val_m" in df_feats.columns:
            df_feats["log_market_val"] = np.log1p(df_feats["market_val_m"])

        return df_feats
