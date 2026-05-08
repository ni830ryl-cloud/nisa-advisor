"""ファンドスコアリング結果モデル"""

from pydantic import BaseModel, Field


class FundScore(BaseModel):
    """1ファンドのスコアリング結果"""

    fund_id: str
    fund_name: str
    total_score: float = Field(ge=0.0, le=100.0)

    # 各軸スコア（重み付け前）
    component_scores: dict[str, float] = Field(default_factory=dict)

    # 適用した重み
    applied_weights: dict[str, float] = Field(default_factory=dict)

    # なぜこのプロファイルに合うか（自然言語）
    rationale: str = ""

    # 留意事項リスト
    caveats: list[str] = Field(default_factory=list)

    # 対応する方針IDリスト
    matches_strategy: list[str] = Field(default_factory=list)
