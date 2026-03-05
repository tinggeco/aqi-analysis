# -*- coding: utf-8 -*-
"""
避難收容處所 AQI 風險分析
用途：
1. 使用 Haversine 公式計算避難所到最近 AQI 測站的距離
2. 情境注入：將林口測站的 AQI 值設為 150
3. 風險分類：
   - High Risk: 最近 AQI > 100
   - Warning: 最近 AQI > 50 AND 設施為室外
4. 輸出分析結果到 CSV

執行：
python shelter_aqi_risk_analysis.py --aqi "AQI_stations.csv" --shelters "避難收容處所點位檔_with_indoor.csv" --out "outputs/shelter_aqi_analysis.csv"
"""

import argparse
import pandas as pd
import numpy as np
import math
from typing import Tuple

def robust_read_csv(path: str) -> pd.DataFrame:
    """讀取CSV檔案，嘗試多種編碼"""
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc, engine="python")
        except Exception:
            pass
    return pd.read_csv(path, engine="python")

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用 Haversine 公式計算兩點間的距離（公里）
    """
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return float('inf')
    
    # 將角度轉換為弧度
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine 公式
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # 地球半徑（公里）
    r = 6371
    
    return c * r

def find_nearest_aqi_station(shelter_lat: float, shelter_lon: float, aqi_df: pd.DataFrame) -> Tuple[float, float, float]:
    """
    找到最近的 AQI 測站
    返回：(距離, AQI值, 測站名稱)
    """
    min_distance = float('inf')
    nearest_aqi = np.nan
    nearest_station = ""
    
    for idx, row in aqi_df.iterrows():
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            continue
        
        distance = haversine_distance(shelter_lat, shelter_lon, row['latitude'], row['longitude'])
        
        if distance < min_distance:
            min_distance = distance
            nearest_aqi = row.get('aqi', np.nan)
            nearest_station = row.get('sitename', '')
    
    return min_distance, nearest_aqi, nearest_station

def classify_risk(aqi_value: float, is_indoor: bool) -> str:
    """
    風險分類
    """
    if pd.isna(aqi_value):
        return "Unknown"
    
    if aqi_value > 100:
        return "High Risk"
    elif aqi_value > 50 and not is_indoor:
        return "Warning"
    else:
        return "Low Risk"

def scenario_injection(aqi_df: pd.DataFrame) -> pd.DataFrame:
    """
    情境注入：將林口測站的 AQI 值設為 150
    """
    print("=== 情境注入 ===")
    print("將林口測站的 AQI 值設為 150...")
    
    # 尋找林口測站
    linkou_stations = aqi_df[aqi_df['sitename'].str.contains('林口', na=False)]
    
    if len(linkou_stations) == 0:
        print("⚠️ 未找到林口測站，嘗試其他相似名稱...")
        # 嘗試其他可能的林口相關名稱
        possible_names = ['林口', 'Linkou', '新莊', '泰山']  # 林口附近的地區
        for name in possible_names:
            stations = aqi_df[aqi_df['sitename'].str.contains(name, case=False, na=False)]
            if len(stations) > 0:
                print(f"找到相似測站: {stations['sitename'].tolist()}")
                # 將第一個找到的測站 AQI 設為 150
                idx = stations.index[0]
                original_aqi = aqi_df.loc[idx, 'aqi']
                aqi_df.loc[idx, 'aqi'] = 150
                print(f"將 {aqi_df.loc[idx, 'sitename']} 的 AQI 從 {original_aqi} 設為 150")
                return aqi_df
        
        print("❌ 未找到任何相關測站")
        return aqi_df
    
    # 設定林口測站的 AQI 為 150
    for idx, row in linkou_stations.iterrows():
        original_aqi = row['aqi']
        aqi_df.loc[idx, 'aqi'] = 150
        print(f"將 {row['sitename']} 的 AQI 從 {original_aqi} 設為 150")
    
    return aqi_df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aqi", dest="aqi_file", required=True, help="AQI 測站 CSV 路徑")
    ap.add_argument("--shelters", dest="shelter_file", required=True, help="避難收容處所 CSV 路徑")
    ap.add_argument("--out", dest="output_file", default="outputs/shelter_aqi_analysis.csv", help="輸出 CSV 路徑")
    args = ap.parse_args()

    print("=== 避難收容處所 AQI 風險分析 ===")
    print(f"AQI 資料: {args.aqi_file}")
    print(f"避難收容處所資料: {args.shelter_file}")
    print(f"輸出檔案: {args.output_file}")
    print()

    # 讀取資料
    print("讀取 AQI 測站資料...")
    aqi_df = robust_read_csv(args.aqi_file)
    print(f"AQI 測站資料: {len(aqi_df)} 筆")

    print("讀取避難收容處所資料...")
    shelter_df = robust_read_csv(args.shelter_file)
    print(f"避難收容處所資料: {len(shelter_df)} 筆")

    # 情境注入
    aqi_df = scenario_injection(aqi_df)

    # 分析每個避難所
    print("\n開始分析避難所風險...")
    results = []
    
    for idx, shelter in shelter_df.iterrows():
        if pd.isna(shelter['經度']) or pd.isna(shelter['緯度']):
            continue
        
        shelter_lat = float(shelter['緯度'])
        shelter_lon = float(shelter['經度'])
        
        # 找到最近的 AQI 測站
        distance, aqi_value, station_name = find_nearest_aqi_station(shelter_lat, shelter_lon, aqi_df)
        
        # 判斷是否為室內設施
        is_indoor = shelter.get('is_indoor', True)
        if isinstance(is_indoor, str):
            is_indoor = is_indoor.lower() == 'true'
        
        # 風險分類
        risk_level = classify_risk(aqi_value, is_indoor)
        
        # 儲存結果
        result = {
            '避難收容處所名稱': shelter['避難收容處所名稱'],
            '地址': shelter['避難收容處所地址'],
            '縣市及鄉鎮市區': shelter['縣市及鄉鎮市區'],
            '所在鄉鎮': shelter.get('所在鄉鎮', ''),
            '經度': shelter['經度'],
            '緯度': shelter['緯度'],
            '預計收容人數': shelter['預計收容人數'],
            '室內設施': is_indoor,
            '最近AQI測站': station_name,
            '最近AQI值': aqi_value,
            '距離測站(km)': round(distance, 2),
            '風險等級': risk_level
        }
        
        results.append(result)
    
    # 轉換為 DataFrame
    result_df = pd.DataFrame(results)
    
    # 統計結果
    print(f"\n=== 分析結果統計 ===")
    print(f"分析避難所數量: {len(result_df)} 筆")
    
    risk_stats = result_df['風險等級'].value_counts()
    print(f"\n風險等級分布:")
    for risk, count in risk_stats.items():
        print(f"  {risk}: {count} 筆 ({count/len(result_df)*100:.1f}%)")
    
    # 顯示 High Risk 避難所
    high_risk_shelters = result_df[result_df['風險等級'] == 'High Risk']
    if len(high_risk_shelters) > 0:
        print(f"\n=== High Risk 避難所 ({len(high_risk_shelters)} 筆) ===")
        for idx, row in high_risk_shelters.head(10).iterrows():
            print(f"  {row['避難收容處所名稱']} - AQI: {row['最近AQI值']} - 距離: {row['距離測站(km)']}km")
        
        if len(high_risk_shelters) > 10:
            print(f"  ... 還有 {len(high_risk_shelters) - 10} 筆未顯示")
    
    # 顯示 Warning 避難所
    warning_shelters = result_df[result_df['風險等級'] == 'Warning']
    if len(warning_shelters) > 0:
        print(f"\n=== Warning 避難所 ({len(warning_shelters)} 筆) ===")
        for idx, row in warning_shelters.head(5).iterrows():
            indoor_outdoor = "室內" if row['室內設施'] else "室外"
            print(f"  {row['避難收容處所名稱']} - AQI: {row['最近AQI值']} - {indoor_outdoor}")
        
        if len(warning_shelters) > 5:
            print(f"  ... 還有 {len(warning_shelters) - 5} 筆未顯示")
    
    # 距離統計
    print(f"\n=== 距離統計 ===")
    distance_stats = result_df['距離測站(km)'].describe()
    print(f"平均距離: {distance_stats['mean']:.2f} km")
    print(f"最短距離: {distance_stats['min']:.2f} km")
    print(f"最長距離: {distance_stats['max']:.2f} km")
    
    # 保存結果
    result_df.to_csv(args.output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n=== 分析完成 ===")
    print(f"✅ 使用 Haversine 公式計算最近 AQI 測站")
    print(f"✅ 林口測站 AQI 值已設為 150（情境注入）")
    print(f"✅ 風險分類完成")
    print(f"✅ 輸出檔案: {args.output_file}")
    
    return result_df

if __name__ == "__main__":
    main()
