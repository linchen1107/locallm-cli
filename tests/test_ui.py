#!/usr/bin/env python3
"""
測試 LocalLM CLI 的新介面設計
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from models import is_available, list_models
from tools import get_current_path

def test_banner():
    """測試新的橫幅設計"""
    print()
    print("  ╭─────────────────────────────────────────╮")
    print("  │                                         │")
    print("  │          🤖  LocalLM CLI                │")
    print("  │                                         │")
    print("  │      本地模型 × 智能檔案操作              │")
    print("  │                                         │")
    print("  ╰─────────────────────────────────────────╯")
    print()
    
    # 簡化狀態顯示
    status_line = "  "
    if is_available():
        models = list_models()
        model_count = len(models) if models else 0
        status_line += f"✓ Ollama ({model_count} models)"
    else:
        status_line += "✗ Ollama offline"
    
    status_line += f"  •  Model: llama3.2"
    status_line += f"  •  Path: {Path(get_current_path()).name}"
    print(status_line)
    print()
    
    # 簡潔的使用提示
    print("  Commands: /read /write /edit /list /models /help /exit")
    print("  或直接對話提問")
    print()

def test_help():
    """測試新的幫助指令輸出"""
    print("\n")
    print("  ╭─ Commands ─────────────────────────╮")
    print("  │                                    │")
    print("  │  /read <path>     Read file        │")
    print("  │  /write <path>    Write file       │")  
    print("  │  /edit <path>     Edit file        │")
    print("  │  /list [dir]      List files       │")
    print("  │  /pwd             Show path        │")
    print("  │  /models          Show models      │")
    print("  │  /help            This help        │")
    print("  │  /exit            Exit program     │")
    print("  │                                    │")
    print("  │  Or just ask questions naturally  │")
    print("  │                                    │")
    print("  ╰────────────────────────────────────╯")
    print()

def test_command_outputs():
    """測試各種指令的輸出格式"""
    print("=== 測試指令輸出格式 ===")
    print()
    
    # 模擬成功的檔案操作
    print("  ✓ Written: example.txt")
    print("  ✓ Edited: config.json")
    print("  Current: C:\\Users\\will\\Desktop\\locallm-cli")
    print()
    
    # 模擬錯誤情況
    print("  ✗ File not found: missing.txt")
    print("  ✗ Permission denied: protected.sys")
    print("  ⚠ Usage: /read <file_path>")
    print()
    
    # 模擬檔案內容顯示
    print("  ── example.py ──")
    print()
    print("def hello():")
    print("    print('Hello, World!')")
    print()
    
    # 模擬對話
    print("  llama3.2 ›")
    print()
    print("This is a clean, minimalist interface design that focuses on clarity")
    print("and readability. The new layout uses simple symbols and consistent")
    print("spacing to create a professional, uncluttered appearance.")
    print()

if __name__ == "__main__":
    print("🎨 LocalLM CLI - 新的簡約大氣介面設計")
    print("=" * 50)
    
    print("\n1. 啟動橫幅:")
    test_banner()
    
    print("\n2. 幫助指令:")
    test_help()
    
    print("\n3. 指令輸出示例:")
    test_command_outputs()
    
    print("4. 提示符示例:")
    print("  › /help")
    print("  › 請幫我分析一下這個程式")
    print("  › /read main.py")
    print()
    
    print("✨ 設計特點:")
    print("  • 使用簡潔的 Unicode 符號和線框")
    print("  • 統一的縮排和間距")
    print("  • 清晰的狀態指示（✓ ✗ ⚠）")
    print("  • 簡約的提示符（›）")
    print("  • 減少視覺雜訊，提升可讀性")
    print()