#!/usr/bin/env python3
"""
send_lark.py — 推送日报到飞书个人消息
使用 lark-cli (官方 @larksuite/cli)
目标：ou_6b3764961072debe462a17eb1176a8df（Linna 个人）
"""

import subprocess, os, sys, datetime

REPORT_PATH = os.path.expanduser("~/macro_daily/report.md")
OPEN_ID     = "ou_6b3764961072debe462a17eb1176a8df"
MAX_LEN     = 4000   # 飞书文本消息上限约4096字符

def read_report() -> str:
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def split_chunks(text: str, size: int) -> list[str]:
    """超长日报分段发送"""
    if len(text) <= size:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:size])
        text = text[size:]
    return chunks

def send_chunk(text: str, part: int, total: int) -> bool:
    prefix = f"📊 宏观日报 {datetime.date.today()} [{part}/{total}]\n\n" if total > 1 else ""
    content = prefix + text

    result = subprocess.run(
        ["lark-cli", "im", "+messages-send",
         "--as", "user",
         "--open-id", OPEN_ID,
         "--text", content],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        print(f"  ✅ 第{part}段发送成功")
        return True
    else:
        print(f"  ❌ 第{part}段失败: {result.stderr[:200]}")
        # 打印完整命令帮助排查
        print(f"     stdout: {result.stdout[:200]}")
        return False

def main():
    today = datetime.date.today().isoformat()
    print(f"📨 [{today}] 推送日报到飞书...")

    report  = read_report()
    chunks  = split_chunks(report, MAX_LEN)
    success = 0

    for i, chunk in enumerate(chunks, 1):
        ok = send_chunk(chunk, i, len(chunks))
        if ok:
            success += 1
        if i < len(chunks):
            import time; time.sleep(1)   # 多段之间间隔1秒

    print(f"\n{'✅' if success==len(chunks) else '⚠️'} "
          f"{success}/{len(chunks)} 段发送完成")
    return success == len(chunks)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
