# -*- coding: utf-8 -*-
"""
根據設施名稱新增 is_indoor 欄位
用途：
1. 讀取清理後的避難收容處所資料
2. 根據設施名稱判斷是否為室內設施
3. 新增 is_indoor 欄位 (True=室內, False=室外)
4. 分析分類結果並保存

判斷規則：
- 室內設施 (True): 學校、活動中心、社區活動中心、國小、國中、高中、大學、圖書館、體育館、禮堂、教室、會議室、辦公處、村民活動中心、里民活動中心等
- 室外設施 (False): 公園、廣場、運動場、球場、河濱公園、森林遊樂區、海灘、登山步道等

執行：
python add_is_indoor_column.py --in "避難收容處所點位檔_shape_cleaned.csv" --out "避難收容處所點位檔_with_indoor.csv"
"""

import argparse
import pandas as pd
import numpy as np
import re

def robust_read_csv(path: str) -> pd.DataFrame:
    """讀取CSV檔案，嘗試多種編碼"""
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc, engine="python")
        except Exception:
            pass
    return pd.read_csv(path, engine="python")

def classify_indoor_facility(facility_name: str) -> bool:
    """
    根據設施名稱判斷是否為室內設施
    """
    if pd.isna(facility_name) or facility_name == "":
        return False
    
    facility_name = str(facility_name).strip()
    
    # 室內設施關鍵字
    indoor_keywords = [
        # 學校相關
        '國小', '國中', '高中', '大學', '學校', '小學', '中學', '幼稚園', '托兒所',
        # 活動中心相關
        '活動中心', '社區活動中心', '村民活動中心', '里民活動中心', '鄰里活動中心',
        '社區中心', '村里中心', '里辦公處', '村辦公處', '鄉公所', '鎮公所', '區公所',
        # 室內場所
        '圖書館', '體育館', '禮堂', '教室', '會議室', '辦公室', '辦公處', '服務中心',
        '集會所', '集會堂', '社教館', '文化中心', '藝文中心', '訓練中心',
        '健康中心', '衛生所', '診所', '醫院', '消防局', '警察局', '分局',
        # 宗教場所
        '寺廟', '教堂', '宮', '廟', '教會', '清真寺',
        # 其他室內
        '招待所', '旅社', '飯店', '民宿', '會館', '俱樂部', '中心', '館', '堂', '樓',
        '大廳', '廳', '室', '舍', '房', '家', '局', '署', '處', '部'
    ]
    
    # 室外設施關鍵字
    outdoor_keywords = [
        '公園', '廣場', '運動場', '球場', '河濱公園', '森林', '遊樂區', '海灘',
        '登山', '步道', '營地', '露營', '烤肉區', '野餐區', '遊憩區', '綠地',
        '濕地', '生態', '自然', '山', '河', '湖', '海', '溪', '港', '碼頭'
    ]
    
    # 檢查是否包含室內關鍵字
    for keyword in indoor_keywords:
        if keyword in facility_name:
            return True
    
    # 檢查是否包含室外關鍵字
    for keyword in outdoor_keywords:
        if keyword in facility_name:
            return False
    
    # 特殊規則：如果名稱包含「活動中心」但同時包含「公園」或「廣場」，判斷為室外
    if '活動中心' in facility_name:
        if '公園' in facility_name or '廣場' in facility_name:
            return False
        else:
            return True
    
    # 特殊規則：如果名稱包含「學校」但同時包含「運動場」，判斷為室外
    if '學校' in facility_name and '運動場' in facility_name:
        return False
    
    # 預設情況：如果名稱包含「中心」但沒有明確的室外關鍵字，判斷為室內
    if '中心' in facility_name:
        return True
    
    # 如果無法確定，預設為室內（因為大部分避難收容處所都是室內）
    return True

def analyze_classification(df: pd.DataFrame):
    """
    分析分類結果
    """
    print("=== 分類結果分析 ===")
    
    # 統計室內外設施數量
    indoor_count = df['is_indoor'].sum()
    outdoor_count = len(df) - indoor_count
    
    print(f"室內設施: {indoor_count} 筆 ({indoor_count/len(df)*100:.1f}%)")
    print(f"室外設施: {outdoor_count} 筆 ({outdoor_count/len(df)*100:.1f}%)")
    
    # 顯示室內設施範例
    print("\n=== 室內設施範例 ===")
    indoor_facilities = df[df['is_indoor'] == True]['避難收容處所名稱'].head(10)
    for facility in indoor_facilities:
        print(f"  {facility}")
    
    # 顯示室外設施範例
    print("\n=== 室外設施範例 ===")
    outdoor_facilities = df[df['is_indoor'] == False]['避難收容處所名稱'].head(10)
    for facility in outdoor_facilities:
        print(f"  {facility}")
    
    # 按縣市統計室內外分布
    print("\n=== 按縣市統計室內外分布 ===")
    county_stats = df.groupby([
        df['縣市及鄉鎮市區'].str.extract(r'([^市縣]+[市縣])')[0],
        df['is_indoor']
    ]).size().unstack(fill_value=0)
    
    county_stats.columns = ['室外', '室內']
    county_stats['總計'] = county_stats['室內'] + county_stats['室外']
    county_stats['室內比例'] = (county_stats['室內'] / county_stats['總計'] * 100).round(1)
    
    # 顯示前10名縣市
    top_counties = county_stats['總計'].nlargest(10).index
    for county in top_counties:
        indoor = county_stats.loc[county, '室內']
        outdoor = county_stats.loc[county, '室外']
        ratio = county_stats.loc[county, '室內比例']
        print(f"  {county}: 室內 {indoor} 筆, 室外 {outdoor} 筆 (室內比例: {ratio}%)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True, help="輸入CSV路徑")
    ap.add_argument("--out", dest="outfile", default="避難收容處所點位檔_with_indoor.csv", help="輸出CSV路徑")
    ap.add_argument("--name", dest="name_col", default="避難收容處所名稱", help="設施名稱欄位名")
    args = ap.parse_args()

    print("=== 根據設施名稱新增 is_indoor 欄位 ===")
    print(f"輸入檔案: {args.infile}")
    print(f"輸出檔案: {args.outfile}")
    print()

    # 讀取資料
    df = robust_read_csv(args.infile)
    print(f"讀取資料: {len(df)} 筆")

    if args.name_col not in df.columns:
        raise ValueError(f"找不到欄位：{args.name_col}")

    # 新增 is_indoor 欄位
    print("正在根據設施名稱判斷室內外...")
    df['is_indoor'] = df[args.name_col].apply(classify_indoor_facility)
    
    # 分析分類結果
    analyze_classification(df)
    
    # 保存資料
    df.to_csv(args.outfile, index=False, encoding='utf-8-sig')
    
    print(f"\n=== 處理完成 ===")
    print(f"原始資料: {len(df)} 筆")
    print(f"新增欄位: is_indoor (True=室內, False=室外)")
    print(f"輸出檔案: {args.outfile}")
    
    # 顯示分類統計摘要
    indoor_count = df['is_indoor'].sum()
    outdoor_count = len(df) - indoor_count
    print(f"\n分類摘要:")
    print(f"  室內設施: {indoor_count} 筆 ({indoor_count/len(df)*100:.1f}%)")
    print(f"  室外設施: {outdoor_count} 筆 ({outdoor_count/len(df)*100:.1f}%)")

if __name__ == "__main__":
    main()
