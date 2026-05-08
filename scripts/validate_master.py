"""ファンドマスタCSVの検証スクリプト"""

import sys
from pathlib import Path

import pandas as pd

REQUIRED_COLS = [
    "fund_id", "fund_name", "company", "rakuten_category", "asset_type",
    "region", "is_index", "is_leveraged", "expense_ratio",
    "aum_oku_yen", "operation_years", "fund_score_3y",
    "return_5y", "sharpe_5y", "stddev_5y",
    "is_nisa_growth_eligible", "philosophy_tags",
]

NUMERIC_COLS = [
    "expense_ratio", "aum_oku_yen", "operation_years",
    "return_5y", "sharpe_5y", "stddev_5y",
]


def validate(csv_path: str) -> bool:
    """CSVを検証し、問題があればエラーを出力する"""
    df = pd.read_csv(csv_path)
    ok = True

    # 必須カラムチェック
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print(f"[ERROR] 必須カラムが不足: {missing}")
        ok = False

    # 数値カラムの型チェック
    for col in NUMERIC_COLS:
        if col in df.columns:
            non_numeric = df[col].apply(
                lambda x: pd.isna(x) or str(x).replace(".", "").replace("-", "").isdigit()
            )
            # NaNはOK

    # philosophy_tagsの形式確認（|区切り）
    if "philosophy_tags" in df.columns:
        bad_tags = df[df["philosophy_tags"].notna() & ~df["philosophy_tags"].str.contains(r"^[a-z_|]+$", na=False)]
        if len(bad_tags) > 0:
            print(f"[WARN] philosophy_tagsに不正な形式: {len(bad_tags)}件")

    # fund_idの重複チェック
    if "fund_id" in df.columns:
        dup = df[df["fund_id"].duplicated()]
        if len(dup) > 0:
            print(f"[ERROR] fund_idが重複: {dup['fund_id'].tolist()}")
            ok = False

    # stddev_5yの妥当性レンジチェック
    if "stddev_5y" in df.columns:
        numeric = pd.to_numeric(df["stddev_5y"], errors="coerce").dropna()
        out_of_range = numeric[(numeric < 1) | (numeric > 100)]
        if len(out_of_range) > 0:
            print(f"[WARN] stddev_5yが妥当範囲外: {len(out_of_range)}件")

    print(f"[INFO] 総ファンド数: {len(df)}")
    if ok:
        print("[OK] 検証完了。問題は見つかりませんでした。")
    return ok


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/fund_master.csv"
    success = validate(csv_path)
    sys.exit(0 if success else 1)
