"""Layer 3: ファンドスコアリングアルゴリズム"""

import pandas as pd

from src.models.fund_score import FundScore
from src.models.user_profile import UserProfile
from src.utils.constants import (
    DEFAULT_SCORE_ON_MISSING_DATA,
    HORIZON_COEF,
    LOSS_REACTION_COEF,
    TOLERANCE_COEF,
    WEIGHTS,
)
from src.core.profiling import determine_user_type


def compute_return_score(fund: dict, horizon: str) -> float:
    """期間別リターンを0-100にスコア化する"""
    if horizon == "5_10":
        primary = _coalesce(fund, "return_3y", "return_1y")
        secondary = _coalesce(fund, "return_5y")
    elif horizon == "10_20":
        primary = _coalesce(fund, "return_5y", "return_3y")
        secondary = _coalesce(fund, "return_10y")
    else:  # 20_plus
        primary = _coalesce(fund, "return_10y", "return_5y")
        secondary = _coalesce(fund, "return_inception")

    return_value = primary if primary is not None else secondary

    if return_value is None or _is_nan(return_value):
        return DEFAULT_SCORE_ON_MISSING_DATA

    return_value = float(return_value)

    if return_value < 0:
        return max(0.0, 20.0 + return_value)
    elif return_value < 10:
        return 20.0 + return_value * 4.0
    elif return_value < 20:
        return 60.0 + (return_value - 10.0) * 3.0
    elif return_value < 30:
        return 90.0 + (return_value - 20.0)
    else:
        return 100.0


def compute_sharpe_score(fund: dict, horizon: str) -> float:
    """シャープレシオを0-100にスコア化する"""
    if horizon == "5_10":
        sharpe = _coalesce(fund, "sharpe_3y", "sharpe_1y")
    elif horizon == "10_20":
        sharpe = _coalesce(fund, "sharpe_5y", "sharpe_3y")
    else:  # 20_plus
        sharpe = _coalesce(fund, "sharpe_10y", "sharpe_5y")

    if sharpe is None or _is_nan(sharpe):
        return DEFAULT_SCORE_ON_MISSING_DATA

    sharpe = float(sharpe)

    if sharpe < 0:
        return max(0.0, 20.0 + sharpe * 20.0)
    elif sharpe < 0.5:
        return 20.0 + sharpe * 60.0
    elif sharpe < 1.0:
        return 50.0 + (sharpe - 0.5) * 40.0
    elif sharpe < 1.5:
        return 70.0 + (sharpe - 1.0) * 30.0
    elif sharpe < 2.0:
        return 85.0 + (sharpe - 1.5) * 30.0
    else:
        return 100.0


def compute_fund_score(fund: dict, horizon: str) -> float:
    """楽天証券ファンドスコア（1-5）を0-100にスコア化する"""
    if horizon == "5_10":
        score = _coalesce_int(fund, "fund_score_3y", "fund_score_1y")
    elif horizon == "10_20":
        score = _coalesce_int(fund, "fund_score_5y", "fund_score_3y")
    else:  # 20_plus
        score = _coalesce_int(fund, "fund_score_10y", "fund_score_5y")

    if not score or _is_nan(score):
        return DEFAULT_SCORE_ON_MISSING_DATA

    score = int(score)
    return float(score * 20)


def compute_cost_score(fund: dict, fund_master: pd.DataFrame) -> float:
    """
    同じ楽天証券分類内での信託報酬パーセンタイルを評価する。
    低コストほど高得点。
    """
    category = fund.get("rakuten_category")
    same_category = fund_master[fund_master["rakuten_category"] == category]

    if len(same_category) < 3:
        return _absolute_cost_score(float(fund.get("expense_ratio", 1.0) or 1.0))

    expense = float(fund.get("expense_ratio", 1.0) or 1.0)
    expenses = same_category["expense_ratio"].dropna()

    if len(expenses) == 0:
        return _absolute_cost_score(expense)

    percentile = (expenses < expense).mean()
    return (1.0 - percentile) * 100.0


def _absolute_cost_score(expense_ratio: float) -> float:
    """絶対値ベースのコストスコア（比較対象不足時のフォールバック）"""
    if expense_ratio < 0.1:
        return 100.0
    elif expense_ratio < 0.3:
        return 90.0
    elif expense_ratio < 0.5:
        return 75.0
    elif expense_ratio < 1.0:
        return 60.0
    elif expense_ratio < 1.5:
        return 40.0
    elif expense_ratio < 2.0:
        return 20.0
    else:
        return 5.0


def compute_scale_score(fund: dict) -> float:
    """純資産と運用期間の合成スコアを計算する"""
    aum = float(fund.get("aum_oku_yen", 0) or 0)
    if aum < 30:
        aum_score = 30.0
    elif aum < 100:
        aum_score = 50.0
    elif aum < 500:
        aum_score = 70.0
    elif aum < 2000:
        aum_score = 85.0
    else:
        aum_score = 100.0

    years = float(fund.get("operation_years", 0) or 0)
    if years < 1:
        track_score = 20.0
    elif years < 3:
        track_score = 40.0
    elif years < 5:
        track_score = 60.0
    elif years < 10:
        track_score = 80.0
    else:
        track_score = 100.0

    return (aum_score + track_score) / 2.0


def compute_stddev_penalty(fund: dict, profile: UserProfile) -> float:
    """
    標準偏差ペナルティを計算する（ホライズン・下落耐性で動的調整）。

    Returns:
        0-100のペナルティ値（大きいほど不利）
    """
    stddev = (
        fund.get("stddev_5y")
        or fund.get("stddev_3y")
        or fund.get("stddev_1y")
    )

    if stddev is None or _is_nan(stddev):
        return 0.0

    stddev = float(stddev)

    if stddev < 10:
        raw_penalty = 0.0
    elif stddev < 15:
        raw_penalty = 10.0
    elif stddev < 20:
        raw_penalty = 25.0
    elif stddev <= 25:  # 仕様: stddev=25 → 45点ペナルティ
        raw_penalty = 45.0
    elif stddev < 30:
        raw_penalty = 65.0
    else:
        raw_penalty = 90.0

    horizon_coef = HORIZON_COEF.get(profile.horizon or "5_10", 1.0)

    # loss_reactionが回答済みの場合は優先、未回答時はdrawdown_toleranceにフォールバック
    if profile.loss_reaction is not None:
        tolerance_coef = LOSS_REACTION_COEF.get(profile.loss_reaction, 0.5)
    else:
        tolerance_coef = TOLERANCE_COEF.get(profile.drawdown_tolerance or "low", 1.0)

    return raw_penalty * horizon_coef * tolerance_coef


def compute_total_score(
    fund: dict,
    profile: UserProfile,
    fund_master: pd.DataFrame,
) -> FundScore:
    """
    ファンドの総合スコアを計算する（メイン関数）。
    ユーザータイプに応じた動的重みを適用する。
    """
    user_type = determine_user_type(profile)
    weights = WEIGHTS[user_type]

    horizon = profile.horizon or "5_10"

    return_score = compute_return_score(fund, horizon)
    sharpe_score = compute_sharpe_score(fund, horizon)
    fund_score_val = compute_fund_score(fund, horizon)
    cost_score = compute_cost_score(fund, fund_master)
    scale_score = compute_scale_score(fund)
    stddev_penalty = compute_stddev_penalty(fund, profile)

    base = (
        weights["alpha"] * return_score
        + weights["beta"] * sharpe_score
        + weights["gamma"] * fund_score_val
        + weights["delta"] * cost_score
        + weights["epsilon"] * scale_score
    )

    total = base - weights["zeta"] * stddev_penalty
    total = max(0.0, min(100.0, total))

    component_scores = {
        "total_return": round(return_score, 1),
        "sharpe": round(sharpe_score, 1),
        "fund_score": round(fund_score_val, 1),
        "cost": round(cost_score, 1),
        "scale_track_record": round(scale_score, 1),
        "stddev_penalty": round(-stddev_penalty * weights["zeta"], 1),
    }

    return FundScore(
        fund_id=str(fund.get("fund_id", "")),
        fund_name=str(fund.get("fund_name", "")),
        total_score=round(total, 1),
        component_scores=component_scores,
        applied_weights=weights,
        rationale="",
        caveats=[],
        matches_strategy=[],
    )


def _is_nan(value: object) -> bool:
    """NaN・None・空文字列を検出する"""
    if value is None:
        return True
    try:
        import math
        return math.isnan(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return True


def _coalesce(fund: dict, *keys: str) -> float | None:
    """複数キーを順に試し、最初のNaNでない値を返す（0.0も有効値として扱う）"""
    for key in keys:
        v = fund.get(key)
        if v is not None and not _is_nan(v):
            return float(v)
    return None


def _coalesce_int(fund: dict, *keys: str) -> int:
    """複数キーを順に試し、最初の正の整数を返す。なければ0"""
    for key in keys:
        v = fund.get(key)
        if v is not None and not _is_nan(v):
            iv = int(float(v))
            if iv > 0:
                return iv
    return 0
