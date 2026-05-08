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

    # Layer 1-B
    horizon: Literal["5_10", "10_20", "20_plus"] | None = None
    drawdown_tolerance: Literal["low", "medium", "high"] | None = None
    return_expectation: Literal["modest", "market", "above_market"] | None = None
    region_preference: Literal["japan", "us", "world", "with_em", "auto"] | None = None
    style_preference: Literal["growth", "dividend", "balanced", "index_auto"] | None = None

    # Layer 1-C（経験者のみ）
    current_holdings: list[Holding] = Field(default_factory=list)

    # 派生プロファイル（Layer 1完了後に設定）
    user_type: str = ""

    def is_experienced(self) -> bool:
        """経験者（PF分析対象）かどうか"""
        return self.experience == "current_holder"

    def is_profile_complete(self) -> bool:
        """Layer 1-B 5問が全て回答済みか"""
        return all([
            self.horizon is not None,
            self.drawdown_tolerance is not None,
            self.return_expectation is not None,
            self.region_preference is not None,
            self.style_preference is not None,
        ])
