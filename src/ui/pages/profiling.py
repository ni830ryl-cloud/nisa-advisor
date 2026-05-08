"""Layer 1-A/1-B: 経験判定 + 5問プロファイリング画面"""

import streamlit as st


_EXPERIENCE_OPTIONS = [
    "まったく初めて（ファンドを買ったことがない）",
    "経験あり・現在も保有中",
    "過去に経験あり・現在は保有なし",
]

_EXPERIENCE_VALUES = ["none", "current_holder", "past_holder"]

_HORIZON_OPTIONS = [
    "5〜10年後（住宅購入、子どもの教育費など）",
    "10〜20年後（早期退職資金、長期的な資産形成）",
    "20年以上先（老後資金、世代を超える資産）",
]
_HORIZON_VALUES = ["5_10", "10_20", "20_plus"]

_DRAWDOWN_OPTIONS = [
    "不安・10%下落でも気になる（安定性を重視）",
    "-30%程度なら持ち続けられる（ある程度の変動は受け入れる）",
    "-50%でも長期目線で保有を続けられる（短期変動は気にしない）",
]
_DRAWDOWN_VALUES = ["low", "medium", "high"]

_RETURN_OPTIONS = [
    "インフレに負けなければ十分（年3〜5%）",
    "市場平均並み（年5〜7%）",
    "市場平均を超えたい（年8%以上）",
]
_RETURN_VALUES = ["modest", "market", "above_market"]

_REGION_OPTIONS = [
    "日本中心（自国経済を重視、為替リスクを抑えたい）",
    "米国中心（過去30年の実績を信頼）",
    "全世界に分散（特定の国に偏らない安心感）",
    "新興国も含めて成長期待（高リスク・高リターン許容）",
    "おまかせ（プロファイルに合わせて自動提案）",
]
_REGION_VALUES = ["japan", "us", "world", "with_em", "auto"]

_STYLE_OPTIONS = [
    "値上がり重視（値上がり益で資産を増やしたい）",
    "配当重視（定期的なインカムが欲しい）",
    "両方バランス",
    "インデックスでおまかせ（市場全体に投資、低コスト重視）",
]
_STYLE_VALUES = ["growth", "dividend", "balanced", "index_auto"]


def render() -> None:
    """経験判定と5問プロファイリングを表示する"""
    if not st.session_state.get("consent"):
        st.warning("先に免責事項への同意が必要です。")
        if st.button("最初に戻る"):
            st.session_state.current_page = "disclaimer"
            st.rerun()
        return

    st.title("投資プロファイルの診断")
    st.caption("⚠️ 本ツールは投資助言ではありません。スコアリング情報の提供を目的とします。")
    st.write("---")

    # ステップ 1: 経験判定
    st.subheader("ステップ 1/3: 投資経験")
    st.write("最適な提案をするため、現在の投資状況について教えてください。")

    experience_idx = st.radio(
        "あなたの投資経験は？",
        options=range(len(_EXPERIENCE_OPTIONS)),
        format_func=lambda i: _EXPERIENCE_OPTIONS[i],
        key="experience_radio",
    )

    st.write("---")

    # ステップ 2: 5問
    st.subheader("ステップ 2/3: 投資スタイル（5問）")

    q1 = st.radio(
        "Q1: このお金を**いつ使う予定**がありますか？",
        options=range(len(_HORIZON_OPTIONS)),
        format_func=lambda i: _HORIZON_OPTIONS[i],
        key="q1_horizon",
        help="💡 期間が長いほど、一時的な値動きは長期的なリターンで吸収されやすくなります",
    )

    q2 = st.radio(
        "Q2: 投資したお金が一時的に**半分になっても**、保有を続けられますか？",
        options=range(len(_DRAWDOWN_OPTIONS)),
        format_func=lambda i: _DRAWDOWN_OPTIONS[i],
        key="q2_drawdown",
        help="💡 ここでの選択が、提案されるファンドのリスクレベルに大きく影響します",
    )

    q3 = st.radio(
        "Q3: どのくらいのリターンを期待しますか？",
        options=range(len(_RETURN_OPTIONS)),
        format_func=lambda i: _RETURN_OPTIONS[i],
        key="q3_return",
        help="💡 高いリターンを目指すほど、短期的な変動も大きくなる傾向があります",
    )

    q4 = st.radio(
        "Q4: どの地域に投資したいですか？",
        options=range(len(_REGION_OPTIONS)),
        format_func=lambda i: _REGION_OPTIONS[i],
        key="q4_region",
        help="💡 「全世界」を選ぶと、世界中の経済成長の恩恵を受けやすくなります",
    )

    q5 = st.radio(
        "Q5: どんな運用スタイルが好みですか？",
        options=range(len(_STYLE_OPTIONS)),
        format_func=lambda i: _STYLE_OPTIONS[i],
        key="q5_style",
        help="💡 「インデックスでおまかせ」は最もシンプルで王道の選択肢です",
    )

    st.write("---")

    if st.button("次へ進む", type="primary"):
        # セッションステートに保存
        st.session_state.experience = _EXPERIENCE_VALUES[experience_idx]
        st.session_state.horizon = _HORIZON_VALUES[q1]
        st.session_state.drawdown_tolerance = _DRAWDOWN_VALUES[q2]
        st.session_state.return_expectation = _RETURN_VALUES[q3]
        st.session_state.region_preference = _REGION_VALUES[q4]
        st.session_state.style_preference = _STYLE_VALUES[q5]

        experience_val = _EXPERIENCE_VALUES[experience_idx]
        if experience_val == "current_holder":
            st.session_state.current_page = "portfolio"
        else:
            st.session_state.current_page = "results"
        st.rerun()
