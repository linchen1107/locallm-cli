#!/usr/bin/env python3
"""
測試 LocalLM CLI 的所有命令功能
"""

import subprocess
import sys
import time
from pathlib import Path

def run_locallm_command(command, cwd=None, timeout=10):
    """執行 locallm 命令並返回結果"""
    try:
        # 使用 echo 將命令通過管道傳遞給 locallm
        process = subprocess.Popen(
            ["locallm"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        
        # 發送命令並立即退出
        commands = f"{command}\n/exit\n"
        stdout, stderr = process.communicate(input=commands, timeout=timeout)
        
        return stdout, stderr, process.returncode
        
    except subprocess.TimeoutExpired:
        process.kill()
        return "", "Timeout", -1
    except Exception as e:
        return "", str(e), -1

def test_commands():
    """測試各種命令"""
    print("🧪 測試 LocalLM CLI 命令功能")
    print("=" * 50)
    
    # 測試目錄
    test_dir = Path.home() / "Desktop"
    
    print(f"📁 測試目錄: {test_dir}")
    print()
    
    # 創建測試檔案
    test_file = test_dir / "locallm_test.txt"
    test_file.write_text("This is a test file for LocalLM CLI")
    
    # 測試命令列表
    test_cases = [
        ("/help", "幫助命令"),
        ("/pwd", "顯示路徑命令"),
        ("/list", "列出檔案命令"),
        (f"/read {test_file.name}", "讀取檔案命令"),
        ("/models", "列出模型命令"),
    ]
    
    results = []
    
    for command, description in test_cases:
        print(f"🔧 測試: {description}")
        print(f"   命令: {command}")
        
        stdout, stderr, returncode = run_locallm_command(command, cwd=str(test_dir))
        
        if returncode == 0:
            print(f"   ✅ 成功")
            if "Unknown command" in stdout:
                print(f"   ❌ 但命令未被識別")
                results.append(False)
            else:
                results.append(True)
        else:
            print(f"   ❌ 失敗 (退出碼: {returncode})")
            if stderr:
                print(f"   錯誤: {stderr[:100]}...")
            results.append(False)
        
        print()
    
    # 清理測試檔案
    if test_file.exists():
        test_file.unlink()
    
    # 總結
    success_count = sum(results)
    total_count = len(results)
    
    print("📊 測試結果")
    print("-" * 30)
    print(f"成功: {success_count}/{total_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 所有命令都正常工作！")
    else:
        print(f"\n⚠️  {total_count - success_count} 個命令需要修正")

if __name__ == "__main__":
    test_commands()