"""Layer 1: ユーザープロファイリングおよびユーザータイプ判定"""

from src.models.user_profile import UserProfile


def determine_user_type(profile: UserProfile) -> str:
    """
    5つのユーザータイプに分類する。

    Returns:
        "beginner_low_risk" | "index_auto" | "dividend_focused"
        | "advanced_long_growth" | "intermediate_balanced"
    """
    if profile.experience == "none" and profile.drawdown_tolerance == "low":
        return "beginner_low_risk"

    if profile.style_preference == "index_auto":
        return "index_auto"

    if profile.style_preference == "dividend":
        return "dividend_focused"

    if (
        profile.horizon == "20_plus"
        and profile.drawdown_tolerance == "high"
        and profile.return_expectation == "above_market"
    ):
        return "advanced_long_growth"

    return "intermediate_balanced"
