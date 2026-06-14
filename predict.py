import requests
import json
import os
from datetime import datetime, timedelta

# =====================================================================
# 1. 讀取保險箱密鑰
# =====================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROK_API_KEY = os.environ.get("GROK_API_KEY")
CHANNEL_ID = "@my_ball_predict_3034"

# =====================================================================
# 2. 自動抓取馬會實時 JSON 並篩選【今日07:00 - 翌日07:00】的比賽
# =====================================================================
def get_hkjc_target_odds():
    print("🔄 正在從馬會 API 抓取賽事並進行【今日07:00至翌日07:00】時間篩選...")
    url = "https://bet.hkjc.com/contentserver/jcbw/api/v1/odds/had"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 計算香港時間的今日 07:00 與翌日 07:00
    # GitHub 伺服器通常是 UTC 時間，香港時間 = UTC + 8 小時
    now_hk = datetime.utcnow() + timedelta(hours=8)
    
    # 定義今日 07:00 
    today_0700 = now_hk.replace(hour=7, minute=0, second=0, microsecond=0)
    # 如果執行時還沒到早上 7 點（例如 6 點行），今日起點就要減一日
    if now_hk < today_0700:
        today_0700 = today_0700 - timedelta(days=1)
        
    tomorrow_0700 = today_0700 + timedelta(days=1)
    
    print(f"⏰ 目標賽事開波時間必須在：\n[由] {today_0700.strftime('%Y-%m-%d %H:%M')}\n[至] {tomorrow_0700.strftime('%Y-%m-%d %H:%M')} 之間")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            match_list = response.json().get("matches", [])
            
            # 遍歷馬會所有比賽，搵出符合時間範圍嘅第一場焦點賽事
            for match in match_list:
                # 馬會的 matchTime 範例: "2026-06-15T20:45:00+08:00"
                match_time_str = match.get("matchTime", "")
                if not match_time_str:
                    continue
                
                # 轉換成 Python 時間物件進行比較 (切走時區部分簡化處理)
                match_time_clean = match_time_str.split("+")[0].split(".")[0]
                match_time = datetime.strptime(match_time_clean, "%Y-%m-%dT%H:%M:%S")
                
                # ⚡ 核心篩選條件
                if today_0700 <= match_time < tomorrow_0700:
                    home_team = match.get("homeTeam", {}).get("teamNameCH", "主隊")
                    away_team = match.get("awayTeam", {}).get("teamNameCH", "客隊")
                    had_odds = match.get("hadOdds", {})
                    
                    print(f"🎯 成功鎖定目標賽事：{home_team} vs {away_team} (開賽時間: {match_time_clean})")
                    return {
                        "match_name": f"{home_team} vs {away_team}",
                        "match_time": match_time_clean,
                        "h_odds": had_odds.get("h", "0.00"), 
                        "a_odds": had_odds.get("a", "0.00"), 
                        "d_odds": had_odds.get("d", "0.00")
                    }
            print("ℹ️ 馬會目前沒有賽事符合【今日07:00至翌日07:00】時間段。")
    except Exception as e:
        print(f"⚠️ 馬會 API 連線異常 ({e})")
    
    print("💡 啟動備用焦點賽事數據頂住。")
    return {"match_name": "皇家馬德里 vs 巴塞隆拿", "match_time": "今日焦點時間", "h_odds": "1.95", "a_odds": "3.20",
