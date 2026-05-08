#!/usr/bin/env python3
"""
楽天証券 NISA成長投資枠 ファンドマスタスクレイピング

事前準備:
    uv add --dev playwright requests
    uv run playwright install chromium

実行:
    uv run python scripts/scrape_fund_master.py

動作原理:
    1. Playwright で検索ページをロードし「成長投資枠」フィルタを適用
    2. そのときの POST リクエスト（フィルタパラメータ入り）を記録
    3. requests で同じ POST を recsPerPage=9999 で送信 → 全件JSON取得
    4. 列マッピングに従ってCSVに変換・保存
"""

from __future__ import annotations

import asyncio
import csv
import math
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlencode

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.auto_tag import derive_region, derive_region_pcts, derive_tags

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "fund_master.csv"
API_URL = "https://www.rakuten-sec.co.jp/web/fund/scr/find/search/reloadscreener.asp"

# reloadscreener.asp の列順（POST query の result= に対応）
# 0列目はISINコード（result=に含まれず、常に先頭に付与される）
COLUMNS = [
    "fund_id",          # 0  ISIN (常に先頭)
    "fund_name",        # 1  ファンド名称
    "company",          # 2  運用会社
    "_nav",             # 3  基準価額 (不使用)
    "_daily_change",    # 4  前日比% (不使用)
    "aum_oku_yen",      # 5  純資産(億円)
    "_tsumitate",       # 6  積立フラグ
    "_suishou",         # 7  suishouFlag
    "_reinvest",        # 8  再投資フラグ
    "_description",     # 9  運用方針
    "_week_all",        # 10 week_all_all
    "_week_updown",     # 11 weekallallUPDOWN
    "_sma",             # 12 smaFlag
    "_ideco",           # 13 401kFlag
    "fund_score_3y",    # 14 rakutenScore3 (1-5)
    "expense_ratio",    # 15 actual_charge (%)
    "rakuten_category", # 16 リッパー分類
    "_fee_text",        # 17 手数料テキスト
    "fund_score_1y",    # 18 rakutenScore1
    "fund_score_5y",    # 19 rakutenScore5
    "fund_score_10y",   # 20 rakutenScore10
    "return_1y",        # 21 リターン(年率)1年
    "return_3y",        # 22 リターン(年率)3年
    "return_5y",        # 23 リターン(年率)5年
    "return_10y",       # 24 リターン(年率)10年
    "_return_20y",      # 25
    "stddev_1y",        # 26 リスク(年率)1年
    "stddev_3y",        # 27 リスク(年率)3年
    "stddev_5y",        # 28 リスク(年率)5年
    "stddev_10y",       # 29 リスク(年率)10年
    "_stddev_20y",      # 30
    "sharpe_1y",        # 31 シャープレシオ1年
    "sharpe_3y",        # 32 シャープレシオ3年
    "sharpe_5y",        # 33 シャープレシオ5年
    "sharpe_10y",       # 34 シャープレシオ10年
    "_sharpe_20y",      # 35
    "_wam_week",        # 36
    "_fund_code",       # 37 楽天内部コード (例:0331418A)
    "_week3",           # 38
    "_ranking",         # 39
    "return_inception", # 40 設定来リターン(年率)
    "return_6m",        # 41 リターン(年率)6ヶ月
    "_badge",           # 42
    "fund_nickname",    # 43 愛称
    "_rakuraku",        # 44
    "_wealth_navi",     # 45
]

CSV_COLUMNS = [
    "fund_id", "fund_name", "fund_nickname", "company", "rakuten_category",
    "asset_type", "region", "region_japan_pct", "region_us_pct", "region_em_pct",
    "is_index", "is_leveraged", "is_currency_select", "has_currency_hedge",
    "is_monthly_payout", "payout_type", "expense_ratio", "aum_oku_yen",
    "operation_years", "fund_score_1y", "fund_score_3y", "fund_score_5y",
    "fund_score_10y", "return_6m", "return_1y", "return_3y", "return_5y",
    "return_10y", "return_inception", "sharpe_1y", "sharpe_3y", "sharpe_5y",
    "sharpe_10y", "stddev_1y", "stddev_3y", "stddev_5y", "stddev_10y",
    "is_nisa_growth_eligible", "data_updated_at", "philosophy_tags",
]


# ---------------------------------------------------------------------------
# Playwright: NISA フィルタ付き POST パラメータを取得
# ---------------------------------------------------------------------------

async def scrape_all_funds_via_playwright() -> list[list]:
    """
    pagingControl.next(n) でページ番号を直接指定してナビゲートしながら
    レスポンスをインターセプトする。
    - pagingControl.next(n) は「ページn に移動」という絶対指定
    - 各ナビゲーションで複数レスポンスが発生するため、fund_id で重複排除
    """
    from playwright.async_api import async_playwright

    # fund_id をキーにした重複排除（ページ1の再送レスポンス対策）
    seen_fund_ids: set[str] = set()
    all_data: list[list] = []
    total_pages = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(locale="ja-JP")
        page = await context.new_page()

        nisa_applied = False

        async def on_response(resp):
            nonlocal total_pages, nisa_applied
            if "reloadscreener" in resp.url and resp.status == 200:
                try:
                    body = await resp.json()
                    data = body.get("Data", [])
                    pi = body.get("PageInfo", {})
                    selected = int(pi.get("NbrRecsSelected", 0))
                    if nisa_applied and data and selected < 2500:
                        if not total_pages:
                            total_pages = int(pi.get("NbrPagesTotal", 0))
                            print(f"  成長投資枠ファンド総数: {selected} 件 / {total_pages} ページ")
                        # fund_id(index=0) で重複排除しながら追加
                        for row in data:
                            fid = str(row[0]) if row else ""
                            if fid and fid not in seen_fund_ids:
                                seen_fund_ids.add(fid)
                                all_data.append(row)
                except Exception:
                    pass

        page.on("response", on_response)

        print("楽天証券 ファンド検索ページをロード中...")
        await page.goto(
            "https://www.rakuten-sec.co.jp/web/fund/search/",
            wait_until="networkidle",
            timeout=60_000,
        )
        await page.wait_for_timeout(2000)

        print("「成長投資枠」フィルタをクリック中...")
        for sel in ["label:has-text('成長投資枠')", "text=成長投資枠"]:
            try:
                elem = page.locator(sel).first
                if await elem.is_visible(timeout=2000):
                    nisa_applied = True
                    await elem.click()
                    await page.wait_for_timeout(4000)
                    print(f"  クリック成功: {sel}")
                    break
            except Exception:
                continue

        if not all_data:
            print("❌ フィルタ後のデータ取得失敗")
            await browser.close()
            return []

        # pagingControl.next(n) はページ番号 n への絶対移動
        # ページ 2 〜 total_pages を順番にリクエスト
        for target_page in range(2, (total_pages or 9999) + 1):
            prev_count = len(all_data)
            await page.evaluate(f"pagingControl.next({target_page})")
            # 新データが届くまで最大8秒待機
            for _ in range(16):
                await page.wait_for_timeout(500)
                if len(all_data) > prev_count:
                    break
            else:
                print(f"  ページ {target_page} タイムアウト（データなし）。終了。")
                break

            if target_page % 10 == 0:
                print(f"  ページ {target_page}/{total_pages}... ({len(all_data)} 件 unique)")

            if len(all_data) >= (total_pages or 9999) * 20:
                break

        await browser.close()

    print(f"  取得完了: {len(all_data)} 件 (unique)")
    return all_data


def _parse_post_data(raw: str) -> dict:
    """application/x-www-form-urlencoded の POST データを dict に変換する"""
    params: dict = {}
    for part in raw.split("&"):
        if "=" in part:
            k, _, v = part.partition("=")
            params[unquote(k)] = unquote(v)
        else:
            params[unquote(part)] = ""
    return params


# ---------------------------------------------------------------------------
# requests: 全件取得
# ---------------------------------------------------------------------------

def fetch_all_funds(post_params: dict, cookies: dict | None = None) -> list[list]:
    """POST パラメータを使って全ファンドデータをページネーションで取得する"""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.rakuten-sec.co.jp/web/fund/search/",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    # ページ1で総ページ数を確認
    params = dict(post_params)
    params["pg"] = "1"
    resp = requests.post(API_URL, data=params, headers=headers,
                         cookies=cookies or {}, timeout=30)
    resp.raise_for_status()
    body = resp.json()

    page_info = body.get("PageInfo", {})
    total_pages = int(page_info.get("NbrPagesTotal", 1))
    total_records = int(page_info.get("NbrRecsSelected", 0))
    print(f"  成長投資枠ファンド総数: {total_records} 件 / {total_pages} ページ")

    all_data = list(body.get("Data", []))

    # ページ2以降を取得（1秒インターバルでサーバ負荷を抑える）
    import time
    for pg in range(2, total_pages + 1):
        params["pg"] = str(pg)
        resp = requests.post(API_URL, data=params, headers=headers,
                             cookies=cookies or {}, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("Data", [])
        all_data.extend(data)
        if pg % 10 == 0:
            print(f"  ページ {pg}/{total_pages} 取得中... ({len(all_data)} 件)")
        time.sleep(0.5)

    print(f"  取得完了: {len(all_data)} 件")
    return all_data


# ---------------------------------------------------------------------------
# データ変換
# ---------------------------------------------------------------------------

def load_existing_nicknames() -> dict[str, str]:
    """既存CSV から fund_id → nickname マッピングを読み込む"""
    nicknames: dict[str, str] = {}
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = row.get("fund_id", "")
                nick = row.get("fund_nickname", "")
                if fid and nick:
                    nicknames[fid] = nick
    return nicknames


def row_to_dict(row: list) -> dict:
    """配列データを列名付き dict に変換する"""
    result: dict = {}
    for i, col in enumerate(COLUMNS):
        result[col] = row[i] if i < len(row) else None
    return result


def parse_float(v) -> float | None:
    if v is None or v == "" or v == "na":
        return None
    try:
        f = float(str(v).replace(",", ""))
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def parse_int_score(v) -> int | None:
    f = parse_float(v)
    if f is None:
        return None
    i = int(f)
    return i if 1 <= i <= 5 else None


def infer_operation_years(r: dict) -> float | None:
    """リターンデータの有無から運用年数を推定する"""
    if parse_float(r.get("return_10y")) is not None:
        return 12.0
    if parse_float(r.get("return_5y")) is not None:
        return 7.0
    if parse_float(r.get("return_3y")) is not None:
        return 4.0
    if parse_float(r.get("return_1y")) is not None:
        return 1.5
    return None


def infer_flags(fund_name: str, category: str) -> dict:
    """ファンド名・カテゴリからフラグを推定する"""
    name = fund_name or ""
    cat = category or ""
    text = name + cat

    is_index = any(kw in text for kw in [
        "インデックス", "Index", "index", "ETF", "S&P", "TOPIX", "日経",
        "NASDAQ", "SOX", "MSCI", "FTSE", "Russell",
    ])
    is_leveraged = any(kw in name for kw in ["レバ", "ブル", "ベア", "2倍", "3倍", "4倍"])
    is_monthly = any(kw in name for kw in ["毎月", "月次", "毎月決算"])
    is_currency_select = "通貨選択" in name
    has_hedge = "ヘッジあり" in name or "(H)" in name
    payout_type = "income" if is_monthly else "none"
    # 元本払い出し系の判定
    if is_monthly and any(kw in name for kw in ["世界のベスト", "毎月分配", "プレミアム", "インカム"]):
        payout_type = "principal"

    return {
        "is_index": is_index,
        "is_leveraged": is_leveraged,
        "is_monthly_payout": is_monthly,
        "payout_type": payout_type,
        "is_currency_select": is_currency_select,
        "has_currency_hedge": has_hedge,
    }


def build_csv_row(raw: dict, nicknames: dict[str, str], today: str) -> dict | None:
    fund_id = str(raw.get("fund_id", "")).strip()
    if not fund_id or not fund_id.startswith("JP"):
        return None

    fund_name = str(raw.get("fund_name", "")).strip()
    company = str(raw.get("company", "")).strip()
    category = str(raw.get("rakuten_category", "")).strip()
    expense_ratio = parse_float(raw.get("expense_ratio"))
    aum = parse_float(raw.get("aum_oku_yen"))

    flags = infer_flags(fund_name, category)
    region = derive_region(fund_name, category)
    jpct, upct, epct = derive_region_pcts(fund_name, region)
    operation_years = infer_operation_years(raw)

    tag_input = {
        **flags,
        "fund_name": fund_name,
        "stddev_5y": parse_float(raw.get("stddev_5y")),
        "stddev_3y": parse_float(raw.get("stddev_3y")),
    }
    tags = "|".join(derive_tags(tag_input))

    return {
        "fund_id": fund_id,
        "fund_name": fund_name,
        "fund_nickname": nicknames.get(fund_id, raw.get("fund_nickname", "") or ""),
        "company": company,
        "rakuten_category": category,
        "asset_type": _infer_asset_type(fund_name, category),
        "region": region,
        "region_japan_pct": jpct,
        "region_us_pct": upct,
        "region_em_pct": epct,
        **flags,
        "expense_ratio": expense_ratio,
        "aum_oku_yen": aum,
        "operation_years": operation_years,
        "fund_score_1y": parse_int_score(raw.get("fund_score_1y")),
        "fund_score_3y": parse_int_score(raw.get("fund_score_3y")),
        "fund_score_5y": parse_int_score(raw.get("fund_score_5y")),
        "fund_score_10y": parse_int_score(raw.get("fund_score_10y")),
        "return_6m": parse_float(raw.get("return_6m")),
        "return_1y": parse_float(raw.get("return_1y")),
        "return_3y": parse_float(raw.get("return_3y")),
        "return_5y": parse_float(raw.get("return_5y")),
        "return_10y": parse_float(raw.get("return_10y")),
        "return_inception": parse_float(raw.get("return_inception")),
        "sharpe_1y": parse_float(raw.get("sharpe_1y")),
        "sharpe_3y": parse_float(raw.get("sharpe_3y")),
        "sharpe_5y": parse_float(raw.get("sharpe_5y")),
        "sharpe_10y": parse_float(raw.get("sharpe_10y")),
        "stddev_1y": parse_float(raw.get("stddev_1y")),
        "stddev_3y": parse_float(raw.get("stddev_3y")),
        "stddev_5y": parse_float(raw.get("stddev_5y")),
        "stddev_10y": parse_float(raw.get("stddev_10y")),
        "is_nisa_growth_eligible": True,
        "data_updated_at": today,
        "philosophy_tags": tags,
    }


def _infer_asset_type(name: str, category: str) -> str:
    text = name + category
    if any(kw in text for kw in ["債券", "ボンド", "Bond"]):
        return "債券"
    if any(kw in text for kw in ["バランス", "8資産", "均等"]):
        return "バランス"
    if any(kw in text for kw in ["REIT", "リート", "不動産"]):
        return "不動産"
    return "株式"


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

async def main():
    print("=" * 60)
    print("楽天証券 NISA成長投資枠 ファンドマスタ更新")
    print("=" * 60)

    today = date.today().isoformat()
    nicknames = load_existing_nicknames()
    print(f"既存ニックネーム: {len(nicknames)} 件を保持")

    # Step 1 & 2: Playwright セッション内で全件取得
    raw_rows = await scrape_all_funds_via_playwright()

    if not raw_rows:
        print("❌ データ取得に失敗しました。")
        sys.exit(1)

    if not raw_rows:
        print("❌ データ取得に失敗しました。")
        sys.exit(1)

    # Step 3: レスポンスハンドラ内で既に重複排除済み
    print(f"\n取得: {len(raw_rows)} 件 (unique)")

    # Step 4: CSV に変換
    print(f"データ変換中...")
    rows = []
    skipped = 0
    for raw_row in raw_rows:
        raw_dict = row_to_dict(raw_row)
        row = build_csv_row(raw_dict, nicknames, today)
        if row:
            rows.append(row)
        else:
            skipped += 1

    print(f"  変換成功: {len(rows)} 件 / スキップ: {skipped} 件")

    # Step 4: 保存
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ 完了: {len(rows)} 件 → {OUTPUT_PATH}")
    print(f"   更新日: {today}")


if __name__ == "__main__":
    asyncio.run(main())
