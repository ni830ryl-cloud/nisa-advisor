"""投資方針（Strategy）の生成"""

import pandas as pd

from src.models.portfolio import PortfolioAnalysis
from src.models.user_profile import UserProfile


def generate_strategies(
    profile: UserProfile,
    pf_analysis: PortfolioAnalysis | None,
) -> list[dict]:
    """
    ユーザーに提示する2-3の投資方針を生成する。

    Returns:
        方針辞書のリスト（id, title, description, filter_tags, priority）
    """
    strategies = []

    if pf_analysis:
        # 方針A: PFギャップ補完
        if pf_analysis.gaps:
            gap_desc = _gap_to_description(pf_analysis.gaps[0])
            strategies.append({
                "id": "strategy_a_diversification",
                "title": "🛡️ PFの守りを固める",
                "description": f"現在のPFは{gap_desc}が不足しています。これを補う候補ファンドを提示します。",
                "filter_tags": _gap_to_tags(pf_analysis.gaps),
                "exclude_tags": _get_dominant_tags(pf_analysis),
                "priority": 1,
            })

        # 方針B: 既存スタイル拡張
        strategies.append({
            "id": "strategy_b_expansion",
            "title": "🚀 既存スタイルを拡張する",
            "description": "現在のPFと同じスタイルで、別の切り口を加える候補を提示します。",
            "filter_tags": _get_dominant_tags(pf_analysis),
            "exclude_tags": [],
            "priority": 2,
        })

        # 方針C: 新領域挑戦
        strategies.append({
            "id": "strategy_c_new_area",
            "title": "🌍 新しい領域に挑戦する",
            "description": "現在のPFにない哲学・地域を取り入れる候補を提示します。",
            "filter_tags": [],
            "exclude_tags": _get_dominant_tags(pf_analysis),
            "priority": 3,
        })

    else:
        # PFなし: プロファイルベース
        strategies.append({
            "id": "strategy_core",
            "title": "📌 PFのコアとなる1本",
            "description": "長期保有のメインとなる王道候補を提示します。",
            "filter_tags": _profile_to_core_tags(profile),
            "exclude_tags": [],
            "priority": 1,
        })

        if profile.horizon == "20_plus":
            strategies.append({
                "id": "strategy_satellite",
                "title": "⚡ 成長期待のサテライト",
                "description": "コアに加えるリターン狙いの候補を提示します。",
                "filter_tags": ["growth_focused"],
                "exclude_tags": [],
                "priority": 2,
            })

        if profile.style_preference == "dividend":
            strategies.append({
                "id": "strategy_dividend",
                "title": "💰 配当・インカム重視",
                "description": "定期的なインカムを得られる候補を提示します。",
                "filter_tags": ["dividend_focused"],
                "exclude_tags": [],
                "priority": 3,
            })

    return sorted(strategies, key=lambda s: s["priority"])


def filter_funds_by_strategy(
    strategy: dict,
    fund_master: pd.DataFrame,
) -> pd.DataFrame:
    """
    方針に合致するファンドをファンドマスタからフィルタリングする。
    filter_tagsが空の場合は全ファンドを対象とする。
    """
    if not strategy.get("filter_tags"):
        candidates = fund_master.copy()
    else:
        mask = fund_master["philosophy_tags"].fillna("").apply(
            lambda tags: any(t in tags for t in strategy["filter_tags"])
        )
        candidates = fund_master[mask]

    # 除外タグが指定されている場合（除外タグを全て含む場合のみ除外）
    exclude_tags = strategy.get("exclude_tags", [])
    if exclude_tags:
        def _not_all_excluded(tags_str: str) -> bool:
            tags = tags_str.split("|")
            matched = sum(1 for t in exclude_tags if t in tags)
            return matched < len(exclude_tags)

        exclude_mask = candidates["philosophy_tags"].fillna("").apply(_not_all_excluded)
        candidates = candidates[exclude_mask]

    return candidates.reset_index(drop=True)


def _gap_to_description(gap: str) -> str:
    """ギャップIDを人間向けの説明文に変換する"""
    mapping = {
        "no_japan_exposure": "日本株への分散",
        "no_em_exposure": "新興国への分散",
        "no_dividend_strategy": "配当・インカム戦略",
    }
    return mapping.get(gap, gap)


def _gap_to_tags(gaps: list[str]) -> list[str]:
    """ギャップIDをフィルタ用タグに変換する"""
    tag_map = {
        "no_japan_exposure": ["japan_centric"],
        "no_em_exposure": ["em_centric"],
        "no_dividend_strategy": ["dividend_focused"],
    }
    tags: list[str] = []
    for gap in gaps:
        tags.extend(tag_map.get(gap, []))
    return tags


def _get_dominant_tags(pf_analysis: PortfolioAnalysis) -> list[str]:
    """PF分析からドミナントな哲学タグを取得する"""
    style_tags = [
        t for t in pf_analysis.dominant_philosophy_tags
        if t not in ("medium_risk", "high_risk", "very_high_risk", "low_risk", "passive_index")
    ]
    return style_tags[:2]


def _profile_to_core_tags(profile: UserProfile) -> list[str]:
    """ユーザープロファイルからコア方針のフィルタタグを生成する"""
    tags: list[str] = []

    region = profile.region_preference
    if region == "japan":
        tags.append("japan_centric")
    elif region == "us":
        tags.append("us_centric")
    elif region in ("world", "auto"):
        tags.append("global_diversified")
    elif region == "with_em":
        tags.append("em_centric")

    style = profile.style_preference
    if style == "dividend":
        tags.append("dividend_focused")
    elif style == "growth":
        tags.append("growth_focused")
    elif style == "index_auto":
        tags.append("passive_index")

    return tags
