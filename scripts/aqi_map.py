#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣即時空氣品質指標 (AQI) 地圖視覺化程式
串接環境部 API 獲取全台測站數據並使用 Folium 在地圖上標示
"""

import os
import requests
import folium
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
import math

# 載入環境變數
load_dotenv()

class AQIMapVisualizer:
    def __init__(self):
        self.api_key = os.getenv('MOENV_API_KEY')
        if not self.api_key:
            raise ValueError("請在 .env 檔案中設定 MOENV_API_KEY")
        
        self.api_url = "https://data.moenv.gov.tw/api/v2/AQX_P_432"
        self.data = None
        # 台北車站座標
        self.taipei_station_lat = 25.0478
        self.taipei_station_lon = 121.5170
        
    def fetch_aqi_data(self):
        """獲取環境部 AQI API 數據"""
        print("正在獲取空氣品質數據...")
        
        params = {
            'api_key': self.api_key,
            'limit': 1000,
            'sort': 'ImportDate desc',
            'format': 'json'
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            self.data = response.json()
            print(f"成功獲取 {len(self.data)} 筆測站數據")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"API 請求失敗: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"JSON 解析失敗: {e}")
            return False
    
    def calculate_distance_to_taipei(self, lat, lon):
        """計算測站到台北車站的距離（公里）"""
        # 使用 Haversine 公式計算兩點間距離
        R = 6371  # 地球半徑（公里）
        
        lat1, lon1 = math.radians(lat), math.radians(lon)
        lat2, lon2 = math.radians(self.taipei_station_lat), math.radians(self.taipei_station_lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        return round(distance, 2)
    
    def process_data(self):
        """處理和清理數據"""
        if not self.data:
            return None
            
        processed_data = []
        for record in self.data:
            try:
                # 提取必要欄位 (使用英文欄位名稱)
                station_data = {
                    'site_name': record.get('sitename', ''),
                    'county': record.get('county', ''),
                    'aqi': record.get('aqi', 0),
                    'pollutant': record.get('pollutant', ''),
                    'status': record.get('status', ''),
                    'latitude': float(record.get('latitude', 0)),
                    'longitude': float(record.get('longitude', 0)),
                    'pm25': record.get('pm2.5', ''),
                    'pm10': record.get('pm10', ''),
                    'o3': record.get('o3', ''),
                    'no2': record.get('no2', ''),
                    'so2': record.get('so2', ''),
                    'co': record.get('co', ''),
                    'wind_speed': record.get('wind_speed', ''),
                    'wind_direction': record.get('wind_direc', ''),
                    'publish_time': record.get('publishtime', '')
                }
                
                # 計算到台北車站的距離
                station_data['distance_to_taipei'] = self.calculate_distance_to_taipei(
                    station_data['latitude'], station_data['longitude']
                )
                
                # 過濾掉無效座標的測站
                if station_data['latitude'] != 0 and station_data['longitude'] != 0:
                    processed_data.append(station_data)
                    
            except (ValueError, TypeError) as e:
                print(f"處理測站 {record.get('sitename', 'Unknown')} 數據時發生錯誤: {e}")
                continue
        
        print(f"成功處理 {len(processed_data)} 筆有效測站數據")
        return processed_data
    
    def get_aqi_color(self, aqi_value):
        """根據 AQI 值返回對應顏色"""
        try:
            aqi = int(aqi_value)
        except (ValueError, TypeError):
            return 'gray'
        
        if aqi <= 50:
            return 'green'
        elif aqi <= 100:
            return 'yellow'
        else:
            return 'red'
    
    def create_map(self, processed_data):
        """創建 Folium 地圖"""
        if not processed_data:
            print("沒有有效數據可創建地圖")
            return None
            
        # 計算台灣中心點
        lats = [station['latitude'] for station in processed_data]
        lons = [station['longitude'] for station in processed_data]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # 創建地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加測站標記
        for station in processed_data:
            aqi = station['aqi']
            color = self.get_aqi_color(aqi)
            
            # 創建簡化的彈出窗口內容
            popup_content = f"""
            <div style="font-size: 14px; min-width: 150px;">
                <h4 style="margin: 5px 0; color: #333;">{station['site_name']}</h4>
                <p style="margin: 3px 0;"><b>所在地:</b> {station['county']}</p>
                <p style="margin: 3px 0;"><b>即時 AQI:</b> <span style="font-size: 16px; font-weight: bold; color: {color};">{aqi}</span></p>
            </div>
            """
            
            # 創建圓形標記
            folium.CircleMarker(
                location=[station['latitude'], station['longitude']],
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                weight=1,
                fillColor=color,
                fillOpacity=0.7,
                tooltip=f"{station['site_name']} - AQI: {aqi}"
            ).add_to(m)
        
        # 添加簡化的圖例
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 180px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;">
        <h4 style="margin: 0 0 10px 0;">AQI 狀態</h4>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <div style="width: 20px; height: 20px; background-color: green; border-radius: 50%; margin-right: 10px;"></div>
            <span>良好 (0-50)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <div style="width: 20px; height: 20px; background-color: yellow; border-radius: 50%; margin-right: 10px;"></div>
            <span>普通 (51-100)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <div style="width: 20px; height: 20px; background-color: red; border-radius: 50%; margin-right: 10px;"></div>
            <span>不健康 (101+)</span>
        </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def export_to_csv(self, processed_data, filename=None):
        """將數據匯出為 CSV 檔案"""
        if not processed_data:
            print("沒有數據可匯出")
            return False
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"outputs/aqi_data_{timestamp}.csv"
        
        try:
            # 創建 DataFrame
            df = pd.DataFrame(processed_data)
            
            # 重新排列欄位順序，將重要欄位放在前面
            columns_order = [
                'site_name', 'county', 'aqi', 'status', 'distance_to_taipei',
                'latitude', 'longitude', 'pollutant', 'pm25', 'pm10', 'o3', 
                'no2', 'so2', 'co', 'wind_speed', 'wind_direction', 'publish_time'
            ]
            
            # 確保所有欄位都存在
            available_columns = [col for col in columns_order if col in df.columns]
            df = df[available_columns]
            
            # 匯出 CSV
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"數據已匯出至: {filename}")
            
            # 顯示匯出統計
            print(f"匯出 {len(df)} 筆測站數據")
            print(f"包含欄位: {', '.join(df.columns.tolist())}")
            
            return True
            
        except Exception as e:
            print(f"匯出 CSV 失敗: {e}")
            return False
    
    def save_map(self, map_obj, filename=None):
        """保存地圖為 HTML 檔案"""
        if not map_obj:
            print("無法保存空地圖")
            return False
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"outputs/aqi_map_{timestamp}.html"
        
        try:
            map_obj.save(filename)
            print(f"地圖已保存至: {filename}")
            return True
        except Exception as e:
            print(f"保存地圖失敗: {e}")
            return False
    
    def run(self):
        """執行完整流程"""
        print("=" * 50)
        print("台灣即時空氣品質指標 (AQI) 地圖視覺化")
        print("=" * 50)
        
        # 1. 獲取數據
        if not self.fetch_aqi_data():
            return False
        
        # 2. 處理數據
        processed_data = self.process_data()
        if not processed_data:
            print("沒有有效的測站數據")
            return False
        
        # 3. 創建地圖
        aqi_map = self.create_map(processed_data)
        if not aqi_map:
            return False
        
        # 4. 保存地圖
        self.save_map(aqi_map)
        
        # 5. 匯出 CSV 數據
        self.export_to_csv(processed_data)
        
        # 6. 顯示統計信息
        self.show_statistics(processed_data)
        
        print("\n程式執行完成！")
        return True
    
    def show_statistics(self, data):
        """顯示數據統計信息"""
        if not data:
            return
            
        df = pd.DataFrame(data)
        
        print("\n" + "=" * 30)
        print("數據統計")
        print("=" * 30)
        print(f"總測站數量: {len(df)}")
        print(f"平均 AQI: {df['aqi'].astype(float).mean():.1f}")
        print(f"最高 AQI: {df['aqi'].astype(float).max()}")
        print(f"最低 AQI: {df['aqi'].astype(float).min()}")
        
        # 各縣市測站數量
        print("\n各縣市測站數量:")
        county_counts = df['county'].value_counts().head(10)
        for county, count in county_counts.items():
            print(f"  {county}: {count} 個測站")
        
        # 顯示距離統計
        print("\n距離統計 (到台北車站):")
        df_sorted = df.sort_values('distance_to_taipei')
        print(f"最近測站: {df_sorted.iloc[0]['site_name']} ({df_sorted.iloc[0]['distance_to_taipei']} 公里)")
        print(f"最遠測站: {df_sorted.iloc[-1]['site_name']} ({df_sorted.iloc[-1]['distance_to_taipei']} 公里)")
        print(f"平均距離: {df['distance_to_taipei'].mean():.2f} 公里")
        
        # 顯示前5名最近的測站
        print("\n距離台北車站最近的5個測站:")
        for i, (_, row) in enumerate(df_sorted.head(5).iterrows(), 1):
            print(f"  {i}. {row['site_name']} ({row['county']}) - {row['distance_to_taipei']} 公里")
        
        # AQI 分佈 (簡化版)
        print("\nAQI 狀態分佈:")
        aqi_ranges = [
            (0, 50, "良好"),
            (51, 100, "普通"), 
            (101, 999, "不健康")
        ]
        
        for min_aqi, max_aqi, status in aqi_ranges:
            count = len(df[(df['aqi'].astype(float) >= min_aqi) & 
                          (df['aqi'].astype(float) <= max_aqi)])
            if count > 0:
                print(f"  {status} ({min_aqi}-{max_aqi if max_aqi < 999 else '+'}): {count} 個測站")

def main():
    """主程式入口"""
    try:
        visualizer = AQIMapVisualizer()
        visualizer.run()
    except Exception as e:
        print(f"程式執行錯誤: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
