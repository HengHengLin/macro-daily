#!/usr/bin/env python3
"""
fetch_data.py — 宏观日报数据抓取（全自动版）
数据源：yfinance（行情）+ FRED（美国宏观）+ AKShare（国内宏观，全自动）
"""

import json, datetime, subprocess, sys, time, os

def pip_install(pkg):
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", pkg, "-q", "--break-system-packages"],
        stderr=subprocess.DEVNULL)

for pkg, imp in [("yfinance","yfinance"),("requests","requests"),
                  ("akshare","akshare"),("pandas","pandas")]:
    try: __import__(imp)
    except ImportError:
        print(f"📦 安装 {pkg}...")
        pip_install(pkg)

import yfinance as yf, requests, akshare as ak, pandas as pd

OUT_PATH = "daily_data.json"

# ═══════════════════════════════════════
# 1. 市场行情（yfinance）
# ═══════════════════════════════════════
TICKERS = {
    "sp500":"^GSPC", "nasdaq":"^IXIC", "dow":"^DJI",
    "hsi":"^HSI", "csi300":"000300.SS", "nikkei":"^N225",
    "oil_brent":"BZ=F", "gold":"GC=F", "silver":"SI=F",
    "us10y":"^TNX", "us2y":"^IRX",
    "dxy":"DX-Y.NYB", "usdcny":"USDCNY=X", "vix":"^VIX",
}

def fetch_market():
    r = {}
    for name, ticker in TICKERS.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 2:
                c0, c1 = float(hist["Close"].iloc[-2]), float(hist["Close"].iloc[-1])
                r[name] = {"price": round(c1,4), "change_pct": round((c1-c0)/c0*100, 2)}
            elif len(hist) == 1:
                r[name] = {"price": round(float(hist["Close"].iloc[-1]),4), "change_pct": None}
            else:
                r[name] = {"price": "N/A"}
        except Exception as e:
            r[name] = {"price": "N/A", "error": str(e)[:60]}
    return r

# ═══════════════════════════════════════
# 2. 美国宏观（AKShare，无需API key）
# ═══════════════════════════════════════
def fetch_macro_us():
    us = {}

    def ak_us(fn, process_fn, label):
        for attempt in range(2):
            try:
                df = fn()
                if df is None or df.empty:
                    return {"_error": f"{label}: empty"}
                return process_fn(df)
            except Exception as e:
                if attempt == 0: time.sleep(2)
                else: return {"_error": f"{label}: {str(e)[:80]}"}

    # CPI月率
    us["cpi"] = ak_us(
        ak.macro_usa_cpi_monthly,
        lambda df: {"date": str(df.iloc[0].get("日期","N/A")),
                    "value": str(df.iloc[0].get("今值","N/A")),
                    "forecast": str(df.iloc[0].get("预测值","N/A")),
                    "prev": str(df.iloc[0].get("前值","N/A"))},
        "美国CPI")

    # 核心CPI
    us["core_cpi"] = ak_us(
        ak.macro_usa_core_cpi_monthly,
        lambda df: {"date": str(df.iloc[0].get("日期","N/A")),
                    "value": str(df.iloc[0].get("今值","N/A")),
                    "prev": str(df.iloc[0].get("前值","N/A"))},
        "美国核心CPI")

    # PPI
    us["ppi"] = ak_us(
        ak.macro_usa_ppi,
        lambda df: {"date": str(df.iloc[0].get("日期","N/A")),
                    "value": str(df.iloc[0].get("今值","N/A")),
                    "prev": str(df.iloc[0].get("前值","N/A"))},
        "美国PPI")

    # 核心PCE
    us["core_pce"] = ak_us(
        ak.macro_usa_core_pce_price,
        lambda df: {"date": str(df.iloc[0].get("日期","N/A")),
                    "value": str(df.iloc[0].get("今值","N/A")),
                    "prev": str(df.iloc[0].get("前值","N/A"))},
        "美国核心PCE")

    # 失业率
    us["unemployment"] = ak_us(
        ak.macro_usa_unemployment_rate,
        lambda df: {"date": str(df.iloc[0].get("日期","N/A")),
                    "value": str(df.iloc[0].get("今值","N/A")),
                    "prev": str(df.iloc[0].get("前值","N/A"))},
        "美国失业率")

    # ISM制造业PMI
    us["ism_pmi"] = ak_us(
        ak.macro_usa_ism_pmi,
        lambda df: {"date": str(df.iloc[0].get("日期","N/A")),
                    "value": str(df.iloc[0].get("今值","N/A")),
                    "prev": str(df.iloc[0].get("前值","N/A"))},
        "美国ISM制造业PMI")

    # 非农就业
    us["non_farm"] = ak_us(
        ak.macro_usa_non_farm,
        lambda df: {"date": str(df.iloc[0].get("日期","N/A")),
                    "value": str(df.iloc[0].get("今值","N/A")),
                    "prev": str(df.iloc[0].get("前值","N/A"))},
        "美国非农")

    # GDP月率
    us["gdp"] = ak_us(
        ak.macro_usa_gdp_monthly,
        lambda df: {"date": str(df.iloc[0].get("日期","N/A")),
                    "value": str(df.iloc[0].get("今值","N/A")),
                    "prev": str(df.iloc[0].get("前值","N/A"))},
        "美国GDP")

    return us

# ═══════════════════════════════════════
# 3. 国内宏观（AKShare）
# ═══════════════════════════════════════
def safe_ak(fn, process_fn, label):
    """AKShare调用包装：失败返回{"_error":...}而非崩溃"""
    for attempt in range(2):
        try:
            df = fn()
            if df is None or df.empty:
                return {"_error": f"{label}: empty"}
            return process_fn(df)
        except Exception as e:
            if attempt == 0: time.sleep(3)
            else: return {"_error": f"{label}: {str(e)[:100]}"}

def fetch_macro_cn():
    cn = {}

    # ── CPI（金十数据，月度）──
    cn["cpi"] = safe_ak(
        ak.macro_china_cpi_monthly,
        lambda df: {"date": str(df.iloc[0].get("月份","N/A")),
                    "yoy":  str(df.iloc[0].get("同比增长","N/A")),
                    "mom":  str(df.iloc[0].get("环比增长","N/A"))},
        "CPI")

    # ── PPI（金十数据，月度）──
    cn["ppi"] = safe_ak(
        ak.macro_china_ppi,
        lambda df: {"date": str(df.iloc[0].get("月份", df.iloc[0].get("date","N/A"))),
                    "yoy":  str(df.iloc[0].get("同比增长", df.iloc[0].get("今值","N/A")))},
        "PPI")

    # ── PMI 官方（制造业+非制造业）──
    cn["pmi_official"] = safe_ak(
        ak.macro_china_pmi,
        lambda df: {"date":    str(df.iloc[0].get("月份","N/A")),
                    "mfg":     str(df.iloc[0].get("制造业-指数","N/A")),
                    "non_mfg": str(df.iloc[0].get("非制造业-指数","N/A"))},
        "PMI官方")

    # ── PMI 财新制造业（月度）──
    cn["pmi_caixin_mfg"] = safe_ak(
        ak.index_pmi_man_cx,
        lambda df: {"date":  str(df.iloc[-1].get("date", df.iloc[-1].get("时间","N/A"))),
                    "value": str(df.iloc[-1].get("pmi", df.iloc[-1].iloc[1] if len(df.columns)>1 else "N/A"))},
        "财新制造业PMI")

    # ── PMI 财新服务业 ──
    cn["pmi_caixin_ser"] = safe_ak(
        ak.index_pmi_ser_cx,
        lambda df: {"date":  str(df.iloc[-1].get("date","N/A")),
                    "value": str(df.iloc[-1].get("pmi", df.iloc[-1].iloc[1] if len(df.columns)>1 else "N/A"))},
        "财新服务业PMI")

    # ── M1/M2货币供应 ──
    cn["money_supply"] = safe_ak(
        ak.macro_china_money_supply,
        lambda df: {"date":   str(df.iloc[0].get("月份","N/A")),
                    "m2_yoy": str(df.iloc[0].get("货币和准货币(M2)-同比增长","N/A")),
                    "m1_yoy": str(df.iloc[0].get("货币(M1)-同比增长","N/A"))},
        "M1/M2")

    # ── 社融 ──
    cn["social_finance"] = safe_ak(
        ak.macro_china_new_financial_credit,
        lambda df: {"date":  str(df.iloc[0].get("月份", df.iloc[0].iloc[0])),
                    "value": str(df.iloc[0].iloc[1] if len(df.columns) > 1 else "N/A"),
                    "col":   str(df.columns[1] if len(df.columns) > 1 else "N/A")},
        "社融")

    # ── Shibor ──
    cn["shibor"] = safe_ak(
        ak.macro_china_shibor_all,
        lambda df: {"date":      str(df.iloc[0].get("日期","N/A")),
                    "overnight": str(df.iloc[0].get("隔夜","N/A")),
                    "1w":        str(df.iloc[0].get("1周","N/A")),
                    "1m":        str(df.iloc[0].get("1月","N/A"))},
        "Shibor")

    # ── DR007（逆回购利率）──
    cn["dr007"] = safe_ak(
        ak.repo_rate_hist,
        lambda df: {"date":  str(df.iloc[-1].get("日期", df.iloc[-1].iloc[0])),
                    "value": str(df.iloc[-1].get("DR007", df.iloc[-1].iloc[-1]))},
        "DR007")

    # ── LPR ──
    cn["lpr"] = safe_ak(
        ak.macro_china_lpr,
        lambda df: {"date": str(df.iloc[-1].get("TRADE_DATE","N/A")),
                    "1y":   str(df.iloc[-1].get("LPR1Y","N/A")),
                    "5y":   str(df.iloc[-1].get("LPR5Y","N/A"))},
        "LPR")

    # ── 波罗的海指数（航运）──
    cn["bdi"] = safe_ak(
        ak.macro_shipping_bdi,
        lambda df: {"date":  str(df.iloc[-1].get("日期","N/A")),
                    "value": str(df.iloc[-1].get("收盘","N/A"))},
        "BDI")

    return cn

# ═══════════════════════════════════════
# 4. 比价计算
# ═══════════════════════════════════════
def calc_ratios(mkt):
    def p(k):
        try: return float(mkt.get(k,{}).get("price","x"))
        except: return None
    oil, gold, us10, us2, dxy = p("oil_brent"),p("gold"),p("us10y"),p("us2y"),p("dxy")
    return {
        "oil_gold_ratio":    round(oil/gold,4)  if oil and gold  else "N/A",
        "yield_spread_10_2": round(us10-us2,3)  if us10 and us2  else "N/A",
        "gold_dxy_ratio":    round(gold/dxy,3)  if gold and dxy  else "N/A",
    }

# ═══════════════════════════════════════
# 主流程
# ═══════════════════════════════════════
def main():
    today = datetime.date.today().isoformat()
    print(f"\n{'='*52}\n🚀 宏观数据抓取 — {today}\n{'='*52}")

    print("📡 [1/4] 市场行情 (yfinance)...")
    market = fetch_market()
    ok = sum(1 for v in market.values() if v.get("price","N/A") != "N/A")
    print(f"   ✅ {ok}/{len(market)} 个标的")

    print("📡 [2/4] 美国宏观 (FRED)...")
    macro_us = fetch_macro_us()
    ok = sum(1 for v in macro_us.values() if v.get("value","N/A") != "N/A")
    print(f"   ✅ {ok}/{len(macro_us)} 个指标")

    print("📡 [3/4] 国内宏观 (AKShare)...")
    macro_cn = fetch_macro_cn()
    errs = [k for k,v in macro_cn.items() if isinstance(v,dict) and "_error" in v]
    print(f"   ✅ {len(macro_cn)-len(errs)}/{len(macro_cn)} 个指标" +
          (f"，失败: {errs}" if errs else ""))

    print("🧮 [4/4] 比价...")
    ratios = calc_ratios(market)

    output = {"date": today, "market": market,
               "macro_us": macro_us, "macro_cn": macro_cn, "ratios": ratios}

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 数据已保存 → {OUT_PATH}\n")
    return output

if __name__ == "__main__":
    main()
