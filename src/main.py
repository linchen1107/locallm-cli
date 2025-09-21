#!/usr/bin/env python3
"""
LocalLM CLI - 本地模型驅動的檔案操作命令行工具
一個最小可行產品 (MVP)，提供本地模型驅動的檔案操作功能
"""

import sys
import os
import re
import json
import shutil
import argparse
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional

# 添加 src 目錄到 Python 路徑，這樣可以正確導入同級模組
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from models import chat_stream, list_models, is_available
from tools import read_file, write_file, edit_file, file_exists, list_files, get_current_path
from tools.file_classifier import FileClassifier


class ThinkingAnimation:
    """思考動畫類"""
    
    def __init__(self):
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.running = False
        self.thread = None
        self.message = "Thinking"
    
    def start(self, message: str = "Thinking"):
        """開始動畫"""
        if self.running:
            return
        
        self.message = message
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """停止動畫"""
        self.running = False
        if self.thread:
            self.thread.join()
        # 清除動畫行
        print('\r' + ' ' * (len(self.message) + 10), end='', flush=True)
        print('\r', end='', flush=True)
    
    def _animate(self):
        """動畫循環"""
        i = 0
        while self.running:
            spinner = self.spinner_chars[i % len(self.spinner_chars)]
            print(f'\r  {spinner} {self.message}', end='', flush=True)
            i += 1
            time.sleep(0.1)


class LocalLMCLI:
    """LocalLM CLI 主程式類"""
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """計算兩個字符串的編輯距離"""
        if len(s1) < len(s2):
            return LocalLMCLI.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    def _validate_and_fix_model(self, model_name: str) -> str:
        """驗證模型是否存在，如果不存在則尋找替代方案"""
        try:
            # 首先嘗試獲取可用模型列表
            available_models_data = list_models()
            if not available_models_data:
                print(f"  ⚠ No models available in Ollama")
                return model_name
            
            # 提取模型名稱列表
            available_models = [model.get('name', '') for model in available_models_data]
            
            # 檢查指定的模型是否存在
            if model_name in available_models:
                return model_name
            
            # 如果 qwen3:8b 不存在，嘗試尋找替代方案
            if model_name == "qwen3:8b":
                alternatives = ["qwen3:latest", "qwen3", "llama3.1:8b", "gemma3:12b"]
                for alt in alternatives:
                    if alt in available_models:
                        print(f"  ℹ Model '{model_name}' not found, using '{alt}' instead")
                        return alt
            
            # 如果找不到替代方案，使用第一個可用的模型
            if available_models[0]:
                fallback = available_models[0]
                print(f"  ℹ Model '{model_name}' not found, using '{fallback}' instead")
                return fallback
            
            return model_name
            
        except Exception as e:
            print(f"  ⚠ Error validating model: {e}")
            return model_name
    
    def __init__(self, default_model: str = "qwen3:latest"):
        """
        初始化 CLI
        
        Args:
            default_model: 預設使用的模型名稱
        """
        self.default_model = self._validate_and_fix_model(default_model)
        self.conversation_history: List[Dict] = []
        self.running = True
        self.exit_count = 0  # 用於處理雙重 Ctrl+C 退出
        self.thinking_animation = ThinkingAnimation()  # 思考動畫
        
        # 工作區目錄管理
        self.workspace_config_file = Path.home() / ".locallm" / "workspaces.json"
        self.workspace_directories = self._load_workspace_directories()
        
        # 檢查點系統
        self.checkpoints_dir = Path.home() / ".locallm" / "checkpoints"
        self.checkpoints_file = Path.home() / ".locallm" / "checkpoints.json"
        self.checkpointing_enabled = True  # 可透過設定控制
        self._init_checkpoint_system()
        
        # 儲存的聊天模型管理
        self.saved_models_dir = Path.home() / ".locallm" / "saved_models"
        self.saved_models_file = Path.home() / ".locallm" / "saved_models.json"
        self._init_saved_models_system()
        
    def print_banner(self):
        """顯示程式橫幅"""
        try:
            from rich.console import Console
            from rich.text import Text
            import pyfiglet
            
            console = Console()
            
            # 生成 ASCII 字體
            ascii_text = pyfiglet.figlet_format("LOCALLM")
            
            # 手動創建漸層效果
            lines = ascii_text.strip().split('\n')
            total_lines = len(lines)
            
            print()
            for i, line in enumerate(lines):
                # 計算漸層位置 (0.0 到 1.0)
                gradient_pos = i / max(1, total_lines - 1)
                
                # 青色到橘色的漸層
                if gradient_pos < 0.25:
                    color = "#00CFFF"  # 青色
                elif gradient_pos < 0.5:
                    color = "#00A8FF"  # 淺藍
                elif gradient_pos < 0.75:
                    color = "#FFB347"  # 淺橘
                else:
                    color = "#FF8C42"  # 橘色
                
                console.print(line, style=f"bold {color}")
            
            # 副標題固定顏色：粉紅
            console.print("[bold #FF5FA2]本地模型 × 智能檔案操作[/]", justify="center")
            print()
            
        except (ImportError, AttributeError) as e:
            # 備用方案：使用原本的 ASCII 藝術
            print()
            print("  ██      ██████   ██████  █████  ██      ██      ███    ███")
            print("  ██     ██    ██ ██      ██   ██ ██      ██      ████  ████")
            print("  ██     ██    ██ ██      ███████ ██      ██      ██ ████ ██")
            print("  ██     ██    ██ ██      ██   ██ ██      ██      ██  ██  ██")
            print("  ███████ ██████   ██████ ██   ██ ███████ ███████ ██      ██")
            print()
            print("                 本地模型 × 智能檔案操作")
            print()
        
        # 顯示當前工作目錄
        current_path = Path(get_current_path())
        try:
            home_path = Path.home()
            if current_path.is_relative_to(home_path):
                relative_path = current_path.relative_to(home_path)
                display_path = f"~/{relative_path}" if str(relative_path) != "." else "~"
            else:
                display_path = current_path.name if current_path.name else str(current_path)
        except:
            display_path = current_path.name
            
        print(f"  Working in: {display_path}")
        
        # 狀態顯示
        status_line = "  "
        if is_available():
            models = list_models()
            model_count = len(models) if models else 0
            status_line += f"✓ Ollama ({model_count} models)"
        else:
            status_line += "✗ Ollama offline"
        
        status_line += f"  •  Model: {self.default_model}"
        print(status_line)
        print()
        
        # 簡潔的使用提示
        print("  Tips for getting started:")
        print("  1. Ask questions, edit files, or run commands naturally.")
        print("  2. Be specific for the best results (e.g., 'read 開發問題.txt').")
        print("  3. Use natural language: 'create a Python script' or 'analyze this file'.")
        print("  4. /help for more information and commands.")
        print()
    
    def parse_command(self, input_text: str) -> tuple:
        """
        解析使用者輸入的指令
        
        Args:
            input_text: 使用者輸入
            
        Returns:
            tuple: (命令類型, 參數列表)
        """
        input_text = input_text.strip()
        
        if not input_text.startswith('/'):
            return ('chat', [input_text])
        
        # 移除開頭的 /
        command_line = input_text[1:]
        
        # 使用正規表達式解析指令和參數
        # 支援引號包圍的參數
        parts = re.findall(r'"([^"]*)"|(\S+)', command_line)
        # 正規表達式會返回元組，需要提取非空的部分
        parts = [part[0] if part[0] else part[1] for part in parts]
        
        if not parts:
            return ('unknown', [])
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        return (command, args)
    
    def _load_workspace_directories(self) -> List[str]:
        """載入工作區目錄列表"""
        try:
            if self.workspace_config_file.exists():
                with open(self.workspace_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('directories', [])
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            # 如果無法讀取檔案，返回空列表
            pass
        return []
    
    def _save_workspace_directories(self) -> None:
        """儲存工作區目錄列表"""
        try:
            # 確保配置目錄存在
            self.workspace_config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'directories': self.workspace_directories,
                'last_updated': str(Path().cwd())  # 記錄最後更新時的目錄
            }
            
            with open(self.workspace_config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (PermissionError, OSError) as e:
            print(f"  ⚠ Cannot save workspace config: {e}")
    
    def _resolve_path(self, path_str: str) -> Optional[Path]:
        """解析路徑，支援絕對路徑、相對路徑和家目錄參照"""
        try:
            path_str = path_str.strip()
            
            # 處理家目錄參照
            if path_str.startswith('~'):
                path = Path(path_str).expanduser()
            # 處理絕對路徑
            elif Path(path_str).is_absolute():
                path = Path(path_str)
            # 處理相對路徑
            else:
                path = Path.cwd() / path_str
            
            # 解析為絕對路徑
            path = path.resolve()
            
            return path
        except (OSError, ValueError) as e:
            return None
    
    def _init_checkpoint_system(self) -> None:
        """初始化檢查點系統"""
        try:
            # 確保檢查點目錄存在
            self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果檢查點檔案不存在，創建空的
            if not self.checkpoints_file.exists():
                self._save_checkpoints_index({})
        except (PermissionError, OSError) as e:
            print(f"  ⚠ Cannot initialize checkpoint system: {e}")
            self.checkpointing_enabled = False
    
    def _load_checkpoints_index(self) -> Dict:
        """載入檢查點索引"""
        try:
            if self.checkpoints_file.exists():
                with open(self.checkpoints_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            pass
        return {}
    
    def _save_checkpoints_index(self, checkpoints: Dict) -> None:
        """儲存檢查點索引"""
        try:
            with open(self.checkpoints_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoints, f, indent=2, ensure_ascii=False)
        except (PermissionError, OSError) as e:
            print(f"  ⚠ Cannot save checkpoints index: {e}")
    
    def _create_checkpoint(self, operation_type: str, files_affected: List[str]) -> Optional[str]:
        """創建檢查點"""
        if not self.checkpointing_enabled:
            return None
        
        try:
            from datetime import datetime
            import uuid
            import shutil
            
            # 生成唯一的檢查點 ID
            checkpoint_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 創建檢查點目錄
            checkpoint_dir = self.checkpoints_dir / f"{timestamp}_{checkpoint_id}"
            checkpoint_dir.mkdir(exist_ok=True)
            
            # 備份影響的檔案
            backed_up_files = []
            for file_path in files_affected:
                if Path(file_path).exists():
                    file_name = Path(file_path).name
                    backup_file = checkpoint_dir / file_name
                    shutil.copy2(file_path, backup_file)
                    backed_up_files.append({
                        'original_path': str(Path(file_path).resolve()),
                        'backup_path': str(backup_file),
                        'file_name': file_name
                    })
            
            # 更新檢查點索引
            checkpoints = self._load_checkpoints_index()
            checkpoints[checkpoint_id] = {
                'timestamp': timestamp,
                'operation_type': operation_type,
                'files': backed_up_files,
                'checkpoint_dir': str(checkpoint_dir),
                'created_at': datetime.now().isoformat()
            }
            
            self._save_checkpoints_index(checkpoints)
            return checkpoint_id
            
        except Exception as e:
            print(f"  ⚠ Failed to create checkpoint: {e}")
            return None
    
    def _init_saved_models_system(self) -> None:
        """初始化儲存的聊天模型系統"""
        try:
            # 確保儲存模型目錄存在
            self.saved_models_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果索引檔案不存在，創建空的
            if not self.saved_models_file.exists():
                self._save_models_index({})
        except (PermissionError, OSError) as e:
            print(f"  ⚠ Cannot initialize saved models system: {e}")
    
    def _load_models_index(self) -> Dict:
        """載入儲存的模型索引"""
        try:
            if self.saved_models_file.exists():
                with open(self.saved_models_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            pass
        return {}
    
    def _save_models_index(self, models: Dict) -> None:
        """儲存模型索引"""
        try:
            with open(self.saved_models_file, 'w', encoding='utf-8') as f:
                json.dump(models, f, indent=2, ensure_ascii=False)
        except (PermissionError, OSError) as e:
            print(f"  ⚠ Cannot save models index: {e}")
    
    def _generate_modelfile(self, model_name: str, base_model: str, conversation_history: List[Dict]) -> str:
        """生成 Ollama Modelfile 內容"""
        
        # 將聊天記錄轉換為系統提示
        system_prompt = f"""You are {model_name}, an AI assistant trained from conversation history.

CONVERSATION CONTEXT:
The following is your conversation history that defines your personality and knowledge:

"""
        
        for i, entry in enumerate(conversation_history):
            if entry.get('role') == 'user':
                system_prompt += f"USER: {entry.get('content', '')}\n\n"
            elif entry.get('role') == 'assistant':
                system_prompt += f"ASSISTANT: {entry.get('content', '')}\n\n"
        
        system_prompt += f"""
INSTRUCTIONS:
- Continue conversations in the same style and tone established above
- Reference previous context when relevant
- Maintain consistency with the personality shown in the conversation history
- If asked about your training or background, mention that you were created from conversation history in LocalLM CLI
"""
        
        # 生成 Modelfile
        template_content = "{{ if .System }}<|start_header_id|>system<|end_header_id|>\n\n{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>\n\n{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>\n\n{{ .Response }}<|eot_id|>"
        
        modelfile_content = f"""FROM {base_model}

SYSTEM \"\"\"{system_prompt}\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

TEMPLATE \"\"\"{template_content}\"\"\"
"""
        
        return modelfile_content
    
    def handle_read_command(self, args: List[str]) -> None:
        """處理讀取檔案指令"""
        if not args:
            print("  ⚠ Usage: /read <file_path>")
            print("  支援格式: .txt, .py, .md, .pdf, .docx, .xlsx, .xlsm, .pptx")
            return
        
        file_path = args[0]
        file_ext = file_path.lower().split('.')[-1]
        
        try:
            # 根據檔案類型選擇讀取方法
            if file_ext == 'pdf':
                # 導入 PDF 讀取功能
                from tools import read_pdf
                content = read_pdf(file_path)
                print(f"\n  ── {file_path} (PDF) ──")
            
            elif file_ext == 'docx':
                # 導入 Word 讀取功能
                from tools.file_tools import default_file_tools
                content = default_file_tools.read_word(file_path)
                print(f"\n  ── {file_path} (Word) ──")
            
            elif file_ext in ['xlsx', 'xlsm']:
                # 導入 Excel 讀取功能
                from tools.file_tools import default_file_tools
                # 如果有指定工作表名稱，可以作為第二個參數
                sheet_name = args[1] if len(args) > 1 else None
                content = default_file_tools.read_excel(file_path, sheet_name)
                sheet_info = f" (工作表: {sheet_name})" if sheet_name else ""
                print(f"\n  ── {file_path} (Excel{sheet_info}) ──")
            
            elif file_ext == 'pptx':
                # 導入 PowerPoint 讀取功能
                from tools.file_tools import default_file_tools
                content = default_file_tools.read_powerpoint(file_path)
                print(f"\n  ── {file_path} (PowerPoint) ──")
            
            else:
                # 一般文字檔案
                content = read_file(file_path)
                print(f"\n  ── {file_path} ──")
            
            print()
            print(content)
            print()
            
        except FileNotFoundError:
            print(f"  ✗ File not found: {file_path}")
        except PermissionError:
            print(f"  ✗ Permission denied: {file_path}")
        except ImportError as e:
            print(f"  ✗ 缺少必要的依賴套件: {e}")
            if 'docx' in str(e):
                print("  💡 安裝 Word 支援: pip install python-docx")
            elif 'openpyxl' in str(e):
                print("  💡 安裝 Excel 支援: pip install openpyxl")
            elif 'pptx' in str(e):
                print("  💡 安裝 PowerPoint 支援: pip install python-pptx")
            elif 'PyMuPDF' in str(e):
                print("  💡 安裝 PDF 支援: pip install pymupdf")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def handle_analyze_command(self, args: List[str]) -> None:
        """處理深度分析 PDF 指令"""
        if not args:
            print("  ⚠ Usage: /analyze <pdf_path> [query]")
            print("  Examples:")
            print("    /analyze document.pdf")
            print("    /analyze document.pdf 「這份文件的主要內容是什麼？」")
            return
        
        pdf_path = args[0]
        query = ' '.join(args[1:]) if len(args) > 1 else None
        
        try:
            # 檢查是否為 PDF 文件
            if not pdf_path.lower().endswith('.pdf'):
                print("  ⚠ 分析功能目前只支援 PDF 文件")
                return
            
            # 檢查 RAG 支援
            try:
                from rag import is_rag_available, create_rag_processor
                if not is_rag_available():
                    print("  ✗ RAG 功能不可用，請安裝依賴:")
                    print("    pip install sentence-transformers chromadb")
                    return
            except ImportError:
                print("  ✗ RAG 模組不可用")
                return
            
            # 讀取 PDF 內容
            try:
                from tools import read_pdf
                print(f"  📖 正在讀取 PDF: {pdf_path}")
                pdf_content = read_pdf(pdf_path)
                
                if not pdf_content.strip():
                    print("  ⚠ PDF 內容為空或無法提取文字")
                    return
                
            except Exception as e:
                print(f"  ✗ 無法讀取 PDF: {e}")
                return
            
            # 創建 RAG 處理器
            print("  🔧 初始化 RAG 處理器...")
            rag_processor = create_rag_processor()
            
            # 處理 PDF 文字並建立向量資料庫
            print("  🔄 處理文字並建立向量資料庫...")
            result = rag_processor.process_pdf_text(pdf_content, pdf_path)
            
            print(f"  ✓ 處理完成:")
            print(f"    - 原始長度: {result['original_length']} 字符")
            print(f"    - 清理後長度: {result['cleaned_length']} 字符")
            print(f"    - 分割片段: {result['chunk_count']} 個")
            print(f"    - 向量維度: {result['embedding_dimension']}")
            
            # 如果有查詢，進行搜索和回答
            if query:
                print(f"\n  🔍 搜索查詢: 「{query}」")
                search_results = rag_processor.search_documents(query, n_results=3)
                
                if search_results:
                    print(f"  📋 找到 {len(search_results)} 個相關片段:")
                    for i, result in enumerate(search_results, 1):
                        similarity = result['similarity_score']
                        text_preview = result['text'][:100] + "..." if len(result['text']) > 100 else result['text']
                        print(f"    {i}. 相似度: {similarity:.3f}")
                        print(f"       {text_preview}")
                        print()
                    
                    # 生成 RAG 回答
                    print("  🤖 基於文檔內容的回答:")
                    print("  " + "─" * 50)
                    rag_response = rag_processor.generate_rag_response(query, search_results)
                    print(f"  {rag_response}")
                    print("  " + "─" * 50)
                else:
                    print("  ⚠ 沒有找到相關內容")
            else:
                # 顯示資料庫統計
                stats = rag_processor.get_database_stats()
                print(f"\n  📊 向量資料庫統計:")
                print(f"    - 集合名稱: {stats.get('collection_name', 'N/A')}")
                print(f"    - 文檔數量: {stats.get('document_count', 0)}")
                print(f"    - 存儲路徑: {stats.get('persist_directory', 'N/A')}")
                print("\n  💡 使用 /analyze <pdf_path> <query> 來搜索特定內容")
            
        except Exception as e:
            print(f"  ✗ 分析失敗: {e}")
            import traceback
            print(f"  詳細錯誤: {traceback.format_exc()}")
    
    def handle_ocr_command(self, args: List[str]) -> None:
        """處理 OCR 指令"""
        if not args:
            print("  ⚠ Usage: /ocr <pdf_path>")
            print("  Examples:")
            print("    /ocr scanned_document.pdf")
            print("    /ocr image_based.pdf")
            return
        
        pdf_path = args[0]
        
        try:
            # 檢查是否為 PDF 文件
            if not pdf_path.lower().endswith('.pdf'):
                print("  ⚠ OCR 功能目前只支援 PDF 文件")
                return
            
            # 檢查 OCR 支援
            try:
                from tools.ocr_tools import is_ocr_available, create_ocr_processor, get_ocr_installation_instructions
                
                if not is_ocr_available():
                    print("  ✗ OCR 功能不可用")
                    print("\n  📋 安裝說明:")
                    print(get_ocr_installation_instructions())
                    return
                    
            except ImportError:
                print("  ✗ OCR 模組不可用")
                return
            
            # 檢查文件是否存在
            if not os.path.exists(pdf_path):
                print(f"  ✗ 文件不存在: {pdf_path}")
                return
            
            print(f"  🔍 開始 OCR 處理: {pdf_path}")
            
            # 創建 OCR 處理器
            ocr_processor = create_ocr_processor(language='eng+chi_tra')
            if not ocr_processor:
                print("  ✗ OCR 處理器創建失敗")
                return
            
            # 使用 OCR 提取文字
            print("  ⏳ 正在進行 OCR 識別，請稍候...")
            ocr_text = ocr_processor.extract_text_from_pdf(pdf_path)
            
            if ocr_text.strip():
                print(f"\n  ✅ OCR 識別完成")
                print(f"  📄 識別出的文字內容:")
                print("  " + "─" * 50)
                # 顯示前 500 字符的預覽
                preview = ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text
                print(f"  {preview}")
                print("  " + "─" * 50)
                print(f"  📊 總字符數: {len(ocr_text)}")
                
                # 詢問是否保存結果
                response = input("\n  💾 是否將 OCR 結果保存到文字檔？ (y/N): ").strip().lower()
                if response in ['y', 'yes', '是']:
                    output_path = pdf_path.replace('.pdf', '_ocr.txt')
                    try:
                        from tools import write_file
                        write_file(output_path, ocr_text)
                        print(f"  ✅ OCR 結果已保存至: {output_path}")
                    except Exception as e:
                        print(f"  ✗ 保存失敗: {e}")
            else:
                print("  ⚠ OCR 未能識別出任何文字內容")
                print("  💡 可能原因:")
                print("    - 圖片質量不佳")
                print("    - 字體過小或模糊")
                print("    - 語言設定不正確")
                print("    - PDF 本身沒有文字內容")
        
        except Exception as e:
            print(f"  ✗ OCR 處理失敗: {e}")
    
    def handle_write_command(self, args: List[str]) -> None:
        """處理寫入檔案指令"""
        if len(args) < 2:
            print("  ⚠ Usage: /write <file_path> <content>")
            return
        
        file_path = args[0]
        content = ' '.join(args[1:])  # 將剩餘參數合併為內容
        
        try:
            write_file(file_path, content)
            print(f"  ✓ Written: {file_path}")
        except PermissionError:
            print(f"  ✗ Permission denied: {file_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def handle_edit_command(self, args: List[str]) -> None:
        """處理編輯檔案指令"""
        if len(args) < 2:
            print("  ⚠ Usage: /edit <file_path> <content>")
            return
        
        file_path = args[0]
        new_content = ' '.join(args[1:])
        
        try:
            edit_file(file_path, new_content)
            print(f"  ✓ Edited: {file_path}")
        except PermissionError:
            print(f"  ✗ Permission denied: {file_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def handle_create_command(self, args: List[str]) -> None:
        """處理創建檔案指令"""
        if not args:
            print("  ⚠ Usage: /create <file_path> [content]")
            print("  If no content provided, AI will generate appropriate content")
            return
        
        file_path = args[0]
        
        # 檢查檔案是否已存在
        if file_exists(file_path):
            response = input(f"  ⚠ File {file_path} already exists. Overwrite? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("  ⚠ File creation cancelled")
                return
        
        if len(args) > 1:
            # 有提供內容，直接使用
            content = ' '.join(args[1:])
            try:
                write_file(file_path, content)
                print(f"  ✓ Created: {file_path}")
            except Exception as e:
                print(f"  ✗ Error creating file: {e}")
        else:
            # 沒有提供內容，使用 AI 生成
            creation_request = f"create {file_path}"
            self.handle_file_creation_request(file_path, creation_request)
    
    def handle_list_command(self, args: List[str]) -> None:
        """處理列出檔案指令"""
        directory = args[0] if args else "."
        
        try:
            files = list_files(directory)
            if files:
                print(f"\n  Files in {directory}:")
                for i, file in enumerate(files, 1):
                    print(f"    {i:2d}. {file}")
                print()
            else:
                print(f"  Empty directory: {directory}")
        except FileNotFoundError:
            print(f"  ✗ Directory not found: {directory}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def handle_tree_command(self, args: List[str]) -> None:
        """處理樹狀顯示目錄結構指令"""
        directory = args[0] if args else "."
        max_depth = int(args[1]) if len(args) > 1 and args[1].isdigit() else 3
        
        try:
            from pathlib import Path
            
            def print_tree(path: Path, prefix: str = "", depth: int = 0):
                if depth > max_depth:
                    return
                
                items = []
                try:
                    # 分別收集資料夾和檔案
                    dirs = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith('.')]
                    files = [p for p in path.iterdir() if p.is_file() and not p.name.startswith('.')]
                    items = sorted(dirs) + sorted(files)
                except PermissionError:
                    return
                
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    
                    # 添加類型標示
                    if item.is_dir():
                        icon = "📁"
                        name = f"{icon} {item.name}/"
                    else:
                        # 根據副檔名顯示不同圖示
                        suffix = item.suffix.lower()
                        if suffix in ['.py', '.pyw']:
                            icon = "🐍"
                        elif suffix in ['.js', '.ts', '.jsx', '.tsx']:
                            icon = "📜"
                        elif suffix in ['.md', '.txt', '.doc', '.docx']:
                            icon = "📄"
                        elif suffix in ['.json', '.yaml', '.yml', '.xml']:
                            icon = "⚙️"
                        elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                            icon = "🖼️"
                        else:
                            icon = "📝"
                        name = f"{icon} {item.name}"
                    
                    print(f"  {prefix}{current_prefix}{name}")
                    
                    # 遞迴顯示子目錄
                    if item.is_dir() and depth < max_depth:
                        print_tree(item, next_prefix, depth + 1)
            
            root_path = Path(directory).resolve()
            print(f"\n  📂 {root_path.name if root_path.name else root_path} (depth: {max_depth})")
            print_tree(root_path)
            print()
            
        except FileNotFoundError:
            print(f"  ✗ Directory not found: {directory}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def handle_models_command(self) -> None:
        """處理列出模型指令"""
        models = list_models()
        if models:
            print(f"\n  Available models ({len(models)}):")
            for i, model in enumerate(models, 1):
                name = model.get('name', 'unknown')
                size = model.get('size', 0)
                size_gb = size / (1024 * 1024 * 1024) if size else 0
                if size_gb >= 1:
                    size_str = f"{size_gb:.1f}GB"
                else:
                    size_mb = size / (1024 * 1024) if size else 0
                    size_str = f"{size_mb:.0f}MB"
                
                # 標示當前使用的模型
                current_marker = " ← current" if name == self.default_model else ""
                print(f"    {i:2d}. {name} ({size_str}){current_marker}")
            print()
            print("  💡 Use '/switch <name>' to switch models")
            print()
        else:
            print("  ✗ No models available")
    
    def handle_model_command(self, args: List[str]) -> None:
        """處理切換模型指令"""
        if not args:
            print(f"  Current model: {self.default_model}")
            print("  💡 Use '/switch <name>' to switch models")
            print("  💡 Use '/switch <number>' to switch by number")
            print("  💡 Use '/models' to see available models")
            return
        
        new_model = args[0]
        available_models = list_models()
        model_names = [model.get('name', '') for model in available_models]
        
        # 檢查是否是數字選擇
        if new_model.isdigit():
            model_index = int(new_model) - 1
            if 0 <= model_index < len(model_names):
                new_model = model_names[model_index]
            else:
                print(f"  ❌ Invalid model number: {new_model}")
                print(f"  📝 Available models: 1-{len(model_names)}")
                return
        
        # 模型別名支援
        model_aliases = {
            'llama': 'llama3.2:latest',
            'llama3': 'llama3.2:latest',
            'mistral': 'mistral:7b',
            'codellama': 'codellama:13b',
            'gemma': 'gemma3:12b',
            'phi': 'phi4:14b',
            'qwen': 'qwen3:8b',
            'deepseek': 'deepseek-r1:8b'
        }
        
        # 檢查別名
        if new_model.lower() in model_aliases:
            aliased_model = model_aliases[new_model.lower()]
            if aliased_model in model_names:
                new_model = aliased_model
                print(f"  🔗 Using alias: {args[0]} → {new_model}")
            else:
                print(f"  ⚠️  Alias '{args[0]}' points to '{aliased_model}' but model not found")
        
        # 檢查模型是否存在
        if new_model in model_names:
            old_model = self.default_model
            self.default_model = new_model
            print(f"  ✅ Model switched: {old_model} → {new_model}")
            
            # 清空對話歷史，因為不同模型可能有不同的對話格式
            if self.conversation_history:
                print("  🔄 Conversation history cleared for new model")
                self.conversation_history = []
        else:
            print(f"  ❌ Model '{new_model}' not found")
            print("  💡 Use '/models' to see available models")
            
            # 提供模糊匹配建議
            suggestions = []
            
            # 0. 首先檢查是否與別名相似
            for alias, full_name in model_aliases.items():
                if self.levenshtein_distance(new_model.lower(), alias) <= 2 and full_name in model_names:
                    suggestions.append(f"{full_name} (alias: {alias})")
            
            # 1. 檢查是否包含部分匹配
            for name in model_names:
                if new_model.lower() in name.lower() or name.lower() in new_model.lower():
                    if name not in [s.split(' (alias:')[0] for s in suggestions]:  # 避免重複
                        suggestions.append(name)
            
            # 2. 如果沒有部分匹配，嘗試相似度匹配
            if not suggestions:
                for name in model_names:
                    # 簡單的相似度計算：計算相同字符的比例
                    def similarity(s1, s2):
                        s1, s2 = s1.lower(), s2.lower()
                        common = sum(1 for c in s1 if c in s2)
                        return common / max(len(s1), len(s2))
                    
                    # 如果相似度超過 60%，加入建議
                    if similarity(new_model, name) > 0.6:
                        suggestions.append(name)
            
            # 3. 特別檢查拼寫錯誤的情況
            if not suggestions:
                for name in model_names:
                    name_base = name.split(':')[0].lower()
                    input_base = new_model.split(':')[0].lower()
                    
                    # 如果編輯距離 <= 2，加入建議
                    distance = self.levenshtein_distance(input_base, name_base)
                    if distance <= 2 and len(input_base) >= 3:
                        suggestions.append(name)
            
            if suggestions:
                print("  📝 Did you mean:")
                for suggestion in suggestions[:3]:  # 最多顯示3個建議
                    print(f"     - {suggestion}")
            
            # 顯示可用的別名
            print("  🔗 Available aliases:")
            print("     llama, mistral, codellama, gemma, phi, qwen, deepseek")
    
    def handle_switch_command(self, args: List[str]) -> None:
        """處理切換模型指令 (switch 別名)"""
        self.handle_model_command(args)
    
    def handle_chat_command(self, message: str) -> None:
        """處理對話指令"""
        if not message.strip():
            return
        
        # 檢查是否包含檔案操作的自然語言請求
        if self.should_use_file_tools(message):
            self.handle_natural_file_operation(message)
            return
        
        # 添加系統提示信息（僅在對話歷史為空時）
        if not self.conversation_history:
            system_prompt = self._get_system_prompt()
            self.conversation_history.append({
                "role": "system",
                "content": system_prompt
            })
        
        # 添加使用者訊息到對話歷史
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        print(f"\n  {self.default_model} ›")
        print()
        
        # 使用流式輸出
        assistant_response = ""
        try:
            # 開始思考動畫
            self.thinking_animation.start("Thinking")
            
            # 等待一小段時間讓動畫顯示
            time.sleep(0.5)
            
            # 停止動畫並開始流式輸出
            self.thinking_animation.stop()
            
            for chunk in chat_stream(self.default_model, self.conversation_history):
                print(chunk, end='', flush=True)
                assistant_response += chunk
            
            print("\n")  # 雙換行
            
            # 添加助手回應到對話歷史
            if assistant_response:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_response
                })
                
        except KeyboardInterrupt:
            self.thinking_animation.stop()
            print("\n  ⚠ Interrupted\n")
        except Exception as e:
            self.thinking_animation.stop()
            print(f"\n  ✗ Error: {e}\n")
    
    def should_use_file_tools(self, message: str) -> bool:
        """判斷是否應該使用檔案工具"""
        file_keywords = [
            # 讀取相關
            '讀取', '讀', 'read', '檔案內容', '查看', '顯示', '打開', '開啟',
            '分析', '總結', '重點', '條列', '列出', '數個', '大重點',
            
            # 寫入相關
            '寫入', '寫', 'write', '建立檔案', '創建檔案', '新增檔案', '製作',
            '撰寫', '產生', 'generate', 'create', '創建', '建立', '新增',
            
            # 編輯相關
            '編輯', 'edit', '修改檔案', '更改', '更新', '修改',
            
            # 文件操作
            '檔案', '文件', '文件夾', '資料夾', '目錄', '資料',
            'txt', 'py', 'md', 'json', 'html', 'css', 'js',
            
            # 自然語言模式
            '這個檔案', '這個文件', '那個檔案', '那個文件',
            '檔案名', '文件名', '檔名', '文名'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in file_keywords)
    
    def handle_natural_file_operation(self, message: str) -> None:
        """處理自然語言的檔案操作請求"""
        import re
        
        # 改進的檔案路徑提取
        file_path = self._extract_file_path_from_message(message)
        
        if not file_path:
            print("❌ 無法從訊息中識別檔案路徑")
            print("💡 請嘗試以下格式:")
            print("   • '讀取 開發問題.txt'")
            print("   • '創建 hello.py'")
            print("   • '查看 config.json'")
            return
        
        # 判斷操作類型
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['讀取', '讀', 'read', '分析', '查看', '顯示', '打開', '開啟', '總結', '重點', '條列']):
            print(f"  📖 正在讀取: {file_path}")
            self.handle_read_command([file_path])
            
            # 如果是分析請求，提供額外的AI分析
            if any(word in message_lower for word in ['分析', '總結', '重點', '條列']):
                self._provide_ai_analysis(file_path, message)
                
        elif any(word in message_lower for word in ['撰寫', '產生', 'generate', 'create', '製作', '建立', '創建', '新增']):
            print(f"  ✏️  正在創建: {file_path}")
            self.handle_file_creation_request(file_path, message)
        elif any(word in message_lower for word in ['寫入', '寫', 'write', '編輯', 'edit', '修改', '更改', '更新']):
            print(f"  ✏️  正在寫入: {file_path}")
            self.handle_write_from_message(file_path, message)
        else:
            print("  ⚠ 無法確定檔案操作類型")
            print("  💡 請明確說明要執行的操作")
    
    def _extract_file_path_from_message(self, message: str) -> str:
        """從訊息中提取檔案路徑"""
        import re
        
        # 移除引號
        message = message.replace('"', '').replace("'", '')
        
        # 多種檔案路徑模式
        patterns = [
            # 引號包圍的檔案名
            r'["\']([^"\']+\.[a-zA-Z0-9]+)["\']',
            # 中文描述後的檔案名（支持中文檔名）
            r'(?:讀取|讀|查看|顯示|分析|創建|建立|撰寫|寫入|編輯|修改)\s+([a-zA-Z0-9_\-\.\u4e00-\u9fff]+\.(?:txt|py|md|json|html|css|js|docx|pdf|xlsx|pptx))',
            # 檔案名在句末（支持中文檔名）
            r'([a-zA-Z0-9_\-\.\u4e00-\u9fff]+\.(?:txt|py|md|json|html|css|js|docx|pdf|xlsx|pptx))(?:\s|$|，|。|！|？)',
            # 簡單的檔案名模式（支持中文檔名）
            r'([a-zA-Z0-9_\-\.\u4e00-\u9fff]+\.(?:txt|py|md|json|html|css|js|docx|pdf|xlsx|pptx))',
            # Windows 絕對路徑
            r'([a-zA-Z]:[\\\/][^"\s]+)',
            # 相對路徑
            r'([\.\/][^"\s]+\.[a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                # 返回第一個匹配的檔案路徑
                file_path = matches[0].strip()
                # 檢查檔案是否存在於當前目錄
                if self._file_exists_in_current_dir(file_path):
                    return file_path
                # 如果不存在，也返回路徑讓用戶知道
                return file_path
        
        return None
    
    def _file_exists_in_current_dir(self, file_path: str) -> bool:
        """檢查檔案是否存在於當前目錄"""
        try:
            current_dir = Path.cwd()
            full_path = current_dir / file_path
            return full_path.exists() and full_path.is_file()
        except:
            return False
    
    def _provide_ai_analysis(self, file_path: str, original_message: str) -> None:
        """提供AI分析"""
        try:
            # 讀取檔案內容
            content = read_file(file_path)
            if not content.strip():
                print("  ⚠ 檔案內容為空")
                return
            
            # 準備分析提示
            analysis_prompt = f"""請分析以下檔案內容，並根據用戶的要求提供分析：

檔案名稱: {file_path}
用戶要求: {original_message}

檔案內容:
{content[:2000]}  # 限制內容長度避免過長

請提供簡潔的分析結果，包括：
1. 主要內容概述
2. 重要重點或問題
3. 具體建議（如適用）

請用繁體中文回答。"""
            
            # 使用AI進行分析
            messages = [{"role": "user", "content": analysis_prompt}]
            
            print(f"\n  🤖 AI 分析結果:")
            print("  " + "─" * 50)
            
            # 開始思考動畫
            self.thinking_animation.start("Analyzing")
            
            # 等待一小段時間讓動畫顯示
            time.sleep(0.3)
            
            # 停止動畫並開始流式輸出
            self.thinking_animation.stop()
            
            analysis_response = ""
            for chunk in chat_stream(self.default_model, messages):
                print(chunk, end='', flush=True)
                analysis_response += chunk
            
            print("\n  " + "─" * 50)
            
        except Exception as e:
            self.thinking_animation.stop()
            print(f"\n  ⚠ AI 分析失敗: {e}")
    
    def handle_file_creation_request(self, file_path: str, original_message: str) -> None:
        """處理檔案創建請求，使用 AI 生成內容"""
        print(f"  🤖 Generating content for {file_path}...")
        
        # 準備 AI 提示
        file_extension = Path(file_path).suffix.lower()
        
        # 根據檔案類型準備提示
        if file_extension == '.txt':
            prompt = f"請根據使用者的要求創建一個文字檔案的內容。使用者的要求是：{original_message}\n\n請直接提供檔案內容，不要加上其他說明文字。"
        elif file_extension == '.py':
            prompt = f"請根據使用者的要求創建一個 Python 程式檔案。使用者的要求是：{original_message}\n\n請提供完整的 Python 程式碼，包含適當的註解。"
        elif file_extension == '.md':
            prompt = f"請根據使用者的要求創建一個 Markdown 檔案。使用者的要求是：{original_message}\n\n請提供格式化的 Markdown 內容。"
        elif file_extension == '.html':
            prompt = f"請根據使用者的要求創建一個 HTML 檔案。使用者的要求是：{original_message}\n\n請提供完整的 HTML 結構。"
        elif file_extension == '.js':
            prompt = f"請根據使用者的要求創建一個 JavaScript 檔案。使用者的要求是：{original_message}\n\n請提供完整的 JavaScript 程式碼。"
        elif file_extension == '.json':
            prompt = f"請根據使用者的要求創建一個 JSON 檔案。使用者的要求是：{original_message}\n\n請提供有效的 JSON 格式內容。"
        else:
            prompt = f"請根據使用者的要求創建檔案內容。使用者的要求是：{original_message}\n\n請提供適合的檔案內容。"
        
        # 使用 AI 生成內容
        try:
            messages = [{"role": "user", "content": prompt}]
            
            print(f"  {self.default_model} ›")
            print()
            
            # 開始思考動畫
            self.thinking_animation.start("Creating")
            
            # 等待一小段時間讓動畫顯示
            time.sleep(0.3)
            
            # 停止動畫並開始流式輸出
            self.thinking_animation.stop()
            
            generated_content = ""
            for chunk in chat_stream(self.default_model, messages):
                print(chunk, end='', flush=True)
                generated_content += chunk
            
            print("\n")
            
            if generated_content.strip():
                # 清理生成的內容（移除可能的前後說明文字）
                content_lines = generated_content.strip().split('\n')
                
                # 如果第一行看起來像說明文字，跳過它
                if content_lines and any(word in content_lines[0].lower() for word in ['這是', '以下是', 'here is', 'here\'s']):
                    content_lines = content_lines[1:]
                
                # 如果最後幾行看起來像說明文字，移除它們
                while content_lines and any(word in content_lines[-1].lower() for word in ['希望', '這個', '以上', '請注意']):
                    content_lines.pop()
                
                final_content = '\n'.join(content_lines).strip()
                
                if final_content:
                    # 寫入檔案
                    write_file(file_path, final_content)
                    print(f"  ✓ Created: {file_path}")
                    print(f"  📄 Content length: {len(final_content)} characters")
                else:
                    print(f"  ⚠ Generated content is empty")
            else:
                print(f"  ⚠ No content generated")
                
        except Exception as e:
            self.thinking_animation.stop()
            print(f"  ✗ Error generating content: {e}")
    
    def handle_write_from_message(self, file_path: str, message: str) -> None:
        """從訊息中提取內容並寫入檔案"""
        # 嘗試從訊息中提取要寫入的內容
        import re
        
        # 尋找引號內的內容
        quoted_content = re.findall(r'"([^"]*)"', message)
        if quoted_content:
            content = quoted_content[0]
            write_file(file_path, content)
            print(f"  ✓ Written: {file_path}")
            return
        
        # 如果沒有引號，使用 AI 生成內容
        print(f"  🤖 No explicit content found, generating content...")
        self.handle_file_creation_request(file_path, message)
    
    def handle_help_command(self) -> None:
        """顯示幫助資訊"""
        print("\n  📚 LocalLM CLI 命令說明")
        print("  " + "─" * 40)
        print()
        print("  🔤 自然語言命令 (推薦使用):")
        print("     • '讀取 開發問題.txt 並總結重點'")
        print("     • '創建一個 Python 腳本'")
        print("     • '列出當前目錄的檔案'")
        print("     • '分析 config.json 的內容'")
        print()
        print("  📁 檔案操作:")
        print("     /read <檔案>    讀取檔案內容")
        print("     /write <檔案>   寫入檔案")
        print("     /create <檔案>  創建新檔案")
        print("     /list [目錄]    列出檔案")
        print("     /tree [目錄]    樹狀顯示")
        print()
        print("  🛠️  系統操作:")
        print("     /mkdir <目錄>   創建目錄")
        print("     /cd <目錄>     切換目錄")
        print("     /mv <來源> <目標>  移動/重命名")
        print("     /cp <來源> <目標>  複製檔案")
        print("     /rm <檔案>     刪除檔案")
        print()
        print("  ⚙️  其他功能:")
        print("     /models         顯示可用模型")
        print("     /switch <模型>  切換模型")
        print("     /clear         清除畫面")
        print("     /bye           清除對話歷史")
        print("     /exit          退出程式")
        print()
        print("  💡 提示: 直接說出您的需求，AI 會自動理解並執行!")
        print()
    
    def handle_clear_command(self) -> None:
        """清除終端畫面與 CLI 歷史記錄（僅視覺）"""
        os.system('cls' if os.name == 'nt' else 'clear')
        self.conversation_history.clear()
        print("\n  [畫面已清除]\n")
    
    def handle_bye_command(self, args: Optional[List[str]] = None) -> None:
        """清空對話歷史並重新開始（類似 Ollama 的 /bye）"""
        history_count = len(self.conversation_history)
        
        if history_count > 0:
            self.conversation_history.clear()
            print(f"  👋 Bye! Cleared {history_count} conversation entries")
            print(f"  🔄 Restarted fresh session with {self.default_model}")
        else:
            print("  👋 Bye! (No conversation history to clear)")
        
        print(f"  💭 Ready for a new conversation...")
        print()
    
    def handle_load_command(self, args: List[str]) -> None:
        """重新載入指定模型並清空歷史記錄"""
        if not args:
            # 如果沒有指定模型，重新載入當前模型
            self.handle_load_command([self.default_model])
            return
        
        new_model = args[0]
        
        # 檢查模型是否存在
        from models import list_models
        available_models = list_models()
        
        if not available_models:
            print("  ❌ Cannot get model list from Ollama")
            return
        
        # 建立模型名稱列表（包含別名）
        model_names = set()
        for model in available_models:
            name = model.get('name', '')
            if name:
                model_names.add(name)
                # 添加不帶標籤的版本
                if ':' in name:
                    base_name = name.split(':')[0]
                    model_names.add(base_name)
        
        # 檢查模型是否存在
        if new_model not in model_names:
            print(f"  ❌ Model '{new_model}' not found")
            print("  💡 Use '/models' to see available models")
            return
        
        # 記錄舊狀態
        old_model = self.default_model
        history_count = len(self.conversation_history)
        
        # 更新模型
        self.default_model = new_model
        
        # 清空對話歷史
        self.conversation_history.clear()
        
        # 顯示結果
        if old_model == new_model:
            print(f"  🔄 Reloaded model: {new_model}")
        else:
            print(f"  🔄 Loaded model: {old_model} → {new_model}")
        
        if history_count > 0:
            print(f"  🧹 Cleared {history_count} conversation entries")
        
        print(f"  ✨ Fresh start with {new_model}")
        print()
    
    def handle_restore_command(self, args: List[str]) -> None:
        """處理檔案還原指令"""
        if not self.checkpointing_enabled:
            print("  ⚠ Checkpointing is disabled")
            print("  Enable with --checkpointing option or in settings")
            return
        
        checkpoints = self._load_checkpoints_index()
        
        # 如果沒有指定檢查點 ID，列出所有可用的檢查點
        if not args:
            if not checkpoints:
                print("  ℹ No checkpoints available")
                print("  Checkpoints are created automatically during file operations")
                return
            
            print(f"  📋 Available Checkpoints ({len(checkpoints)}):")
            print()
            
            # 依時間排序檢查點
            sorted_checkpoints = sorted(
                checkpoints.items(), 
                key=lambda x: x[1]['timestamp'], 
                reverse=True
            )
            
            for checkpoint_id, info in sorted_checkpoints:
                timestamp = info['timestamp']
                operation = info['operation_type']
                file_count = len(info['files'])
                
                # 格式化時間戳記
                try:
                    from datetime import datetime
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_time = timestamp
                
                print(f"    🔖 {checkpoint_id}")
                print(f"       Time: {formatted_time}")
                print(f"       Operation: {operation}")
                print(f"       Files: {file_count} file{'s' if file_count != 1 else ''}")
                
                # 顯示涉及的檔案名稱
                file_names = [f['file_name'] for f in info['files']]
                if file_names:
                    if len(file_names) <= 3:
                        print(f"       → {', '.join(file_names)}")
                    else:
                        print(f"       → {', '.join(file_names[:3])} and {len(file_names)-3} more...")
                print()
            
            print("  Use '/restore <checkpoint_id>' to restore files")
            return
        
        # 還原指定的檢查點
        checkpoint_id = args[0]
        
        if checkpoint_id not in checkpoints:
            print(f"  ✗ Checkpoint not found: {checkpoint_id}")
            print("  Use '/restore' to list available checkpoints")
            return
        
        try:
            import shutil
            
            checkpoint_info = checkpoints[checkpoint_id]
            restored_files = []
            failed_files = []
            
            print(f"  🔄 Restoring checkpoint {checkpoint_id}...")
            
            for file_info in checkpoint_info['files']:
                original_path = file_info['original_path']
                backup_path = file_info['backup_path']
                file_name = file_info['file_name']
                
                try:
                    if Path(backup_path).exists():
                        # 確保目標目錄存在
                        Path(original_path).parent.mkdir(parents=True, exist_ok=True)
                        
                        # 還原檔案
                        shutil.copy2(backup_path, original_path)
                        restored_files.append(file_name)
                        print(f"    ✓ Restored: {file_name}")
                    else:
                        failed_files.append(f"{file_name} (backup not found)")
                        print(f"    ✗ Backup not found: {file_name}")
                        
                except Exception as e:
                    failed_files.append(f"{file_name} ({str(e)})")
                    print(f"    ✗ Failed to restore {file_name}: {e}")
            
            # 總結
            print()
            if restored_files:
                print(f"  ✅ Successfully restored {len(restored_files)} file{'s' if len(restored_files) != 1 else ''}")
            
            if failed_files:
                print(f"  ⚠ Failed to restore {len(failed_files)} file{'s' if len(failed_files) != 1 else ''}: {', '.join(failed_files)}")
                
        except Exception as e:
            print(f"  ✗ Restore operation failed: {e}")
    
    def handle_directory_command(self, args: List[str]) -> None:
        """處理工作區目錄管理指令"""
        if not args:
            print("  ⚠ Usage: /directory <add|show> [paths...]")
            print("  Examples:")
            print("    /directory add /path/to/project")
            print("    /directory add ~/Documents/project1,~/Desktop/project2")
            print("    /directory show")
            print("    /dir add ./src")  # 短形式
            return
        
        subcommand = args[0].lower()
        
        if subcommand == 'add':
            if len(args) < 2:
                print("  ⚠ Usage: /directory add <path1>[,<path2>,...]")
                print("  Examples:")
                print("    /directory add /absolute/path/to/project")
                print("    /directory add ~/Documents/project")
                print("    /directory add ./relative/path")
                print("    /directory add /path1,/path2,/path3")
                return
            
            # 處理逗號分隔的多個路徑
            paths_to_add = []
            path_strings = []
            
            # 合併所有參數，然後按逗號分割
            all_paths_str = ' '.join(args[1:])
            path_candidates = [p.strip() for p in all_paths_str.split(',') if p.strip()]
            
            for path_str in path_candidates:
                resolved_path = self._resolve_path(path_str)
                if resolved_path is None:
                    print(f"  ⚠ Invalid path format: {path_str}")
                    continue
                
                if not resolved_path.exists():
                    print(f"  ⚠ Path does not exist: {resolved_path}")
                    continue
                
                if not resolved_path.is_dir():
                    print(f"  ⚠ Path is not a directory: {resolved_path}")
                    continue
                
                abs_path_str = str(resolved_path)
                if abs_path_str not in self.workspace_directories:
                    paths_to_add.append(abs_path_str)
                    path_strings.append(path_str)
                else:
                    print(f"  ℹ Already in workspace: {path_str} -> {resolved_path}")
            
            if paths_to_add:
                self.workspace_directories.extend(paths_to_add)
                self._save_workspace_directories()
                
                print(f"  ✓ Added {len(paths_to_add)} director{'y' if len(paths_to_add) == 1 else 'ies'} to workspace:")
                for orig, resolved in zip(path_strings, paths_to_add):
                    print(f"    {orig} -> {resolved}")
            else:
                print("  ℹ No new directories were added to workspace")
        
        elif subcommand == 'show':
            if not self.workspace_directories:
                print("  ℹ No directories in workspace")
                print("  Use '/directory add <path>' to add directories")
                return
            
            print(f"  📁 Workspace Directories ({len(self.workspace_directories)}):")
            print()
            
            current_dir = str(Path.cwd())
            for i, dir_path in enumerate(self.workspace_directories, 1):
                path_obj = Path(dir_path)
                
                # 檢查目錄是否仍然存在
                if path_obj.exists():
                    status = "✓"
                    # 如果是當前目錄，標記出來
                    if dir_path == current_dir:
                        status = "🔸 (current)"
                    
                    # 嘗試顯示相對於家目錄的路徑
                    try:
                        home_path = Path.home()
                        if path_obj.is_relative_to(home_path):
                            relative_path = path_obj.relative_to(home_path)
                            display_path = f"~/{relative_path}"
                        else:
                            display_path = str(path_obj)
                    except (ValueError, OSError):
                        display_path = str(path_obj)
                    
                    print(f"    {i:2d}. {status} {display_path}")
                else:
                    print(f"    {i:2d}. ✗ {dir_path} (not found)")
            
            print()
            print("  Use '/tree' or '/ls' to browse current directory")
        
        elif subcommand in ('remove', 'rm', 'delete'):
            print("  ℹ Directory removal not yet implemented")
            print("  You can manually edit ~/.locallm/workspaces.json")
        
        else:
            print(f"  ✗ Unknown subcommand: {subcommand}")
            print("  Available subcommands: add, show")
    
    def handle_save_command(self, args: List[str]) -> None:
        """儲存當前聊天記錄為新的 Ollama 模型"""
        if not args:
            print("  ⚠ Usage: /save <model_name> [base_model]")
            print("  Examples:")
            print("    /save translator")
            print("    /save my_assistant llama3.2")
            print("    /save coding_helper deepseek-coder:6.7b")
            return
        
        model_name = args[0]
        base_model = args[1] if len(args) > 1 else self.default_model
        
        # 驗證模型名稱
        if not model_name.replace('-', '').replace('_', '').isalnum():
            print("  ⚠ Model name should only contain letters, numbers, hyphens, and underscores")
            return
        
        # 檢查是否有聊天記錄
        if not self.conversation_history:
            print("  ⚠ No conversation history to save")
            print("  Start a conversation first, then use /save to create a model")
            return
        
        try:
            import subprocess
            import tempfile
            from datetime import datetime
            
            print(f"  💾 Saving conversation as model '{model_name}'...")
            print(f"  📋 Conversation entries: {len(self.conversation_history)}")
            print(f"  🎯 Base model: {base_model}")
            
            # 生成 Modelfile 內容
            modelfile_content = self._generate_modelfile(model_name, base_model, self.conversation_history)
            
            # 創建臨時 Modelfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.Modelfile', delete=False, encoding='utf-8') as f:
                f.write(modelfile_content)
                modelfile_path = f.name
            
            # 使用 ollama create 創建模型
            print(f"  🔨 Creating Ollama model...")
            
            create_cmd = ['ollama', 'create', model_name, '-f', modelfile_path]
            result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=300)
            
            # 清理臨時檔案
            Path(modelfile_path).unlink(missing_ok=True)
            
            if result.returncode == 0:
                # 儲存模型資訊到索引
                models_index = self._load_models_index()
                models_index[model_name] = {
                    'created_at': datetime.now().isoformat(),
                    'base_model': base_model,
                    'conversation_entries': len(self.conversation_history),
                    'model_size': 'unknown',  # Ollama 不提供簡單的方式獲取大小
                    'description': f'Saved from LocalLM CLI conversation with {len(self.conversation_history)} entries'
                }
                self._save_models_index(models_index)
                
                print(f"  ✅ Model '{model_name}' created successfully!")
                print()
                print(f"  🚀 To use this model:")
                print(f"     ollama run {model_name}")
                print()
                print(f"  🗑️  To remove this model:")
                print(f"     ollama rm {model_name}")
                
            else:
                print(f"  ✗ Failed to create model: {result.stderr}")
                if "model not found" in result.stderr.lower():
                    print(f"  💡 Base model '{base_model}' not found. Try:")
                    print(f"     ollama pull {base_model}")
                
        except subprocess.TimeoutExpired:
            print("  ⚠ Model creation timed out (>5 minutes)")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Command failed: {e}")
        except Exception as e:
            print(f"  ✗ Error saving model: {e}")
    
    def handle_saved_command(self, args: Optional[List[str]]) -> None:
        """管理儲存的聊天模型"""
        if not args:
            # 列出所有儲存的模型
            models_index = self._load_models_index()
            
            if not models_index:
                print("  ℹ No saved conversation models")
                print("  Use '/save <model_name>' to save current conversation as a model")
                return
            
            print(f"  🤖 Saved Conversation Models ({len(models_index)}):")
            print()
            
            # 按創建時間排序
            sorted_models = sorted(
                models_index.items(),
                key=lambda x: x[1].get('created_at', ''),
                reverse=True
            )
            
            for model_name, info in sorted_models:
                created_at = info.get('created_at', 'unknown')
                base_model = info.get('base_model', 'unknown')
                entries = info.get('conversation_entries', 0)
                description = info.get('description', 'No description')
                
                # 格式化時間
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = created_at
                
                print(f"    📦 {model_name}")
                print(f"       Created: {formatted_time}")
                print(f"       Base: {base_model}")
                print(f"       Conversations: {entries} entries")
                print(f"       Description: {description}")
                print()
            
            print("  🚀 To use a model: ollama run <model_name>")
            print("  🗑️  To remove a model: ollama rm <model_name>")
            print("  📋 To see all Ollama models: /models")
            return
        
        subcommand = args[0].lower()
        
        if subcommand == 'remove' or subcommand == 'rm':
            if len(args) < 2:
                print("  ⚠ Usage: /saved remove <model_name>")
                return
            
            model_name = args[1]
            
            try:
                import subprocess
                
                print(f"  🗑️  Removing model '{model_name}'...")
                
                # 使用 ollama rm 刪除模型
                result = subprocess.run(['ollama', 'rm', model_name], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # 從索引中移除
                    models_index = self._load_models_index()
                    if model_name in models_index:
                        del models_index[model_name]
                        self._save_models_index(models_index)
                    
                    print(f"  ✅ Model '{model_name}' removed successfully!")
                else:
                    print(f"  ⚠ Failed to remove model: {result.stderr}")
                    if "model not found" in result.stderr.lower():
                        # 即使 Ollama 中不存在，也從索引中移除
                        models_index = self._load_models_index()
                        if model_name in models_index:
                            del models_index[model_name]
                            self._save_models_index(models_index)
                            print(f"  🧹 Cleaned up model from saved models index")
                        
            except subprocess.TimeoutExpired:
                print("  ⚠ Remove operation timed out")
            except Exception as e:
                print(f"  ✗ Error removing model: {e}")
        
        elif subcommand == 'clean':
            # 清理不存在的模型
            self._clean_saved_models_index()
            
        else:
            print(f"  ✗ Unknown subcommand: {subcommand}")
            print("  Available subcommands: remove, clean")
    
    def _clean_saved_models_index(self) -> None:
        """清理索引中不存在的模型"""
        try:
            import subprocess
            
            print("  🧹 Cleaning saved models index...")
            
            # 獲取 Ollama 中的實際模型列表
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print("  ⚠ Could not get Ollama model list")
                return
            
            # 解析 ollama list 輸出
            existing_models = set()
            for line in result.stdout.split('\n')[1:]:  # 跳過標題行
                if line.strip():
                    model_name = line.split()[0]
                    if ':' not in model_name or model_name.endswith(':latest'):
                        model_name = model_name.replace(':latest', '')
                    existing_models.add(model_name)
            
            # 檢查索引中的模型
            models_index = self._load_models_index()
            removed_count = 0
            
            for model_name in list(models_index.keys()):
                if model_name not in existing_models:
                    del models_index[model_name]
                    removed_count += 1
                    print(f"    ✓ Removed '{model_name}' from index (not found in Ollama)")
            
            if removed_count > 0:
                self._save_models_index(models_index)
                print(f"  ✅ Cleaned {removed_count} model{'s' if removed_count != 1 else ''} from index")
            else:
                print("  ✅ Index is already clean")
                
        except Exception as e:
            print(f"  ✗ Error cleaning index: {e}")
    
    def handle_init_command(self, args: List[str]) -> None:
        """分析專案目錄並生成 GEMINI.md 指示檔案"""
        target_dir = Path.cwd()
        
        # 如果指定了目錄參數
        if args:
            resolved_path = self._resolve_path(args[0])
            if resolved_path and resolved_path.exists() and resolved_path.is_dir():
                target_dir = resolved_path
            else:
                print(f"  ⚠ Invalid directory: {args[0]}")
                return
        
        gemini_file = target_dir / "GEMINI.md"
        
        print(f"  🔍 Analyzing project directory: {target_dir}")
        print(f"  📝 Generating GEMINI.md...")
        
        try:
            # 分析專案結構
            project_info = self._analyze_project_structure(target_dir)
            
            # 生成 GEMINI.md 內容
            gemini_content = self._generate_gemini_content(project_info, target_dir)
            
            # 檢查是否已存在 GEMINI.md
            if gemini_file.exists():
                print(f"  ⚠ GEMINI.md already exists")
                response = input("  Overwrite existing file? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("  ✗ Operation cancelled")
                    return
            
            # 寫入檔案
            with open(gemini_file, 'w', encoding='utf-8') as f:
                f.write(gemini_content)
            
            print(f"  ✅ GEMINI.md created successfully!")
            print(f"  📄 File location: {gemini_file}")
            print()
            print("  💡 You can now use this file to provide context to Gemini agents")
            print("  📖 Edit the file to add project-specific instructions")
            
        except Exception as e:
            print(f"  ✗ Failed to create GEMINI.md: {e}")
    
    def _analyze_project_structure(self, project_dir: Path) -> Dict:
        """分析專案結構並收集資訊"""
        info = {
            'name': project_dir.name,
            'path': str(project_dir),
            'files': [],
            'directories': [],
            'languages': set(),
            'frameworks': set(),
            'config_files': [],
            'doc_files': [],
            'total_files': 0,
            'project_type': 'unknown'
        }
        
        # 定義檔案類型和框架標識
        language_extensions = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#',
            '.php': 'PHP', '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust',
            '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS', '.less': 'LESS',
            '.vue': 'Vue.js', '.jsx': 'React', '.tsx': 'React/TypeScript'
        }
        
        framework_files = {
            'package.json': 'Node.js/npm',
            'requirements.txt': 'Python',
            'Pipfile': 'Python/Pipenv', 
            'pyproject.toml': 'Python',
            'Cargo.toml': 'Rust',
            'pom.xml': 'Java/Maven',
            'build.gradle': 'Java/Gradle',
            'composer.json': 'PHP/Composer',
            'Gemfile': 'Ruby/Bundler'
        }
        
        config_patterns = [
            '.gitignore', '.env', 'docker-compose.yml', 'Dockerfile',
            'tsconfig.json', 'webpack.config.js', 'vite.config.js',
            'next.config.js', '.eslintrc', 'pytest.ini', 'setup.cfg'
        ]
        
        doc_patterns = [
            'README.md', 'README.txt', 'CHANGELOG.md', 'LICENSE',
            'CONTRIBUTING.md', 'docs/', 'documentation/'
        ]
        
        try:
            # 遍歷目錄（避免深度過深和隱藏目錄）
            for item in project_dir.rglob('*'):
                if item.is_file():
                    # 跳過隱藏檔案和特定目錄
                    if any(part.startswith('.') for part in item.parts if part != item.name) or \
                       any(part in ['node_modules', '__pycache__', '.git', 'dist', 'build'] for part in item.parts):
                        continue
                    
                    info['total_files'] += 1
                    relative_path = item.relative_to(project_dir)
                    
                    # 檢查語言
                    suffix = item.suffix.lower()
                    if suffix in language_extensions:
                        info['languages'].add(language_extensions[suffix])
                    
                    # 檢查框架和配置檔案
                    if item.name in framework_files:
                        info['frameworks'].add(framework_files[item.name])
                        info['config_files'].append(str(relative_path))
                    
                    # 檢查配置檔案
                    if any(pattern in item.name.lower() for pattern in config_patterns):
                        info['config_files'].append(str(relative_path))
                    
                    # 檢查文檔檔案
                    if any(pattern.lower() in str(relative_path).lower() for pattern in doc_patterns):
                        info['doc_files'].append(str(relative_path))
                    
                    # 限制顯示的檔案數量
                    if len(info['files']) < 50:
                        info['files'].append(str(relative_path))
                
                elif item.is_dir() and len(info['directories']) < 20:
                    relative_path = item.relative_to(project_dir)
                    if not any(part.startswith('.') for part in relative_path.parts):
                        info['directories'].append(str(relative_path))
        
        except Exception as e:
            print(f"  ⚠ Error analyzing directory: {e}")
        
        # 推斷專案類型
        if 'Python' in info['languages']:
            if 'requirements.txt' in [f.split('/')[-1] for f in info['config_files']]:
                info['project_type'] = 'Python Application'
            else:
                info['project_type'] = 'Python Project'
        elif 'JavaScript' in info['languages'] or 'TypeScript' in info['languages']:
            if 'Node.js/npm' in info['frameworks']:
                info['project_type'] = 'Node.js Project'
        elif 'Java' in info['languages']:
            info['project_type'] = 'Java Project'
        
        return info
    
    def _generate_gemini_content(self, project_info: Dict, project_dir: Path) -> str:
        """生成 GEMINI.md 內容"""
        content = f"""# {project_info['name']} - Gemini AI Instructions

Generated by LocalLM CLI on {Path().cwd()}

## Project Overview

**Project Name:** {project_info['name']}
**Project Type:** {project_info['project_type']}
**Location:** {project_info['path']}
**Total Files:** {project_info['total_files']}

## Technology Stack

"""
        
        if project_info['languages']:
            content += "**Languages:** " + ", ".join(sorted(project_info['languages'])) + "\n\n"
        
        if project_info['frameworks']:
            content += "**Frameworks/Tools:** " + ", ".join(sorted(project_info['frameworks'])) + "\n\n"
        
        # 專案結構
        content += "## Project Structure\n\n"
        
        if project_info['directories']:
            content += "**Key Directories:**\n"
            for dir_path in sorted(project_info['directories'][:10]):
                content += f"- `{dir_path}/`\n"
            content += "\n"
        
        if project_info['config_files']:
            content += "**Configuration Files:**\n"
            for config_file in sorted(project_info['config_files'][:10]):
                content += f"- `{config_file}`\n"
            content += "\n"
        
        if project_info['doc_files']:
            content += "**Documentation:**\n"
            for doc_file in sorted(project_info['doc_files'][:5]):
                content += f"- `{doc_file}`\n"
            content += "\n"
        
        # AI 指示
        content += """## Instructions for AI Assistants

### General Guidelines
- This project uses the technologies listed above
- Follow best practices for the identified programming languages
- Respect the existing project structure and naming conventions
- Preserve any configuration files and their formats

### Code Style & Standards
- Maintain consistency with existing code patterns
- Add appropriate comments and documentation
- Follow the project's dependency management approach

### When Making Changes
- Always backup important files before modifications
- Test changes in development environment first  
- Update documentation if adding new features
- Consider backwards compatibility

### Project-Specific Notes

**TODO:** Add project-specific instructions here, such as:
- Special coding conventions
- Deployment procedures  
- Testing requirements
- Business logic explanations
- API documentation links
- Development workflow notes

## File Operations

This project can be managed using LocalLM CLI commands:
- `/read <file>` - Read files (txt, pdf, docx, xlsx, pptx)
- `/write <file>` - Write new files  
- `/edit <file>` - Edit existing files
- `/tree` - View project structure
- `/patch <file>` - Safe code modifications with auto-backup
- `/restore` - Restore from checkpoints if available

---
*This file was auto-generated. Please customize it with project-specific instructions.*
"""
        
        return content
    
    def handle_patch_command(self, args: List[str]) -> None:
        """安全地做小幅程式碼變更，並自動備份"""
        if not args:
            print("  ✗ Usage: /patch <file> [old_text->new_text]")
            print("  Example: /patch main.py 'old_code'->'new_code'")
            print("  Example: /patch config.json  (interactive mode)")
            return
        
        filepath = args[0]
        
        try:
            from datetime import datetime
            import shutil
            
            # 檢查檔案是否存在
            if not file_exists(filepath):
                print(f"  ✗ File not found: {filepath}")
                return
            
            # 自動備份
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{filepath}.backup_{timestamp}"
            shutil.copy2(filepath, backup_path)
            print(f"  📦 Backup created: {backup_path}")
            
            # 讀取原始內容
            original_content = read_file(filepath)
            if not original_content:
                print(f"  ✗ Could not read file: {filepath}")
                return
            
            # 如果有指定變更內容
            if len(args) > 1:
                change_spec = " ".join(args[1:])
                
                # 解析 'old->new' 格式
                if '->' in change_spec:
                    parts = change_spec.split('->', 1)
                    if len(parts) == 2:
                        old_text = parts[0].strip().strip("'\"")
                        new_text = parts[1].strip().strip("'\"")
                        
                        if old_text in original_content:
                            new_content = original_content.replace(old_text, new_text, 1)  # 只替換第一個
                            
                            # 安全寫入
                            if write_file(filepath, new_content):
                                print(f"  ✅ Patched: {filepath}")
                                print(f"  📝 Changed: '{old_text}' -> '{new_text}'")
                                print(f"  💾 Backup: {backup_path}")
                            else:
                                # 寫入失敗，還原備份
                                shutil.copy2(backup_path, filepath)
                                print(f"  ✗ Patch failed, restored from backup")
                        else:
                            print(f"  ✗ Text not found: '{old_text}'")
                    else:
                        print("  ✗ Invalid format. Use: 'old_text'->'new_text'")
                else:
                    print("  ✗ Invalid format. Use: 'old_text'->'new_text'")
            else:
                # 互動模式
                print(f"  📄 File: {filepath} ({len(original_content.splitlines())} lines)")
                print("  🔍 Enter text to find and replace (or 'q' to quit):")
                
                while True:
                    find_text = input("  Find: ").strip()
                    if find_text.lower() == 'q':
                        break
                    
                    if find_text in original_content:
                        replace_text = input("  Replace with: ").strip()
                        
                        # 預覽變更
                        lines = original_content.splitlines()
                        matching_lines = [i+1 for i, line in enumerate(lines) if find_text in line]
                        
                        if matching_lines:
                            print(f"  📍 Found in lines: {', '.join(map(str, matching_lines))}")
                            confirm = input("  Apply patch? (y/N): ").strip().lower()
                            
                            if confirm == 'y':
                                new_content = original_content.replace(find_text, replace_text, 1)
                                
                                if write_file(filepath, new_content):
                                    print(f"  ✅ Patched: {filepath}")
                                    print(f"  💾 Backup: {backup_path}")
                                    break
                                else:
                                    shutil.copy2(backup_path, filepath)
                                    print(f"  ✗ Patch failed, restored from backup")
                                    break
                        else:
                            print("  ✗ No matching lines found")
                    else:
                        print(f"  ✗ Text not found: '{find_text}'")
                        
        except Exception as e:
            print(f"  ✗ Patch error: {e}")
            # 如果有備份，嘗試還原
            try:
                if 'backup_path' in locals():
                    shutil.copy2(backup_path, filepath)
                    print(f"  🔄 Restored from backup: {backup_path}")
            except:
                pass
    
    def handle_classify_command(self, args: List[str]) -> None:
        """處理檔案分類命令"""
        if not args:
            print("  ✗ Usage: /classify <mode> [directory] [target_directory]")
            print()
            print("  分類模式:")
            print("    author   - 按作者分類檔案")
            print("    type     - 按檔案類型分類")
            print("    mixed    - 混合分類（作者+類型）")
            print("    content  - 按檔案內容智能分類")
            print("    preview  - 預覽分類結果（不移動檔案）")
            print()
            print("  範例:")
            print("    /classify author                    # 當前目錄按作者分類")
            print("    /classify type ~/Downloads          # 指定目錄按類型分類")
            print("    /classify mixed ~/Documents ~/Sorted  # 指定來源和目標目錄")
            print("    /classify content ./src             # 按內容智能分類")
            print("    /classify preview author ~/Downloads   # 預覽作者分類")
            print("    /classify preview content ./src     # 預覽內容分類")
            return
        
        mode = args[0].lower()
        directory = args[1] if len(args) > 1 else None
        target_dir = args[2] if len(args) > 2 else None
        
        # 支援的模式
        if mode not in ['author', 'type', 'mixed', 'content', 'preview']:
            print(f"  ✗ 不支援的模式: {mode}")
            print("  支援的模式: author, type, mixed, content, preview")
            return
        
        try:
            # 初始化文件分類器
            classifier = FileClassifier(directory)
            
            # 預覽模式
            if mode == 'preview':
                if len(args) < 2:
                    print("  ✗ 預覽模式需要指定分類類型")
                    print("  Usage: /classify preview <author|type|mixed> [directory]")
                    return
                
                preview_mode = args[1].lower()
                preview_dir = args[2] if len(args) > 2 else None
                
                if preview_mode not in ['author', 'type', 'mixed', 'content']:
                    print(f"  ✗ 不支援的預覽模式: {preview_mode}")
                    return
                
                print(f"  🔍 預覽 {preview_mode} 分類結果...")
                classification = classifier.preview_classification(preview_dir, preview_mode)
                
                if not classification:
                    print("  ℹ 沒有找到檔案可以分類")
                    return
                
                # 顯示分類摘要
                summary = classifier.get_classification_summary(classification)
                print()
                print(summary)
                
                # 詢問是否執行分類
                print()
                confirm = input("  是否執行此分類？ (y/N): ").strip().lower()
                if confirm == 'y':
                    if preview_mode == 'author':
                        result = classifier.classify_files_by_author(preview_dir, target_dir)
                    elif preview_mode == 'type':
                        result = classifier.classify_files_by_type(preview_dir, target_dir)
                    elif preview_mode == 'mixed':
                        result = classifier.classify_files_mixed(preview_dir, target_dir)
                    elif preview_mode == 'content':
                        result = classifier.classify_files_by_content(preview_dir, target_dir)
                    print("  ✅ 分類完成！")
                else:
                    print("  ❌ 分類已取消")
                
            else:
                # 執行分類
                print(f"  📁 開始執行 {mode} 分類...")
                
                if mode == 'author':
                    classification = classifier.classify_files_by_author(directory, target_dir)
                elif mode == 'type':
                    classification = classifier.classify_files_by_type(directory, target_dir)
                elif mode == 'mixed':
                    classification = classifier.classify_files_mixed(directory, target_dir)
                elif mode == 'content':
                    classification = classifier.classify_files_by_content(directory, target_dir)
                
                if not classification:
                    print("  ℹ 沒有找到檔案可以分類")
                    return
                
                # 顯示分類結果摘要
                summary = classifier.get_classification_summary(classification)
                print()
                print(summary)
                print("  ✅ 檔案分類完成！")
                
        except Exception as e:
            print(f"  ✗ 分類失敗: {e}")
            import traceback
            print(f"  詳細錯誤: {traceback.format_exc()}")
    
    def handle_mkdir_command(self, args: List[str]) -> None:
        """創建目錄"""
        if not args:
            print("  ✗ Usage: /mkdir <directory_name>")
            print("  Example: /mkdir new_folder")
            return
        
        try:
            for dir_name in args:
                dir_path = Path(dir_name)
                if dir_path.exists():
                    print(f"  ⚠ Directory already exists: {dir_path}")
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"  ✅ Created directory: {dir_path.absolute()}")
        except Exception as e:
            print(f"  ✗ Failed to create directory: {e}")
    
    def handle_cd_command(self, args: List[str]) -> None:
        """切換目錄"""
        if not args:
            # 顯示當前目錄
            print(f"  Current: {Path.cwd()}")
            return
        
        try:
            target_dir = Path(args[0]).expanduser().resolve()
            if target_dir.exists() and target_dir.is_dir():
                os.chdir(target_dir)
                print(f"  📁 Changed to: {target_dir}")
            else:
                print(f"  ✗ Directory not found: {target_dir}")
        except Exception as e:
            print(f"  ✗ Failed to change directory: {e}")
    
    def handle_move_command(self, args: List[str]) -> None:
        """移動/重命名文件或目錄"""
        if len(args) < 2:
            print("  ✗ Usage: /mv <source> <destination>")
            print("  Example: /mv old_file.txt new_file.txt")
            print("  Example: /mv file.txt ~/Documents/")
            return
        
        try:
            source = Path(args[0])
            destination = Path(args[1])
            
            if not source.exists():
                print(f"  ✗ Source not found: {source}")
                return
            
            # 如果目標是目錄，將源文件移動到該目錄
            if destination.is_dir():
                destination = destination / source.name
            
            shutil.move(str(source), str(destination))
            print(f"  ✅ Moved: {source} → {destination}")
            
        except Exception as e:
            print(f"  ✗ Failed to move: {e}")
    
    def handle_copy_command(self, args: List[str]) -> None:
        """複製文件或目錄"""
        if len(args) < 2:
            print("  ✗ Usage: /cp <source> <destination>")
            print("  Example: /cp file.txt backup.txt")
            print("  Example: /cp -r folder/ backup_folder/")
            return
        
        try:
            recursive = False
            start_idx = 0
            
            # 檢查是否有 -r 或 -R 選項
            if args[0] in ['-r', '-R', '--recursive']:
                recursive = True
                start_idx = 1
                if len(args) < 3:
                    print("  ✗ Usage: /cp -r <source> <destination>")
                    return
            
            source = Path(args[start_idx])
            destination = Path(args[start_idx + 1])
            
            if not source.exists():
                print(f"  ✗ Source not found: {source}")
                return
            
            if source.is_dir() and not recursive:
                print(f"  ✗ Use -r option to copy directories: /cp -r {source} {destination}")
                return
            
            if source.is_file():
                shutil.copy2(str(source), str(destination))
                print(f"  ✅ Copied file: {source} → {destination}")
            elif source.is_dir() and recursive:
                shutil.copytree(str(source), str(destination))
                print(f"  ✅ Copied directory: {source} → {destination}")
                
        except Exception as e:
            print(f"  ✗ Failed to copy: {e}")
    
    def handle_remove_command(self, args: List[str]) -> None:
        """刪除文件或目錄"""
        if not args:
            print("  ✗ Usage: /rm <file_or_directory>")
            print("  Example: /rm file.txt")
            print("  Example: /rm -r folder/")
            print("  ⚠ Be careful! This will permanently delete files.")
            return
        
        try:
            recursive = False
            force = False
            files_to_remove = []
            
            for arg in args:
                if arg in ['-r', '-R', '--recursive']:
                    recursive = True
                elif arg in ['-f', '--force']:
                    force = True
                else:
                    files_to_remove.append(arg)
            
            if not files_to_remove:
                print("  ✗ No files specified for removal")
                return
            
            for file_path in files_to_remove:
                path = Path(file_path)
                
                if not path.exists():
                    print(f"  ⚠ Not found: {path}")
                    continue
                
                # 安全確認（除非使用 -f）
                if not force:
                    if path.is_dir():
                        confirm = input(f"  Remove directory '{path}' and all its contents? (y/N): ").strip().lower()
                    else:
                        confirm = input(f"  Remove file '{path}'? (y/N): ").strip().lower()
                    
                    if confirm != 'y':
                        print(f"  ❌ Skipped: {path}")
                        continue
                
                if path.is_file():
                    path.unlink()
                    print(f"  ✅ Removed file: {path}")
                elif path.is_dir():
                    if recursive:
                        shutil.rmtree(str(path))
                        print(f"  ✅ Removed directory: {path}")
                    else:
                        print(f"  ✗ Use -r option to remove directories: /rm -r {path}")
                        
        except Exception as e:
            print(f"  ✗ Failed to remove: {e}")
    
    def _get_system_prompt(self) -> str:
        """獲取系統提示信息，讓模型了解CLI的所有功能"""
        current_dir = Path.cwd()
        return f"""你是 LocalLM CLI 的智能助手，專門幫助用戶進行檔案操作。

當前工作目錄: {current_dir}

🎯 你的主要任務：
1. 理解用戶的自然語言請求
2. 自動識別檔案操作需求
3. 提供簡潔明確的建議

📁 支援的檔案操作：
- 讀取檔案: txt, py, md, json, html, css, js, docx, pdf, xlsx, pptx
- 創建檔案: 根據用戶需求生成內容
- 編輯檔案: 修改現有檔案
- 分析檔案: 總結重點、提供建議

🔤 自然語言理解：
當用戶說「讀取 開發問題.txt 並總結重點」時，你應該：
1. 識別這是一個檔案讀取和分析請求
2. 建議使用相應的CLI命令
3. 提供具體的操作指導

💡 回應風格：
- 簡潔明瞭，避免冗長說明
- 主動提供解決方案
- 使用繁體中文
- 包含具體的命令示例

請幫助用戶更有效地使用這個工具，讓檔案操作變得簡單直觀。"""
    
    def run(self):
        """執行主程式循環"""
        self.print_banner()
        
        while self.running:
            try:
                # 顯示提示符
                user_input = input("  › ").strip()
                
                if not user_input:
                    continue
                
                # 解析指令
                command, args = self.parse_command(user_input)
                
                # 執行對應的處理函數
                if command == 'exit' or command == 'quit':
                    print("\n  Goodbye! 👋")
                    import os
                    os._exit(0)
                elif command == 'clear':
                    self.handle_clear_command()
                elif command == 'bye':
                    self.handle_bye_command(args)
                elif command == 'load':
                    self.handle_load_command(args)
                elif command == 'patch':
                    self.handle_patch_command(args)
                elif command == 'directory' or command == 'dir':
                    self.handle_directory_command(args)
                elif command == 'restore':
                    self.handle_restore_command(args)
                elif command == 'save':
                    self.handle_save_command(args)
                elif command == 'saved':
                    self.handle_saved_command(args)
                elif command == 'init':
                    self.handle_init_command(args)
                elif command == 'help':
                    self.handle_help_command()
                elif command == 'read':
                    self.handle_read_command(args)
                elif command == 'analyze':
                    self.handle_analyze_command(args)
                elif command == 'ocr':
                    self.handle_ocr_command(args)
                elif command == 'write':
                    self.handle_write_command(args)
                elif command == 'edit':
                    self.handle_edit_command(args)
                elif command == 'create' or command == 'new':
                    self.handle_create_command(args)
                elif command == 'list' or command == 'ls':
                    self.handle_list_command(args)
                elif command == 'tree':
                    self.handle_tree_command(args)
                elif command == 'pwd':
                    print(f"  Current: {get_current_path()}")
                elif command == 'models':
                    self.handle_models_command()
                elif command == 'switch' or command == 'model':
                    self.handle_model_command(args)
                elif command == 'chat':
                    self.handle_chat_command(args[0] if args else "")
                elif command == 'classify':
                    self.handle_classify_command(args)
                elif command == 'mkdir':
                    self.handle_mkdir_command(args)
                elif command == 'cd':
                    self.handle_cd_command(args)
                elif command == 'mv' or command == 'move':
                    self.handle_move_command(args)
                elif command == 'cp' or command == 'copy':
                    self.handle_copy_command(args)
                elif command == 'rm' or command == 'del':
                    self.handle_remove_command(args)
                else:
                    print(f"  ✗ Unknown command: {command}")
                    print("  Type /help for available commands")
                
                self.exit_count = 0  # 重置退出計數
                
            except KeyboardInterrupt:
                self.exit_count += 1
                if self.exit_count >= 2:
                    print("\n\n  Goodbye! 👋")
                    import os
                    os._exit(0)
                else:
                    print(f"\n  ⚠ Press Ctrl+C again to exit")
            except EOFError:
                # Ctrl+D 按鍵：執行 /bye 功能而不是退出程式
                print("\n")
                self.handle_bye_command()
                continue
            except Exception as e:
                print(f"  ✗ Unexpected error: {e}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LocalLM CLI - 本地模型檔案操作工具")
    parser.add_argument(
        '--model', '-m',
        default='qwen3:latest',
        help='指定使用的模型名稱 (預設: qwen3:latest)'
    )
    
    args = parser.parse_args()
    
    # 建立並執行 CLI
    cli = LocalLMCLI(default_model=args.model)
    cli.run()


if __name__ == "__main__":
    main()