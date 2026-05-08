"""Layer 1-C: 保有ポートフォリオの分析"""

import pandas as pd

from src.models.portfolio import PortfolioAnalysis
from src.models.user_profile import Holding, UserProfile
from src.utils.constants import GAP_THRESHOLDS, HIGH_CONCENTRATION_THRESHOLD


def analyze_portfolio(
    holdings: list[Holding],
    fund_master: pd.DataFrame,
) -> PortfolioAnalysis | None:
    """
    保有ファンドリストを分析してPortfolioAnalysisを返す。
    マッチング済みのHoldingが1件もない場合はNoneを返す。
    """
    matched = [h for h in holdings if h.matched and h.fund_id]
    if not matched:
        return None

    # 重みの正規化（合計が1.0になるよう調整）
    total_weight = sum(h.weight for h in matched)
    if total_weight <= 0:
        return None

    enriched = []
    for h in matched:
        rows = fund_master[fund_master["fund_id"] == h.fund_id]
        if rows.empty:
            continue
        fund = rows.iloc[0]
        tags = str(fund.get("philosophy_tags", "")).split("|")
        risk_score = _stddev_to_risk_score(float(fund.get("stddev_5y") or fund.get("stddev_3y") or 15.0))
        gv_score = _compute_growth_value_score(tags)
        normalized_weight = h.weight / total_weight

        enriched.append({
            "weight": normalized_weight,
            "risk_score": risk_score,
            "gv_score": gv_score,
            "is_passive": "passive_index" in tags,
            "region_japan": float(fund.get("region_japan_pct") or 0.0),
            "region_us": float(fund.get("region_us_pct") or 0.0),
            "region_em": float(fund.get("region_em_pct") or 0.0),
            "tags": tags,
        })

    if not enriched:
        return None

    weighted_risk = sum(e["risk_score"] * e["weight"] for e in enriched)
    weighted_gv = sum(e["gv_score"] * e["weight"] for e in enriched)
    weighted_ap = sum((0.0 if e["is_passive"] else 1.0) * e["weight"] for e in enriched)

    geo_dist = {
        "japan": sum(e["region_japan"] * e["weight"] for e in enriched),
        "us": sum(e["region_us"] * e["weight"] for e in enriched),
        "em": sum(e["region_em"] * e["weight"] for e in enriched),
    }
    other = max(0.0, 1.0 - sum(geo_dist.values()))
    geo_dist["other"] = other

    # タグ集計
    tag_counts: dict[str, float] = {}
    for e in enriched:
        for tag in e["tags"]:
            tag = tag.strip()
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0.0) + e["weight"]
    dominant_tags = sorted(tag_counts, key=lambda t: -tag_counts[t])[:3]

    # ギャップ検出
    gaps: list[str] = []
    if geo_dist.get("japan", 0) < GAP_THRESHOLDS["min_japan_pct"]:
        gaps.append("no_japan_exposure")
    if geo_dist.get("em", 0) < GAP_THRESHOLDS["min_em_pct"]:
        gaps.append("no_em_exposure")
    if not any("dividend_focused" in e["tags"] for e in enriched):
        gaps.append("no_dividend_strategy")

    # 警告検出
    warnings: list[str] = []
    if any("leverage_warning" in e["tags"] for e in enriched):
        warnings.append("leverage_etf_detected")
    if geo_dist:
        max_region = max(geo_dist, key=lambda k: geo_dist[k])
        if geo_dist[max_region] > HIGH_CONCENTRATION_THRESHOLD:
            warnings.append(f"high_concentration_{max_region}")

    return PortfolioAnalysis(
        weighted_risk_score=max(1.0, min(10.0, weighted_risk)),
        weighted_growth_value_score=max(1.0, min(10.0, weighted_gv)),
        weighted_active_passive=weighted_ap,
        geographic_distribution=geo_dist,
        sector_concentration={},
        dominant_philosophy_tags=dominant_tags,
        warnings=warnings,
        self_report_conflicts=[],
        gaps=gaps,
    )


def detect_conflicts(
    profile: UserProfile,
    pf_analysis: PortfolioAnalysis,
) -> list[dict]:
    """自己申告とPF実態の矛盾を検出する"""
    conflicts = []

    if (
        profile.drawdown_tolerance == "low"
        and pf_analysis.weighted_risk_score >= 7
    ):
        conflicts.append({
            "type": "risk_mismatch",
            "reported": "low_drawdown_tolerance",
            "actual": f"pf_risk_score_{pf_analysis.weighted_risk_score:.1f}",
            "message": (
                "申告ではリスク回避型ですが、現在のPFのリスクは高めです。"
                "本当のリスク許容度を再考する機会です。"
            ),
        })

    if (
        profile.style_preference == "dividend"
        and pf_analysis.weighted_growth_value_score >= 7
    ):
        conflicts.append({
            "type": "style_mismatch",
            "reported": "dividend_focused",
            "actual": "growth_pf",
            "message": "配当重視と申告ですが、現在のPFはグロース寄りです。",
        })

    return conflicts


def _stddev_to_risk_score(stddev: float) -> float:
    """標準偏差をリスクスコア（1-10）に変換する"""
    if stddev < 8:
        return 2.0
    elif stddev < 12:
        return 4.0
    elif stddev < 18:
        return 6.0
    elif stddev < 25:
        return 8.0
    else:
        return 10.0


def _compute_growth_value_score(tags: list[str]) -> float:
    """哲学タグからグロース-バリュースコア（1=バリュー, 10=グロース）を推定する"""
    if "growth_focused" in tags:
        return 9.0
    elif "tech_heavy" in tags:
        return 8.0
    elif "dividend_focused" in tags or "value_focused" in tags:
        return 2.0
    elif "broad_market" in tags:
        return 5.5
    else:
        return 5.0
