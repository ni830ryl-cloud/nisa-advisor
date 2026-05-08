"""プロファイリングロジックの単体テスト"""

import pytest

from src.core.profiling import determine_user_type
from src.models.user_profile import UserProfile


def _make_profile(**kwargs) -> UserProfile:
    defaults = dict(
        consent_given=True,
        experience="none",
        horizon="5_10",
        drawdown_tolerance="low",
        return_expectation="modest",
        region_preference="world",
        style_preference="balanced",
        investment_goal="asset_building",
        life_stage="40s_stable",
        loss_reaction=3,
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


class TestDetermineUserType:
    def test_初心者低リスク判定(self):
        # 初心者・感情的に弱い（loss_reaction<=2）
        p = _make_profile(experience="none", drawdown_tolerance="low", loss_reaction=2)
        assert determine_user_type(p) == "beginner_low_risk"

    def test_インデックスおまかせ判定(self):
        p = _make_profile(style_preference="index_auto", experience="current_holder")
        assert determine_user_type(p) == "index_auto"

    def test_配当重視判定(self):
        p = _make_profile(style_preference="dividend", experience="current_holder")
        assert determine_user_type(p) == "dividend_focused"

    def test_上級グロース判定(self):
        # 20年以上・感情的に安定（loss_reaction>=4）・高リターン志向
        p = _make_profile(
            experience="current_holder",
            horizon="20_plus",
            drawdown_tolerance="high",
            return_expectation="above_market",
            style_preference="growth",
            loss_reaction=4,
        )
        assert determine_user_type(p) == "advanced_long_growth"

    def test_デフォルトはバランス型(self):
        p = _make_profile(
            experience="current_holder",
            horizon="10_20",
            drawdown_tolerance="medium",
            return_expectation="market",
            style_preference="balanced",
            loss_reaction=3,
        )
        assert determine_user_type(p) == "intermediate_balanced"

    def test_老後安心型判定(self):
        p = _make_profile(
            investment_goal="retirement",
            life_stage="40s_stable",
            loss_reaction=3,
        )
        assert determine_user_type(p) == "retirement_security"

    def test_教育費積立型判定(self):
        p = _make_profile(
            investment_goal="education",
            life_stage="30s_family",
            loss_reaction=3,
        )
        assert determine_user_type(p) == "education_stable"

    def test_FIRE志向型判定(self):
        p = _make_profile(
            investment_goal="fire",
            horizon="20_plus",
            loss_reaction=5,
        )
        assert determine_user_type(p) == "fire_growth"

    def test_資産保全型判定(self):
        # 50代以上 かつ 感情的に弱い
        p = _make_profile(
            life_stage="50s_plus",
            loss_reaction=1,
        )
        assert determine_user_type(p) == "preservation_late"

    def test_若年積極型判定(self):
        p = _make_profile(
            life_stage="20s_single",
            horizon="20_plus",
            loss_reaction=5,
        )
        assert determine_user_type(p) == "young_aggressive"

    def test_中堅成長型判定(self):
        p = _make_profile(
            experience="current_holder",
            return_expectation="above_market",
            loss_reaction=3,
            investment_goal="asset_building",
        )
        assert determine_user_type(p) == "intermediate_growth"
