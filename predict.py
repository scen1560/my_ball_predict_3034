import requests
import os
from datetime import datetime

# ====================== 設定 ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@my_ball_predict_3034")
GROK_API_KEY = os.getenv("GROK_API_KEY")

print("🚀 工具啟動中...")

# ====================== 球隊中文映射 ======================
team_name_map = {
    "Germany": "德國", "Japan": "日本",
    "Ivory Coast": "科特迪瓦", "Ecuador": "厄瓜多爾",
    "Unknown": "未知"
}

def translate_team_name(name):
    return team_name_map.get(name, name)

# ====================== Grok 生成 8 大板塊 ======================
def generate_with_grok(home_en, away_en):
    home = translate_team_name(home_en)
    away = translate_team_name(away_en)
    
    prompt = f"""你是一位專業香港足球分析員，用香港足球術語（波膽、大細球、受讓、派彩快）為以下世界盃比賽寫完整 8 大板塊預測。

比賽：{home} vs {away}

請嚴格按照以下格式輸出：
1️⃣ 預計首發陣容及理由（結合新人和傷停）
2️⃣ 近期狀態與戰術對決
3️⃣ 傷停情況、交手紀錄及背景動機
4️⃣ 投注價值推薦
5️⃣ 風險及冷門可能性
6️⃣ 全體預測
7️⃣ 預測比分（波膽）
8️⃣ 最終總結（加入派彩快提示）

要求：內容自然、強調最新戰意和新陣容，淡化歷史往績。"""

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
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            print("✅ Grok API 成功生成內容")
            return content
    except Exception as e:
        print(f"⚠️ Grok API 失敗: {e}")
    
    # 後備模板
    return f"""⚽️ **【世界盃焦點：{home} vs {away}】**

📊 **馬會即時賠率**：主勝 2.05 | 和 3.40 | 客勝 3.30

**1️⃣ 預計首發陣容及理由**
{home}：4-3-3，新星前鋒即刻正選。

**8️⃣ 最終總結**
看好{home}小勝，建議小注**受讓**或**大球**。中場用**派彩快**調整！"""

# ====================== 發送 ======================
def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram 回應:", response.json())
    except Exception as e:
        print("發送失敗:", e)

# ====================== 主程式 ======================
if __name__ == "__main__":
    matches = [{"home": "Germany", "away": "Japan"}]
    for m in matches:
        report = generate_with_grok(m["home"], m["away"])
        send_to_telegram(report)
        print("✅ 處理完成")
