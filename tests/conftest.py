"""テスト共通フィクスチャ"""

import pytest
import pandas as pd
from pathlib import Path

from src.models.user_profile import UserProfile, Holding


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fund_master() -> pd.DataFrame:
    """本番用ファンドマスタをロードする"""
    from src.data.loader import load_fund_master_plain
    return load_fund_master_plain()


@pytest.fixture
def sample_funds(fund_master) -> pd.DataFrame:
    """テスト用ファンドサブセット（主要10銘柄）"""
    key_ids = [
        "JP90C000H1T1",  # オルカン
        "JP90C000GKC6",  # S&P500
        "JP90C000FHD2",  # 楽天VTI
        "JP90C000FZD4",  # FANG+
        "JP90C000QF22",  # NASDAQ-100
        "JP90C000R6N1",  # SCHD
        "JP90C000MED5",  # WCM
        "JP90C000ENA9",  # TOPIX
        "JP90C000CCD0",  # 4.3倍ブル
        "JP90C000B2P5",  # 先進国債券
    ]
    return fund_master[fund_master["fund_id"].isin(key_ids)].reset_index(drop=True)


@pytest.fixture
def profile_beginner_low() -> UserProfile:
    """TC-1: 初心者・低リスク・全世界"""
    return UserProfile(
        consent_given=True,
        experience="none",
        horizon="5_10",
        drawdown_tolerance="low",
        return_expectation="modest",
        region_preference="world",
        style_preference="index_auto",
    )


@pytest.fixture
def profile_advanced_growth() -> UserProfile:
    """TC-2: 上級・20年・高耐性・グロース"""
    return UserProfile(
        consent_given=True,
        experience="current_holder",
        horizon="20_plus",
        drawdown_tolerance="high",
        return_expectation="above_market",
        region_preference="us",
        style_preference="growth",
    )


@pytest.fixture
def profile_intermediate_us() -> UserProfile:
    """TC-3: 中級・バランス・米国"""
    return UserProfile(
        consent_given=True,
        experience="current_holder",
        horizon="10_20",
        drawdown_tolerance="medium",
        return_expectation="market",
        region_preference="us",
        style_preference="balanced",
    )


@pytest.fixture
def profile_dividend() -> UserProfile:
    """TC-4: 配当重視・米国"""
    return UserProfile(
        consent_given=True,
        experience="current_holder",
        horizon="10_20",
        drawdown_tolerance="medium",
        return_expectation="market",
        region_preference="us",
        style_preference="dividend",
    )


@pytest.fixture
def profile_index_auto() -> UserProfile:
    """TC-5: インデックスおまかせ・全世界"""
    return UserProfile(
        consent_given=True,
        experience="none",
        horizon="10_20",
        drawdown_tolerance="medium",
        return_expectation="market",
        region_preference="world",
        style_preference="index_auto",
    )
