#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
環境安裝腳本
自動安裝所需的 Python 套件
"""

import subprocess
import sys
import os

def install_requirements():
    """安裝 requirements.txt 中的套件"""
    print("正在安裝所需的 Python 套件...")
    
    try:
        # 檢查 requirements.txt 是否存在
        if not os.path.exists('requirements.txt'):
            print("錯誤: 找不到 requirements.txt 檔案")
            return False
        
        # 執行 pip install
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 套件安裝成功!")
            print(result.stdout)
            return True
        else:
            print("❌ 套件安裝失敗:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"安裝過程發生錯誤: {e}")
        return False

def check_python_version():
    """檢查 Python 版本"""
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("⚠️  警告: 建議使用 Python 3.7 或更高版本")
        return False
    
    print("✅ Python 版本符合要求")
    return True

def main():
    """主程式"""
    print("=" * 50)
    print("台灣 AQI 地圖視覺化 - 環境安裝程式")
    print("=" * 50)
    
    # 檢查 Python 版本
    if not check_python_version():
        return False
    
    # 安裝套件
    if not install_requirements():
        return False
    
    print("\n🎉 環境設置完成!")
    print("\n接下來的步驟:")
    print("1. 請在 .env 檔案中設定你的 MOENV_API_KEY")
    print("2. 執行: python aqi_map.py")
    print("3. 地圖將會保存在 outputs/ 資料夾中")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
