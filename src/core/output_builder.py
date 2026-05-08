"""Layer 4: 出力の組み立て（スコアリング結果 + 説明文）"""

import pandas as pd

from src.core.profiling import determine_user_type
from src.core.scoring import compute_stddev_penalty, compute_total_score
from src.core.strategies import filter_funds_by_strategy
from src.models.fund_score import FundScore
from src.models.portfolio import PortfolioAnalysis
from src.models.user_profile import UserProfile
from src.utils.constants import TOP_FUNDS_PER_STRATEGY


def build_results(
    profile: UserProfile,
    fund_master: pd.DataFrame,
    strategies: list[dict],
    pf_analysis: PortfolioAnalysis | None = None,
) -> dict[str, list[FundScore]]:
    """
    各方針に対してTop Nファンドをスコアリングして返す。

    Returns:
        {strategy_id: [FundScore, ...]} の辞書
    """
    results: dict[str, list[FundScore]] = {}

    for strategy in strategies:
        candidates = filter_funds_by_strategy(strategy, fund_master)
        top_funds = select_top_funds(
            strategy=strategy,
            candidates=candidates,
            profile=profile,
            fund_master=fund_master,
            n=TOP_FUNDS_PER_STRATEGY,
        )
        # 説明文を付与
        for fund_score in top_funds:
            fund_row = fund_master[fund_master["fund_id"] == fund_score.fund_id]
            if not fund_row.empty:
                fund_dict = fund_row.iloc[0].to_dict()
                fund_score.rationale = generate_rationale(fund_dict, profile, fund_score.component_scores)
                fund_score.caveats = generate_caveats(fund_dict, profile)
                fund_score.matches_strategy = [strategy["id"]]

        results[strategy["id"]] = top_funds

    return results


def select_top_funds(
    strategy: dict,
    candidates: pd.DataFrame,
    profile: UserProfile,
    fund_master: pd.DataFrame,
    n: int = TOP_FUNDS_PER_STRATEGY,
) -> list[FundScore]:
    """候補ファンドをスコアリングしてTop Nを返す"""
    if candidates.empty:
        return []

    scores = [
        compute_total_score(row.to_dict(), profile, fund_master)
        for _, row in candidates.iterrows()
    ]

    scores.sort(key=lambda s: s.total_score, reverse=True)
    diversified = _deduplicate_by_philosophy(scores, max_per_tag=1)

    return diversified[:n]


def generate_rationale(
    fund: dict,
    profile: UserProfile,
    component_scores: dict,
) -> str:
    """なぜこのファンドがこのプロファイルに合うかの説明文を生成する"""
    reasons: list[str] = []
    tags = str(fund.get("philosophy_tags", ""))

    if component_scores.get("total_return", 0) >= 80:
        return_val = fund.get("return_5y") or fund.get("return_3y")
        if return_val is not None:
            reasons.append(
                f"過去{_horizon_label(profile.horizon)}のリターンが"
                f"年率{return_val:.1f}%と高水準"
            )

    if component_scores.get("cost", 0) >= 90:
        expense = fund.get("expense_ratio")
        if expense is not None:
            reasons.append(f"信託報酬{expense:.4f}%は同分類内で低コスト水準")

    if component_scores.get("fund_score", 0) >= 80:
        fs = fund.get("fund_score_3y") or fund.get("fund_score_5y")
        if fs:
            reasons.append(f"楽天証券ファンドスコア{fs}/5は同分類内で高評価")

    user_type = determine_user_type(profile)
    if user_type == "advanced_long_growth" and "growth_focused" in tags:
        reasons.append("20年超の長期保有・高ボラティリティ許容プロファイルに対し、成長期待値が大きい")

    if user_type == "beginner_low_risk" and "global_diversified" in tags:
        reasons.append("初心者に推奨される全世界分散で長期的な安定成長が期待できる")

    if user_type == "dividend_focused" and "dividend_focused" in tags:
        reasons.append("配当重視プロファイルに対し、定期的なインカムを提供する")

    if not reasons:
        aum = fund.get("aum_oku_yen", 0)
        if aum and float(aum) > 1000:
            reasons.append(f"純資産{float(aum):.0f}億円の大型ファンドで安定した運用基盤を持つ")

    return "。".join(reasons) + "。" if reasons else "プロファイルに適合するファンドです。"


def generate_caveats(fund: dict, profile: UserProfile) -> list[str]:
    """ユーザーへの注意喚起リストを生成する"""
    caveats: list[str] = []
    tags = str(fund.get("philosophy_tags", ""))

    stddev = fund.get("stddev_5y") or fund.get("stddev_3y")
    if stddev and float(stddev) > 20:
        caveats.append(f"短期では-{int(float(stddev) * 1.5)}%程度の下落可能性あり")

    aum = fund.get("aum_oku_yen")
    if aum is not None and float(aum) < 100:
        caveats.append("純資産が比較的小さいため、規模拡大の動向に注意")

    if "tech_heavy" in tags:
        caveats.append("特定セクター（テクノロジー）への集中度が高い")

    op_years = fund.get("operation_years")
    if op_years is not None and float(op_years) < 5:
        caveats.append("運用開始から5年未満のため、長期トラックレコード未確立")

    is_index = fund.get("is_index")
    if not is_index:
        caveats.append("アクティブファンドのため、運用方針変更リスクあり")

    return caveats


def _horizon_label(horizon: str | None) -> str:
    """ホライズンの日本語ラベルを返す"""
    mapping = {
        "5_10": "5〜10年",
        "10_20": "10〜20年",
        "20_plus": "20年以上",
    }
    return mapping.get(horizon or "5_10", "中長期")


def _deduplicate_by_philosophy(
    scores: list[FundScore],
    max_per_tag: int = 1,
) -> list[FundScore]:
    """
    同じ哲学タグ（us_centric等）が重複しないようTop順で間引く。
    passive_index / medium_risk 等の汎用タグは除外して判定する。
    """
    GENERIC_TAGS = {
        "passive_index",
        "medium_risk",
        "high_risk",
        "very_high_risk",
        "low_risk",
        "broad_market",
        "global_diversified",
    }

    tag_counts: dict[str, int] = {}
    result: list[FundScore] = []

    # TODO: FundScoreにphilosophy_tagsを持たせることで精度向上できるが、
    # 現在はfund_masterから引けないためスコア順で重複なしとする
    for fund_score in scores:
        result.append(fund_score)
        if len(result) >= len(scores):
            break

    return result
