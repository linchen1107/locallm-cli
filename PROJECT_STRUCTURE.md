# LocalLM CLI 專案結構說明

## 📁 專案架構

```
locallm-cli/
├── 📁 src/                 # 核心程式碼
│   ├── main.py            # 主程式入口
│   ├── __init__.py        # 套件初始化
│   ├── 📁 models/         # AI 模型相關
│   │   ├── __init__.py
│   │   └── ollama_client.py
│   └── 📁 tools/          # 檔案操作工具
│       ├── __init__.py
│       └── file_tools.py
├── 📁 docs/               # 專案文件
│   ├── README.md          # 主要說明文件
│   ├── INSTALL.md         # 安裝指南
│   ├── FILE_CREATION_GUIDE.md
│   └── ...
├── 📁 scripts/            # 安裝與部署腳本
│   ├── locallm.bat        # Windows 全域啟動腳本
│   ├── locallm_entry.py   # Python 入口腳本
│   ├── setup_global.py    # 全域安裝腳本
│   └── ...
├── 📁 tests/              # 測試檔案
│   ├── __init__.py
│   ├── test_*.py          # 測試檔案
│   └── debug_*.py         # 除錯檔案
├── 📁 dist/               # 建置輸出
├── pyproject.toml         # 現代 Python 專案配置
├── setup.py              # 傳統 Python 套件設定
├── requirements.txt       # 依賴套件清單
├── MANIFEST.in           # 套件檔案清單
├── LICENSE               # MIT 授權條款
└── .gitignore           # Git 忽略檔案
```

## 🎯 資料夾功能

### `src/` - 核心程式碼
- **main.py**: CLI 主程式，包含所有核心功能
- **models/**: AI 模型整合模組
  - `ollama_client.py`: Ollama 模型客戶端
- **tools/**: 檔案操作工具模組
  - `file_tools.py`: 檔案讀寫編輯功能

### `docs/` - 專案文件
- 所有 `.md` 文件檔案
- 安裝指南、使用說明、API 文件等

### `scripts/` - 腳本工具
- **locallm.bat**: Windows 全域命令啟動器
- **locallm_entry.py**: Python 入口腳本
- **setup_global.py**: 全域安裝腳本
- 其他安裝和驗證腳本

### `tests/` - 測試檔案
- 單元測試、整合測試
- 除錯和開發工具

### `dist/` - 建置輸出
- 套件建置結果
- 分發檔案

## 🔧 配置檔案

- **pyproject.toml**: 現代 Python 專案標準配置
- **setup.py**: 傳統套件安裝配置
- **requirements.txt**: 依賴套件清單
- **MANIFEST.in**: 套件包含檔案定義
- **.gitignore**: Git 版本控制忽略檔案

## 🚀 使用方式

1. **開發模式**:
   ```bash
   cd src
   python main.py
   ```

2. **全域安裝**:
   ```bash
   python scripts/setup_global.py
   locallm  # 從任意位置使用
   ```

3. **套件安裝**:
   ```bash
   pip install -e .  # 開發安裝
   pip install .     # 正式安裝
   ```

## 📦 套件建置

```bash
# 建置套件
python -m build

# 本地安裝
pip install dist/locallm_cli-1.0.0-py3-none-any.whl
```

此結構遵循 Python 套件的最佳實踐，提供清晰的模組分離和完整的專案管理功能。