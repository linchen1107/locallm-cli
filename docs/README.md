# LocalLM CLI - 本地模型檔案操作工具

🤖 一個基於本地 Ollama 模型的最小可行產品 (MVP)，提供智能檔案操作功能。

## ✨ 核心特性

- **🏠 完全本地化**: 使用本地 Ollama 模型，無需雲端 API
- **📁 檔案操作核心**: 支援檔案的讀取、寫入、編輯、創建功能
- **🎯 主流格式支援**: 支援 .txt, .py, .js, .md, .json 等常見文字格式
- **💬 自然語言交互**: 支援自然語言檔案操作請求
- **🤖 AI 驅動創建**: 智能生成檔案內容，根據檔案類型自動調整
- **⚡ 流式輸出**: 即時顯示模型回應，提升使用體驗
- **🔧 簡潔易用**: 簡單的命令行介面，易於上手

## 🚀 快速開始

### 前置需求

1. **安裝 Python 3.8+**
2. **安裝 Ollama**
   ```bash
   # Windows (使用 winget)
   winget install Ollama.Ollama
   
   # 或從官網下載: https://ollama.ai/
   ```

3. **下載模型** (建議使用 llama3.2)
   ```bash
   ollama pull llama3.2
   ```

### 安裝與執行

#### 🚀 全域安裝 (推薦)

1. **下載專案**
   ```bash
   git clone <your-repo-url>
   cd locallm-cli
   ```

2. **安裝依賴套件**
   ```bash
   pip install -r requirements.txt
   ```

3. **一鍵全域安裝**
   ```bash
   python scripts/setup_global.py
   ```

4. **重新開啟終端後，在任意位置使用**
   ```bash
   # 在任意目錄啟動
   locallm
   
   # 指定模型
   locallm -m llama3.1
   ```

#### 📁 本地執行

如果只想在專案目錄中使用：

**PowerShell (推薦 - 乾淨退出)：**
```powershell
.\locallm.ps1
.\locallm.ps1 -m llama3.2
```

**批次檔案：**
```cmd
locallm.bat
locallm.bat -m llama3.2
```

**直接 Python：**
```bash
cd src
python main.py
python main.py --model llama3.2
```

#### 🔧 VS Code 開發

專案包含完整的 VS Code 配置：
- 開啟 `locallm-cli.code-workspace` 以獲得最佳開發體驗
- 自動配置 Python 路徑和類型檢查
- 推薦擴充套件: Python, Pylance, Black Formatter

## 📖 使用說明

### 指令格式

#### 檔案操作指令
- `/read <檔案路徑>` - 讀取並顯示檔案內容
- `/write <檔案路徑> <內容>` - 寫入內容到檔案（覆蓋模式）
- `/edit <檔案路徑> <內容>` - 編輯檔案內容（覆蓋模式）
- `/create <檔案路徑> [內容]` - 創建新檔案，可選內容或 AI 生成
- `/list [目錄路徑]` - 列出目錄中的檔案
- `/pwd` - 顯示目前工作路徑

#### 模型相關指令
- `/models` - 列出所有可用的 Ollama 模型
- `/switch <name>` - 切換到指定模型
- `/switch <number>` - 使用數字切換模型  
- `/switch` - 查看當前使用的模型

**模型別名支援**：
- `llama` → `llama3.2:latest`
- `mistral` → `mistral:7b`
- `codellama` → `codellama:13b`
- 更多別名請參考 [模型切換指南](MODEL_SWITCHING.md)

#### 系統指令
- `/help` - 顯示幫助資訊
- `/exit` - 退出程式
- `Ctrl+C` (按兩次) - 強制退出

#### 對話模式
直接輸入問題或訊息即可與模型對話，支援自然語言檔案操作。

#### 🔄 模型切換功能
支援多種切換方式：
```bash
# 使用完整名稱
/switch llama3.2:latest

# 使用別名
/switch llama

# 使用數字選擇
/switch 5

# 查看當前模型
/switch
```

**支援的別名**: `llama`, `mistral`, `codellama`, `gemma`, `phi`, `qwen`, `deepseek`

**智能建議**: 輸入錯誤時自動提供相似模型建議

### 使用範例

```bash
  › /read example.py
  ── example.py ──
  
  print("Hello, World!")

  › /create hello.txt
  🤖 Generating content for hello.txt...
  
  llama3.2 ›
  
  Hello! This is a greeting file created by LocalLM CLI.
  Welcome to the world of AI-powered file operations!
  
  ✓ Created: hello.txt

  › 請撰寫一個計算器程式 calculator.py
  → Creating calculator.py
  🤖 Generating content for calculator.py...
  
  # 簡單計算器程式
  def add(a, b):
      return a + b
  
  def subtract(a, b):
      return a - b
  ...
  
  ✓ Created: calculator.py

  › 請幫我分析一下 calculator.py
  → Reading calculator.py
  
  llama3.2 ›
  
  這是一個簡單的計算器程式，包含基本的數學運算功能...
```

## 🏗️ 專案架構

```
locallm-cli/
│
├── main.py                 # 程式入口點，REPL 循環與指令處理
├── requirements.txt        # Python 依賴套件列表
├── README.md              # 本說明文件
│
├── models/                # 模型相關模組
│   ├── __init__.py
│   └── ollama_client.py   # Ollama 客戶端，處理與本地模型的通信
│
└── tools/                 # 工具模組
    ├── __init__.py
    └── file_tools.py      # 檔案操作核心工具
```

## 🔧 技術細節

### 核心模組說明

#### `models/ollama_client.py`
- 封裝與本地 Ollama 服務的 HTTP 通信
- 支援流式和非流式對話模式
- 自動處理連接錯誤和異常狀況
- 提供模型列表查詢功能

#### `tools/file_tools.py`
- 提供檔案的讀取、寫入、編輯功能
- 自動處理 UTF-8 編碼和路徑解析
- 支援相對路徑和絕對路徑
- 包含檔案存在性檢查和錯誤處理

#### `main.py`
- 實作 REPL (讀取-求值-輸出循環)
- 指令解析與路由處理
- 自然語言檔案操作識別
- 對話歷史管理

### 支援的檔案格式

工具自動支援以下常見的純文字檔案格式：
- **程式碼**: `.py`, `.js`, `.java`, `.go`, `.rs`, `.cpp`, `.c`, `.h`
- **標記語言**: `.md`, `.html`, `.xml`
- **配置檔案**: `.json`, `.yaml`, `.yml`, `.ini`, `.cfg`, `.toml`
- **樣式表**: `.css`, `.scss`, `.less`
- **腳本**: `.sh`, `.bat`, `.ps1`
- **文件**: `.txt`, `.log`

## 🚧 已知限制

1. **檔案編輯**: 目前僅支援覆蓋模式，不支援部分編輯
2. **二進位檔案**: 不支援二進位檔案的處理
3. **大檔案**: 沒有檔案大小限制，可能影響效能
4. **自然語言解析**: 檔案路徑識別較為簡單，複雜情況可能需要明確指令

## 🛣️ 未來規劃

- [ ] 支援檔案的部分編輯功能
- [ ] 添加檔案備份機制
- [ ] 改進自然語言解析能力
- [ ] 支援目錄遞迴操作
- [ ] 添加檔案類型自動檢測
- [ ] 實作對話歷史壓縮
- [ ] 支援多模型並行處理

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

## 📞 支援

如有問題或建議，請建立 Issue 或聯繫開發者。

---

**LocalLM CLI** - 讓本地模型成為您的程式開發助手！ 🚀