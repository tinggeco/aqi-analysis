#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試 API 數據格式
"""

import os
import requests
from dotenv import load_dotenv
import json

# 載入環境變數
load_dotenv()

def debug_api():
    api_key = os.getenv('MOENV_API_KEY')
    api_url = "https://data.moenv.gov.tw/api/v2/AQX_P_432"
    
    params = {
        'api_key': api_key,
        'limit': 5,  # 只取5筆來調試
        'sort': 'ImportDate desc',
        'format': 'json'
    }
    
    print("API URL:", api_url)
    print("API Key:", api_key[:10] + "..." if api_key else "None")
    print("Params:", params)
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Data length: {len(data)}")
            
            if data:
                print("\n第一筆數據的欄位:")
                first_record = data[0]
                for key, value in first_record.items():
                    print(f"  {key}: {value}")
                
                # 檢查經緯度欄位
                print(f"\n經緯度欄位檢查:")
                print(f"緯度: {first_record.get('緯度', 'Not found')}")
                print(f"經度: {first_record.get('經度', 'Not found')}")
                
                # 檢查其他可能的經緯度欄位名稱
                lat_fields = [k for k in first_record.keys() if 'lat' in k.lower() or '緯' in k]
                lon_fields = [k for k in first_record.keys() if 'lon' in k.lower() or '經' in k]
                
                print(f"可能的緯度欄位: {lat_fields}")
                print(f"可能的經度欄位: {lon_fields}")
            else:
                print("沒有數據")
        else:
            print(f"API 錯誤: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    debug_api()
