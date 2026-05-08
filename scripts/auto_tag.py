"""ファンド属性から philosophy_tags・その他フラグを自動付与するロジック"""

from __future__ import annotations


def derive_tags(fund: dict) -> list[str]:
    """ファンド名・カテゴリ・数値から philosophy_tags リストを生成する"""
    tags: list[str] = []
    name: str = fund.get("fund_name", "") or ""
    category: str = fund.get("rakuten_category", "") or ""
    region: str = fund.get("region", "") or ""
    expense: float = float(fund.get("expense_ratio", 1.0) or 1.0)
    stddev = fund.get("stddev_5y") or fund.get("stddev_3y")

    # インデックス / アクティブ
    if fund.get("is_index"):
        tags.append("passive_index")
    elif _contains_any(name, ["アクティブ", "厳選", "成長株", "バリュー", "高配当株", "ひふみ", "コモンズ", "WCM"]):
        if _contains_any(name, ["厳選", "集中"]):
            tags.append("active_concentrated")
        else:
            tags.append("active_diversified")

    # 地域
    if region == "world" or _contains_any(name, ["全世界", "オールカントリー", "グローバル", "世界"]):
        tags.append("global_diversified")
    if region == "us" or _contains_any(name, ["米国", "S&P", "NASDAQ", "FANG", "SOX", "VTI", "全米", "SCHD", "JEPQ"]):
        tags.append("us_centric")
    if region == "japan" or _contains_any(name, ["日本", "TOPIX", "日経", "国内"]):
        tags.append("japan_centric")
    if region == "em" or _contains_any(name, ["新興国", "インド", "中国", "エマージング"]):
        tags.append("em_centric")
    if _contains_any(name, ["先進国"]) and "新興国" not in name:
        tags.append("developed_only")

    # スタイル
    if _contains_any(name, ["FANG", "NASDAQ", "SOX", "テック", "半導体", "IT", "情報技術"]):
        tags.append("tech_heavy")
    if _contains_any(name, ["高配当", "配当", "SCHD", "インカム"]):
        tags.append("dividend_focused")
    if _contains_any(name, ["グロース", "成長株", "成長投資"]):
        tags.append("growth_focused")
    if _contains_any(name, ["バリュー", "割安"]):
        tags.append("value_focused")
    if _contains_any(name, ["バランス", "8資産", "均等型"]):
        tags.append("broad_market")
    if _contains_any(name, ["ひふみ", "コモンズ", "WCM", "アライアンス"]):
        tags.append("quality")
    if _contains_any(name, ["モメンタム"]):
        tags.append("momentum")
    if _contains_any(name, ["スマートベータ", "ファクター"]):
        tags.append("smart_beta")

    # リスクレベル（標準偏差ベース or 名称ベース）
    if fund.get("is_leveraged"):
        tags.append("very_high_risk")
        tags.append("leverage_warning")
    elif stddev is not None:
        stddev_f = float(stddev)
        if stddev_f < 8:
            tags.append("low_risk")
        elif stddev_f < 15:
            tags.append("medium_risk")
        elif stddev_f < 22:
            tags.append("high_risk")
        else:
            tags.append("very_high_risk")
    elif _contains_any(name, ["FANG", "SOX", "レバ", "ブル", "ベア"]):
        tags.append("high_risk")
    elif _contains_any(name, ["債券", "ボンド"]):
        tags.append("low_risk")
    else:
        tags.append("medium_risk")

    # 複雑構造
    if fund.get("is_monthly_payout") and fund.get("payout_type") == "principal":
        tags.append("principal_payout_warning")
    if fund.get("is_currency_select"):
        tags.append("complex_structure")

    # コスト区分（テーマ的タグとして）
    if _contains_any(name, ["インド", "テーマ", "メガトレンド", "DX", "ESG", "カーボン"]):
        tags.append("thematic")
    if _contains_any(name, ["ディフェンシブ", "低ボラ", "最小分散"]):
        tags.append("defensive")
    if _contains_any(name, ["景気敏感", "シクリカル"]):
        tags.append("cyclical")

    return sorted(set(tags))


def derive_region(fund_name: str, category: str) -> str:
    """ファンド名からregionコードを推定する"""
    if _contains_any(fund_name, ["全世界", "オールカントリー", "グローバル", "先進国", "世界"]):
        return "world"
    if _contains_any(fund_name, ["米国", "S&P", "NASDAQ", "FANG", "SOX", "VTI", "全米", "SCHD", "JEPQ"]):
        return "us"
    if _contains_any(fund_name, ["日本", "TOPIX", "日経", "国内"]):
        return "japan"
    if _contains_any(fund_name, ["新興国", "インド", "中国", "エマージング"]):
        return "em"
    return "world"


def derive_region_pcts(fund_name: str, region: str) -> tuple[float, float, float]:
    """region から japan_pct, us_pct, em_pct を推定する（粗い近似）"""
    if region == "japan":
        return 1.0, 0.0, 0.0
    if region == "us":
        return 0.0, 1.0, 0.0
    if region == "em":
        return 0.0, 0.0, 1.0
    if "新興国も含む" in fund_name or "with_em" in fund_name:
        return 0.05, 0.60, 0.10
    # world: MSCI ACWIベースの近似
    return 0.06, 0.62, 0.11


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)
