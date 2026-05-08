"""ユーザープロファイルおよびポートフォリオ保有モデル"""

from typing import Literal
from pydantic import BaseModel, Field


class Holding(BaseModel):
    """ユーザーが保有する個別ファンド"""

    fund_id: str | None = None
    fund_name_input: str
    weight: float = Field(ge=0.0, le=1.0)
    matched: bool = False


class UserProfile(BaseModel):
    """5層パイプラインを通じて収集されるユーザーの全プロファイル"""

    # Layer 0
    consent_given: bool = False

    # Layer 1-A
    experience: Literal["none", "current_holder", "past_holder"] | None = None

    # Layer 1-B（基本5問）
    horizon: Literal["5_10", "10_20", "20_plus"] | None = None
    drawdown_tolerance: Literal["low", "medium", "high"] | None = None
    return_expectation: Literal["modest", "market", "above_market"] | None = None
    region_preference: Literal["japan", "us", "world", "with_em", "auto"] | None = None
    style_preference: Literal["growth", "dividend", "balanced", "index_auto"] | None = None

    # Layer 1-B（心情・ライフステージ追加3問）
    investment_goal: Literal[
        "retirement", "education", "fire", "asset_building", "dividend_income"
    ] | None = None
    life_stage: Literal["20s_single", "30s_family", "40s_stable", "50s_plus"] | None = None
    loss_reaction: int | None = Field(default=None, ge=1, le=5)
    # 1=パニックして売りたい … 5=買い増しのチャンスと思える

    # Layer 1-C（経験者のみ）
    current_holdings: list[Holding] = Field(default_factory=list)

    # 派生プロファイル（Layer 1完了後に設定）
    user_type: str = ""

    def is_experienced(self) -> bool:
        """経験者（PF分析対象）かどうか"""
        return self.experience == "current_holder"

    def is_profile_complete(self) -> bool:
        """Layer 1-B 全問が回答済みか"""
        return all([
            self.horizon is not None,
            self.drawdown_tolerance is not None,
            self.return_expectation is not None,
            self.region_preference is not None,
            self.style_preference is not None,
            self.investment_goal is not None,
            self.life_stage is not None,
            self.loss_reaction is not None,
        ])
