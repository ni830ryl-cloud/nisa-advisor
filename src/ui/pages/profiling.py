"""Layer 1-A/1-B: 経験判定 + 8問プロファイリング画面"""

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
    "😱 なるべく早く売りたい（損失が怖い）",
    "😐 不安だが保有を続ける（様子を見る）",
    "💪 むしろ買い増しのチャンスと思う",
]
_DRAWDOWN_VALUES = ["low", "medium", "high"]

_RETURN_OPTIONS = [
    "約150万円（年率4%相当）でも満足",
    "約200万円（年率7%相当）を目指したい",
    "300万円以上（年率12%超）を狙いたい",
]
_RETURN_VALUES = ["modest", "market", "above_market"]

_CURRENT_STYLE_OPTIONS = [
    "📊 インデックスファンド中心（低コスト・市場連動）",
    "🔍 アクティブファンド中心（運用会社の銘柄選択に期待）",
    "📈 個別株・ETF中心（自分で銘柄を選ぶ）",
    "🔀 バラバラ・わからない",
]
_CURRENT_STYLE_VALUES = ["index_heavy", "active_heavy", "individual_stocks", "mixed"]

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

# 追加問: 投資目的
_GOAL_OPTIONS = [
    "老後資金（ゆとりある老後のために積み立てたい）",
    "教育費（子どもの進学資金を準備したい）",
    "FIRE・経済的自立（早期に労働収入に頼らない生活を目指す）",
    "資産形成全般（特定の目的はなく、着実に増やしたい）",
    "配当収入（毎月・毎年の収入として受け取りたい）",
]
_GOAL_VALUES = ["retirement", "education", "fire", "asset_building", "dividend_income"]

# 追加問: ライフステージ
_LIFE_STAGE_OPTIONS = [
    "20代・独身（まずは長期積立のスタート）",
    "30代・子育て中（教育費と資産形成を両立したい）",
    "40代・安定期（収入は安定、老後準備を本格化）",
    "50代以上（定年が見えてきた・守りに入りたい）",
]
_LIFE_STAGE_VALUES = ["20s_single", "30s_family", "40s_stable", "50s_plus"]

# 追加問: 損失時の感情反応ラベル
_LOSS_REACTION_LABELS = {
    1: "1 — すぐ売りたくなる（損失が怖い）",
    2: "2 — かなり不安になる",
    3: "3 — 様子を見て判断する",
    4: "4 — ある程度冷静でいられる",
    5: "5 — 買い増しのチャンスと思える",
}


def render() -> None:
    """経験判定と8問プロファイリングを表示する"""
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

    current_style_idx = None
    if _EXPERIENCE_VALUES[experience_idx] == "current_holder":
        st.info("📂 現在も保有中とのこと。今の運用スタイルを教えてください。")
        current_style_idx = st.radio(
            "Q0: 現在の**主な保有スタイル**は？",
            options=range(len(_CURRENT_STYLE_OPTIONS)),
            format_func=lambda i: _CURRENT_STYLE_OPTIONS[i],
            key="q0_current_style",
        )

    st.write("---")

    # ステップ 2: 基本5問
    st.subheader("ステップ 2/3: 投資スタイル（5問）")

    q1 = st.radio(
        "Q1: このお金を**いつ使う予定**がありますか？",
        options=range(len(_HORIZON_OPTIONS)),
        format_func=lambda i: _HORIZON_OPTIONS[i],
        key="q1_horizon",
        help="💡 期間が長いほど、一時的な値動きは長期的なリターンで吸収されやすくなります",
    )

    q2 = st.radio(
        "Q2: 100万円を投資して、**75万円（−25%）に下落**したとしたら？",
        options=range(len(_DRAWDOWN_OPTIONS)),
        format_func=lambda i: _DRAWDOWN_OPTIONS[i],
        key="q2_drawdown",
        help="💡 実際の行動パターンが、提案されるファンドのリスクレベルに大きく影響します",
    )

    q3 = st.radio(
        "Q3: 10年後、100万円が**いくらになっていれば満足**ですか？",
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

    # ステップ 3: 心情・ライフステージ（3問）
    st.subheader("ステップ 3/3: あなたの心情・ライフステージ（3問）")
    st.caption("より精度の高い提案のために、あなたの状況を教えてください。")

    q6 = st.radio(
        "Q6: この投資を通じて**最も達成したいこと**は何ですか？",
        options=range(len(_GOAL_OPTIONS)),
        format_func=lambda i: _GOAL_OPTIONS[i],
        key="q6_goal",
        help="💡 目的によって、短期の安定性か長期の成長性かの優先度が変わります",
    )

    q7 = st.radio(
        "Q7: 現在のライフステージを教えてください。",
        options=range(len(_LIFE_STAGE_OPTIONS)),
        format_func=lambda i: _LIFE_STAGE_OPTIONS[i],
        key="q7_life_stage",
        help="💡 ライフステージによって、適切なリスク水準と投資期間が変わります",
    )

    q8 = st.select_slider(
        "Q8: 保有ファンドが**20%下落**したとき、あなたはどう感じますか？",
        options=list(_LOSS_REACTION_LABELS.keys()),
        format_func=lambda v: _LOSS_REACTION_LABELS[v],
        value=3,
        key="q8_loss_reaction",
        help="💡 感情的な反応は行動リスク（最悪のタイミングで売ること）と直結します",
    )

    st.write("---")

    if st.button("次へ進む", type="primary"):
        st.session_state.experience = _EXPERIENCE_VALUES[experience_idx]
        st.session_state.current_style = (
            _CURRENT_STYLE_VALUES[current_style_idx]
            if current_style_idx is not None else None
        )
        st.session_state.horizon = _HORIZON_VALUES[q1]
        st.session_state.drawdown_tolerance = _DRAWDOWN_VALUES[q2]
        st.session_state.return_expectation = _RETURN_VALUES[q3]
        st.session_state.region_preference = _REGION_VALUES[q4]
        st.session_state.style_preference = _STYLE_VALUES[q5]
        st.session_state.investment_goal = _GOAL_VALUES[q6]
        st.session_state.life_stage = _LIFE_STAGE_VALUES[q7]
        st.session_state.loss_reaction = int(q8)

        experience_val = _EXPERIENCE_VALUES[experience_idx]
        if experience_val == "current_holder":
            st.session_state.current_page = "portfolio"
        else:
            st.session_state.current_page = "results"
        st.rerun()
