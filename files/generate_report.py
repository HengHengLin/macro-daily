#!/usr/bin/env python3
"""
generate_report.py — 调用Claude API生成宏观日报
读取 daily_data.json → 精简prompt → Claude API → 输出 report.md
"""

import json
import datetime
import os
import requests
import sys

# ── 配置 ───────────────────────────────────────────────────────────────────
CLAUDE_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")   # 从环境变量读取
CLAUDE_MODEL    = "claude-opus-4-5"
DATA_PATH       = "/home/claude/macro_daily/daily_data.json"
REPORT_PATH     = "/home/claude/macro_daily/report.md"

if not CLAUDE_API_KEY:
    print("❌ 请设置环境变量 ANTHROPIC_API_KEY")
    sys.exit(1)

# ── 精简版框架Prompt（完整框架在Project Instructions里，这里只是提示词） ──
SYSTEM_PROMPT = """你是一位拥有10年经验的宏观对冲基金经理。
你遵循美林投资时钟和三层流动性框架（三维度细化版）进行分析。

今天你将根据提供的实时市场数据生成一份简洁的宏观日报。

## 输出格式要求（严格遵守）

日报分为以下6个模块，总字数控制在1500字以内，适合飞书消息阅读：

**📍 一、周期定位**
一句话判断当前美林时钟象限，列出核心数据依据。

**💧 二、流动性信号**
海外/狭义/广义三层各1-2句，只写边际变化，忽略平稳项。

**⚖️ 三、关键比价**
油金比、美债利差、股债性价比，各一句结论。

**📰 四、今日事件提示**
根据数据异常点，推测可能的风险事件（无数据时标注"待人工补充"）。

**🏭 五、重点行业变化**
只写有显著变化的行业（涨跌幅异常、资金异动），最多5个，其余不提。

**🎯 六、配置建议摘要**
大类资产建议一句话，最大概率路径一句话，风险提示2条。

---
数据置信度说明：如某项数据为N/A或明显异常，请在该项加注⚠️并说明可能原因，不要编造数据。"""


def build_user_prompt(data: dict) -> str:
    """把json数据格式化成易读的prompt"""
    today = data.get("date", datetime.date.today().isoformat())
    mkt   = data.get("market", {})
    macro = data.get("macro_us", {})
    ratio = data.get("ratios", {})
    cn    = data.get("macro_cn", {})

    def fmt(d: dict, key: str) -> str:
        v = d.get(key, {})
        if isinstance(v, dict):
            price = v.get("price", "N/A")
            chg   = v.get("change_pct")
            chg_s = f"({'+' if chg and chg > 0 else ''}{chg}%)" if chg is not None else ""
            return f"{price} {chg_s}".strip()
        return str(v)

    def fred_fmt(d: dict) -> str:
        return f"{d.get('value','N/A')} ({d.get('date','N/A')})"

    lines = [
        f"# 宏观日报数据包 — {today}",
        "",
        "## 【市场行情】",
        f"- 标普500: {fmt(mkt,'sp500')}",
        f"- 纳斯达克: {fmt(mkt,'nasdaq')}",
        f"- 道琼斯: {fmt(mkt,'dow')}",
        f"- 恒生指数: {fmt(mkt,'hsi')}",
        f"- 沪深300: {fmt(mkt,'csi300')}",
        f"- 布伦特原油: {fmt(mkt,'oil_brent')}",
        f"- 黄金: {fmt(mkt,'gold')}",
        f"- 美元指数DXY: {fmt(mkt,'dxy')}",
        f"- 美元/人民币: {fmt(mkt,'usdcny')}",
        f"- 美债10Y收益率: {fmt(mkt,'us10y')}",
        f"- 美债2Y收益率: {fmt(mkt,'us2y')}",
        f"- VIX恐慌指数: {fmt(mkt,'vix')}",
        "",
        "## 【关键比价】",
        f"- 油金比: {ratio.get('oil_gold_ratio','N/A')}",
        f"- 美债10Y-2Y利差: {ratio.get('us_yield_spread_10_2','N/A')}bps",
        "",
        "## 【美国宏观(FRED最新)】",
        f"- 美联储资产负债表: {fred_fmt(macro.get('fed_balance_sheet',{}))}",
        f"- 美国M2: {fred_fmt(macro.get('m2_us',{}))}",
        f"- 美国CPI: {fred_fmt(macro.get('cpi_us',{}))}",
        f"- 美国PCE: {fred_fmt(macro.get('pce',{}))}",
        f"- 失业率: {fred_fmt(macro.get('unemployment',{}))}",
        "",
        "## 【国内宏观(月度，最新一期)】",
        f"- CPI同比: {cn.get('cpi_yoy','N/A')}",
        f"- PPI同比: {cn.get('ppi_yoy','N/A')}",
        f"- 官方PMI: {cn.get('pmi_official','N/A')}",
        f"- 财新PMI: {cn.get('pmi_caixin','N/A')}",
        f"- M1同比: {cn.get('m1_yoy','N/A')}",
        f"- M2同比: {cn.get('m2_yoy','N/A')}",
        f"- 社融同比: {cn.get('social_finance_yoy','N/A')}",
        "",
        "---",
        "请根据以上数据，按照你的分析框架，输出今日宏观日报。",
        "国内月度数据若为N/A，请在对应分析模块注明⚠️数据待更新，并用最近已知值推断趋势。"
    ]
    return "\n".join(lines)


def call_claude(system: str, user: str) -> str:
    """调用Claude API"""
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": user}]
        },
        timeout=120
    )
    if response.status_code != 200:
        raise RuntimeError(f"API错误 {response.status_code}: {response.text[:300]}")
    return response.json()["content"][0]["text"]


def main():
    today = datetime.date.today().isoformat()
    print(f"🤖 [{today}] 生成宏观日报...")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_prompt = build_user_prompt(data)
    report_text = call_claude(SYSTEM_PROMPT, user_prompt)

    # 加上日期头
    header = f"# 宏观日报 {today}\n\n"
    full_report = header + report_text

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"  ✅ 日报已生成 → {REPORT_PATH}")
    print(f"  📊 字数: {len(report_text)} 字")
    return full_report


if __name__ == "__main__":
    main()
