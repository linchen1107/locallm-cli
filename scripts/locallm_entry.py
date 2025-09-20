#!/usr/bin/env python3
"""
LocalLM CLI 全域入口點
這個腳本可以從任意位置啟動 LocalLM CLI，同時保持在當前工作目錄運行
"""

import sys
import os
from pathlib import Path

def main():
    # 獲取腳本所在的目錄（scripts 資料夾）
    script_dir = Path(__file__).parent.absolute()
    # 獲取專案根目錄（scripts 的上一層）
    project_root = script_dir.parent
    # 獲取 src 目錄
    src_dir = project_root / "src"
    
    # 將 src 目錄添加到 Python 路徑
    sys.path.insert(0, str(src_dir))
    
    # 保存當前工作目錄
    original_cwd = Path.cwd()
    
    # 暫時切換到 src 目錄以確保模組能正確導入
    os.chdir(src_dir)
    
    try:
        # 導入主程式
        from main import LocalLMCLI  # type: ignore
        import argparse
        
        # 解析命令列參數
        parser = argparse.ArgumentParser(description="LocalLM CLI - 本地模型檔案操作工具")
        parser.add_argument(
            '--model', '-m',
            default='qwen3:8b',
            help='指定使用的模型名稱 (預設: qwen3:8b)'
        )
        
        args = parser.parse_args()
        
        # 切換回原始工作目錄
        os.chdir(original_cwd)
        
        # 創建 CLI 實例，使用原始工作目錄作為基礎路徑
        from tools import FileTools  # type: ignore
        
        # 設置檔案工具的基礎路徑為使用者的當前目錄
        file_tools = FileTools(str(original_cwd))
        
        # 更新預設檔案工具實例
        import tools.file_tools as ft  # type: ignore
        ft.default_file_tools.base_path = original_cwd
        
        # 顯示工作目錄資訊
        print(f"\n  Working in: {original_cwd}")
        
        # 建立並執行 CLI
        cli = LocalLMCLI(default_model=args.model)
        cli.run()
        
    except ImportError as e:
        print(f"錯誤: 無法導入 LocalLM CLI 模組")
        print(f"請確保在正確的目錄中執行，或檢查安裝是否完整")
        print(f"詳細錯誤: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n  程式被使用者中斷")
        sys.exit(0)
    except Exception as e:
        print(f"錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()