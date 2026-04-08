#!/bin/bash
# run_daily.sh — 宏观日报自动化主脚本
# 每天早上7:00由 Mac launchd 触发

set -e
DIR="$HOME/macro_daily"
LOG="$DIR/logs/$(date +%Y%m%d).log"
mkdir -p "$DIR/logs"

echo "=============================" >> "$LOG"
echo "🚀 $(date '+%Y-%m-%d %H:%M:%S') 开始运行" >> "$LOG"

# 激活环境（如果你用了venv）
# source "$DIR/venv/bin/activate"

# 第1步：抓数据
echo "📡 Step 1: 抓取市场数据" >> "$LOG"
python3 "$DIR/fetch_data.py" >> "$LOG" 2>&1

# 第2步：生成日报
echo "🤖 Step 2: 生成日报" >> "$LOG"
python3 "$DIR/generate_report.py" >> "$LOG" 2>&1

# 第3步：推送飞书
echo "📨 Step 3: 推送飞书" >> "$LOG"
python3 "$DIR/send_lark.py" >> "$LOG" 2>&1

echo "✅ $(date '+%Y-%m-%d %H:%M:%S') 完成" >> "$LOG"
echo "=============================" >> "$LOG"
