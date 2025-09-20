#!/usr/bin/env python3
"""
測試 LocalLM CLI 的檔案創建功能
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from main import LocalLMCLI

def test_file_creation():
    """測試檔案創建功能"""
    print("🧪 測試檔案創建功能")
    print("=" * 40)
    
    # 創建 CLI 實例
    cli = LocalLMCLI()
    
    # 測試案例
    test_cases = [
        "請撰寫一個 hello.txt",
        "create test.py",
        "建立一個 README.md",
        "製作一個 config.json",
        "產生 script.js"
    ]
    
    print("以下是一些使用範例:")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. 輸入: {test_case}")
        
        # 檢查是否會觸發檔案工具
        should_use_tools = cli.should_use_file_tools(test_case)
        print(f"   會觸發檔案工具: {'是' if should_use_tools else '否'}")
        
        if should_use_tools:
            print("   → 會自動識別為檔案創建請求")
        
        print()
    
    print("💡 使用說明:")
    print("- 直接說 '請撰寫一個 hello.txt' 會自動創建檔案")
    print("- 使用 '/create hello.txt' 明確創建檔案")
    print("- AI 會根據檔案類型生成適當內容")
    print("- 支援 .txt, .py, .md, .html, .js, .json 等格式")

if __name__ == "__main__":
    test_file_creation()