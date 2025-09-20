# LocalLM CLI 開發指南

## 🛠️ 開發環境設定

### 前置需求
- Python 3.8+
- Ollama
- VS Code (推薦)

### 設定開發環境

1. **Clone 專案**
   ```bash
   git clone <https://github.com/linchen1107/locallm-cli.git>
   cd locallm-cli
   ```

2. **安裝開發依賴**
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8
   ```

3. **VS Code 設定**
   專案已包含 `.vscode/settings.json` 配置檔，提供：
   - Python 路徑設定 (`src` 目錄)
   - Linting 和 formatting 設定
   - 自動導入補全

## 📁 專案架構

```
locallm-cli/
├── src/                    # 核心原始碼
│   ├── main.py            # CLI 主程式
│   ├── models/            # AI 模型模組
│   └── tools/             # 檔案操作工具
├── docs/                  # 專案文件
├── scripts/               # 安裝腳本
├── tests/                 # 測試套件
└── dist/                  # 建置輸出
```

## 🔧 開發工作流程

### 本地開發
```bash
# 直接執行
cd src
python main.py

# 使用全域命令 (需先安裝)
python scripts/setup_global.py
locallm
```

### 測試
```bash
# 執行所有測試
python -m pytest tests/

# 執行特定測試
python tests/test_commands.py

# 手動測試 UI
python tests/test_ui.py
```

### 程式碼品質
```bash
# 格式化程式碼
black src/ tests/ scripts/

# Linting
flake8 src/ tests/ scripts/
```

## 🏗️ 建置與分發

### 建置套件
```bash
# 建置 wheel 和 tar.gz
python -m build

# 檢查建置結果
ls dist/
```

### 本地安裝測試
```bash
# 開發模式安裝
pip install -e .

# 正式安裝
pip install dist/locallm_cli-1.0.0-py3-none-any.whl
```

## 🔍 除錯技巧

### 常見問題

1. **模組導入錯誤**
   - 確保在 `src/` 目錄中執行
   - 檢查 `PYTHONPATH` 設定

2. **Pylance 錯誤**
   - 專案已配置 `.vscode/settings.json`
   - 重新載入 VS Code 窗口

3. **全域命令不工作**
   - 重新執行 `python scripts/setup_global.py`
   - 檢查 PATH 環境變數

### 除錯工具
```bash
# 除錯命令解析
python tests/debug_commands.py

# 測試 Ollama 連線
python -c "from src.models import is_available; print(is_available())"
```

## 📝 貢獻指南

1. **程式碼風格**
   - 使用 Black 格式化
   - 遵循 PEP 8
   - 添加適當的類型提示

2. **提交訊息**
   ```
   類型(範圍): 簡短描述
   
   詳細描述...
   ```

3. **測試要求**
   - 新功能需要添加測試
   - 確保所有測試通過

## 🚀 發佈流程

1. 更新版本號 (`src/__init__.py`, `setup.py`, `pyproject.toml`)
2. 更新 CHANGELOG
3. 建置和測試
4. 標記版本並推送
5. 建置分發套件
6. 上傳到 PyPI (如需要)

## 📞 支援

如有問題或建議，請：
- 提交 Issue
- 發起 Pull Request
- 查看文件 (`docs/`)