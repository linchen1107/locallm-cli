#!/usr/bin/env python3
"""
測試全域 locallm 命令的工作目錄功能
"""

import sys
import os
from pathlib import Path

# 添加 LocalLM CLI 目錄到路徑
locallm_dir = Path(r"C:\Users\will\Desktop\locallm-cli")
sys.path.insert(0, str(locallm_dir))

# 模擬在不同目錄下運行
test_dirs = [
    Path.cwd(),
    Path.home(),
    Path("C:\\"),
    Path("C:\\Users"),
    Path("C:\\Windows")
]

print("🧪 測試 LocalLM CLI 在不同目錄下的工作目錄顯示")
print("=" * 60)

for test_dir in test_dirs:
    if test_dir.exists():
        original_cwd = Path.cwd()
        try:
            os.chdir(test_dir)
            
            # 導入工具來測試路徑顯示
            from tools import get_current_path
            
            current = Path(get_current_path())
            
            # 測試路徑顯示邏輯
            try:
                home_path = Path.home()
                if current.is_relative_to(home_path):
                    relative_path = current.relative_to(home_path)
                    display_path = f"~/{relative_path}" if str(relative_path) != "." else "~"
                else:
                    display_path = current.name if current.name else str(current)
            except:
                display_path = current.name
                
            print(f"📁 在 {test_dir}")
            print(f"   實際路徑: {current}")
            print(f"   顯示為:   {display_path}")
            print()
            
        except Exception as e:
            print(f"❌ 測試 {test_dir} 時發生錯誤: {e}")
        finally:
            os.chdir(original_cwd)

print("✅ 全域命令測試完成！")
print("\n使用方式:")
print("1. 開啟新的 PowerShell 或命令提示字元")
print("2. 切換到任意目錄: cd C:\\your\\project")
print("3. 執行: locallm")
print("4. LocalLM CLI 將在該目錄中工作！")