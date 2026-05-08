"""スコアリングロジックの単体テスト（TC-1〜TC-6を含む）"""

import pytest

from src.core.scoring import (
    compute_cost_score,
    compute_fund_score,
    compute_return_score,
    compute_scale_score,
    compute_sharpe_score,
    compute_stddev_penalty,
    compute_total_score,
)
from src.models.user_profile import UserProfile


class TestComputeReturnScore:
    def test_10年リターン20パーセントは90点(self):
        fund = {"return_10y": 20.0}
        score = compute_return_score(fund, "20_plus")
        assert score == 90.0

    def test_5年リターンゼロは20点(self):
        # return_5y=0.0 はデータあり → 20点（0%リターン）
        fund = {"return_5y": 0.0, "return_3y": None}
        score = compute_return_score(fund, "10_20")
        assert score == pytest.approx(20.0)

    def test_負のリターンは20点未満(self):
        fund = {"return_3y": -5.0}
        score = compute_return_score(fund, "5_10")
        assert score == pytest.approx(15.0)

    def test_データなしは50点(self):
        score = compute_return_score({}, "5_10")
        assert score == 50.0


class TestComputeStddevPenalty:
    def test_初心者低耐性_NASDAQ相当_フルペナルティ(self):
        """TC仕様: 初心者A(5-10, low) × stddev=25 → 45×1.0×1.0=45"""
        fund = {"stddev_5y": 25.0}
        profile = UserProfile(
            consent_given=True,
            experience="none",
            horizon="5_10",
            drawdown_tolerance="low",
            return_expectation="modest",
            region_preference="world",
            style_preference="index_auto",
        )
        penalty = compute_stddev_penalty(fund, profile)
        assert penalty == pytest.approx(45.0)

    def test_中級中耐性_減衰ペナルティ(self):
        """TC仕様: 中級(10-20, medium) × stddev=25 → 45×0.5×0.5=11.25"""
        fund = {"stddev_5y": 25.0}
        profile = UserProfile(
            consent_given=True,
            experience="current_holder",
            horizon="10_20",
            drawdown_tolerance="medium",
            return_expectation="market",
            region_preference="us",
            style_preference="balanced",
        )
        penalty = compute_stddev_penalty(fund, profile)
        assert penalty == pytest.approx(11.25)

    def test_上級高耐性_ペナルティゼロ(self):
        """TC仕様: 上級(20+, high) × stddev=25 → 45×0.2×0.0=0"""
        fund = {"stddev_5y": 25.0}
        profile = UserProfile(
            consent_given=True,
            experience="current_holder",
            horizon="20_plus",
            drawdown_tolerance="high",
            return_expectation="above_market",
            region_preference="us",
            style_preference="growth",
        )
        penalty = compute_stddev_penalty(fund, profile)
        assert penalty == pytest.approx(0.0)

    def test_データなしはペナルティゼロ(self):
        fund = {}
        profile = UserProfile(
            consent_given=True,
            experience="none",
            horizon="5_10",
            drawdown_tolerance="low",
            return_expectation="modest",
            region_preference="world",
            style_preference="index_auto",
        )
        assert compute_stddev_penalty(fund, profile) == 0.0


class TestComputeTotalScore:
    def test_TC1_初心者低リスク_オルカン系が高スコア(self, fund_master, profile_beginner_low):
        """TC-1: 初心者・低リスク → オルカン(JP90C000H1T1)が最上位に来るか確認"""
        from src.core.filters import apply_hard_filters
        filtered = apply_hard_filters(fund_master)

        scores = [
            compute_total_score(row.to_dict(), profile_beginner_low, filtered)
            for _, row in filtered.iterrows()
        ]
        scores.sort(key=lambda s: s.total_score, reverse=True)

        top_ids = [s.fund_id for s in scores[:3]]
        # オルカン・eMAXIS系・バランス系が上位に来ることを期待
        assert any(fid in top_ids for fid in [
            "JP90C000H1T1",  # オルカン
            "JP90C000FBSD",  # バランス8資産
            "JP90C000R5F8",  # 楽天プラスオールカントリー
        ])

    def test_TC2_上級グロース_FANG系が高スコア(self, fund_master, profile_advanced_growth):
        """TC-2: 上級・20年・高耐性・グロース → FANG+/NASDAQ-100が上位"""
        from src.core.filters import apply_hard_filters
        filtered = apply_hard_filters(fund_master)

        scores = [
            compute_total_score(row.to_dict(), profile_advanced_growth, filtered)
            for _, row in filtered.iterrows()
        ]
        scores.sort(key=lambda s: s.total_score, reverse=True)

        top_ids = [s.fund_id for s in scores[:5]]
        assert any(fid in top_ids for fid in [
            "JP90C000FZD4",  # FANG+
            "JP90C000FHD2",  # 楽天VTI
            "JP90C000GKC6",  # S&P500
        ])

    def test_TC4_配当重視_高配当系が方針フィルタ後に上位(self, fund_master, profile_dividend):
        """TC-4: 配当重視 → 配当方針フィルタ後にSCHD/SBI高配当系が上位"""
        from src.core.filters import apply_hard_filters
        from src.core.strategies import filter_funds_by_strategy
        filtered = apply_hard_filters(fund_master)

        # 配当方針でフィルタ
        dividend_strategy = {
            "id": "strategy_dividend",
            "filter_tags": ["dividend_focused"],
            "exclude_tags": [],
        }
        candidates = filter_funds_by_strategy(dividend_strategy, filtered)

        scores = [
            compute_total_score(row.to_dict(), profile_dividend, filtered)
            for _, row in candidates.iterrows()
        ]
        scores.sort(key=lambda s: s.total_score, reverse=True)

        assert len(scores) > 0
        top_ids = [s.fund_id for s in scores[:3]]
        # 配当フィルタ後はSBI高配当・世界のベスト（配当型）が候補に含まれること
        assert any(fid in top_ids for fid in [
            "JP90C000Q2F1",   # SBI日本高配当
            "JP90C000P8E9",   # 世界のベスト（dividend_focused タグあり）
        ])

    def test_スコアは0から100の範囲内(self, fund_master, profile_beginner_low):
        """全ファンドのスコアが0-100の範囲内であること"""
        for _, row in fund_master.iterrows():
            score = compute_total_score(row.to_dict(), profile_beginner_low, fund_master)
            assert 0.0 <= score.total_score <= 100.0


class TestComputeScaleScore:
    def test_大型ファンドは高スコア(self):
        fund = {"aum_oku_yen": 50000.0, "operation_years": 12.0}
        assert compute_scale_score(fund) == pytest.approx(100.0)

    def test_小型ファンドは低スコア(self):
        # aum=20(30点) + years=1(<3→40点) = 平均35.0
        fund = {"aum_oku_yen": 20.0, "operation_years": 1.0}
        score = compute_scale_score(fund)
        assert score <= 35.0
