"""ファンドマスタCSVの読み込みおよびキャッシュ"""

from pathlib import Path

import pandas as pd
import streamlit as st

_DEFAULT_CSV = Path(__file__).parent.parent.parent / "data" / "fund_master.csv"

_BOOL_COLS = [
    "is_index",
    "is_leveraged",
    "is_currency_select",
    "has_currency_hedge",
    "is_monthly_payout",
    "is_nisa_growth_eligible",
]

_FLOAT_COLS = [
    "region_japan_pct",
    "region_us_pct",
    "region_em_pct",
    "expense_ratio",
    "aum_oku_yen",
    "operation_years",
    "return_6m",
    "return_1y",
    "return_3y",
    "return_5y",
    "return_10y",
    "return_inception",
    "sharpe_1y",
    "sharpe_3y",
    "sharpe_5y",
    "sharpe_10y",
    "stddev_1y",
    "stddev_3y",
    "stddev_5y",
    "stddev_10y",
]

_INT_COLS = [
    "fund_score_1y",
    "fund_score_3y",
    "fund_score_5y",
    "fund_score_10y",
]


@st.cache_data(ttl=3600)
def load_fund_master(csv_path: str | None = None) -> pd.DataFrame:
    """ファンドマスタCSVを読み込み、型を正規化して返す"""
    path = Path(csv_path) if csv_path else _DEFAULT_CSV
    df = pd.read_csv(path)

    for col in _BOOL_COLS:
        if col in df.columns:
            df[col] = df[col].map({"True": True, "False": False, True: True, False: False})

    for col in _FLOAT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in _INT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df


def load_fund_master_plain(csv_path: str | None = None) -> pd.DataFrame:
    """Streamlitキャッシュなし版（テスト用）"""
    path = Path(csv_path) if csv_path else _DEFAULT_CSV
    df = pd.read_csv(path)

    for col in _BOOL_COLS:
        if col in df.columns:
            df[col] = df[col].map({"True": True, "False": False, True: True, False: False})

    for col in _FLOAT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in _INT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df
