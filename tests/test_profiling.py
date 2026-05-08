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
        style_preference="index_auto",
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


class TestDetermineUserType:
    def test_初心者低リスク判定(self):
        p = _make_profile(experience="none", drawdown_tolerance="low")
        assert determine_user_type(p) == "beginner_low_risk"

    def test_インデックスおまかせ判定(self):
        p = _make_profile(style_preference="index_auto", experience="current_holder")
        assert determine_user_type(p) == "index_auto"

    def test_配当重視判定(self):
        p = _make_profile(style_preference="dividend", experience="current_holder")
        assert determine_user_type(p) == "dividend_focused"

    def test_上級グロース判定(self):
        p = _make_profile(
            experience="current_holder",
            horizon="20_plus",
            drawdown_tolerance="high",
            return_expectation="above_market",
            style_preference="growth",
        )
        assert determine_user_type(p) == "advanced_long_growth"

    def test_デフォルトはバランス型(self):
        p = _make_profile(
            experience="current_holder",
            horizon="10_20",
            drawdown_tolerance="medium",
            return_expectation="market",
            style_preference="balanced",
        )
        assert determine_user_type(p) == "intermediate_balanced"
