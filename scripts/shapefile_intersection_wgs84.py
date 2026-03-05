# -*- coding: utf-8 -*-
"""
使用 Shapefile 交集檢查的離群值清除程式 (WGS84 版本)
用途：
1. 讀取 TOWN_MOI_1140318.shp 檔案 (台灣鄉鎮界線)
2. 將 Shapefile 和避難收容處所都轉換為 WGS84 (EPSG:4326)
3. 將避難收容處所點位與鄉鎮多邊形做交集檢查
4. 刪除沒有與任何鄉鎮多邊形相交的點位

執行：
python shapefile_intersection_wgs84.py --in "避難收容處所點位檔.csv" --shp "TOWN_MOI_1140318.shp" --out "避難收容處所點位檔_shape_cleaned.csv"
"""

import argparse
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import os
import warnings
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# 載入環境變數
load_dotenv()

def robust_read_csv(path: str) -> pd.DataFrame:
    """讀取CSV檔案，嘗試多種編碼"""
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc, engine="python")
        except Exception:
            pass
    return pd.read_csv(path, engine="python")

def to_float_series(s: pd.Series) -> pd.Series:
    """轉換為浮點數"""
    s2 = s.astype(str).str.strip()
    s2 = s2.str.replace(r"[,\s]", "", regex=True)
    s2 = s2.replace({"nan": np.nan, "None": np.nan, "": np.nan})
    return pd.to_numeric(s2, errors="coerce")

def load_town_shapefile(shapefile_path: str, target_crs: str = "EPSG:4326"):
    """
    載入鄉鎮界線 Shapefile 並轉換為目標坐標系統
    """
    print(f"正在載入鄉鎮界線 Shapefile: {shapefile_path}")
    print(f"目標坐標系統: {target_crs}")
    
    try:
        # 使用 pyogrio 載入
        towns = gpd.read_file(shapefile_path, engine="pyogrio")
        print(f"✅ 成功載入 {len(towns)} 個鄉鎮多邊形")
        print(f"原始坐標系統: {towns.crs}")
        
        # 檢查坐標範圍
        bounds = towns.total_bounds
        print(f"原始坐標範圍: X({bounds[0]:.2f} ~ {bounds[2]:.2f}), Y({bounds[1]:.2f} ~ {bounds[3]:.2f})")
        
        # 轉換為目標坐標系統
        if towns.crs != target_crs:
            print(f"轉換坐標系統: {towns.crs} -> {target_crs}")
            towns = towns.to_crs(target_crs)
            print(f"✅ 坐標系統轉換完成")
            
            # 重新檢查坐標範圍
            bounds = towns.total_bounds
            print(f"轉換後坐標範圍: X({bounds[0]:.6f} ~ {bounds[2]:.6f}), Y({bounds[1]:.6f} ~ {bounds[3]:.6f})")
        
        # 檢查重要欄位
        print(f"可用欄位: {list(towns.columns)}")
        
        # 顯示前幾筆資料
        if 'COUNTYNAME' in towns.columns and 'TOWNNAME' in towns.columns:
            print("鄉鎮資料範例:")
            for idx, row in towns.head(5).iterrows():
                print(f"  {row['COUNTYNAME']} {row['TOWNNAME']}")
        
        return towns
        
    except Exception as e:
        print(f"❌ 無法載入 Shapefile: {e}")
        raise

def check_point_intersection(lon: float, lat: float, towns_gdf) -> bool:
    """
    檢查點位是否與任何鄉鎮多邊形相交
    """
    if pd.isna(lon) or pd.isna(lat):
        return False
    
    # 建立點位
    point = Point(lon, lat)
    
    # 使用空間索引加速查詢
    try:
        # 建立空間索引
        towns_gdf_sindex = towns_gdf.sindex
        
        # 取得可能相交的多邊形
        possible_matches_index = list(towns_gdf_sindex.intersection(point.bounds))
        possible_matches = towns_gdf.iloc[possible_matches_index]
        
        # 精確檢查
        for idx, town in possible_matches.iterrows():
            if town.geometry.contains(point) or town.geometry.intersects(point):
                return True
        
        return False
        
    except:
        # 如果空間索引失敗，使用傳統方法
        for idx, town in towns_gdf.iterrows():
            if town.geometry.contains(point) or town.geometry.intersects(point):
                return True
        return False

def get_town_name(lon: float, lat: float, towns_gdf) -> str:
    """
    取得點位所在的鄉鎮名稱
    """
    if pd.isna(lon) or pd.isna(lat):
        return "未知"
    
    # 建立點位
    point = Point(lon, lat)
    
    # 檢查是否與任何鄉鎮多邊形相交
    try:
        # 建立空間索引
        towns_gdf_sindex = towns_gdf.sindex
        
        # 取得可能相交的多邊形
        possible_matches_index = list(towns_gdf_sindex.intersection(point.bounds))
        possible_matches = towns_gdf.iloc[possible_matches_index]
        
        # 精確檢查
        for idx, town in possible_matches.iterrows():
            if town.geometry.contains(point) or town.geometry.intersects(point):
                # 嘗試取得鄉鎮名稱
                if 'COUNTYNAME' in town and 'TOWNNAME' in town:
                    return f"{town['COUNTYNAME']}{town['TOWNNAME']}"
                elif 'TOWNNAME' in town:
                    return town['TOWNNAME']
                elif 'NAME' in town:
                    return town['NAME']
                else:
                    return f"鄉鎮{idx}"
        
        return "未知"
        
    except:
        # 如果空間索引失敗，使用傳統方法
        for idx, town in towns_gdf.iterrows():
            if town.geometry.contains(point) or town.geometry.intersects(point):
                # 嘗試取得鄉鎮名稱
                if 'COUNTYNAME' in town and 'TOWNNAME' in town:
                    return f"{town['COUNTYNAME']}{town['TOWNNAME']}"
                elif 'TOWNNAME' in town:
                    return town['TOWNNAME']
                elif 'NAME' in town:
                    return town['NAME']
                else:
                    return f"鄉鎮{idx}"
        
        return "未知"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True, help="輸入CSV路徑")
    ap.add_argument("--shp", dest="shapefile", required=True, help="Shapefile路徑")
    ap.add_argument("--out", dest="outfile", default="避難收容處所點位檔_shape_cleaned.csv", help="輸出CSV路徑")
    ap.add_argument("--lon", dest="lon_col", default="經度", help="經度欄位名")
    ap.add_argument("--lat", dest="lat_col", default="緯度", help="緯度欄位名")
    ap.add_argument("--crs", dest="target_crs", default="EPSG:4326", help="目標坐標系統")
    args = ap.parse_args()

    print("=== 使用 Shapefile 交集檢查的離群值清除 (WGS84 版本) ===")
    print(f"Shapefile: {args.shapefile}")
    print(f"目標坐標系統: {args.target_crs}")
    print()

    # 讀取避難收容處所資料
    df = robust_read_csv(args.infile)
    print(f"讀取避難收容處所資料: {len(df)} 筆")

    if args.lon_col not in df.columns or args.lat_col not in df.columns:
        raise ValueError(f"找不到欄位：{args.lon_col} / {args.lat_col}")

    # 載入鄉鎮界線 Shapefile 並轉換為 WGS84
    try:
        towns_gdf = load_town_shapefile(args.shapefile, args.target_crs)
    except Exception as e:
        print(f"❌ 無法載入 Shapefile: {e}")
        return

    # 轉換經緯度為數值
    df["_lon"] = to_float_series(df[args.lon_col])
    df["_lat"] = to_float_series(df[args.lat_col])

    # 檢查避難收容處所的坐標範圍
    valid_coords = df.dropna(subset=["_lon", "_lat"])
    if len(valid_coords) > 0:
        min_lon = valid_coords["_lon"].min()
        max_lon = valid_coords["_lon"].max()
        min_lat = valid_coords["_lat"].min()
        max_lat = valid_coords["_lat"].max()
        print(f"避難收容處所坐標範圍: 經度({min_lon:.6f} ~ {max_lon:.6f}), 緯度({min_lat:.6f} ~ {max_lat:.6f})")
        
        # 檢查幾個範例點
        print("檢查範例點:")
        for idx, row in valid_coords.head(5).iterrows():
            town_name = get_town_name(row["_lon"], row["_lat"], towns_gdf)
            is_intersect = check_point_intersection(row["_lon"], row["_lat"], towns_gdf)
            print(f"  {row['避難收容處所名稱']}: ({row['_lon']:.6f}, {row['_lat']:.6f}) -> {town_name} (相交: {is_intersect})")

    # 檢查每個點是否與鄉鎮多邊形相交
    print("\n正在檢查每個點是否與鄉鎮多邊形相交...")
    df["是否在鄉鎮內"] = df.apply(
        lambda row: check_point_intersection(row["_lon"], row["_lat"], towns_gdf), 
        axis=1
    )

    # 取得所在的鄉鎮名稱
    df["所在鄉鎮"] = df.apply(
        lambda row: get_town_name(row["_lon"], row["_lat"], towns_gdf), 
        axis=1
    )

    # 找出不在任何鄉鎮內的點
    outliers = df[~df["是否在鄉鎮內"]]
    
    print(f"\n=== 不在任何鄉鎮內的點: {len(outliers)} 筆 ===")
    
    if len(outliers) > 0:
        # 按縣市統計離群點
        print("\n按縣市統計離群點:")
        county_stats = outliers['縣市及鄉鎮市區'].str.extract(r'([^市縣]+[市縣])')[0].value_counts()
        for county, count in county_stats.head(10).items():
            print(f"  {county}: {count} 筆")
        
        print(f"\n詳細資訊 (前20筆):")
        for idx, row in outliers.head(20).iterrows():
            print(f"  {row['避難收容處所名稱']} ({row['縣市及鄉鎮市區']})")
            print(f"    座標: ({row['_lon']:.6f}, {row['_lat']:.6f})")
        
        if len(outliers) > 20:
            print(f"  ... 還有 {len(outliers) - 20} 筆未顯示")
        
        # 保存離群點清單
        outliers.to_csv("../data/shape_outliers.csv", index=False, encoding="utf-8-sig")
        print(f"\n離群點清單已保存至: ../data/shape_outliers.csv")
    else:
        print("✅ 所有點都在鄉鎮內")

    # 保留在鄉鎮內的點
    df_cleaned = df[df["是否在鄉鎮內"]].copy()
    
    # 移除臨時欄位
    df_cleaned = df_cleaned.drop(columns=["_lon", "_lat", "是否在鄉鎮內"])

    # 保存清理後的資料
    df_cleaned.to_csv(args.outfile, index=False, encoding="utf-8-sig")

    print(f"\n=== 清理完成 ===")
    print(f"原始資料: {len(df)} 筆")
    print(f"清理後資料: {len(df_cleaned)} 筆")
    print(f"刪除離群點: {len(df) - len(df_cleaned)} 筆 ({((len(df) - len(df_cleaned))/len(df)*100):.1f}%)")
    print(f"保留率: {(len(df_cleaned)/len(df)*100):.1f}%")
    print(f"輸出檔案: {args.outfile}")
    
    # 統計清理後的縣市分布
    if len(df_cleaned) > 0:
        print(f"\n=== 清理後縣市分布 (前10名) ===")
        cleaned_county_stats = df_cleaned['縣市及鄉鎮市區'].str.extract(r'([^市縣]+[市縣])')[0].value_counts()
        for county, count in cleaned_county_stats.head(10).items():
            print(f"{county}: {count} 筆")
        
        # 統計鄉鎮分布
        print(f"\n=== 清理後鄉鎮分布 (前10名) ===")
        town_stats = df_cleaned['所在鄉鎮'].value_counts()
        for town, count in town_stats.head(10).items():
            print(f"{town}: {count} 筆")

if __name__ == "__main__":
    main()
