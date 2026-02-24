# 台灣即時空氣品質指標 (AQI) 分析與視覺化

這個程式串接環境部 API 獲取全台即時 AQI 數據，提供地圖視覺化、空間距離計算和數據匯出功能。

## 功能特色

- 🌍 串接環境部 AQI API (aqx_p_432) 獲取即時數據
- 📍 在台灣地圖上標示所有測站位置
- 🎨 簡化三色分類顯示空氣品質狀態（綠/黃/紅）
- 📊 詳細測站資訊彈出窗口（站名、縣市、AQI 數值）
- 📏 **空間計算**：計算各測站到台北車站的距離
- 📈 **數據統計**：距離分析、AQI 分佈、縣市統計
- 📄 **CSV 匯出**：完整測站數據含距離計算結果
- 🔧 自動環境安裝

## 快速開始

### 1. 設定 API Key

在 `.env` 檔案中新增你的環境部 API Key：

```bash
MOENV_API_KEY=your_api_key_here
```

### 2. 自動安裝環境

```bash
python scripts/setup.py
```

### 3. 執行程式

```bash
python scripts/aqi_map.py
```

地圖和 CSV 數據會自動保存在 `outputs/` 資料夾中。

## 手動安裝

如果自動安裝失敗，可以手動安裝所需套件：

```bash
pip install requests folium python-dotenv pandas
```

## 程式結構

```
hw1/
├── scripts/          # 程式腳本資料夾
│   ├── aqi_map.py   # 主程式
│   └── setup.py     # 環境安裝腳本
├── requirements.txt  # 套件需求列表
├── .env             # 環境變數設定
├── .gitignore       # Git 忽略檔案
├── data/            # 資料資料夾
├── outputs/         # 輸出資料夾
└── README.md        # 說明文件
```

## AQI 顏色對應

- 🟢 **綠色** (0-50): 良好
- 🟡 **黃色** (51-100): 普通
- � **紅色** (101+): 不健康

## 空間距離計算

使用 Haversine 公式計算每個測站到台北車站 (25.0478, 121.5170) 的直線距離：

- � **基準點**: 台北車站
- 📏 **計算方式**: 球面距離公式
- � **單位**: 公里（精確到小數點後2位）

## 輸出檔案

### 🗺️ **地圖檔案**
- 檔名: `outputs/aqi_map_YYYYMMDD_HHMMSS.html`
- 格式: 互動式 HTML 地圖
- 功能: 點擊測站查看詳細資訊

### � **CSV 數據檔案**
- 檔名: `outputs/aqi_data_YYYYMMDD_HHMMSS.csv`
- 格式: UTF-8 編碼 CSV
- 包含欄位:
  - 測站基本資訊: site_name, county, aqi, status
  - **空間計算**: distance_to_taipei, latitude, longitude
  - 環境數據: pollutant, pm25, pm10, o3, no2, so2, co
  - 氣象資訊: wind_speed, wind_direction, publish_time

## 輸出範例

程式執行後會顯示：

### 📊 **統計信息**
```
總測站數量: 85
平均 AQI: 78.1
最高 AQI: 106.0
最低 AQI: 26.0

距離統計 (到台北車站):
最近測站: 萬華 (0.92 公里)
最遠測站: 恆春 (351.49 公里)
平均距離: 146.38 公里

距離台北車站最近的5個測站:
  1. 萬華 (臺北市) - 0.92 公里
  2. 大同 (臺北市) - 1.76 公里
  3. 中山 (臺北市) - 1.88 公里
  4. 古亭 (臺北市) - 3.28 公里
  5. 永和 (新北市) - 3.43 公里

AQI 狀態分佈:
  良好 (0-50): 7 個測站
  普通 (51-100): 73 個測站
  不健康 (101+): 5 個測站
```

### 📁 **輸出檔案**
- **地圖檔案**: `outputs/aqi_map_YYYYMMDD_HHMMSS.html`
- **CSV 數據**: `outputs/aqi_data_YYYYMMDD_HHMMSS.csv`

## 注意事項

- 需要有效的環境部 API Key
- 確保網路連線正常
- 地圖檔案需要用瀏覽器開啟查看
- CSV 檔案支援 Excel 開啟（UTF-8 編碼）

## 技術規格

### 📐 **距離計算**
- **公式**: Haversine 公式
- **地球半徑**: 6,371 公里
- **精度**: 小數點後 2 位
- **基準點**: 台北車站 (25.0478, 121.5170)

### 🎨 **視覺化設計**
- **地圖庫**: Folium
- **圖標**: 圓形標記
- **圖例**: 簡化三色分類
- **彈出窗口**: 簡潔資訊設計

### 📊 **數據處理**
- **API**: 環境部 AQI API v2
- **格式**: JSON
- **編碼**: UTF-8
- **時區**: 台灣標準時間

## API 資訊

- **API 端點**: `https://data.moenv.gov.tw/api/v2/AQX_P_432`
- **資料來源**: 環境部環境資料開放平臺
- **更新頻率**: 即時更新

## 故障排除

### API Key 錯誤
請確認 `.env` 檔案中的 `MOENV_API_KEY` 正確設定。

### 網路連線問題
請檢查網路連線，確保可以存取環境部 API。

### 套件安裝失敗
嘗試更新 pip：
```bash
python -m pip install --upgrade pip
```

## 授權

本專案遵循環境部開放資料授權條款。
