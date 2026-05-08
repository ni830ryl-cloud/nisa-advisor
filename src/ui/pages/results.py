"""Layer 4: 結果表示画面"""

import streamlit as st

from src.core.filters import apply_hard_filters
from src.core.output_builder import build_results
from src.core.pf_analyzer import analyze_portfolio, detect_conflicts
from src.core.strategies import generate_strategies
from src.data.loader import load_fund_master
from src.models.user_profile import UserProfile, Holding
from src.ui.components.result_card import render_fund_card


_USER_TYPE_LABELS = {
    "beginner_low_risk": "初心者・低リスク型",
    "index_auto": "インデックスおまかせ派",
    "intermediate_balanced": "中級・バランス型",
    "dividend_focused": "配当重視型",
    "advanced_long_growth": "上級・長期グロース志向型",
}

_HORIZON_LABELS = {
    "5_10": "5〜10年",
    "10_20": "10〜20年",
    "20_plus": "20年以上",
}

_DRAWDOWN_LABELS = {
    "low": "-10%でも不安",
    "medium": "-30%まで許容",
    "high": "-50%でも継続",
}

_STYLE_LABELS = {
    "growth": "値上がり重視",
    "dividend": "配当重視",
    "balanced": "バランス",
    "index_auto": "インデックスおまかせ",
}


def render() -> None:
    """スコアリング結果をレイアウトして表示する"""
    if not st.session_state.get("consent"):
        st.warning("最初から診断を開始してください。")
        if st.button("最初から始める"):
            st.session_state.current_page = "disclaimer"
            st.rerun()
        return

    st.title("📈 分析結果")
    st.caption("⚠️ 本ツールは投資助言ではありません。スコアリング情報の提供を目的とします。")

    profile = _build_profile_from_session()

    fund_master_raw = load_fund_master()
    fund_master = apply_hard_filters(fund_master_raw)

    # PF分析
    holdings: list[Holding] = st.session_state.get("holdings", [])
    pf_analysis = None
    if holdings:
        pf_analysis = analyze_portfolio(holdings, fund_master_raw)
        if pf_analysis and profile:
            conflicts = detect_conflicts(profile, pf_analysis)
            pf_analysis.self_report_conflicts = conflicts

    # プロファイルサマリー
    _render_profile_summary(profile, holdings, pf_analysis)

    st.write("---")

    # スコアリング実行
    if profile is None:
        st.error("プロファイルが不完全です。診断をやり直してください。")
        return

    with st.spinner("スコアリング中..."):
        strategies = generate_strategies(profile, pf_analysis)
        results = build_results(profile, fund_master, strategies, pf_analysis)

    # 方針別ファンドカード表示
    st.subheader("投資方針の提案")
    st.write("以下の方針から、それぞれの候補ファンドをご確認ください。")

    for strategy in strategies:
        sid = strategy["id"]
        top_funds = results.get(sid, [])

        st.markdown(f"### {strategy['title']}")
        st.caption(strategy["description"])

        if not top_funds:
            st.info("条件に合うファンドが見つかりませんでした。")
            continue

        cols = st.columns(len(top_funds))
        for col, fund_score in zip(cols, top_funds):
            with col:
                render_fund_card(fund_score)

        st.write("")

    st.write("---")

    # やり直しボタン
    if st.button("条件を変えて再診断"):
        for key in ["experience", "horizon", "drawdown_tolerance", "return_expectation",
                    "region_preference", "style_preference", "holdings", "pf_analysis", "results"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.current_page = "profiling"
        st.rerun()


def _build_profile_from_session() -> UserProfile | None:
    """セッションステートからUserProfileを構築する"""
    try:
        return UserProfile(
            consent_given=True,
            experience=st.session_state.get("experience"),
            horizon=st.session_state.get("horizon"),
            drawdown_tolerance=st.session_state.get("drawdown_tolerance"),
            return_expectation=st.session_state.get("return_expectation"),
            region_preference=st.session_state.get("region_preference"),
            style_preference=st.session_state.get("style_preference"),
            current_holdings=st.session_state.get("holdings", []),
        )
    except Exception:
        return None


def _render_profile_summary(
    profile: UserProfile | None,
    holdings: list[Holding],
    pf_analysis,
) -> None:
    """ユーザープロファイルのサマリーを表示する"""
    st.subheader("あなたの投資家プロファイル")

    if profile is None:
        st.warning("プロファイルデータが見つかりません。")
        return

    from src.core.profiling import determine_user_type
    user_type = determine_user_type(profile)
    type_label = _USER_TYPE_LABELS.get(user_type, user_type)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**推定タイプ:** {type_label}")
        st.markdown(f"**投資期間:** {_HORIZON_LABELS.get(profile.horizon or '', '-')}")
        st.markdown(f"**下落耐性:** {_DRAWDOWN_LABELS.get(profile.drawdown_tolerance or '', '-')}")
        st.markdown(f"**運用スタイル:** {_STYLE_LABELS.get(profile.style_preference or '', '-')}")

    if pf_analysis and holdings:
        with col2:
            st.markdown("**現在のポートフォリオ概要**")

            fund_master = load_fund_master()
            for h in holdings[:5]:
                if h.matched and h.fund_id:
                    rows = fund_master[fund_master["fund_id"] == h.fund_id]
                    name = rows.iloc[0]["fund_name"] if not rows.empty else h.fund_name_input
                else:
                    name = h.fund_name_input
                st.caption(f"• {name}: {int(h.weight * 100)}%")

    # 警告表示
    if pf_analysis:
        if pf_analysis.warnings:
            for w in pf_analysis.warnings:
                if "leverage" in w:
                    st.error(
                        "🚨 **重要な注意**: 保有ファンドの中にレバレッジ型商品が含まれています。"
                        "これらは長期保有に向きません（ボラティリティドラッグによる減価）。"
                        "本ツールの提案は、長期保有目的の追加購入を前提としています。"
                    )
                elif "high_concentration" in w:
                    region = w.replace("high_concentration_", "")
                    st.warning(f"⚠️ 地域集中度が高い状態です: {region}への集中が80%超")

        if pf_analysis.self_report_conflicts:
            st.warning("**申告内容とPF実態に相違があります**")
            for c in pf_analysis.self_report_conflicts:
                st.caption(f"⚠️ {c.get('message', '')}")

        # 強み・弱み
        col_s, col_w = st.columns(2)
        with col_s:
            st.markdown("**💪 PFの強み**")
            if "passive_index" in " ".join(pf_analysis.dominant_philosophy_tags):
                st.caption("• 低コストインデックス運用")
            if pf_analysis.weighted_active_passive < 0.3:
                st.caption("• パッシブ比率が高くコスト効率が良い")

        with col_w:
            st.markdown("**⚠️ PFの弱み**")
            for gap in pf_analysis.gaps:
                gap_msgs = {
                    "no_japan_exposure": "日本株への分散が不足",
                    "no_em_exposure": "新興国への分散が不足",
                    "no_dividend_strategy": "配当・インカム戦略なし",
                }
                st.caption(f"• {gap_msgs.get(gap, gap)}")
