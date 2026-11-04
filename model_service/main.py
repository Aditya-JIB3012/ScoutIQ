"""HTTP API that exposes ScoutIQ's existing Python data and valuation pipeline."""

from __future__ import annotations

import re
import threading
import time
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from scoutiq.data.dataset_generator import get_all_real_players, get_current_players
from scoutiq.data.preprocessor import (
    FootballDataCleaner,
    FootballFeatureEngineer,
    LEAGUE_TIER_MAP,
)
from scoutiq.models.regressor import ScoutIQModelManager

app = FastAPI(title="ScoutIQ Model API", version="1.0.0")

_lock = threading.Lock()
_players: pd.DataFrame | None = None
_model: ScoutIQModelManager | None = None
_data_source = ""
_loaded_at: float | None = None
_cache_seconds = 24 * 60 * 60


def _player_id(name: str, club: str) -> str:
    text = f"{name}-{club}".lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _plain(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value


def _record(row: pd.Series) -> dict[str, Any]:
    return {key: _plain(value) for key, value in row.to_dict().items()}


def _ensure_loaded() -> tuple[pd.DataFrame, ScoutIQModelManager]:
    global _players, _model, _data_source, _loaded_at
    if _players is not None and _model is not None and _loaded_at and time.time() - _loaded_at < _cache_seconds:
        return _players, _model
    with _lock:
        if _players is not None and _model is not None and _loaded_at and time.time() - _loaded_at < _cache_seconds:
            return _players, _model
        try:
            raw, _data_source = get_current_players()
        except Exception:
            raw = get_all_real_players()
            _data_source = "Bundled fallback · 2024-era data"
        clean = FootballDataCleaner().fit_transform(raw)
        processed = FootballFeatureEngineer().transform(clean)
        manager = ScoutIQModelManager()
        manager.train_and_evaluate(processed)
        processed["pred_val_m"] = manager.predict_value(processed)
        processed["val_delta_m"] = processed["pred_val_m"] - processed["market_val_m"]
        processed["val_ratio"] = processed["pred_val_m"] / processed["market_val_m"].clip(lower=0.5)
        processed["performance_score"] = processed.apply(manager.compute_performance_index, axis=1)
        processed["player_id"] = [
            _player_id(name, club) for name, club in zip(processed["name"], processed["club"])
        ]
        _players = processed.reset_index(drop=True)
        _model = manager
        _loaded_at = time.time()
    return _players, _model


def _get_player(player_id: str) -> pd.Series:
    players, _ = _ensure_loaded()
    matches = players[players["player_id"] == player_id]
    if matches.empty:
        raise HTTPException(status_code=404, detail="Player not found")
    return matches.iloc[0]


def _profile(row: pd.Series, model: ScoutIQModelManager) -> dict[str, Any]:
    report = row.copy()
    report["explanations"] = model.explain_player_valuation(row)
    report["source"] = _data_source
    return _record(report)


class SimulationInput(BaseModel):
    player_id: str
    age: int | None = Field(default=None, ge=16, le=45)
    ovr: int | None = Field(default=None, ge=40, le=99)
    pot: int | None = Field(default=None, ge=40, le=99)
    pace: int | None = Field(default=None, ge=1, le=99)
    shooting: int | None = Field(default=None, ge=1, le=99)
    passing: int | None = Field(default=None, ge=1, le=99)
    dribbling: int | None = Field(default=None, ge=1, le=99)
    defending: int | None = Field(default=None, ge=1, le=99)
    physical: int | None = Field(default=None, ge=1, le=99)
    goals_p90: float | None = Field(default=None, ge=0, le=2)
    assists_p90: float | None = Field(default=None, ge=0, le=2)
    contract_years_left: float | None = Field(default=None, ge=0, le=8)
    league: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metadata")
def metadata() -> dict[str, Any]:
    players, model = _ensure_loaded()
    return {
        "source": _data_source,
        "refreshed_at": pd.Timestamp.fromtimestamp(_loaded_at, tz="UTC").isoformat() if _loaded_at else None,
        "player_count": int(len(players)),
        "average_value": round(float(players["market_val_m"].mean()), 1),
        "value_gap_count": int((players["pred_val_m"] > players["market_val_m"]).sum()),
        "leagues": sorted(players["league"].dropna().unique().tolist()),
        "roles": sorted(players["pos_role"].dropna().unique().tolist()),
        "models": model.metrics,
        "best_model": model.best_model_name,
    }


@app.get("/players")
def list_players(
    search: str = "",
    league: str = "",
    role: str = "",
    min_age: int = Query(default=16, ge=16, le=45),
    max_age: int = Query(default=45, ge=16, le=45),
    max_value: float = Query(default=250, ge=0, le=500),
    sort: str = "value",
    order: str = "desc",
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    players, _ = _ensure_loaded()
    subset = players.copy()
    if search.strip():
        pattern = re.escape(search.strip())
        mask = (
            subset["name"].astype(str).str.contains(pattern, case=False, na=False)
            | subset["club"].astype(str).str.contains(pattern, case=False, na=False)
        )
        subset = subset[mask]
    if league:
        subset = subset[subset["league"] == league]
    if role:
        subset = subset[subset["pos_role"] == role]
    subset = subset[(subset["age"] >= min_age) & (subset["age"] <= max_age) & (subset["market_val_m"] <= max_value)]
    sort_cols = {
        "value": "market_val_m", "predicted": "pred_val_m",
        "performance": "performance_score", "age": "age", "name": "name",
    }
    subset = subset.sort_values(sort_cols.get(sort, "market_val_m"), ascending=order == "asc")
    total = len(subset)
    items = [_record(row) for _, row in subset.iloc[offset:offset + limit].iterrows()]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/players/{player_id}")
def player_detail(player_id: str) -> dict[str, Any]:
    _, model = _ensure_loaded()
    return _profile(_get_player(player_id), model)


@app.get("/compare")
def compare_players(first: str, second: str) -> dict[str, Any]:
    _, model = _ensure_loaded()
    return {"players": [_profile(_get_player(first), model), _profile(_get_player(second), model)]}


@app.get("/opportunities")
def opportunities(
    budget: float = Query(default=60, ge=1, le=500),
    under_24: bool = True,
    limit: int = Query(default=12, ge=1, le=50),
) -> dict[str, Any]:
    players, _ = _ensure_loaded()
    deals = players[(players["market_val_m"] <= budget) & (players["val_delta_m"] > 0)].copy()
    if under_24:
        deals = deals[deals["age"] <= 24]
    deals = deals.sort_values(["val_ratio", "performance_score"], ascending=False)
    total = int(len(deals))
    deals = deals.head(limit)
    return {"items": [_record(row) for _, row in deals.iterrows()], "total": total}


@app.post("/simulate")
def simulate(payload: SimulationInput) -> dict[str, Any]:
    players, model = _ensure_loaded()
    base = _get_player(payload.player_id).copy()
    for key, value in payload.model_dump(exclude={"player_id"}, exclude_none=True).items():
        base[key] = value
    base["pot_ovr_growth"] = max(0, base["pot"] - base["ovr"])
    base["age_squared"] = base["age"] ** 2
    base["age_pot_synergy"] = base["pot_ovr_growth"] / max(base["age"] - 14, 1)
    base["goal_xg_diff"] = base["goals_p90"] - base["xg_p90"]
    base["assist_xa_diff"] = base["assists_p90"] - base["xa_p90"]
    base["goal_involvement_p90"] = base["goals_p90"] + base["assists_p90"]
    base["expected_involvement_p90"] = base["xg_p90"] + base["xa_p90"]
    base["athletic_index"] = base["pace"] * 0.55 + base["physical"] * 0.45
    base["technical_index"] = base["shooting"] * 0.35 + base["passing"] * 0.35 + base["dribbling"] * 0.30
    base["contract_leverage"] = float(np.clip(base["contract_years_left"] / 4, 0.25, 1.25))
    if payload.league:
        base["league_tier_factor"] = LEAGUE_TIER_MAP.get(payload.league, 0.6)
    row = pd.DataFrame([base])
    predicted = float(model.predict_value(row)[0])
    return {
        "predicted_value": predicted,
        "range_low": round(predicted * 0.9, 1),
        "range_high": round(predicted * 1.1, 1),
        "baseline_value": float(_get_player(payload.player_id)["market_val_m"]),
    }


@app.get("/analytics")
def analytics() -> dict[str, Any]:
    players, model = _ensure_loaded()
    feature_rows = model.feature_importances.head(10).to_dict("records")
    return {
        "metrics": model.metrics,
        "best_model": model.best_model_name,
        "features": [_record(pd.Series(row)) for row in feature_rows],
        "league_values": players.groupby("league")["market_val_m"].median().round(1).to_dict(),
    }
