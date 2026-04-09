import json, os, requests, datetime

with open("daily_data.json", "r") as f:
    d = json.load(f)

mkt = d.get("market", {})
cn  = d.get("macro_cn", {})
us  = d.get("macro_us", {})
rat = d.get("ratios", {})

def p(key):
    v = mkt.get(key, {})
    price = v.get("price", "N/A")
    chg = v.get("change_pct")
    if chg is not None:
        arrow = "▲" if chg > 0 else "▼"
        return str(price) + "(" + arrow + str(abs(chg)) + "%)"
    return str(price)

def m(obj, *keys):
    for k in keys:
        if isinstance(obj, dict):
            obj = obj.get(k, "N/A")
    return str(obj)

today = datetime.date.today().strftime("%Y-%m-%d")
lines = [
    "宏观日报数据包 " + today,
    "",
    "【市场行情】",
    "标普500: " + p("sp500"),
    "纳斯达克: " + p("nasdaq"),
    "沪深300: " + p("csi300"),
    "恒生: " + p("hsi"),
    "黄金: " + p("gold"),
    "布伦特油: " + p("oil_brent"),
    "美元指数: " + p("dxy"),
    "美元/人民币: " + p("usdcny"),
    "美债10Y: " + p("us10y"),
    "VIX: " + p("vix"),
    "",
    "【关键比价】",
    "油金比: " + str(rat.get("oil_gold_ratio","N/A")),
    "10Y-2Y利差: " + str(rat.get("yield_spread_10_2","N/A")),
    "",
    "【国内宏观】",
    "CPI同比: " + m(cn,"cpi","yoy") + "%",
    "PPI同比: " + m(cn,"ppi","yoy") + "%",
    "PMI官方: " + m(cn,"pmi_official","mfg"),
    "PMI财新: " + m(cn,"pmi_caixin_mfg","value"),
    "M1同比: " + m(cn,"money_supply","m1_yoy") + "%",
    "M2同比: " + m(cn,"money_supply","m2_yoy") + "%",
    "DR007: " + m(cn,"dr007","value"),
    "",
    "【美国宏观】",
    "CPI: " + m(us,"cpi","value") + " (前值" + m(us,"cpi","prev") + ")",
    "核心CPI: " + m(us,"core_cpi","value"),
    "非农: " + m(us,"non_farm","value") + "万",
    "失业率: " + m(us,"unemployment","value") + "%",
    "ISM PMI: " + m(us,"ism_pmi","value"),
    "",
    "---",
    "复制以上内容到宏观分析 Project，发送「请生成今日日报」",
]

msg = "\n".join(lines)
webhook = os.environ.get("LARK_WEBHOOK_URL", "")
if webhook:
    r = requests.post(webhook, json={"msg_type": "text", "content": {"text": msg}})
    print("飞书推送状态: " + str(r.status_code))
else:
    print("未配置 LARK_WEBHOOK_URL")
