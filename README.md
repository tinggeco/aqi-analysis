# 台灣即時空氣品質指標 (AQI) 地圖視覺化

這個程式串接環境部 API 獲取全台即時 AQI 數據，並使用 Folium 在地圖上標示所有測站位置。

## 功能特色

- 🌍 串接環境部 AQI API (aqx_p_432) 獲取即時數據
- 📍 在台灣地圖上標示所有測站位置
- 🎨 根據 AQI 值使用不同顏色顯示空氣品質狀態
- 📊 顯示詳細的測站資訊（PM2.5、PM10、O₃ 等）
- 📈 提供數據統計分析
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

地圖會自動保存在 `outputs/` 資料夾中。

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
- 🟠 **橙色** (101-150): 對敏感族群不健康
- 🔴 **紅色** (151-200): 對所有族群不健康
- 🟣 **紫色** (201-300): 非常不健康
- 🟤 **褐色** (301+): 危害

## 輸出範例

程式會顯示：

1. **數據獲取狀態**: 成功獲取的測站數量
2. **統計信息**: 平均 AQI、最高/最低值、各縣市測站數量
3. **地圖檔案**: 儲存在 `outputs/aqi_map_YYYYMMDD_HHMMSS.html`

## 注意事項

- 需要有效的環境部 API Key
- 確保網路連線正常
- 地圖檔案需要用瀏覽器開啟查看

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
