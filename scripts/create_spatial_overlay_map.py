# -*- coding: utf-8 -*-
"""
建立環境與社會資料交集的 Folium 地圖
用途：
1. 視覺化 AQI 測站與避難收容處所的空間分布
2. AQI 測站依嚴重程度分色顯示
3. 避難收容處所區分室內外圖標
4. 驗證避難所不在海中

執行：
python create_spatial_overlay_map.py --aqi "AQI_stations.csv" --shelters "避難收容處所點位檔_with_indoor.csv" --out "spatial_overlay_map.html"
"""

import argparse
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
import warnings
warnings.filterwarnings('ignore')

def robust_read_csv(path: str) -> pd.DataFrame:
    """讀取CSV檔案，嘗試多種編碼"""
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc, engine="python")
        except Exception:
            pass
    return pd.read_csv(path, engine="python")

def get_aqi_color(aqi_value: float) -> str:
    """
    根據 AQI 值決定顏色
    """
    if pd.isna(aqi_value) or aqi_value < 0:
        return 'gray'
    
    aqi = float(aqi_value)
    
    if aqi <= 50:
        return 'green'      # 良好
    elif aqi <= 100:
        return 'yellow'     # 普通
    elif aqi <= 150:
        return 'orange'     # 對敏感族群不健康
    elif aqi <= 200:
        return 'red'        # 對所有族群不健康
    elif aqi <= 300:
        return 'purple'     # 非常不健康
    else:
        return 'maroon'     # 危害

def get_aqi_level(aqi_value: float) -> str:
    """
    根據 AQI 值決定等級文字
    """
    if pd.isna(aqi_value) or aqi_value < 0:
        return '無資料'
    
    aqi = float(aqi_value)
    
    if aqi <= 50:
        return '良好'
    elif aqi <= 100:
        return '普通'
    elif aqi <= 150:
        return '對敏感族群不健康'
    elif aqi <= 200:
        return '對所有族群不健康'
    elif aqi <= 300:
        return '非常不健康'
    else:
        return '危害'

def validate_shelter_coordinates(df: pd.DataFrame) -> tuple:
    """
    驗證避難所座標是否合理
    """
    print("=== 驗證避難所座標 ===")
    
    # 檢查座標範圍
    valid_coords = df.dropna(subset=['經度', '緯度'])
    
    if len(valid_coords) == 0:
        print("❌ 沒有有效的座標資料")
        return False, []
    
    min_lon = valid_coords['經度'].min()
    max_lon = valid_coords['經度'].max()
    min_lat = valid_coords['緯度'].min()
    max_lat = valid_coords['緯度'].max()
    
    print(f"座標範圍: 經度({min_lon:.6f} ~ {max_lon:.6f}), 緯度({min_lat:.6f} ~ {max_lat:.6f})")
    
    # 檢查是否在合理範圍內 (台灣周邊)
    reasonable_range = (119 <= min_lon <= 124 and 119 <= max_lon <= 124 and 
                       21 <= min_lat <= 26 and 21 <= max_lat <= 26)
    
    if not reasonable_range:
        print("⚠️ 座標範圍可能不合理")
    
    # 檢查是否有明顯錯誤的座標
    suspicious_points = []
    
    # 檢查 (0,0) 座標
    zero_coords = valid_coords[(valid_coords['經度'] == 0) | (valid_coords['緯度'] == 0)]
    if len(zero_coords) > 0:
        print(f"⚠️ 發現 {len(zero_coords)} 個 (0,0) 座標")
        suspicious_points.extend(zero_coords['避難收容處所名稱'].tolist())
    
    # 檢查極端座標
    extreme_coords = valid_coords[
        (valid_coords['經度'] < 118) | (valid_coords['經度'] > 125) |
        (valid_coords['緯度'] < 20) | (valid_coords['緯度'] > 27)
    ]
    if len(extreme_coords) > 0:
        print(f"⚠️ 發現 {len(extreme_coords)} 個極端座標")
        suspicious_points.extend(extreme_coords['避難收容處所名稱'].tolist())
    
    if len(suspicious_points) > 0:
        print("可疑的避難所:")
        for name in suspicious_points[:10]:  # 只顯示前10個
            print(f"  {name}")
        if len(suspicious_points) > 10:
            print(f"  ... 還有 {len(suspicious_points) - 10} 個")
    
    # 總結驗證結果
    is_valid = len(suspicious_points) == 0 and reasonable_range
    
    if is_valid:
        print("✅ 避難所座標驗證通過")
    else:
        print("❌ 避難所座標驗證失敗，可能需要重新審計")
    
    return is_valid, suspicious_points

def create_spatial_overlay_map(aqi_df: pd.DataFrame, shelter_df: pd.DataFrame, output_file: str):
    """
    建立空間疊加地圖
    """
    print("=== 建立空間疊加地圖 ===")
    
    # 計算台灣中心點
    taiwan_center_lat = 23.8
    taiwan_center_lon = 120.9
    
    # 建立地圖
    m = folium.Map(
        location=[taiwan_center_lat, taiwan_center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # 建立圖層群組
    aqi_cluster = MarkerCluster(name="AQI 測站").add_to(m)
    shelter_indoor_cluster = MarkerCluster(name="室內避難收容處所").add_to(m)
    shelter_outdoor_cluster = MarkerCluster(name="室外避難收容處所").add_to(m)
    
    # 新增 AQI 測站 (圖層 A)
    print("正在新增 AQI 測站...")
    valid_aqi = aqi_df.dropna(subset=['longitude', 'latitude'])
    
    for idx, row in valid_aqi.iterrows():
        lon = float(row['longitude'])
        lat = float(row['latitude'])
        
        # 基本座標驗證
        if not (100 <= lon <= 140 and 10 <= lat <= 35):
            continue
        
        aqi_value = row.get('aqi', np.nan)
        aqi_color = get_aqi_color(aqi_value)
        aqi_level = get_aqi_level(aqi_value)
        
        # 建立彈出視窗內容
        popup_content = f"""
        <b>{row.get('sitename', '未知測站')}</b><br>
        縣市: {row.get('county', '未知')}<br>
        AQI: {int(aqi_value) if not pd.isna(aqi_value) else '無資料'}<br>
        等級: {aqi_level}<br>
        主要污染物: {row.get('pollutant', '未知')}<br>
        狀態: {row.get('status', '未知')}<br>
        PM2.5: {row.get('pm2.5', '無資料')}<br>
        更新時間: {row.get('publishtime', '未知')}
        """
        
        # 新增標記
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{row.get('sitename', '未知測站')} (AQI: {int(aqi_value) if not pd.isna(aqi_value) else 'N/A'})",
            icon=folium.Icon(color=aqi_color, icon='info-sign', prefix='fa')
        ).add_to(aqi_cluster)
    
    # 新增避難收容處所 (圖層 B)
    print("正在新增避難收容處所...")
    valid_shelters = shelter_df.dropna(subset=['經度', '緯度'])
    
    indoor_count = 0
    outdoor_count = 0
    
    for idx, row in valid_shelters.iterrows():
        lon = float(row['經度'])
        lat = float(row['緯度'])
        
        # 基本座標驗證
        if not (100 <= lon <= 140 and 10 <= lat <= 35):
            continue
        
        # 判斷室內外
        is_indoor = row.get('is_indoor', True)
        if isinstance(is_indoor, str):
            is_indoor = is_indoor.lower() == 'true'
        
        # 建立彈出視窗內容
        popup_content = f"""
        <b>{row['避難收容處所名稱']}</b><br>
        地址: {row['避難收容處所地址']}<br>
        縣市: {row['縣市及鄉鎮市區']}<br>
        所在鄉鎮: {row.get('所在鄉鎮', '未知')}<br>
        預計收容人數: {row['預計收容人數']} 人<br>
        適用災害: {row['適用災害類別']}<br>
        類型: {'室內' if is_indoor else '室外'}<br>
        適合弱者: {row['適合避難弱者安置']}<br>
        管理人: {row['管理人姓名']}<br>
        電話: {row['管理人電話']}
        """
        
        # 根據室內外設定不同圖標
        if is_indoor:
            icon_color = 'blue'
            icon_symbol = 'home'
            indoor_count += 1
            target_cluster = shelter_indoor_cluster
        else:
            icon_color = 'green'
            icon_symbol = 'tree'
            outdoor_count += 1
            target_cluster = shelter_outdoor_cluster
        
        # 新增標記
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{row['避難收容處所名稱']} ({'室內' if is_indoor else '室外'})",
            icon=folium.Icon(color=icon_color, icon=icon_symbol, prefix='fa')
        ).add_to(target_cluster)
    
    # 新增圖例
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 320px; height: 220px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
    <h4 style="margin: 0 0 10px 0; font-size: 14px; font-weight: bold;">空間品質與避難收容處所疊加圖</h4>
    
    <b style="font-size: 12px;">AQI 測站:</b><br>
    <span style="color:green; font-size: 11px;">●</span> 良好 (0-50)<br>
    <span style="color:yellow; font-size: 11px;">●</span> 普通 (51-100)<br>
    <span style="color:orange; font-size: 11px;">●</span> 對敏感族群不健康 (101-150)<br>
    <span style="color:red; font-size: 11px;">●</span> 對所有族群不健康 (151-200)<br>
    <span style="color:purple; font-size: 11px;">●</span> 非常不健康 (201-300)<br>
    <span style="color:maroon; font-size: 11px;">●</span> 危害 (300+)<br>
    
    <b style="font-size: 12px;">避難收容處所:</b><br>
    <span style="color:blue; font-size: 11px;">●</span> 室內設施<br>
    <span style="color:green; font-size: 11px;">●</span> 室外設施<br>
    
    <hr style="margin: 8px 0; border: 1px solid #ccc;">
    <small style="font-size: 10px; color: #666;">使用左上角圖層控制開關圖層</small>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 新增圖層控制
    folium.LayerControl().add_to(m)
    
    # 保存地圖
    m.save(output_file)
    
    # 顯示統計結果
    print(f"\n=== 地圖統計結果 ===")
    print(f"AQI 測站: {len(valid_aqi)} 筆")
    print(f"避難收容處所: {len(valid_shelters)} 筆")
    print(f"  室內設施: {indoor_count} 筆")
    print(f"  室外設施: {outdoor_count} 筆")
    
    # AQI 統計
    if 'aqi' in valid_aqi.columns:
        aqi_stats = valid_aqi['aqi'].describe()
        print(f"\n=== AQI 統計 ===")
        print(f"平均 AQI: {aqi_stats['mean']:.1f}")
        print(f"最高 AQI: {aqi_stats['max']:.0f}")
        print(f"最低 AQI: {aqi_stats['min']:.0f}")
        
        # AQI 等級分布
        aqi_levels = valid_aqi['aqi'].apply(get_aqi_level).value_counts()
        print(f"\n=== AQI 等級分布 ===")
        for level, count in aqi_levels.items():
            print(f"{level}: {count} 筆")
    
    print(f"\n地圖已保存至: {output_file}")
    print("請使用瀏覽器開啟檔案查看互動式地圖")
    
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aqi", dest="aqi_file", required=True, help="AQI 測站 CSV 路徑")
    ap.add_argument("--shelters", dest="shelter_file", required=True, help="避難收容處所 CSV 路徑")
    ap.add_argument("--out", dest="output_file", default="spatial_overlay_map.html", help="輸出 HTML 路徑")
    args = ap.parse_args()

    print("=== 環境與社會資料空間疊加分析 ===")
    print(f"AQI 資料: {args.aqi_file}")
    print(f"避難收容處所資料: {args.shelter_file}")
    print(f"輸出檔案: {args.output_file}")
    print()

    # 讀取 AQI 資料
    print("讀取 AQI 測站資料...")
    aqi_df = robust_read_csv(args.aqi_file)
    print(f"AQI 測站資料: {len(aqi_df)} 筆")

    # 讀取避難收容處所資料
    print("讀取避難收容處所資料...")
    shelter_df = robust_read_csv(args.shelter_file)
    print(f"避難收容處所資料: {len(shelter_df)} 筆")

    # 驗證避難所座標
    is_valid, suspicious_points = validate_shelter_coordinates(shelter_df)
    
    if not is_valid:
        print("\n⚠️ 警告: 避難所座標驗證失敗")
        print("這可能表示你的審計邏輯有問題")
        print("但仍會繼續建立地圖以供檢查")
    
    # 建立空間疊加地圖
    print("\n開始建立空間疊加地圖...")
    create_spatial_overlay_map(aqi_df, shelter_df, args.output_file)
    
    print(f"\n=== 分析完成 ===")
    print(f"✅ 空間疊加地圖已建立")
    print(f"✅ AQI 測站依嚴重程度分色顯示")
    print(f"✅ 避難收容處所區分室內外圖標")
    print(f"✅ 座標驗證: {'通過' if is_valid else '失敗'}")
    print(f"📌 輸出檔案: {args.output_file}")

if __name__ == "__main__":
    main()
