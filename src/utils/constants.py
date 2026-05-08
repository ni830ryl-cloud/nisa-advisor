"""マジックナンバーおよびアプリ全体の定数"""

from typing import Final

# Layer 2 ハードフィルタ閾値
HARD_FILTER_THRESHOLDS: Final[dict] = {
    "min_aum_oku_yen": 30,
    "min_operation_years": 3,
    "max_index_expense_ratio": 1.5,
    "min_fund_score_3y": 2,
}

# ユーザータイプ別スコアリング重み
# α=リターン, β=シャープ, γ=ファンドスコア, δ=コスト, ε=規模, ζ=ペナルティ係数
WEIGHTS: Final[dict] = {
    "beginner_low_risk": {
        "alpha": 0.15,
        "beta": 0.20,
        "gamma": 0.10,
        "delta": 0.30,
        "epsilon": 0.15,
        "zeta": 1.00,
    },
    "index_auto": {
        "alpha": 0.20,
        "beta": 0.15,
        "gamma": 0.05,
        "delta": 0.35,
        "epsilon": 0.20,
        "zeta": 0.70,
    },
    "intermediate_balanced": {
        "alpha": 0.25,
        "beta": 0.20,
        "gamma": 0.20,
        "delta": 0.15,
        "epsilon": 0.10,
        "zeta": 0.80,
    },
    "dividend_focused": {
        "alpha": 0.20,
        "beta": 0.20,
        "gamma": 0.20,
        "delta": 0.15,
        "epsilon": 0.20,
        "zeta": 0.60,
    },
    "advanced_long_growth": {
        "alpha": 0.45,
        "beta": 0.10,
        "gamma": 0.20,
        "delta": 0.10,
        "epsilon": 0.05,
        "zeta": 0.10,
    },
}

# ホライズン係数（標準偏差ペナルティ）
HORIZON_COEF: Final[dict] = {
    "5_10": 1.0,
    "10_20": 0.5,
    "20_plus": 0.2,
}

# 下落耐性係数（標準偏差ペナルティ）
TOLERANCE_COEF: Final[dict] = {
    "low": 1.0,
    "medium": 0.5,
    "high": 0.0,
}

# UI定数
MAX_HOLDINGS_INPUT: Final[int] = 10
TOP_FUNDS_PER_STRATEGY: Final[int] = 3

# 愛称辞書（ユーザー入力表記揺れ対応）
NICKNAME_DICT: Final[dict[str, str]] = {
    "オルカン": "JP90C000H1T1",
    "eMAXIS Slim 全世界": "JP90C000H1T1",
    "S&P500": "JP90C000GKC6",
    "eMAXIS S&P500": "JP90C000GKC6",
    "楽天VTI": "JP90C000FHD2",
    "楽天VTI": "JP90C000FHD2",
    "NASDAQ100": "JP90C000QF22",
    "ナスダック100": "JP90C000QF22",
    "楽天NASDAQ100": "JP90C000QF22",
    "FANG+": "JP90C000FZD4",
    "FANG": "JP90C000FZD4",
    "iFreeNEXT FANG": "JP90C000FZD4",
    "SOX": "JP90C000QF30",
    "楽天SOX": "JP90C000QF30",
    "SCHD": "JP90C000R6N1",
    "楽天SCHD": "JP90C000R6N1",
    "JEPQ": "JP90C000S1R2",
    "WCM": "JP90C000MED5",
    "ネクストジェネレーション": "JP90C000MED5",
    "TOPIX": "JP90C000ENA9",
    "日経225": "JP90C000FXV1",
    "ニッセイ日経225": "JP90C000FXV1",
    "オルカン楽天": "JP90C000R5F8",
    "楽天オルカン": "JP90C000R5F8",
    "楽天プラスオールカントリー": "JP90C000R5F8",
    "新興国": "JP90C000CX77",
    "eMAXIS Slim 新興国": "JP90C000CX77",
    "先進国債券": "JP90C000B2P5",
    "eMAXIS Slim 先進国債券": "JP90C000B2P5",
    "バランス8資産": "JP90C000FBSD",
    "eMAXIS Slim バランス": "JP90C000FBSD",
    "8資産均等": "JP90C000FBSD",
    "インド株": "JP90C000T5P0",
}

# フィロソフィータグ一覧
PHILOSOPHY_TAGS: Final[list[str]] = [
    "growth_focused",
    "value_focused",
    "dividend_focused",
    "momentum",
    "quality",
    "us_centric",
    "japan_centric",
    "global_diversified",
    "em_centric",
    "developed_only",
    "tech_heavy",
    "defensive",
    "cyclical",
    "thematic",
    "broad_market",
    "passive_index",
    "active_concentrated",
    "active_diversified",
    "smart_beta",
    "low_risk",
    "medium_risk",
    "high_risk",
    "very_high_risk",
    "leverage_warning",
    "complex_structure",
    "principal_payout_warning",
]

# データ不足時のデフォルトスコア
DEFAULT_SCORE_ON_MISSING_DATA: Final[float] = 50.0

# PFギャップ検出閾値
GAP_THRESHOLDS: Final[dict] = {
    "min_japan_pct": 0.05,
    "min_em_pct": 0.05,
}

# 警告：地域集中閾値
HIGH_CONCENTRATION_THRESHOLD: Final[float] = 0.8
