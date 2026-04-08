# 宏观日报自动化 — 安装说明

## 文件结构
```
~/macro_daily/
├── fetch_data.py          # 数据抓取
├── generate_report.py     # 调Claude API生成日报
├── send_lark.py           # 推送飞书
├── run_daily.sh           # 主运行脚本
├── daily_data.json        # 每日数据（自动生成）
├── report.md              # 日报正文（自动生成）
├── macro_cn_state.json    # 国内月度数据（手动更新）
└── logs/                  # 日志目录
```

---

## 安装步骤

### 第1步：复制文件到 Mac
```bash
mkdir -p ~/macro_daily/logs
# 把所有 .py 和 .sh 文件复制到 ~/macro_daily/
```

### 第2步：安装依赖
```bash
pip3 install yfinance requests
```

### 第3步：配置 API Key
在 plist 文件里填入：
- `ANTHROPIC_API_KEY`：你的Claude API key
- `LARK_WEBHOOK_URL`：飞书webhook（见下方说明）

### 第4步：获取飞书Webhook
1. 打开飞书 → 设置 → 机器人
2. 或者在飞书群里添加自定义机器人，复制webhook地址
3. 也可以用 `opencli lark login` 登录后直接用lark-cli发送

### 第5步：安装 launchd 定时任务
```bash
# 把plist复制到正确位置
cp ~/macro_daily/com.linna.macro-daily.plist \
   ~/Library/LaunchAgents/com.linna.macro-daily.plist

# 加载定时任务
launchctl load ~/Library/LaunchAgents/com.linna.macro-daily.plist

# 验证是否加载成功
launchctl list | grep macro

# 立即手动测试一次
launchctl start com.linna.macro-daily
```

### 第6步：手动测试
```bash
# 先单独测试数据抓取
python3 ~/macro_daily/fetch_data.py

# 再测试日报生成
python3 ~/macro_daily/generate_report.py

# 最后测试飞书推送
python3 ~/macro_daily/send_lark.py
```

---

## 国内月度数据手动更新

每月初数据发布后（一般月初1-15日陆续发布），更新以下文件：
`~/macro_daily/daily_data.json` 中的 `macro_cn` 字段：

```json
"macro_cn": {
    "cpi_yoy":            "0.1%",   ← 国家统计局
    "ppi_yoy":            "-2.8%",  ← 国家统计局
    "pmi_official":       "50.5",   ← 统计局PMI
    "pmi_caixin":         "51.2",   ← 财新PMI
    "m1_yoy":             "1.1%",   ← 央行数据
    "m2_yoy":             "7.0%",   ← 央行数据
    "social_finance_yoy": "8.5%"    ← 央行社融
}
```

数据来源：
- 国家统计局：https://www.stats.gov.cn
- 央行：https://www.pbc.gov.cn
- 财新PMI：https://cn.caixin.com/economy

---

## Claude Project配置（节省token的关键）

在 claude.ai 新建一个 Project，把完整框架（Version 2.4）放进 Project Instructions。
每天的日报对话在这个Project下新建chat，脚本调API时只传数据，不重复传框架。
这样每次对话的context只有数据 + 当次问答，大幅减少token消耗。

---

## 常见问题

**Q: launchd任务没有触发？**
```bash
launchctl list com.linna.macro-daily   # 查看状态
cat ~/macro_daily/logs/launchd_stderr.log  # 看错误
```

**Q: 飞书收不到消息？**
先测试 webhook 是否有效：
```bash
curl -X POST "你的webhook地址" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"测试消息"}}'
```

**Q: yfinance数据延迟？**
yfinance 使用Yahoo Finance，A股数据有时延迟15分钟，
建议设置触发时间为早上9点后（美股数据用前一天收盘）。
