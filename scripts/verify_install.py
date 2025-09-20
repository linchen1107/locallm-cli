#!/usr/bin/env python3
"""
最終驗證 LocalLM 全域命令功能
"""

import os
import subprocess
from pathlib import Path

def test_locallm_in_directory(test_dir):
    """在指定目錄測試 locallm 命令"""
    print(f"📁 測試目錄: {test_dir}")
    
    if not Path(test_dir).exists():
        print(f"  ❌ 目錄不存在，跳過")
        return False
    
    try:
        # 切換到測試目錄並執行 locallm --help
        result = subprocess.run(
            ["locallm", "--help"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"  ✅ 命令成功執行")
            print(f"  📝 輸出摘要: {result.stdout.split(chr(10))[0]}")
            return True
        else:
            print(f"  ❌ 命令執行失敗 (退出碼: {result.returncode})")
            if result.stderr:
                print(f"  🔍 錯誤: {result.stderr[:100]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ⏰ 命令執行超時")
        return False
    except FileNotFoundError:
        print(f"  ❌ 找不到 locallm 命令")
        return False
    except Exception as e:
        print(f"  ❌ 其他錯誤: {e}")
        return False

def main():
    print("🚀 LocalLM CLI 全域命令驗證")
    print("=" * 50)
    print()
    
    # 測試目錄列表
    test_directories = [
        str(Path.home()),                    # 使用者家目錄
        str(Path.home() / "Desktop"),        # 桌面
        "C:\\",                              # C: 根目錄
        "C:\\Users",                         # Users 目錄
        str(Path.cwd()),                     # 當前目錄
    ]
    
    success_count = 0
    total_count = len(test_directories)
    
    for test_dir in test_directories:
        result = test_locallm_in_directory(test_dir)
        if result:
            success_count += 1
        print()
    
    print("📊 測試結果總結")
    print("-" * 30)
    print(f"總測試數: {total_count}")
    print(f"成功數量: {success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 全域命令設定完美！")
        print("您現在可以在任意位置使用 'locallm' 命令！")
    elif success_count > 0:
        print(f"\n⚠️  部分測試通過，可能需要重新開啟終端")
    else:
        print(f"\n❌ 全域命令設定失敗，請檢查 PATH 環境變數")
        
    print("\n📋 使用說明:")
    print("1. 開啟新的 PowerShell 或命令提示字元")
    print("2. 切換到任意專案目錄")
    print("3. 輸入 'locallm' 開始使用")

if __name__ == "__main__":
    main()