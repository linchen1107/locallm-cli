#!/usr/bin/env python3
"""
LocalLM CLI - 本地模型驅動的檔案操作命令行工具
一個最小可行產品 (MVP)，提供本地模型驅動的檔案操作功能
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Optional

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from models import chat_stream, list_models, is_available
from tools import read_file, write_file, edit_file, file_exists, list_files, get_current_path


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
    
    def __init__(self, default_model: str = "llama3.2"):
        """
        初始化 CLI
        
        Args:
            default_model: 預設使用的模型名稱
        """
        self.default_model = default_model
        self.conversation_history: List[Dict] = []
        self.running = True
        self.exit_count = 0  # 用於處理雙重 Ctrl+C 退出
        
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
        
        # 簡化狀態顯示
        status_line = "  "
        if is_available():
            models = list_models()
            model_count = len(models) if models else 0
            status_line += f"✓ Ollama ({model_count} models)"
        else:
            status_line += "✗ Ollama offline"
        
        status_line += f"  •  Model: {self.default_model}"
        
        # 顯示當前工作目錄的相對路徑或名稱
        current_path = Path(get_current_path())
        try:
            # 嘗試顯示相對於 home 目錄的路徑
            home_path = Path.home()
            if current_path.is_relative_to(home_path):
                relative_path = current_path.relative_to(home_path)
                display_path = f"~/{relative_path}" if str(relative_path) != "." else "~"
            else:
                display_path = current_path.name if current_path.name else str(current_path)
        except:
            display_path = current_path.name
            
        status_line += f"  •  {display_path}"
        print(status_line)
        print()
        
        # 簡潔的使用提示
        print("  Commands: /read /write /edit /create /list /models /switch /help /exit")
        print("  或直接對話提問，例如: '請撰寫一個 hello.txt'")
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
    
    def handle_read_command(self, args: List[str]) -> None:
        """處理讀取檔案指令"""
        if not args:
            print("  ⚠ Usage: /read <file_path>")
            return
        
        file_path = args[0]
        try:
            content = read_file(file_path)
            print(f"\n  ── {file_path} ──")
            print()
            print(content)
            print()
        except FileNotFoundError:
            print(f"  ✗ File not found: {file_path}")
        except PermissionError:
            print(f"  ✗ Permission denied: {file_path}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
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
            print("\n  ⚠ Interrupted\n")
        except Exception as e:
            print(f"\n  ✗ Error: {e}\n")
    
    def should_use_file_tools(self, message: str) -> bool:
        """判斷是否應該使用檔案工具"""
        file_keywords = [
            '讀取', '讀', 'read', '檔案內容',
            '寫入', '寫', 'write', '建立檔案', '創建檔案', '新增檔案',
            '編輯', 'edit', '修改檔案',
            '分析檔案', '查看檔案', '顯示檔案',
            '撰寫', '產生', 'generate', 'create', '製作'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in file_keywords)
    
    def handle_natural_file_operation(self, message: str) -> None:
        """處理自然語言的檔案操作請求"""
        # 簡單的檔案路徑提取
        # 這裡可以使用更複雜的 NLP 技術，但為了 MVP 保持簡單
        
        # 尋找檔案路徑模式
        import re
        path_patterns = [
            r'([a-zA-Z]:[\\\/][^"\s]+)',  # Windows 絕對路徑
            r'([\.\/][^"\s]+\.[a-zA-Z0-9]+)',  # 相對路徑
            r'([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z0-9]+)',  # 簡單檔名
        ]
        
        found_paths = []
        for pattern in path_patterns:
            matches = re.findall(pattern, message)
            found_paths.extend(matches)
        
        if not found_paths:
            print("❌ 無法從訊息中識別檔案路徑")
            print("請使用明確的指令格式，或包含具體的檔案路徑")
            return
        
        file_path = found_paths[0]  # 使用第一個找到的路徑
        
        # 判斷操作類型
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['讀取', '讀', 'read', '分析', '查看', '顯示']):
            print(f"  → Reading {file_path}")
            self.handle_read_command([file_path])
        elif any(word in message_lower for word in ['撰寫', '產生', 'generate', 'create', '製作', '建立', '創建', '新增']):
            print(f"  → Creating {file_path}")
            self.handle_file_creation_request(file_path, message)
        elif any(word in message_lower for word in ['寫入', '寫', 'write', '編輯', 'edit', '修改']):
            print(f"  → Writing to {file_path}")
            # 對於寫入操作，我們需要從訊息中提取內容
            self.handle_write_from_message(file_path, message)
        else:
            print("  ⚠ Unable to determine file operation")
            print("  Please use explicit commands")
    
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
        print("\n")
        print("  ╭─ Commands ─────────────────────────╮")
        print("  │                                    │")
        print("  │  /read <path>     Read file        │")
        print("  │  /write <path>    Write file       │")  
        print("  │  /edit <path>     Edit file        │")
        print("  │  /create <path>   Create file      │")
        print("  │  /list [dir]      List files       │")
        print("  │  /pwd             Show path        │")
        print("  │  /models          Show models      │")
        print("  │  /switch <name>   Switch model     │")
        print("  │  /help            This help        │")
        print("  │  /exit            Exit program     │")
        print("  │                                    │")
        print("  │  Or just ask questions naturally   │")
        print("  │                                    │")
        print("  ╰────────────────────────────────────╯")
        print()
    
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
                elif command == 'help':
                    self.handle_help_command()
                elif command == 'read':
                    self.handle_read_command(args)
                elif command == 'write':
                    self.handle_write_command(args)
                elif command == 'edit':
                    self.handle_edit_command(args)
                elif command == 'create' or command == 'new':
                    self.handle_create_command(args)
                elif command == 'list' or command == 'ls':
                    self.handle_list_command(args)
                elif command == 'pwd':
                    print(f"  Current: {get_current_path()}")
                elif command == 'models':
                    self.handle_models_command()
                elif command == 'switch' or command == 'model':
                    self.handle_model_command(args)
                elif command == 'chat':
                    self.handle_chat_command(args[0] if args else "")
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
                print("\n\n  Goodbye! 👋")
                import os
                os._exit(0)
            except Exception as e:
                print(f"  ✗ Unexpected error: {e}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LocalLM CLI - 本地模型檔案操作工具")
    parser.add_argument(
        '--model', '-m',
        default='llama3.2',
        help='指定使用的模型名稱 (預設: llama3.2)'
    )
    
    args = parser.parse_args()
    
    # 建立並執行 CLI
    cli = LocalLMCLI(default_model=args.model)
    cli.run()


if __name__ == "__main__":
    main()