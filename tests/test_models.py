"""データモデルの単体テスト"""

import pytest
from pydantic import ValidationError

from src.models.user_profile import UserProfile, Holding
from src.models.portfolio import PortfolioAnalysis
from src.models.fund_score import FundScore


class TestHolding:
    def test_正常なHoldingが作れる(self):
        h = Holding(fund_name_input="オルカン", weight=0.6)
        assert h.weight == 0.6
        assert not h.matched

    def test_重みが0以上1以下の制約(self):
        with pytest.raises(ValidationError):
            Holding(fund_name_input="test", weight=1.5)

    def test_負の重みはエラー(self):
        with pytest.raises(ValidationError):
            Holding(fund_name_input="test", weight=-0.1)


class TestUserProfile:
    def test_完全なプロファイルを作れる(self):
        p = UserProfile(
            consent_given=True,
            experience="none",
            horizon="5_10",
            drawdown_tolerance="low",
            return_expectation="modest",
            region_preference="world",
            style_preference="index_auto",
            investment_goal="asset_building",
            life_stage="30s_family",
            loss_reaction=3,
        )
        assert p.is_profile_complete()
        assert not p.is_experienced()

    def test_経験者判定(self):
        p = UserProfile(
            consent_given=True,
            experience="current_holder",
            horizon="10_20",
            drawdown_tolerance="medium",
            return_expectation="market",
            region_preference="us",
            style_preference="balanced",
            investment_goal="retirement",
            life_stage="40s_stable",
            loss_reaction=3,
        )
        assert p.is_experienced()

    def test_不完全なプロファイルはFalseを返す(self):
        p = UserProfile(consent_given=True)
        assert not p.is_profile_complete()


class TestPortfolioAnalysis:
    def test_正常なPortfolioAnalysisを作れる(self):
        pa = PortfolioAnalysis(
            weighted_risk_score=5.0,
            weighted_growth_value_score=7.0,
            weighted_active_passive=0.3,
        )
        assert pa.weighted_risk_score == 5.0

    def test_リスクスコア範囲バリデーション(self):
        with pytest.raises(ValidationError):
            PortfolioAnalysis(
                weighted_risk_score=11.0,
                weighted_growth_value_score=5.0,
                weighted_active_passive=0.5,
            )


class TestFundScore:
    def test_正常なFundScoreを作れる(self):
        fs = FundScore(
            fund_id="JP90C000H1T1",
            fund_name="テストファンド",
            total_score=85.5,
        )
        assert fs.total_score == 85.5
        assert fs.caveats == []

    def test_スコアが範囲外はエラー(self):
        with pytest.raises(ValidationError):
            FundScore(
                fund_id="test",
                fund_name="test",
                total_score=101.0,
            )
