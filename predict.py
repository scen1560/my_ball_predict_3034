import requests
import json
import os

# =====================================================================
# 1. 讀取保險箱密鑰
# =====================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROK_API_KEY = os.environ.get("GROK_API_KEY")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHANNEL_ID = "@my_ball_predict_3034"

# =====================================================================
# 2. 自動從 The Odds API 抓取焦點賽事與國際賠率
# =====================================================================
def get_international_odds():
    print("🔄 正在從 The Odds API 抓取即將開賽的焦點大戰...")
    
    if not ODDS_API_KEY:
        print("❌ 錯誤：找不到 ODDS_API_KEY！")
        return None

    # 優先抓取 2026 世界盃賽事 (可隨時改為 soccer_epl 英超等)
    SPORT = 'soccer_fifa_world_cup' 
    REGIONS = 'eu' # 歐洲大莊家數據
    MARKETS = 'h2h' # 主客和賠率
    
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            match_list = response.json()
            if match_list and len(match_list) > 0:
                match = match_list[0]
                home_team = match.get("home_team", "主隊")
                away_team = match.get("away_team", "客隊")
                start_time = match.get("commence_time", "即將開賽")
                
                # 提取第一間大莊家賠率
                bookmaker = match['bookmakers'][0]
                outcomes = bookmaker['markets'][0]['outcomes']
                
                h_odds, d_odds, a_odds = "0.00", "0.00", "0.00"
                for outcome in outcomes:
                    if outcome['name'] == home_team:
                        h_odds = str(outcome['price'])
                    elif outcome['name'] == away_team:
                        a_odds = str(outcome['price'])
                    elif outcome['name'] == 'Draw':
                        d_odds = str(outcome['price'])

                print(f"🎯 成功鎖定賽事：{home_team} vs {away_team}")
                return {
                    "match_name": f"{home_team} vs {away_team}",
                    "match_time": start_time,
                    "h_odds": h_odds,
                    "a_odds": a_odds,
                    "d_odds": d_odds,
                    "bookmaker": bookmaker['title']
                }
            else:
                print("ℹ️ 目前該聯賽沒有即將開賽的賽事，啟動備用焦點戰數據。")
        else:
            print(f"❌ The Odds API 錯誤：{response.text}")
    except Exception as e:
        print(f"⚠️ 網絡連線異常：{e}")
    
    # 備用數據，確保程式日日都有波出
    return {
        "match_name": "阿仙奴 vs 車路士", "match_time": "今晚深夜",
        "h_odds": "2.10", "a_odds": "3.20", "d_odds": "3.40", "bookmaker": "備用大莊家"
    }

# =====================================================================
# 3. 呼叫 Grok AI 大腦寫地道波經
# =====================================================================
def generate_report_with_grok(match_info):
    if not match_info:
        return None
        
    print("🧠 正在啟動 xAI Grok 大腦進行即時深度分析...")
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    
    prompt = f"""
你現在是一位精通香港馬會波經的頂級足球分析師。
請根據以下提供的【國際莊家即時賠率】，撰寫今日的深度預測。

【賽事資料】：
球賽：{match_info['match_name']}
開賽時間：{match_info['match_time']}
國際莊家 ({match_info['bookmaker']}) 賠率：主勝 {match_info['h_odds']} | 客勝 {match_info['a_odds']} | 和局 {match_info['d_odds']}

⚠️ 嚴格核心要求：
1. 球隊近期有重大變動，請完全忽略歷史往績，將分析重心放在「球隊最新陣容磨合度」及「進攻意慾」。
2. 必須嚴格使用地道【香港足球術語】（例如：波膽、大細球、受讓、讓球、上/下盤、派彩快、走印、針、半全場、熱門、爆冷）。
3. 必須嚴格按照以下「8大板塊」的順序輸出，每板塊加上清晰的 Emoji 標題，文字要精煉吸睛，適合 Telegram 閱讀：

1. 預計首發陣容及理由（結合新人和傷停）
2. 近期狀態與戰術對決（分析主隊新進攻線vs客隊防線）
3. 傷停情況、交手紀錄及背景動機（強調最新戰意，淡化歷史往績）
4. 投注價值推薦（對比賠率，找出最穩健的選項）
5. 風險及冷門可能性
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
            print(f"❌ Grok API 錯誤：{response.text}")
    except Exception as e:
        print(f"❌ 呼叫 Grok 發生錯誤：{e}")
    return None

# =====================================================================
# 4. 外賣仔出 Post
# =====================================================================
def send_to_telegram(text):
    if not text:
        return
    print("🚀 正在將 AI 預測發送到 Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        print("🎉【100% 全自動化完成！】預測已成功出 Post！")
    else:
        print(f"❌ Telegram 發送失敗：{res.text}")

if __name__ == "__main__":
    data = get_international_odds()
    report = generate_report_with_grok(data)
    send_to_telegram(report)
