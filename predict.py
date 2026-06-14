import requests
import json
import os

# =====================================================================
# 1. 讀取保險箱密鑰
# =====================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # <--- 讀取 Gemini 鎖匙
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHANNEL_ID = "@my_ball_predict_3034"

# =====================================================================
# 2. 智能雷達：只抓取真實賽事
# =====================================================================
def get_international_odds():
    print("🔄 正在啟動智能雷達，搜尋今日真實賽事...")
    
    if not ODDS_API_KEY:
        print("❌ 錯誤：找不到 ODDS_API_KEY！")
        return None

    # 📡 聯賽搜尋名單
    SPORTS_TO_TRY = [
        'soccer_fifa_world_cup',       # 世界盃
        'soccer_conmebol_copa_america',# 美洲盃
        'soccer_usa_mls',              # 美職聯
        'soccer_japan_j_league',       # 日職聯
        'soccer_epl'                   # 英超
    ]
    
    for sport in SPORTS_TO_TRY:
        print(f"🔍 正在尋找聯賽：{sport} ...")
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                match_list = response.json()
                if match_list and len(match_list) > 0:
                    match = match_list[0]
                    home_team = match.get("home_team", "主隊")
                    away_team = match.get("away_team", "客隊")
                    start_time = match.get("commence_time", "即將開賽")
                    
                    bookmaker = match['bookmakers'][0]
                    outcomes = bookmaker['markets'][0]['outcomes']
                    
                    h_odds, d_odds, a_odds = "0.00", "0.00", "0.00"
                    for outcome in outcomes:
                        if outcome['name'] == home_team: h_odds = str(outcome['price'])
                        elif outcome['name'] == away_team: a_odds = str(outcome['price'])
                        elif outcome['name'] == 'Draw': d_odds = str(outcome['price'])

                    print(f"🎯 成功鎖定真實賽事：{home_team} vs {away_team}")
                    return {
                        "match_name": f"{home_team} vs {away_team}",
                        "match_time": start_time,
                        "h_odds": h_odds,
                        "a_odds": a_odds,
                        "d_odds": d_odds,
                        "bookmaker": bookmaker['title']
                    }
        except Exception as e:
            print(f"⚠️ 嘗試 {sport} 時發生錯誤：{e}")
            continue 

    print("ℹ️ 今日雷達名單內的所有聯賽均無即將開賽的數據。")
    return None

# =====================================================================
# 3. 呼叫 最新 Gemini 3.5 Flash 大腦
# =====================================================================
def generate_report_with_gemini(match_info):
    if not match_info:
        return None
        
    print("🧠 正在啟動 Gemini 3.5 Flash 大腦進行即時深度分析...")
    
    if not GEMINI_API_KEY:
        print("❌ 錯誤：找不到 GEMINI_API_KEY！")
        return None

    # 使用最新的 gemini-3.5-flash 模型 REST 端點
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""你現在是一位精通香港馬會波經的頂級足球分析師。
請根據以下提供的【真實賽事資料與國際莊家賠率】，撰寫今日的深度預測。

【真實賽事資料】：
球賽：{match_info['match_name']}
開賽時間：{match_info['match_time']}
莊家 ({match_info['bookmaker']}) 賠率：主勝 {match_info['h_odds']} | 客勝 {match_info['a_odds']} | 和局 {match_info['d_odds']}

⚠️ 【極度重要警告】：
你必須【絕對忠於】上方提供的【真實賽事資料】！
千萬不要憑空捏造對賽球隊，也不要拿歷史經典戰役當作今日賽事。我給你什麼球隊，你就只能分析什麼！
如果球隊名是英文，請自動翻譯為香港球迷熟悉的中文譯名。

⚠️ 嚴格核心要求：
1. 忽略歷史往績，重心放在「球隊最新陣容磨合度」及「進攻意慾」。
2. 必須嚴格使用地道【香港足球術語】（波膽、大細球、受讓、讓球、上/下盤、派彩快、走印、針、半全場）。
3. 必須嚴格按照以下「8大板塊」的順序輸出，每板塊加上 Emoji 標題，文字精煉：

1. 預計首發陣容及理由（結合新人和傷停）
2. 近期狀態與戰術對決
3. 傷停情況、交手紀錄及背景動機（強調最新戰意）
4. 投注價值推薦（對比賠率，找出最穩健的選項）
5. 風險及冷門可能性
6. 全體預測
7. 預測比分（波膽）
8. 最終總結（加入溫馨提示：若半場形勢有暗湧，可使用「派彩快」提早走印鎖定利潤）
"""

    # 配合 Gemini API 的 JSON 格式
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3  # 低溫設定，防老作發夢
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"❌ Gemini API 錯誤：{response.text}")
    except Exception as e:
        print(f"❌ 呼叫 Gemini 發生錯誤：{e}")
    return None

# =====================================================================
# 4. 外賣仔出 Post
# =====================================================================
def send_to_telegram(text):
    if not text:
        return
    print("🚀 正在將真實賽事 AI 預測發送到 Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        print("🎉【真實賽事全自動化完成！】預測已成功出 Post！")
    else:
        print(f"❌ Telegram 發送失敗：{res.text}")

# =====================================================================
# 5. 主程式執行
# =====================================================================
if __name__ == "__main__":
    data = get_international_odds()
    if data:
        report = generate_report_with_gemini(data)
        send_to_telegram(report)
    else:
        print("⏸️ 今日雷達找不到真實賽事。為保證準確，今日提早收工不出 Post。")
