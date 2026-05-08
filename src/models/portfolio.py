"""PF分析結果モデル"""

from pydantic import BaseModel, Field


class PortfolioAnalysis(BaseModel):
    """保有ポートフォリオの分析結果"""

    # 加重平均プロファイル
    weighted_risk_score: float = Field(ge=1.0, le=10.0)
    weighted_growth_value_score: float = Field(ge=1.0, le=10.0)
    weighted_active_passive: float = Field(ge=0.0, le=1.0)

    # 地域分布 {"japan": 0.0, "us": 1.0, ...}
    geographic_distribution: dict[str, float] = Field(default_factory=dict)

    # セクター集中度
    sector_concentration: dict[str, float] = Field(default_factory=dict)

    # 上位哲学タグ
    dominant_philosophy_tags: list[str] = Field(default_factory=list)

    # 警告リスト
    warnings: list[str] = Field(default_factory=list)

    # 自己申告との矛盾
    self_report_conflicts: list[dict] = Field(default_factory=list)

    # ギャップリスト
    gaps: list[str] = Field(default_factory=list)
