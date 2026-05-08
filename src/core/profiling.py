"""Layer 1: ユーザープロファイリングおよびユーザータイプ判定"""

from src.models.user_profile import UserProfile


def determine_user_type(profile: UserProfile) -> str:
    """
    10のユーザータイプに分類する（心情・ライフステージ・感情反応を考慮）。

    Returns:
        "beginner_low_risk" | "index_auto" | "dividend_focused"
        | "advanced_long_growth" | "intermediate_balanced"
        | "retirement_security" | "education_stable" | "fire_growth"
        | "preservation_late" | "young_aggressive" | "intermediate_growth"
    """
    goal = profile.investment_goal
    life_stage = profile.life_stage
    experience = profile.experience
    horizon = profile.horizon
    loss_reaction = profile.loss_reaction or 3
    drawdown = profile.drawdown_tolerance
    return_exp = profile.return_expectation
    style = profile.style_preference

    # 配当収入目的（スタイル優先）
    if style == "dividend" or goal == "dividend_income":
        return "dividend_focused"

    # 資産保全型: 50代以上 かつ 感情的に弱い
    if life_stage == "50s_plus" and loss_reaction <= 2:
        return "preservation_late"

    # 老後安心型: 老後資金目的（50代以外でも）
    if goal == "retirement":
        return "retirement_security"

    # FIRE志向型: FIRE目的 かつ 長期 かつ 感情的に安定
    if goal == "fire" and horizon == "20_plus" and loss_reaction >= 4:
        return "fire_growth"

    # 若年積極型: 20代独身 かつ 長期 かつ 感情的に安定
    if life_stage == "20s_single" and horizon == "20_plus" and loss_reaction >= 4:
        return "young_aggressive"

    # 教育費積立型: 教育費目的 または 子育て中（期限が決まっている）
    if goal == "education" or life_stage == "30s_family":
        return "education_stable"

    # 初心者・不安型（心情優先 — loss_reactionで細分化）
    if experience == "none" and loss_reaction <= 2:
        return "beginner_low_risk"

    # インデックスおまかせ
    if style == "index_auto":
        return "index_auto"

    # 上級長期成長（旧来のhigh/20+判定を維持）
    if (
        horizon == "20_plus"
        and loss_reaction >= 4
        and return_exp == "above_market"
    ):
        return "advanced_long_growth"

    # 中堅成長型: 高リターン志向 かつ 感情的に中程度以上
    if return_exp == "above_market" and loss_reaction >= 3:
        return "intermediate_growth"

    return "intermediate_balanced"
