"""Layer 1-C: 保有ポートフォリオ入力画面（経験者向け）"""

import streamlit as st

from src.data.loader import load_fund_master
from src.data.matcher import match_fund, match_fund_candidates
from src.models.user_profile import Holding
from src.utils.constants import MAX_HOLDINGS_INPUT


def render() -> None:
    """保有ファンド入力フォームを表示する"""
    if not st.session_state.get("experience") == "current_holder":
        st.session_state.current_page = "results"
        st.rerun()
        return

    st.title("現在の保有ファンドを教えてください")
    st.caption("⚠️ 本ツールは投資助言ではありません。スコアリング情報の提供を目的とします。")

    st.info("""
**入力のヒント:**
- 「オルカン」「S&P500」などの愛称・略称でもOKです
- 比率は概算で構いません（合計が100%になるようにしてください）
- 個別株（トヨタ、Apple等）は本ツールでは扱いません
    """)

    fund_master = load_fund_master()

    # 行の初期化
    if "holdings_input" not in st.session_state or not st.session_state.holdings_input:
        st.session_state.holdings_input = [{"name": "", "weight": 0}]

    holdings_input = st.session_state.holdings_input

    st.subheader("保有ファンド入力")

    updated = []
    to_delete = []

    for i, h in enumerate(holdings_input):
        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            name = st.text_input(
                f"ファンド名 {i+1}",
                value=h.get("name", ""),
                key=f"fund_name_{i}",
                placeholder="例: オルカン、S&P500",
            )
        with col2:
            weight = st.number_input(
                f"比率 (%) {i+1}",
                min_value=0,
                max_value=100,
                value=int(h.get("weight", 0)),
                step=5,
                key=f"fund_weight_{i}",
            )
        with col3:
            st.write("")
            st.write("")
            if st.button("削除", key=f"del_{i}"):
                to_delete.append(i)
                continue

        updated.append({"name": name, "weight": weight})

    # 削除処理
    holdings_input = [h for i, h in enumerate(updated) if i not in to_delete]

    col_add, col_total = st.columns([1, 2])
    with col_add:
        if len(holdings_input) < MAX_HOLDINGS_INPUT:
            if st.button("＋ 行を追加"):
                holdings_input.append({"name": "", "weight": 0})

    st.session_state.holdings_input = holdings_input

    total_weight = sum(h.get("weight", 0) for h in holdings_input if h.get("name"))
    with col_total:
        if total_weight < 95:
            st.warning(f"合計: {total_weight}% / 100% ⚠️ 100%にしてください")
        elif total_weight > 105:
            st.warning(f"合計: {total_weight}% / 100% ⚠️ 100%を超えています")
        else:
            st.success(f"合計: {total_weight}%  ✓")

    st.write("---")

    # マッチング確認エリア
    valid_inputs = [(i, h) for i, h in enumerate(holdings_input) if h.get("name", "").strip()]

    if valid_inputs:
        with st.expander("マッチング結果を確認", expanded=True):
            for i, h in valid_inputs:
                name = h["name"].strip()
                fund_id, confidence = match_fund(name, fund_master)

                if confidence >= 0.75:
                    rows = fund_master[fund_master["fund_id"] == fund_id]
                    if not rows.empty:
                        matched_name = rows.iloc[0]["fund_name"]
                        st.success(f"✓ **{name}** → {matched_name} ({int(confidence*100)}%)")
                elif confidence >= 0.5:
                    candidates = match_fund_candidates(name, fund_master, top_n=3)
                    st.warning(f"⚠️ **{name}** の照合候補:")
                    for cid, cname, cscore in candidates:
                        st.write(f"  - {cname} ({int(cscore*100)}%)")
                else:
                    st.error(f"✗ **{name}** は認識できませんでした。正式名称で入力してください。")

    st.write("---")

    can_proceed = (
        95 <= total_weight <= 105
        and len(valid_inputs) >= 1
    )

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("← 戻る"):
            st.session_state.current_page = "profiling"
            st.rerun()

    with col_next:
        if st.button("分析結果を見る", disabled=not can_proceed, type="primary"):
            _save_holdings(holdings_input, fund_master)
            st.session_state.current_page = "results"
            st.rerun()


def _save_holdings(
    holdings_input: list[dict],
    fund_master,
) -> None:
    """入力されたホールディングスをセッションステートに保存する"""
    total = sum(h.get("weight", 0) for h in holdings_input if h.get("name", "").strip())
    if total <= 0:
        return

    holdings = []
    for h in holdings_input:
        name = h.get("name", "").strip()
        weight = h.get("weight", 0)
        if not name or weight <= 0:
            continue

        fund_id, confidence = match_fund(name, fund_master)
        holdings.append(Holding(
            fund_id=fund_id if confidence >= 0.5 else None,
            fund_name_input=name,
            weight=weight / 100.0,
            matched=confidence >= 0.5,
        ))

    st.session_state.holdings = holdings
