"""ハードフィルタの単体テスト"""

import pytest

from src.core.filters import apply_hard_filters


class TestApplyHardFilters:
    def test_レバレッジファンドが除外される(self, fund_master):
        filtered = apply_hard_filters(fund_master)
        assert "JP90C000CCD0" not in filtered["fund_id"].values  # 4.3倍ブル

    def test_純資産30億円未満が除外される(self, fund_master):
        filtered = apply_hard_filters(fund_master)
        assert (filtered["aum_oku_yen"] >= 30).all()

    def test_運用期間3年未満が除外される(self, fund_master):
        filtered = apply_hard_filters(fund_master)
        assert (filtered["operation_years"] >= 3).all()

    def test_オルカンは除外されない(self, fund_master):
        filtered = apply_hard_filters(fund_master)
        assert "JP90C000H1T1" in filtered["fund_id"].values

    def test_フィルタ後はファンド数が減る(self, fund_master):
        filtered = apply_hard_filters(fund_master)
        assert len(filtered) < len(fund_master)
