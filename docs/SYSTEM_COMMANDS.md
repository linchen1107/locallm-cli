# LocalLM CLI 系統功能說明

## 可用命令列表

### 檔案操作命令
- `/read <path>` - 讀取檔案內容，支援多種格式 (txt, pdf, docx, xlsx, pptx 等)
- `/write <path>` - 寫入檔案內容
- `/edit <path>` - 編輯現有檔案
- `/create <path>` - 創建新檔案
- `/analyze <pdf>` - 深度分析PDF檔案 (RAG功能)
- `/ocr <pdf>` - 對掃描PDF進行OCR識別

### 目錄操作命令
- `/list [dir]` - 列出目錄內容 (別名: /ls)
- `/tree [dir]` - 顯示目錄樹狀結構
- `/pwd` - 顯示當前工作目錄

### 系統管理命令
- `/mkdir <dir>` - 創建目錄
- `/cd <dir>` - 切換工作目錄
- `/mv <src> <dst>` - 移動/重命名檔案或目錄 (別名: /move)
- `/cp <src> <dst>` - 複製檔案或目錄 (別名: /copy)
  - 使用 `-r` 選項可遞歸複製目錄
- `/rm <file>` - 刪除檔案或目錄 (別名: /del)
  - 使用 `-r` 選項可遞歸刪除目錄
  - 使用 `-f` 選項可強制刪除無需確認

### 智能分類命令
- `/classify author` - 按檔案名中的作者分類
- `/classify type` - 按檔案類型分類
- `/classify content` - 按檔案內容智能分類
- `/classify mixed` - 混合分類（作者+類型）
- `/classify preview <mode>` - 預覽分類結果

### 程式碼操作命令
- `/patch <file>` - 安全地修改程式碼並自動備份

### 模型管理命令
- `/models` - 顯示可用模型列表
- `/switch <name>` - 切換到指定模型 (別名: /model)
- `/load <model>` - 重新載入模型
- `/save <name>` - 將當前對話保存為新模型
- `/saved [cmd]` - 管理已保存的對話模型

### 工作區管理命令
- `/dir add <path>` - 添加工作區目錄
- `/dir show` - 顯示工作區目錄列表
- `/init [dir]` - 在目錄中創建GEMINI.md檔案

### 歷史與恢復命令
- `/restore [id]` - 恢復檔案備份
- `/bye` - 清空對話歷史
- `/clear` - 清除畫面

### 幫助命令
- `/help` - 顯示幫助資訊
- `/exit` - 退出程式 (別名: /quit)

## 智能檔案內容分類

系統能夠根據檔案內容自動識別以下類型：
- **API文檔** - REST API、端點定義等
- **配置檔案** - 環境設定、專案配置等
- **測試檔案** - 單元測試、集成測試等
- **資料庫相關** - SQL、ORM模型等
- **前端UI** - React、Vue組件等
- **後端邏輯** - 服務器、控制器等
- **文檔說明** - README、指南等
- **腳本工具** - 自動化腳本等
- **數據分析** - pandas、numpy等
- **機器學習** - TensorFlow、PyTorch等

## 特殊功能

### RAG (檢索增強生成)
- 使用 `/analyze` 命令可以深度分析PDF文件
- 系統會自動建立向量索引並支援智能問答
- 支援大型文件的分塊處理

### OCR 文字識別
- 使用 `/ocr` 命令可以識別掃描PDF中的文字
- 支援中英文混合識別

### Office檔案支援
- 支援讀取Word (.docx)、Excel (.xlsx)、PowerPoint (.pptx)
- 自動提取文字內容、表格資料和結構化資訊

### 安全備份
- `/patch` 命令會自動創建時間戳備份
- `/restore` 命令可以恢復歷史版本

當用戶詢問關於檔案操作、系統管理或任何CLI功能時，請根據以上資訊提供準確的幫助和建議。