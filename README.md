# LocalLM CLI - 智能本地檔案助手

<div align="center">

![LocalLM CLI](https://img.shields.io/badge/LocalLM-CLI-blue?style=for-the-badge&logo=terminal)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange?style=for-the-badge&logo=ollama)

**🤖 基於本地 Ollama 模型的智能檔案操作工具**

[快速開始](#-快速開始) • [功能特色](#-功能特色) • [使用指南](#-使用指南) • [安裝說明](#-安裝說明)

</div>

---

## ✨ 功能特色

### 🎯 核心能力
- **🏠 完全本地化**: 使用本地 Ollama 模型，無需雲端 API，保護隱私
- **💬 自然語言交互**: 支援中文自然語言檔案操作請求
- **🔄 思考動畫**: 優雅的旋轉動畫顯示 AI 處理狀態
- **⚡ 流式輸出**: 即時顯示模型回應，提升使用體驗
- **🎨 美觀界面**: 漸層色彩 ASCII 橫幅，簡潔直觀的設計

### 📁 檔案操作
- **多格式支援**: txt, py, md, json, html, css, js, docx, pdf, xlsx, pptx
- **智能讀取**: 自動識別檔案類型並使用相應解析器
- **AI 創建**: 根據自然語言描述智能生成檔案內容
- **內容分析**: 自動總結檔案重點，提供智能建議
- **安全編輯**: 自動備份機制，支援檔案恢復

### 🧠 AI 功能
- **RAG 分析**: 深度 PDF 文檔分析，支援語義搜索和問答
- **OCR 識別**: 掃描型 PDF 光學字符識別
- **智能分類**: 按作者、類型、內容自動分類檔案
- **程式碼修補**: 安全的程式碼修改與自動備份
- **對話模型**: 保存對話為自定義 Ollama 模型

### 🛠️ 系統工具
- **目錄管理**: 完整的檔案系統操作（創建、移動、複製、刪除）
- **工作區管理**: 多目錄工作區支援
- **模型管理**: 動態切換 Ollama 模型，支援別名
- **檢查點系統**: 自動備份重要操作，支援一鍵恢復

---

## 🚀 快速開始

### 前置需求

1. **安裝 Python 3.8+**
2. **安裝 Ollama**
   ```bash
   # Windows (使用 winget)
   winget install Ollama.Ollama
   
   # macOS (使用 Homebrew)
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

3. **下載模型** (建議使用 qwen3:latest)
   ```bash
   ollama pull qwen3:latest
   ```

### 安裝與執行

#### 🌍 全域安裝 (推薦)

```bash
# 1. 下載專案
git clone <your-repo-url>
cd locallm-cli

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 一鍵全域安裝
python scripts/setup_global.py

# 4. 重新開啟終端後，在任意位置使用
locallm
```

#### 📁 本地執行

**PowerShell (推薦):**
```powershell
.\locallm.ps1
.\locallm.ps1 -m qwen3:latest
```

**批次檔案:**
```cmd
locallm.bat
locallm.bat -m qwen3:latest
```

**直接 Python:**
```bash
python src/main.py
python src/main.py --model qwen3:latest
```

---

## 📖 使用指南

### 🔤 自然語言命令 (推薦)

直接說出您的需求，AI 會自動理解並執行：

```bash
› 讀取 開發問題.txt 並總結重點
› 創建一個 Python 腳本
› 列出當前目錄的檔案
› 分析 config.json 的內容
```

### 📁 檔案操作命令

| 命令 | 功能 | 範例 |
|------|------|------|
| `/read <檔案>` | 讀取檔案內容 | `/read example.py` |
| `/write <檔案> <內容>` | 寫入檔案 | `/write test.txt "Hello World"` |
| `/create <檔案>` | 創建新檔案 | `/create hello.py` |
| `/edit <檔案> <內容>` | 編輯檔案 | `/edit config.json "{}"` |
| `/list [目錄]` | 列出檔案 | `/list` 或 `/list ~/Documents` |
| `/tree [目錄]` | 樹狀顯示 | `/tree` 或 `/tree src/` |

### 🛠️ 系統操作命令

| 命令 | 功能 | 範例 |
|------|------|------|
| `/mkdir <目錄>` | 創建目錄 | `/mkdir new_folder` |
| `/cd <目錄>` | 切換目錄 | `/cd ~/Documents` |
| `/mv <來源> <目標>` | 移動/重命名 | `/mv old.txt new.txt` |
| `/cp <來源> <目標>` | 複製檔案 | `/cp file.txt backup.txt` |
| `/rm <檔案>` | 刪除檔案 | `/rm temp.txt` |

### 🧠 AI 功能命令

| 命令 | 功能 | 範例 |
|------|------|------|
| `/analyze <pdf> [查詢]` | RAG PDF 分析 | `/analyze document.pdf "主要內容是什麼？"` |
| `/ocr <pdf>` | OCR 文字識別 | `/ocr scanned.pdf` |
| `/classify <模式>` | 智能檔案分類 | `/classify content` |
| `/patch <檔案>` | 安全程式碼修改 | `/patch main.py` |

### ⚙️ 模型管理命令

| 命令 | 功能 | 範例 |
|------|------|------|
| `/models` | 顯示可用模型 | `/models` |
| `/switch <模型>` | 切換模型 | `/switch qwen3:latest` |
| `/save <名稱>` | 保存對話為模型 | `/save my_assistant` |
| `/saved` | 管理已保存模型 | `/saved` |

### 🔧 其他命令

| 命令 | 功能 | 範例 |
|------|------|------|
| `/help` | 顯示幫助 | `/help` |
| `/clear` | 清除畫面 | `/clear` |
| `/bye` | 清除對話歷史 | `/bye` |
| `/exit` | 退出程式 | `/exit` |

---

## 🎯 使用範例

### 基本檔案操作

```bash
# 讀取並分析檔案
› 讀取 開發問題.txt 並總結重點
  📖 正在讀取: 開發問題.txt
  ── 開發問題.txt ──
  
  開發問題總結
  1. 用戶界面過於複雜...
  
  🤖 AI 分析結果:
  ──────────────────────────────────────────────────
  主要內容概述：
  這份文件總結了開發過程中的主要問題...
  ──────────────────────────────────────────────────

# 創建 Python 腳本
› 創建一個計算器程式 calculator.py
  ✏️ 正在創建: calculator.py
  ⠦ Creating
  def add(a, b):
      return a + b
  
  def subtract(a, b):
      return a - b
  ...
  ✓ Created: calculator.py
```

### RAG 文檔分析

```bash
# PDF 深度分析
› /analyze document.pdf "這份文件的主要內容是什麼？"
  📖 正在讀取 PDF: document.pdf
  🔧 初始化 RAG 處理器...
  🔄 處理文字並建立向量資料庫...
  ✓ 處理完成:
    - 原始長度: 1250 字符
    - 清理後長度: 1180 字符
    - 分割片段: 5 個
    - 向量維度: 384
  
  🔍 搜索查詢: 「這份文件的主要內容是什麼？」
  📋 找到 3 個相關片段:
    1. 相似度: 0.892
       這份文件主要討論了...
  
  🤖 基於文檔內容的回答:
  ──────────────────────────────────────────────────
  根據文檔內容，這份文件主要涵蓋了...
  ──────────────────────────────────────────────────
```

### 智能檔案分類

```bash
# 按內容分類檔案
› /classify content
  📁 開始執行 content 分類...
  🔍 正在分析檔案內容...
    📄 main.py -> 後端邏輯 (信心度: 0.85)
    📄 test.py -> 測試檔案 (信心度: 0.92)
    📄 config.json -> 配置檔案 (信心度: 0.78)
    📄 README.md -> 文檔說明 (信心度: 0.88)
  
  分類摘要報告 - 2024-01-15 14:30:25
  ==================================================
  總共檔案數: 4
  分類數量: 4
  
  📁 後端邏輯 (1 個檔案)
     - main.py
  
  📁 測試檔案 (1 個檔案)
     - test.py
  
  📁 配置檔案 (1 個檔案)
     - config.json
  
  📁 文檔說明 (1 個檔案)
     - README.md
  
  ✅ 檔案分類完成！
```

---

## 🔧 進階功能

### RAG 功能

RAG (檢索增強生成) 功能提供深度文檔分析：

```bash
# 安裝 RAG 依賴
pip install sentence-transformers chromadb numpy pymupdf

# 使用 RAG 分析
/analyze document.pdf "文檔中的關鍵技術點是什麼？"
```

**支援功能:**
- PDF 文字提取與清理
- 智能文字分割
- 語義向量嵌入
- 相似度搜索
- 基於上下文的問答

### OCR 功能

支援掃描型 PDF 的光學字符識別：

```bash
# 安裝 OCR 依賴
pip install pytesseract pillow pymupdf

# 使用 OCR
/ocr scanned_document.pdf
```

**支援語言:** 英文、繁體中文、簡體中文

### 檔案分類

智能檔案分類支援多種模式：

- **按作者分類**: `/classify author`
- **按類型分類**: `/classify type`
- **按內容分類**: `/classify content`
- **混合分類**: `/classify mixed`
- **預覽模式**: `/classify preview content`

### 模型管理

支援動態模型切換和自定義模型：

```bash
# 查看可用模型
/models

# 切換模型
/switch qwen3:latest
/switch llama  # 使用別名

# 保存對話為新模型
/save my_assistant

# 管理已保存模型
/saved
```

---

## 📦 依賴套件

### 核心依賴
```
requests>=2.31.0
rich>=13.0.0
pyfiglet>=0.8.0
```

### 可選依賴

**Office 文件支援:**
```
python-docx>=0.8.11    # Word 文件
openpyxl>=3.1.0        # Excel 文件
python-pptx>=0.6.21    # PowerPoint 文件
```

**PDF 支援:**
```
pymupdf>=1.23.0        # PDF 讀取
```

**RAG 功能:**
```
sentence-transformers>=2.2.0
chromadb>=0.4.0
numpy>=2.3.0
```

**OCR 功能:**
```
pytesseract>=0.3.10
pillow>=10.0.0
```

---

## 🏗️ 專案結構

```
locallm-cli/
├── src/                    # 主要源碼
│   ├── main.py            # 主程式入口
│   ├── models/            # Ollama 模型接口
│   │   └── ollama_client.py
│   ├── tools/             # 工具模組
│   │   ├── file_tools.py  # 檔案操作
│   │   ├── file_classifier.py  # 檔案分類
│   │   └── ocr_tools.py   # OCR 功能
│   └── rag/               # RAG 功能
│       ├── rag_core.py    # RAG 核心
│       └── pdf_processor.py
├── scripts/               # 安裝腳本
│   ├── setup_global.py   # 全域安裝
│   └── locallm_entry.py  # 入口點
├── docs/                 # 文檔
├── data/                 # 數據目錄
└── requirements.txt      # 依賴清單
```

---

## 🎨 界面特色

### 歡迎界面
```
_     ___   ____    _    _     _     __  __ 
| |   / _ \ / ___|  / \  | |   | |   |  \/  |
| |  | | | | |     / _ \ | |   | |   | |\/| |
| |__| |_| | |___ / ___ \| |___| |___| |  | |
|_____\___/ \____/_/   \_\_____|_____|_|  |_|
                                         本地模型 × 智能檔案操作
  Working in: ~/Desktop/locallm-cli
  ✓ Ollama (9 models)  •  Model: qwen3:latest
  Tips for getting started:
  1. Ask questions, edit files, or run commands naturally.
  2. Be specific for the best results (e.g., 'read 開發問題.txt').
  3. Use natural language: 'create a Python script' or 'analyze this file'.
  4. /help for more information and commands.
```

### 思考動畫
```
› 你好
  qwen3:latest ›
  ⠦ Thinking
你好！我是 LocalLM CLI 的智能助手...
```

---

## 🚀 開發指南

### VS Code 開發
專案包含完整的 VS Code 配置：
- 開啟 `locallm-cli.code-workspace` 獲得最佳開發體驗
- 自動配置 Python 路徑和類型檢查
- 推薦擴充套件: Python, Pylance, Black Formatter

### 貢獻指南
1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件

---

## 🤝 支援與回饋

- **問題回報**: [GitHub Issues](https://github.com/your-repo/issues)
- **功能建議**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **文檔**: [專案文檔](docs/)

---

<div align="center">

**🌟 如果這個專案對您有幫助，請給我們一個 Star！**

Made with ❤️ by LocalLM CLI Team

</div>
