"""
簡易圖形化界面
使用 tkinter 提供基本的 GUI 功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import sys
from pathlib import Path

# 添加 src 目錄到路徑
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from tools.file_tools import default_file_tools
from tools.data_visualizer import default_data_visualizer
from tools.batch_processor import default_batch_processor
from models import chat_stream, list_models

class LocalLMGUI:
    """LocalLM 簡易圖形化界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LocalLM CLI - 圖形化界面")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # 設置樣式
        self.setup_styles()
        
        # 創建界面
        self.create_widgets()
        
        # 當前文件路徑
        self.current_file = None
        self.current_directory = os.getcwd()
        
        # 可用模型
        self.available_models = []
        self.current_model = "qwen3:latest"
        
        # 初始化模型列表
        self.load_models()
    
    def setup_styles(self):
        """設置界面樣式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置樣式
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Info.TLabel', font=('Arial', 10))
        
        # 配置按鈕樣式
        style.configure('Action.TButton', padding=(10, 5))
        style.configure('File.TButton', padding=(5, 2))
    
    def create_widgets(self):
        """創建界面組件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 標題
        title_label = ttk.Label(main_frame, text="LocalLM CLI - 智能檔案助手", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 左側面板
        self.create_left_panel(main_frame)
        
        # 右側面板
        self.create_right_panel(main_frame)
        
        # 底部狀態欄
        self.create_status_bar(main_frame)
    
    def create_left_panel(self, parent):
        """創建左側面板"""
        left_frame = ttk.LabelFrame(parent, text="文件操作", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 文件選擇
        file_frame = ttk.Frame(left_frame)
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(file_frame, text="選擇文件:", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W)
        
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_select_frame, textvariable=self.file_path_var, width=30)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(file_select_frame, text="瀏覽", command=self.browse_file,
                  style='File.TButton').grid(row=0, column=1)
        
        file_select_frame.columnconfigure(0, weight=1)
        
        # 操作按鈕
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(buttons_frame, text="讀取文件", command=self.read_file,
                  style='Action.TButton').grid(row=0, column=0, padx=(0, 5), pady=2)
        
        ttk.Button(buttons_frame, text="分析文件", command=self.analyze_file,
                  style='Action.TButton').grid(row=0, column=1, padx=(0, 5), pady=2)
        
        ttk.Button(buttons_frame, text="創建圖表", command=self.create_chart,
                  style='Action.TButton').grid(row=0, column=2, pady=2)
        
        # 批量操作
        batch_frame = ttk.LabelFrame(left_frame, text="批量操作", padding="5")
        batch_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(batch_frame, text="批量讀取", command=self.batch_read,
                  style='File.TButton').grid(row=0, column=0, padx=(0, 5), pady=2)
        
        ttk.Button(batch_frame, text="批量分析", command=self.batch_analyze,
                  style='File.TButton').grid(row=0, column=1, padx=(0, 5), pady=2)
        
        ttk.Button(batch_frame, text="批量搜索", command=self.batch_search,
                  style='File.TButton').grid(row=0, column=2, pady=2)
        
        # 模型選擇
        model_frame = ttk.LabelFrame(left_frame, text="模型設置", padding="5")
        model_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(model_frame, text="當前模型:", style='Info.TLabel').grid(row=0, column=0, sticky=tk.W)
        
        self.model_var = tk.StringVar(value=self.current_model)
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                       values=self.available_models, state='readonly')
        self.model_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(model_frame, text="刷新模型", command=self.load_models,
                  style='File.TButton').grid(row=2, column=0, pady=(5, 0))
        
        model_frame.columnconfigure(0, weight=1)
    
    def create_right_panel(self, parent):
        """創建右側面板"""
        right_frame = ttk.LabelFrame(parent, text="結果顯示", padding="10")
        right_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 創建筆記本（標籤頁）
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 文件內容標籤頁
        self.create_file_content_tab()
        
        # 分析結果標籤頁
        self.create_analysis_tab()
        
        # 圖表標籤頁
        self.create_chart_tab()
        
        # 聊天標籤頁
        self.create_chat_tab()
        
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
    
    def create_file_content_tab(self):
        """創建文件內容標籤頁"""
        content_frame = ttk.Frame(self.notebook)
        self.notebook.add(content_frame, text="文件內容")
        
        # 文件內容顯示
        self.content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, 
                                                     font=('Consolas', 10))
        self.content_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
    
    def create_analysis_tab(self):
        """創建分析結果標籤頁"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="分析結果")
        
        # 分析結果顯示
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD,
                                                      font=('Arial', 10))
        self.analysis_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        analysis_frame.columnconfigure(0, weight=1)
        analysis_frame.rowconfigure(0, weight=1)
    
    def create_chart_tab(self):
        """創建圖表標籤頁"""
        chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(chart_frame, text="圖表")
        
        # 圖表信息顯示
        self.chart_text = scrolledtext.ScrolledText(chart_frame, wrap=tk.WORD,
                                                   font=('Arial', 10))
        self.chart_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)
    
    def create_chat_tab(self):
        """創建聊天標籤頁"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text="AI 聊天")
        
        # 聊天輸入
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.chat_input = ttk.Entry(input_frame, font=('Arial', 10))
        self.chat_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(input_frame, text="發送", command=self.send_chat,
                  style='Action.TButton').grid(row=0, column=1)
        
        input_frame.columnconfigure(0, weight=1)
        
        # 聊天記錄
        self.chat_text = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD,
                                                  font=('Arial', 10))
        self.chat_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(1, weight=1)
    
    def create_status_bar(self, parent):
        """創建狀態欄"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_var = tk.StringVar(value="就緒")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                style='Info.TLabel')
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 進度條
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(20, 0))
        
        status_frame.columnconfigure(1, weight=1)
    
    def load_models(self):
        """載入可用模型"""
        try:
            self.available_models = [model.get('name', 'unknown') for model in list_models()]
            self.model_combo['values'] = self.available_models
            if self.available_models and self.current_model not in self.available_models:
                self.current_model = self.available_models[0]
                self.model_var.set(self.current_model)
        except Exception as e:
            messagebox.showerror("錯誤", f"載入模型失敗: {str(e)}")
    
    def browse_file(self):
        """瀏覽文件"""
        file_path = filedialog.askopenfilename(
            title="選擇文件",
            filetypes=[
                ("所有支援的文件", "*.txt;*.py;*.md;*.json;*.csv;*.xlsx;*.pdf;*.docx"),
                ("文本文件", "*.txt;*.md"),
                ("Python文件", "*.py"),
                ("數據文件", "*.csv;*.xlsx;*.json"),
                ("文檔文件", "*.pdf;*.docx"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.current_file = file_path
    
    def read_file(self):
        """讀取文件"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "請先選擇文件")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("錯誤", "文件不存在")
            return
        
        self.status_var.set("正在讀取文件...")
        self.progress.start()
        
        def read_thread():
            try:
                # 根據文件類型讀取
                ext = os.path.splitext(file_path)[1].lower()
                
                if ext == '.pdf':
                    content = default_file_tools.read_pdf(file_path)
                elif ext in ['.xlsx', '.xls']:
                    content = default_file_tools.read_excel(file_path)
                elif ext == '.docx':
                    content = default_file_tools.read_docx(file_path)
                elif ext == '.csv':
                    content = default_file_tools.read_csv(file_path)
                else:
                    content = default_file_tools.read_file(file_path)
                
                # 更新界面
                self.root.after(0, lambda: self.update_content(content))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("錯誤", f"讀取文件失敗: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_var.set("就緒"))
        
        threading.Thread(target=read_thread, daemon=True).start()
    
    def update_content(self, content):
        """更新文件內容顯示"""
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, content)
        self.notebook.select(0)  # 切換到文件內容標籤頁
    
    def analyze_file(self):
        """分析文件"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "請先選擇文件")
            return
        
        self.status_var.set("正在分析文件...")
        self.progress.start()
        
        def analyze_thread():
            try:
                # 根據文件類型進行分析
                ext = os.path.splitext(file_path)[1].lower()
                analysis_result = ""
                
                if ext == '.py':
                    analysis_result = self.analyze_python_file(file_path)
                elif ext in ['.txt', '.md']:
                    analysis_result = self.analyze_text_file(file_path)
                elif ext == '.csv':
                    analysis_result = self.analyze_csv_file(file_path)
                else:
                    analysis_result = self.analyze_generic_file(file_path)
                
                # 更新界面
                self.root.after(0, lambda: self.update_analysis(analysis_result))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("錯誤", f"分析文件失敗: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_var.set("就緒"))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def analyze_python_file(self, file_path):
        """分析 Python 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        total_lines = len(lines)
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        code_lines = total_lines - comment_lines
        
        functions = content.count('def ')
        classes = content.count('class ')
        imports = content.count('import ') + content.count('from ')
        
        return f"""Python 文件分析結果:
文件: {os.path.basename(file_path)}
總行數: {total_lines}
代碼行數: {code_lines}
註釋行數: {comment_lines}
函數數量: {functions}
類數量: {classes}
導入語句: {imports}
複雜度: {'低' if functions < 10 else '中' if functions < 50 else '高'}"""
    
    def analyze_text_file(self, file_path):
        """分析文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chars = len(content)
        words = len(content.split())
        lines = len(content.split('\n'))
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        
        return f"""文本文件分析結果:
文件: {os.path.basename(file_path)}
字符數: {chars}
單詞數: {words}
行數: {lines}
段落數: {paragraphs}
平均每行單詞數: {words / lines if lines > 0 else 0:.1f}"""
    
    def analyze_csv_file(self, file_path):
        """分析 CSV 文件"""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            return f"""CSV 文件分析結果:
文件: {os.path.basename(file_path)}
行數: {len(df)}
列數: {len(df.columns)}
列名: {', '.join(df.columns.tolist())}
數據類型: {df.dtypes.to_dict()}
缺失值: {df.isnull().sum().to_dict()}"""
        except Exception as e:
            return f"CSV 分析失敗: {str(e)}"
    
    def analyze_generic_file(self, file_path):
        """分析通用文件"""
        stat = os.stat(file_path)
        size = stat.st_size
        
        return f"""文件分析結果:
文件: {os.path.basename(file_path)}
大小: {size} 字節 ({size / (1024 * 1024):.2f} MB)
修改時間: {stat.st_mtime}
擴展名: {os.path.splitext(file_path)[1]}"""
    
    def update_analysis(self, analysis_result):
        """更新分析結果顯示"""
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, analysis_result)
        self.notebook.select(1)  # 切換到分析結果標籤頁
    
    def create_chart(self):
        """創建圖表"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "請先選擇文件")
            return
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.csv', '.xlsx', '.xls']:
            messagebox.showwarning("警告", "只有 CSV 和 Excel 文件支援圖表創建")
            return
        
        self.status_var.set("正在創建圖表...")
        self.progress.start()
        
        def chart_thread():
            try:
                # 分析數據結構
                analysis = default_data_visualizer.analyze_data_structure(file_path)
                if "error" in analysis:
                    raise Exception(analysis["error"])
                
                # 建議圖表
                suggestions = default_data_visualizer.suggest_charts(analysis)
                
                # 創建圖表
                chart_info = f"數據分析結果:\n"
                chart_info += f"文件: {os.path.basename(file_path)}\n"
                chart_info += f"形狀: {analysis['shape'][0]} 行 × {analysis['shape'][1]} 列\n"
                chart_info += f"列名: {', '.join(analysis['columns'])}\n\n"
                
                chart_info += "建議的圖表類型:\n"
                for i, suggestion in enumerate(suggestions, 1):
                    chart_info += f"{i}. {suggestion['name']} - {suggestion['description']}\n"
                
                # 創建第一個建議的圖表
                if suggestions:
                    chart_result = default_data_visualizer.create_chart(file_path, suggestions[0]['type'])
                    if "success" in chart_result:
                        chart_info += f"\n圖表已創建: {chart_result['save_path']}"
                    else:
                        chart_info += f"\n圖表創建失敗: {chart_result.get('error', '未知錯誤')}"
                
                # 更新界面
                self.root.after(0, lambda: self.update_chart(chart_info))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("錯誤", f"創建圖表失敗: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_var.set("就緒"))
        
        threading.Thread(target=chart_thread, daemon=True).start()
    
    def update_chart(self, chart_info):
        """更新圖表信息顯示"""
        self.chart_text.delete(1.0, tk.END)
        self.chart_text.insert(1.0, chart_info)
        self.notebook.select(2)  # 切換到圖表標籤頁
    
    def batch_read(self):
        """批量讀取文件"""
        directory = filedialog.askdirectory(title="選擇目錄")
        if not directory:
            return
        
        self.status_var.set("正在批量讀取文件...")
        self.progress.start()
        
        def batch_thread():
            try:
                file_paths = default_batch_processor.get_file_list(directory, "*")
                result = default_batch_processor.batch_read_files(file_paths)
                
                report = f"批量讀取結果:\n"
                report += f"總文件數: {result['total_files']}\n"
                report += f"成功: {result['successful']}\n"
                report += f"失敗: {result['failed']}\n"
                report += f"耗時: {result['duration']:.2f}秒\n\n"
                
                report += "詳細結果:\n"
                for file_result in result['results'][:10]:  # 只顯示前10個
                    status = "✅" if file_result['success'] else "❌"
                    report += f"{status} {os.path.basename(file_result['file_path'])}\n"
                
                if len(result['results']) > 10:
                    report += f"... 還有 {len(result['results']) - 10} 個文件\n"
                
                # 更新界面
                self.root.after(0, lambda: self.update_analysis(report))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("錯誤", f"批量讀取失敗: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_var.set("就緒"))
        
        threading.Thread(target=batch_thread, daemon=True).start()
    
    def batch_analyze(self):
        """批量分析文件"""
        directory = filedialog.askdirectory(title="選擇目錄")
        if not directory:
            return
        
        self.status_var.set("正在批量分析文件...")
        self.progress.start()
        
        def batch_thread():
            try:
                file_paths = default_batch_processor.get_file_list(directory, "*")
                result = default_batch_processor.batch_analyze_files(file_paths)
                
                report = f"批量分析結果:\n"
                report += f"總文件數: {result['total_files']}\n"
                report += f"成功: {result['successful']}\n"
                report += f"失敗: {result['failed']}\n"
                report += f"耗時: {result['duration']:.2f}秒\n\n"
                
                report += "分析結果摘要:\n"
                for file_result in result['results'][:10]:  # 只顯示前10個
                    if file_result['success']:
                        analysis = file_result['result']
                        file_name = os.path.basename(file_result['file_path'])
                        report += f"📄 {file_name}: {analysis.get('type', 'unknown')}\n"
                        if 'total_lines' in analysis:
                            report += f"   行數: {analysis['total_lines']}\n"
                        elif 'characters' in analysis:
                            report += f"   字符: {analysis['characters']}\n"
                
                # 更新界面
                self.root.after(0, lambda: self.update_analysis(report))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("錯誤", f"批量分析失敗: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_var.set("就緒"))
        
        threading.Thread(target=batch_thread, daemon=True).start()
    
    def batch_search(self):
        """批量搜索文件"""
        directory = filedialog.askdirectory(title="選擇目錄")
        if not directory:
            return
        
        search_term = tk.simpledialog.askstring("搜索", "輸入搜索關鍵詞:")
        if not search_term:
            return
        
        self.status_var.set("正在批量搜索文件...")
        self.progress.start()
        
        def batch_thread():
            try:
                file_paths = default_batch_processor.get_file_list(directory, "*")
                result = default_batch_processor.batch_search_files(file_paths, search_term)
                
                report = f"批量搜索結果 (關鍵詞: {search_term}):\n"
                report += f"總文件數: {result['total_files']}\n"
                report += f"成功: {result['successful']}\n"
                report += f"失敗: {result['failed']}\n"
                report += f"耗時: {result['duration']:.2f}秒\n\n"
                
                report += "搜索結果:\n"
                total_matches = 0
                for file_result in result['results']:
                    if file_result['success'] and file_result['result']['matches'] > 0:
                        file_name = os.path.basename(file_result['file_path'])
                        matches = file_result['result']['matches']
                        total_matches += matches
                        report += f"📄 {file_name}: {matches} 個匹配\n"
                        
                        # 顯示前3個匹配行
                        for line_info in file_result['result']['matching_lines'][:3]:
                            report += f"   行 {line_info['line']}: {line_info['content'][:50]}...\n"
                
                report += f"\n總匹配數: {total_matches}\n"
                
                # 更新界面
                self.root.after(0, lambda: self.update_analysis(report))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("錯誤", f"批量搜索失敗: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_var.set("就緒"))
        
        threading.Thread(target=batch_thread, daemon=True).start()
    
    def send_chat(self):
        """發送聊天消息"""
        message = self.chat_input.get().strip()
        if not message:
            return
        
        # 添加到聊天記錄
        self.chat_text.insert(tk.END, f"用戶: {message}\n")
        self.chat_input.delete(0, tk.END)
        
        self.status_var.set("AI 正在思考...")
        self.progress.start()
        
        def chat_thread():
            try:
                # 這裡可以調用 AI 模型
                response = f"AI 回應: 收到您的消息 '{message}'，這是一個簡易的 GUI 界面演示。"
                
                # 更新界面
                self.root.after(0, lambda: self.update_chat(response))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("錯誤", f"聊天失敗: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_var.set("就緒"))
        
        threading.Thread(target=chat_thread, daemon=True).start()
    
    def update_chat(self, response):
        """更新聊天記錄"""
        self.chat_text.insert(tk.END, f"{response}\n\n")
        self.chat_text.see(tk.END)
        self.notebook.select(3)  # 切換到聊天標籤頁
    
    def run(self):
        """運行 GUI"""
        self.root.mainloop()

def main():
    """主函數"""
    try:
        app = LocalLMGUI()
        app.run()
    except Exception as e:
        print(f"GUI 啟動失敗: {e}")
        messagebox.showerror("錯誤", f"GUI 啟動失敗: {e}")

if __name__ == "__main__":
    main()
