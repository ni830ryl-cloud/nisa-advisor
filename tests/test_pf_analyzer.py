"""PF分析の単体テスト（TC-W1〜W3を含む）"""

import pytest

from src.core.pf_analyzer import analyze_portfolio, detect_conflicts
from src.models.user_profile import Holding, UserProfile


class TestAnalyzePortfolio:
    def test_マッチング済みHoldingを分析できる(self, fund_master):
        holdings = [
            Holding(fund_id="JP90C000H1T1", fund_name_input="オルカン", weight=0.6, matched=True),
            Holding(fund_id="JP90C000GKC6", fund_name_input="S&P500", weight=0.4, matched=True),
        ]
        result = analyze_portfolio(holdings, fund_master)
        assert result is not None
        assert 1.0 <= result.weighted_risk_score <= 10.0

    def test_マッチング未成立は分析スキップ(self, fund_master):
        holdings = [
            Holding(fund_name_input="不明なファンド", weight=1.0, matched=False),
        ]
        result = analyze_portfolio(holdings, fund_master)
        assert result is None

    def test_TC_W1_レバレッジ保有で警告が出る(self, fund_master):
        """TC-W1: 小型ブルーチップ(leverage_warning タグあり)保有 → leverage_etf_detected警告"""
        holdings = [
            Holding(fund_id="JP90C0003D90", fund_name_input="小型ブルーチップオープン", weight=1.0, matched=True),
        ]
        result = analyze_portfolio(holdings, fund_master)
        assert result is not None
        assert "leverage_etf_detected" in result.warnings

    def test_TC_W3_米国集中で警告が出る(self, fund_master):
        """TC-W3: 米国100% → high_concentration_us警告"""
        holdings = [
            Holding(fund_id="JP90C000GKC6", fund_name_input="S&P500", weight=0.7, matched=True),
            Holding(fund_id="JP90C000FHD2", fund_name_input="楽天VTI", weight=0.3, matched=True),
        ]
        result = analyze_portfolio(holdings, fund_master)
        assert result is not None
        assert "high_concentration_us" in result.warnings

    def test_ギャップ検出_日本株なし(self, fund_master):
        """米国のみ保有 → no_japan_exposure ギャップ"""
        holdings = [
            Holding(fund_id="JP90C000GKC6", fund_name_input="S&P500", weight=1.0, matched=True),
        ]
        result = analyze_portfolio(holdings, fund_master)
        assert result is not None
        assert "no_japan_exposure" in result.gaps


class TestDetectConflicts:
    def test_TC_W2_申告配当_実態グロース_矛盾検出(self, fund_master):
        """TC-W2: 申告配当重視 + NASDAQ-100 100% → style_mismatch"""
        profile = UserProfile(
            consent_given=True,
            experience="current_holder",
            horizon="10_20",
            drawdown_tolerance="medium",
            return_expectation="market",
            region_preference="us",
            style_preference="dividend",
        )
        holdings = [
            Holding(fund_id="JP90C000QF22", fund_name_input="NASDAQ-100", weight=1.0, matched=True),
        ]
        pf = analyze_portfolio(holdings, fund_master)
        assert pf is not None
        conflicts = detect_conflicts(profile, pf)
        conflict_types = [c["type"] for c in conflicts]
        assert "style_mismatch" in conflict_types

    def test_矛盾なしの場合は空リスト(self, fund_master):
        profile = UserProfile(
            consent_given=True,
            experience="current_holder",
            horizon="10_20",
            drawdown_tolerance="medium",
            return_expectation="market",
            region_preference="world",
            style_preference="index_auto",
        )
        from src.models.portfolio import PortfolioAnalysis
        pf = PortfolioAnalysis(
            weighted_risk_score=5.0,
            weighted_growth_value_score=5.0,
            weighted_active_passive=0.1,
        )
        conflicts = detect_conflicts(profile, pf)
        assert conflicts == []
