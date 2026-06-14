import requests
import json
import os

# =====================================================================
# 1. 讀取保險箱密鑰
# =====================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROK_API_KEY = os.environ.get("GROK_API_KEY")
CHANNEL_ID = "@my_ball_predict_3034"

# =====================================================================
# 2. 今日賽事輸入盒（由你指定，彻底解決假賽程與被馬會封鎖問題）
# 💡 每日開賽前，你隨時可以人手入嚟 GitHub 改改下面呢幾行資料
# =====================================================================
def get_today_focus_match():
    print("🎯 正在讀取今日指定焦點賽事數據...")
    
    return {
        "match_name": "阿仙奴 vs 車路士",    # 👈 喺度改你想預測嘅真球隊
        "match_time": "凌晨 03:00",          # 👈 喺度改開波時間
        "h_odds": "1.85",                    # 👈 填馬會最新主勝賠率
        "a_odds": "3.40",                    # 👈 填客勝賠率
        "d_odds": "3.65",                    # 👈 填和局賠率
        
        # 💡 呢度直接結合埋你喺 Futbin 睇到嘅新兵數值同球隊最新變動
        "team_updates": "主隊（阿仙奴）：新買入前鋒喺 Futbin 速度 94、進攻意慾極強，今場會打正選搶攻。客隊（車路士）：後防主力傷停，防線有重大變動，默契成疑。"
    }

# =====================================================================
# 3. 呼叫 Grok AI 大腦，利用香港足球術語寫波經
# =====================================================================
def generate_report_with_grok(match_info):
    print("🧠 正在啟動 xAI Grok 大腦進行即時深度分析...")
    
    if not GROK_API_KEY:
        print("❌ 錯誤：找不到 GROK_API_KEY！")
        return None

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    
    prompt = f"""
你現在是一位精通香港馬會波經的頂級足球分析師。
請根據以下提供的【賽事資料與馬會賠率】，撰寫深度預測。

【賽事資料】：
球賽：{match_info['match_name']}
開賽時間：{match_info['match_time']}
馬會即時賠率：主勝 {match_info['h_odds']} | 客勝 {match_info['a_odds']} | 和局 {match_info['d_odds']}

【球隊最新主力變動及風格（結合 Futbin 數據）】：
{match_info['team_updates']}

⚠️ 嚴格核心要求：
1. 球隊近期有重大主力變動，請完全忽略多年前的歷史往績，主力分析最新陣容與即時戰意。
2. 必須嚴格使用地道【香港足球術語】（例如：波膽、大細球、受讓、讓球、上/下盤、派彩快、走印、針、半全場、熱門、爆冷）。
3. 必須嚴格按照以下「8大板塊」的順序輸出，每板塊加上清晰的 Emoji 標題，文字要精煉吸睛，適合 Telegram 閱讀：

1. 預計首發陣容及理由（結合新人和傷停）
2. 近期狀態與戰術對決（分析主隊新進攻線vs客隊防線）
3. 傷停情況、交手紀錄及背景動機（強調最新戰意，淡化歷史往績）
4. 投注價值推薦（對比賠率，找出最穩健的選項）
5. 風險及冷門可能性（例如：主隊新陣容默契不足的風險）
6. 全體預測
7. 預測比分（波膽）
8. 最終總結（必須加入溫馨提示：若半場形勢有暗湧，用家可自行決定使用馬會「派彩快」提早走印鎖定利潤）
"""

    payload = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"❌ Grok API 回覆錯誤：{response.text}")
    except Exception as e:
        print(f"❌ 呼叫 Grok 發生錯誤：{e}")
    return None

# =====================================================================
# 4. 外賣仔功能：發送到 Telegram Channel
# =====================================================================
