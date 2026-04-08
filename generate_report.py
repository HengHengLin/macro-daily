#!/usr/bin/env python3
import json, os, requests, datetime

def call_gemini(sys_p, user_p):
    # 切换为配额更宽裕的 gemini-2.0-flash 模型
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    params = {"key": "AIzaSyCoHYWKa9Phk5eKBT6LVbDQ-K2Lx4M9o1A"}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"{sys_p}\n\n数据内容如下：\n{user_p}"
            }]
        }]
    }
    r = requests.post(url, params=params, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()['candidates'][0]['content']['parts'][0]['text']

def main():
    print(f"🤖 [{datetime.date.today()}] 正在调用高效模型 Gemini 2.0 Flash 生成日报...")
    data_path = os.path.expanduser("~/macro_daily/daily_data.json")
    
    if not os.path.exists(data_path):
        print("❌ 找不到数据文件")
        return

    with open(data_path, 'r') as f:
        data = json.load(f)
    
    try:
        # 截取前 10000 字符，保证请求不超载
        data_str = json.dumps(data, ensure_ascii=False)[:10000]
        report = call_gemini("你是一个资深宏观分析师，请根据数据写一份深度的日报。", data_str)
        
        output_path = os.path.expanduser("~/macro_daily/report.md")
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"✅ 【最终胜利】日报已生成！文件：{output_path}")
    except Exception as e:
        print(f"❌ 运行失败：{str(e)}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"服务器回复：{e.response.text}")

if __name__ == "__main__":
    main()
