import requests
import os
from datetime import datetime, timedelta

# ====================== 設定 ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@my_ball_predict_3034")
GROK_API_KEY = os.getenv("GROK_API_KEY")

print(f"🔑 BOT_TOKEN: {'已載入' if BOT_TOKEN else '❌ 未載入'}")
print(f"🔑 GROK_API_KEY: {'已載入' if GROK_API_KEY else '❌ 未載入'}")
print(f"📢 CHANNEL_ID: {CHANNEL_ID}")

# ====================== 球隊中文映射 ======================
team_name_map = {
    "Ivory Coast": "科特迪瓦", "Ecuador": "厄瓜多爾",
    "Netherlands": "荷蘭", "Japan": "日本",
    "Germany": "德國", "Curaçao": "庫拉索",
    "Argentina": "阿根廷", "France": "法國",
    "Brazil": "巴西", "Spain": "西班牙",
    "England": "英格蘭", "Unknown": "未知"
}

def translate_team_name(name):
    return team_name_map.get(name, name)

# ====================== 抓取今天早上7:00 ~ 明天早上7:00 的比賽 ======================
def get_today_worldcup_matches():
    print("🔄 抓取香港時間 07:00 至 明日07:00 的世界盃賽程...")
    url = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        
        now = datetime.now()
        today_7am = now.replace(hour=7, minute=0, second=0, microsecond=0)
        tomorrow_7am = today_7am + timedelta(days=1)
        
        matches = []
        for match in data.get("matches", []):
            try:
                match_date_str = match.get("date", "")
                match_date = datetime.strptime(match_date_str, "%Y-%m-%d")
                if today_7am.date() <= match_date.date() <= tomorrow_7am.date():
                    matches.append({
                        "home": match.get("team1", "未知"),
                        "away": match.get("team2", "未知"),
                        "date": match_date_str,
                        "time": match.get("time", "待定")
                    })
            except:
                continue
                
        if matches:
            print(f"✅ 找到 {len(matches)} 場比賽")
            return matches[:2]  # 最多2場
    except Exception as e:
        print(f"⚠️ 賽程抓取失敗: {e}")
    
    # 備用測試比賽
    return [{"home": "Germany", "away": "Japan"}]

# ====================== 用 Grok 生成 8 大板塊 ======================
def generate_with_grok(home_en, away_en):
    home = translate_team_name(home_en)
    away = translate_team_name(away_en)
    
    prompt = f"""你是一位專業香港足球分析員，用香港足球術語（波膽、大細球、受讓、派彩快）為世界盃比賽寫完整8大板塊：

比賽：{home} vs {away}

請嚴格按以下格式輸出：
1️⃣ 預計首發陣容及理由（結合新人和傷停）
2️⃣ 近期狀態與戰術對決
3️⃣ 傷停情況、交手紀錄及背景動機
4️⃣ 投注價值推薦
5️⃣ 風險及冷門可能性
6️⃣ 全體預測
7️⃣ 預測比分（波膽）
8️⃣ 最終總結（加入派彩快提示）

要求：自然專業、強調最新戰意和新陣容，淡化歷史往績。"""

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "grok-4.3",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1200
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=40)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        print("✅ Grok 成功生成預測")
        return content
    except Exception as e:
        print(f"⚠️ Grok API 失敗: {e}")
        # 後備模板
        return f'''⚽️ **【世界盃焦點：{home} vs {away}】**

📊 **馬會即時賠率**：主勝 2.05 | 和 3.40 | 客勝 3.30

**1️⃣ 預計首發陣容及理由**
{home}：4-3-3，新星前鋒即刻正選。

**2️⃣ 近期狀態與戰術對決**
{home}新進攻線火力強，對住{away}防線有優勢。

**3️⃣ 傷停、背景動機**
最新戰意極高，歷史往績參考價值低。

**4️⃣ 投注價值推薦**
推薦 **受讓** 或 **大細球 2.5** 最穩健。

**7️⃣ 預測比分（波膽）**
**2-1**（{home}勝）

**8️⃣ 最終總結**
看好{home}小勝，建議小注**受讓**或**大球**。中場用**派彩快**再調整！理性投注，娛樂為主！'''

# ====================== 發送到 Telegram ======================
def send_to_telegram(text):
    print("🚀 準備發送到 Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram 回應:", response.json())
        if response.status_code == 200:
            print("🎉 成功發送到頻道！")
        else:
            print("❌ 發送失敗")
    except Exception as e:
        print("❌ 發送異常:", str(e))

# ====================== 主程式 ======================
if __name__ == "__main__":
    print("🚀 世界盃預測工具啟動...")
    matches = get_today_worldcup_matches()
    
    for m in matches:
        print(f"📝 正在分析：{m['home']} vs {m['away']}")
        report = generate_with_grok(m["home"], m["away"])
        send_to_telegram(report)
        print(f"✅ 已處理：{translate_team_name(m['home'])} vs {translate_team_name(m['away'])}\n")
