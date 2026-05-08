"""ユーザー入力のファンド名をマスタにファジーマッチングする"""

import pandas as pd
from rapidfuzz import fuzz, process

from src.utils.constants import NICKNAME_DICT

_SCORE_CUTOFF = 60


def match_fund(
    user_input: str,
    fund_master: pd.DataFrame,
) -> tuple[str | None, float]:
    """
    ユーザー入力文字列からファンドIDを推定する。

    Returns:
        (fund_id, 確信度 0-1)  候補なしは (None, 0.0)
    """
    user_input = user_input.strip()

    # 愛称辞書で完全一致確認（最優先）
    for nickname, fund_id in NICKNAME_DICT.items():
        if nickname.lower() == user_input.lower():
            if fund_id in fund_master["fund_id"].values:
                return fund_id, 1.0

    # 正式名・愛称の候補リスト構築
    name_to_id: dict[str, str] = {}

    for _, row in fund_master.iterrows():
        name_to_id[row["fund_name"]] = row["fund_id"]
        if pd.notna(row.get("fund_nickname")) and str(row["fund_nickname"]).strip():
            name_to_id[str(row["fund_nickname"])] = row["fund_id"]

    # 愛称辞書のキーも候補に追加（IDがマスタに存在する場合のみ）
    valid_ids = set(fund_master["fund_id"].values)
    for nickname, fund_id in NICKNAME_DICT.items():
        if fund_id in valid_ids:
            name_to_id[nickname] = fund_id

    candidates = list(name_to_id.keys())
    if not candidates:
        return None, 0.0

    result = process.extractOne(
        user_input,
        candidates,
        scorer=fuzz.WRatio,
        score_cutoff=_SCORE_CUTOFF,
    )
    if result is None:
        return None, 0.0

    matched_text, score, _ = result
    return name_to_id[matched_text], score / 100.0


def match_fund_candidates(
    user_input: str,
    fund_master: pd.DataFrame,
    top_n: int = 3,
) -> list[tuple[str, str, float]]:
    """
    候補を複数返す。確信度が低い場合のユーザー選択用。

    Returns:
        [(fund_id, fund_name, 確信度)] のリスト（降順）
    """
    user_input = user_input.strip()

    name_to_id: dict[str, str] = {}
    for _, row in fund_master.iterrows():
        name_to_id[row["fund_name"]] = row["fund_id"]
        if pd.notna(row.get("fund_nickname")) and str(row["fund_nickname"]).strip():
            name_to_id[str(row["fund_nickname"])] = row["fund_id"]

    valid_ids = set(fund_master["fund_id"].values)
    for nickname, fund_id in NICKNAME_DICT.items():
        if fund_id in valid_ids:
            name_to_id[nickname] = fund_id

    candidates = list(name_to_id.keys())
    if not candidates:
        return []

    results = process.extract(
        user_input,
        candidates,
        scorer=fuzz.WRatio,
        limit=top_n * 3,
    )

    seen_ids: set[str] = set()
    output: list[tuple[str, str, float]] = []

    for text, score, _ in results:
        fund_id = name_to_id[text]
        if fund_id in seen_ids:
            continue
        seen_ids.add(fund_id)
        rows = fund_master[fund_master["fund_id"] == fund_id]
        if rows.empty:
            continue
        fund_name = rows.iloc[0]["fund_name"]
        output.append((fund_id, fund_name, score / 100.0))
        if len(output) >= top_n:
            break

    return output
