#!/usr/bin/env python3
"""
LocalLM CLI 調試版本 - 用於診斷命令解析問題
"""

import sys
import os
import re
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from models import chat_stream, list_models, is_available
from tools import read_file, write_file, edit_file, file_exists, list_files, get_current_path

def debug_parse_command(input_text: str) -> tuple:
    """調試版本的命令解析"""
    print(f"  🔍 Debug: 原始輸入 = '{input_text}'")
    
    input_text = input_text.strip()
    print(f"  🔍 Debug: strip後 = '{input_text}'")
    
    if not input_text.startswith('/'):
        print(f"  🔍 Debug: 不是命令，返回 chat")
        return ('chat', [input_text])
    
    # 移除開頭的 /
    command_line = input_text[1:]
    print(f"  🔍 Debug: 移除/後 = '{command_line}'")
    
    # 使用正規表達式解析指令和參數
    parts = re.findall(r'"([^"]*)"|(\S+)', command_line)
    # 正規表達式會返回元組，需要提取非空的部分
    parts = [part[0] if part[0] else part[1] for part in parts]
    print(f"  🔍 Debug: 解析結果 = {parts}")
    
    if not parts:
        print(f"  🔍 Debug: 沒有部分，返回 unknown")
        return ('unknown', [])
    
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    print(f"  🔍 Debug: 命令 = '{command}', 參數 = {args}")
    return (command, args)

def test_commands():
    """測試各種命令"""
    test_inputs = [
        "/models",
        "/list",
        "/help",
        "/read test.txt",
        "/write test.txt hello",
        "hello world"
    ]
    
    print("🧪 測試命令解析:")
    print("-" * 40)
    
    for test_input in test_inputs:
        print(f"\n輸入: {test_input}")
        command, args = debug_parse_command(test_input)
        print(f"結果: 命令='{command}', 參數={args}")
        
        # 模擬命令處理
        if command == 'exit' or command == 'quit':
            print("  → 會執行: 退出程式")
        elif command == 'help':
            print("  → 會執行: 顯示幫助")
        elif command == 'read':
            print("  → 會執行: 讀取檔案")
        elif command == 'write':
            print("  → 會執行: 寫入檔案")
        elif command == 'edit':
            print("  → 會執行: 編輯檔案")
        elif command == 'list' or command == 'ls':
            print("  → 會執行: 列出檔案")
        elif command == 'pwd':
            print("  → 會執行: 顯示路徑")
        elif command == 'models':
            print("  → 會執行: 列出模型")
        elif command == 'chat':
            print("  → 會執行: 對話")
        else:
            print(f"  → ❌ 未知命令: {command}")

if __name__ == "__main__":
    test_commands()