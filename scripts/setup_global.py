#!/usr/bin/env python3
"""
LocalLM CLI 永久安裝腳本
"""

import os
import sys
import winreg
from pathlib import Path

def add_to_user_path(directory):
    """永久添加目錄到使用者 PATH"""
    try:
        # 開啟使用者環境變數的註冊表項
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, 
                           winreg.KEY_ALL_ACCESS) as key:
            
            # 讀取現有的 PATH
            try:
                current_path, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                current_path = ""
            
            # 檢查是否已經在 PATH 中
            paths = current_path.split(";") if current_path else []
            directory_str = str(directory)
            
            if directory_str not in paths:
                # 添加新路徑
                new_path = f"{current_path};{directory_str}" if current_path else directory_str
                
                # 寫回註冊表
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                
                print(f"  ✅ 成功添加到 PATH: {directory_str}")
                return True
            else:
                print(f"  ℹ️  已在 PATH 中: {directory_str}")
                return True
                
    except Exception as e:
        print(f"  ❌ 添加到 PATH 失敗: {e}")
        return False

def notify_environment_change():
    """通知系統環境變數已更改"""
    try:
        import ctypes
        from ctypes import wintypes
        
        # 廣播環境變數更改消息
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        
        result = ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            SMTO_ABORTIFHUNG, 5000, ctypes.byref(wintypes.DWORD())
        )
        
        if result:
            print("  📢 已通知系統更新環境變數")
        
    except Exception as e:
        print(f"  ⚠️  通知環境變數更改失敗: {e}")

def main():
    print()
    print("  ╭─────────────────────────────────────────╮")
    print("  │                                         │")
    print("  │     🛠️  LocalLM CLI 永久安裝            │")
    print("  │                                         │")
    print("  ╰─────────────────────────────────────────╯")
    print()
    
    # 獲取 LocalLM CLI 專案根目錄（scripts 的上一層）
    locallm_dir = Path(__file__).parent.parent.absolute()
    
    print(f"  📁 LocalLM CLI 位置: {locallm_dir}")
    print()
    
    # 檢查必要檔案是否存在
    required_files = {
        "locallm.bat": locallm_dir / "locallm.bat",
        "locallm_entry.py": locallm_dir / "scripts" / "locallm_entry.py", 
        "main.py": locallm_dir / "src" / "main.py"
    }
    missing_files = []
    
    for file_name, file_path in required_files.items():
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"  ❌ 缺少必要檔案: {', '.join(missing_files)}")
        print("  請確保在正確的 LocalLM CLI 目錄中執行此腳本")
        return False
    
    print("  🔧 將 LocalLM CLI 永久添加到 PATH...")
    
    # 添加到 PATH
    success = add_to_user_path(locallm_dir)
    
    if success:
        # 通知環境變數更改
        notify_environment_change()
        
        print()
        print("  🎉 安裝完成！")
        print()
        print("  📋 下一步:")
        print("  1. 重新開啟 PowerShell 或命令提示字元")
        print("  2. 切換到任意目錄")
        print("  3. 輸入 'locallm' 開始使用")
        print()
        print("  💡 使用範例:")
        print("    cd C:\\MyProject")
        print("    locallm")
        print("    locallm -m llama3.1")
        print()
        
        return True
    else:
        print()
        print("  ❌ 安裝失敗")
        print("  請嘗試以管理員身份執行，或手動添加以下路徑到 PATH:")
        print(f"  {locallm_dir}")
        print()
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  ⚠️  安裝被中斷")
    except Exception as e:
        print(f"\n  ❌ 安裝過程發生錯誤: {e}")
    
    input("\n  按 Enter 鍵退出...")