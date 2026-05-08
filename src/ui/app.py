"""NISA成長投資枠 ファンド推奨ツール - メインエントリーポイント"""

import os
import sys

# Streamlit Cloud対応: プロジェクトルートをsys.pathに追加
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

st.set_page_config(
    page_title="NISA成長投資枠 ファンド推奨ツール",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """セッションステートを初期化する"""
    defaults = {
        "consent": False,
        "experience": None,
        "horizon": None,
        "drawdown_tolerance": None,
        "return_expectation": None,
        "region_preference": None,
        "style_preference": None,
        "holdings_input": [{"name": "", "weight": 0}],
        "pf_analysis": None,
        "results": None,
        "current_page": "disclaimer",
        "conflict_choice": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def compute_progress() -> float:
    """現在の進捗を0-1で返す"""
    page = st.session_state.get("current_page", "disclaimer")
    mapping = {
        "disclaimer": 0.0,
        "profiling": 0.25,
        "portfolio": 0.65,
        "results": 1.0,
    }
    return mapping.get(page, 0.0)


def render_sidebar() -> None:
    """サイドバーに進捗と免責文言を表示する"""
    with st.sidebar:
        st.title("📊 NISA Advisor")
        st.write("---")
        progress = compute_progress()
        st.progress(progress)
        page_labels = {
            "disclaimer": "免責同意",
            "profiling": "プロファイリング",
            "portfolio": "PF入力",
            "results": "結果表示",
        }
        current = st.session_state.get("current_page", "disclaimer")
        st.caption(f"現在: {page_labels.get(current, '-')}")
        st.write("---")
        st.caption("⚠️ 本ツールは投資助言ではありません")
        st.caption("最終的な投資判断はご自身の責任でお願いします")


init_session_state()
render_sidebar()

# ページルーティング
page = st.session_state.get("current_page", "disclaimer")

if page == "disclaimer":
    from src.ui.pages import disclaimer as p
    p.render()
elif page == "profiling":
    from src.ui.pages import profiling as p
    p.render()
elif page == "portfolio":
    from src.ui.pages import portfolio as p
    p.render()
elif page == "results":
    from src.ui.pages import results as p
    p.render()
else:
    st.error("不明なページです")
