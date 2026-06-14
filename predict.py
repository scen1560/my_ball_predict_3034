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
# 2. 智能雷達：只抓取真實賽事，徹底刪除所有假數據
# =====================================================================
def get_international_odds():
    print("🔄 正在啟動智能雷達，搜尋今日真實賽事...")
    
    if not ODDS_API_KEY:
        print("❌ 錯誤：找不到 ODDS_API_KEY！")
        return None

    # 📡 2026年6月焦點：優先尋找世界盃，然後再搵美職聯、日職等
    SPORTS_TO_TRY = [
        'soccer_fifa_world_cup',      # 世界盃
        'soccer_usa_mls',             # 美國職業聯賽
        'soccer_japan_j_league',      # 日本職業聯賽
        'soccer_conmebol_copa_america'# 美洲盃
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
                    # 成功搵到真波！
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

                    print(f"🎯 成功鎖定真實賽事：{home_team} vs {away_team} (聯賽: {sport})")
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

    # 如果搵勻成個名單都無波，直接回傳 None，絕對唔出假數據！
    print("ℹ️ 今日雷達名單內的所有聯賽均無即將開賽的數據。")
    return None

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

【真實賽事資料】：
球賽：{match_info['match_name']}
開賽時間：{match_info['match_time']}
莊家 ({match_info['bookmaker']}) 賠率：主勝 {match_info['h_odds']} | 客勝 {match_info['a_odds']} | 和局 {match_info['d_odds']}

⚠️ 嚴格核心要求：
1. 球隊近期有重大變動，請完全忽略歷史往績，將分析重心放在「球隊最新陣容磨合度」及「進攻意慾」。如果球隊名是英文，請在分析中自動翻譯為香港球迷熟悉的中文譯名。
2. 必須嚴格使用地道【香港足球術語】（例如：波膽、大細球、受讓、讓球、上/下盤、派彩快、走印、針、半全場、熱門、爆冷）。
3. 必須嚴格按照以下「8大板塊」的順序輸出，每板塊加上清晰的 Emoji 標題，文字要精煉吸睛：

1. 預計首發陣容及理由（結合新人和傷停）
2. 近期狀態與戰術對決
3. 傷停情況、交手紀錄及背景動機（強調最新戰意）
4. 投注價值推薦（對比賠率，找出最穩健的選項）
5. 風險及冷門可能性
6. 全體預測
7. 預測比分（波膽）
8. 最終總結（加入溫馨提示：若半場形勢有暗湧，可使用「派彩快」提早走印鎖定利潤）
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
# 4. 外賣仔
