# LocalLM 全域安裝指南

## 🚀 快速安裝

### 方法一：PowerShell 一鍵安裝 (推薦)

在 LocalLM CLI 目錄中執行：

```powershell
# 臨時添加到當前會話
$env:PATH += ";$(Get-Location)"

# 永久添加到使用者 PATH
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
$newPath = if ($userPath) { "$userPath;$(Get-Location)" } else { "$(Get-Location)" }
[Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
```

### 方法二：手動設定

1. **複製 LocalLM CLI 路徑**
   ```
   C:\Users\will\Desktop\locallm-cli
   ```

2. **添加到系統 PATH**
   - 開啟「設定」→「系統」→「關於」
   - 點擊「進階系統設定」
   - 點擊「環境變數」
   - 在「使用者變數」中選擇「Path」→「編輯」
   - 點擊「新增」，貼上 LocalLM CLI 路徑
   - 確定所有對話框

3. **重新開啟終端**

## ✅ 驗證安裝

開啟新的 PowerShell 或命令提示字元：

```bash
# 檢查命令是否可用
locallm --help

# 在任意目錄測試
cd C:\
locallm --help
```

## 🎯 使用範例

### 基本使用

```bash
# 在任意目錄啟動 LocalLM CLI
locallm

# 使用指定模型
locallm -m llama3.1
```

### 實際工作流程示例

```bash
# 切換到專案目錄
cd C:\Projects\MyProject

# 啟動 LocalLM CLI
locallm

# 在 CLI 中執行操作
  › /read README.md
  › /list src
  › 請幫我分析這個專案的結構
  › /write notes.md "專案分析結果"
```

## 📁 檔案結構

安裝後，您的 LocalLM CLI 目錄包含：

```
locallm-cli/
├── locallm.bat          # Windows 批次檔（全域命令入口）
├── locallm_entry.py     # Python 入口點腳本
├── main.py              # 主程式
├── models/              # 模型通信模組
├── tools/               # 檔案操作工具
├── install.bat          # 批次檔安裝腳本
├── install.ps1          # PowerShell 安裝腳本
└── requirements.txt     # 依賴套件
```

## 🔧 工作原理

1. **`locallm.bat`**: Windows 系統的入口點，調用 Python 腳本
2. **`locallm_entry.py`**: 處理路徑和環境設定，保持在使用者的工作目錄
3. **動態路徑**: 程式始終在使用者當前目錄工作，但模組從安裝目錄載入

## 🐛 故障排除

### 命令未找到
```bash
# 檢查 PATH 是否包含 LocalLM CLI 目錄
echo $env:PATH  # PowerShell
echo %PATH%     # 命令提示字元
```

### Python 錯誤
```bash
# 確保 Python 可用
python --version

# 檢查依賴
cd C:\Users\will\Desktop\locallm-cli
pip install -r requirements.txt
```

### Ollama 連接問題
```bash
# 檢查 Ollama 是否運行
ollama list

# 如果未運行，啟動 Ollama
ollama serve
```

## 🎉 享受使用！

現在您可以在電腦的任意位置輸入 `locallm` 來啟動您的本地智能助手！

### 常用場景

- **程式開發**: 在專案目錄中分析和修改代碼
- **文件處理**: 在任意目錄處理文本檔案
- **學習探索**: 快速查看和分析各種檔案內容

---

*LocalLM CLI - 讓本地模型成為您的全域程式助手！* 🚀