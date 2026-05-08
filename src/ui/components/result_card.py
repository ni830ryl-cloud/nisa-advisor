"""ファンドスコアカードコンポーネント"""

import streamlit as st

from src.models.fund_score import FundScore


_COMPONENT_LABELS = {
    "total_return": "トータルリターン",
    "sharpe": "シャープレシオ",
    "fund_score": "ファンドスコア",
    "cost": "コスト評価",
    "scale_track_record": "規模・運用年数",
    "stddev_penalty": "標準偏差ペナルティ",
}


def render_fund_card(score: FundScore) -> None:
    """ファンドスコアカードをStreamlitで描画する"""
    with st.container(border=True):
        st.markdown(f"**{score.fund_name}**")
        st.caption(score.fund_id)
        st.metric("総合スコア", f"{score.total_score}/100")

        with st.expander("スコア内訳"):
            for key, label in _COMPONENT_LABELS.items():
                value = score.component_scores.get(key, 0.0)
                if key == "stddev_penalty":
                    # ペナルティは負値なので視覚的に表示
                    if value < 0:
                        st.caption(f"⚠️ {label}: {value:.0f}点（リスク調整）")
                    else:
                        st.caption(f"✓ {label}: ペナルティなし")
                else:
                    normalized = max(0.0, min(1.0, value / 100.0))
                    st.progress(normalized, text=f"{label}: {value:.0f}")

        if score.rationale:
            st.markdown("**なぜこのプロファイルに合うか**")
            st.write(score.rationale)

        if score.caveats:
            caveats_text = "\n".join(f"- {c}" for c in score.caveats)
            st.warning(f"**留意事項**\n{caveats_text}")
