# -*- coding: utf-8 -*-
# 引入 curl_cffi 完美偽裝 Chrome 瀏覽器指紋，直接擊破馬會 WAF 防火牆
from curl_cffi import requests
import json
import pandas as pd
from datetime import datetime

# ==================== 【1. 核心設定與 Headers 鎖匙】 ====================
API_URL = "https://info.cld.hkjc.com/graphql/base/"

HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://bet.hkjc.com",
    "referer": "https://bet.hkjc.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
}

# ==================== 【2. 數據中心 - 依據最新真實馬會欄位對接】 ====================
def fetch_hkjc_data():
    print("⚽ 正在啟動 curl_cffi 模擬真・Chrome 瀏覽器讀取馬會全新 API...")
    
    # 壓縮成單行字串，100% 避開語法審查與格式雷區
    graphql_payload = {
        "query": "query allMatchList { matches: matchList { id frontEndId matchDate kickOffTime status homeTeam { name_ch } awayTeam { name_ch } tournament { name_ch } runningResult { homeScore awayScore corner } odds { had { h d a } hil { wording high { o } low { o } } crs { h10 h20 h21 d00 d11 a01 a12 } } } }"
    }
    
    try:
        # impersonate="chrome" 自動模擬 HTTP/2 與 TLS 指紋，破解 400 防爬蟲
        response = requests.post(
            API_URL, 
            headers=HEADERS, 
            json=graphql_payload, 
            timeout=15, 
            impersonate="chrome"
        )
        
        if response.status_code == 200:
            raw_json = response.json()
            matches = raw_json.get("data", {}).get("matches", []) or []
            print(f"✅ 【破防成功】成功獲取數據！共抓取到 {len(matches)} 場比賽。")
            return matches
        else:
            print(f"❌ 馬會拒絕訪問，狀態碼: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 連線異常: {e}")
        return None

# ==================== 【3. 數據處理 - 轉換為 Pandas DataFrame】 ====================
def process_data_to_dataframe(matches):
    if not matches:
        print("⚠️ 沒有數據可供處理。")
        return pd.DataFrame()
        
    processed_list = []
    
    for match in matches:
        base_info = {
            '比賽ID': match.get('id'),
            '前端ID': match.get('frontEndId'),
            '比賽日期': match.get('matchDate'),
            '開賽時間': match.get('kickOffTime'),
            '聯賽': match.get('tournament', {}).get('name_ch', '未知聯賽'),
            '主隊': match.get('homeTeam', {}).get('name_ch', '未知主隊'),
            '客隊': match.get('awayTeam', {}).get('name_ch', '未知客隊'),
            '狀態': match.get('status'),
            '目前比數': f"{match.get('runningResult', {}).get('homeScore', 0)}-{match.get('runningResult', {}).get('awayScore', 0)}" if match.get('runningResult') else "未開賽"
        }
        
        odds_node = match.get('odds', {})
        if odds_node:
            # 1. 獨贏 (HAD)
            had = odds_node.get('had', {})
            if had:
                base_info['HAD_主勝'] = had.get('h')
                base_info['HAD_和局'] = had.get('d')
                base_info['HAD_客勝'] = had.get('a')
                
            # 2. 大細 (HIL)
            hil = odds_node.get('hil', {})
            if hil:
                base_info['HIL_球頭'] = hil.get('wording')
                base_info['HIL_大'] = hil.get('high', {}).get('o')
                base_info['HIL_細'] = hil.get('low', {}).get('o')
                
            # 3. 波膽精選 (CRS)
            crs = odds_node.get('crs', {})
            if crs:
                base_info['CRS_1:0'] = crs.get('h10')
                base_info['CRS_2:0'] = crs.get('h20')
                base_info['CRS_2:1'] = crs.get('h21')
                base_info['CRS_0:0'] = crs.get('d00')
                base_info['CRS_1:1'] = crs.get('d11')
                base_info['CRS_0:1'] = crs.get('a01')
                base_info['CRS_1:2'] = crs.get('a12')

        processed_list.append(base_info)
        
    df = pd.DataFrame(processed_list)
    print("📊 數據已成功清洗並轉換為 DataFrame 格式。")
    return df

# ==================== 【4. 主程序入口】 ====================
if __name__ == "__main__":
    # 步驟 1：抓取最新馬會數據
    match_data = fetch_hkjc_data()
    
    if match_data:
        # 步驟 2：清洗並轉換成表格
        df = process_data_to_dataframe(match_data)
        
        # 步驟 3：數據預覽
        print("\n--- 數據預覽 ---")
        print(df.head(3))
        
        # 步驟 4：儲存至 CSV 檔案 (加入 Excel 兼容的 utf-8-sig 編碼，防止中文亂碼)
        output_filename = 'hkjc_football_realtime_data.csv'
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n🎉【大功告成】最新實時賠率數據已成功保存至：{output_filename}")
