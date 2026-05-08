"""Layer 2: ハードフィルタ（ファンドユニバースの絞り込み）"""

import pandas as pd

from src.utils.constants import HARD_FILTER_THRESHOLDS


def apply_hard_filters(fund_master: pd.DataFrame) -> pd.DataFrame:
    """
    長期投資に不適なファンドをユニバースから除外する。

    除外条件:
    - レバレッジ型
    - 通貨選択型
    - 元本取り崩し型の毎月分配
    - 純資産30億円未満
    - 運用期間3年未満
    - インデックスで信託報酬1.5%超
    - ファンドスコア3年が1（最下位）
    """
    df = fund_master.copy()
    thresholds = HARD_FILTER_THRESHOLDS

    # NISA成長投資枠対象外を除外
    df = df[df["is_nisa_growth_eligible"].fillna(False)]

    # レバレッジ型を除外
    df = df[~df["is_leveraged"].fillna(False)]

    # 通貨選択型を除外
    df = df[~df["is_currency_select"].fillna(False)]

    # 元本取り崩し型の毎月分配を除外
    principal_payout_mask = (
        df["is_monthly_payout"].fillna(False)
        & (df["payout_type"] == "principal")
    )
    df = df[~principal_payout_mask]

    # 純資産30億円未満を除外
    df = df[df["aum_oku_yen"].fillna(0) >= thresholds["min_aum_oku_yen"]]

    # 運用期間3年未満を除外
    df = df[df["operation_years"].fillna(0) >= thresholds["min_operation_years"]]

    # インデックスファンドで信託報酬1.5%超を除外
    index_high_cost = df["is_index"].fillna(False) & (
        df["expense_ratio"].fillna(0) > thresholds["max_index_expense_ratio"]
    )
    df = df[~index_high_cost]

    # ファンドスコア3年が1（最下位）を除外（データあり かつ 1 の場合のみ）
    has_score = df["fund_score_3y"] > 0
    lowest_score = df["fund_score_3y"] == 1
    df = df[~(has_score & lowest_score)]

    return df.reset_index(drop=True)
