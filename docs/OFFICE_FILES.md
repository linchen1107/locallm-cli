# Office 文件支援功能

LocalLM CLI 現在支援讀取多種 Office 文件格式，讓您可以輕鬆處理工作中常用的文檔！

## 🎯 支援的文件格式

### 📄 Word 文件 (.docx)
- **功能**：提取文字內容、段落、表格
- **使用方式**：`/read document.docx`
- **特色**：
  - 自動提取所有段落文字
  - 識別並格式化表格內容
  - 保持文檔結構層次

### 📊 Excel 試算表 (.xlsx, .xlsm)
- **功能**：讀取工作表數據、多工作表支援
- **使用方式**：
  - `/read spreadsheet.xlsx` (讀取預設工作表)
  - `/read spreadsheet.xlsx 工作表名稱` (讀取特定工作表)
- **特色**：
  - 支援多個工作表
  - 自動格式化表格數據
  - 顯示所有可用工作表清單

### 🎯 PowerPoint 簡報 (.pptx)
- **功能**：提取投影片內容、文字、表格
- **使用方式**：`/read presentation.pptx`
- **特色**：
  - 按投影片順序組織內容
  - 提取投影片中的所有文字
  - 識別並格式化表格內容

## 📝 使用範例

### 基本讀取
```bash
# 讀取 Word 文件
/read 報告.docx

# 讀取 Excel 文件 (預設工作表)
/read 數據分析.xlsx

# 讀取特定 Excel 工作表
/read 數據分析.xlsx 月報表

# 讀取 PowerPoint 簡報
/read 專案提案.pptx
```

### 與 AI 對話結合
```bash
# 讀取檔案後提問
/read 財務報表.xlsx
請幫我分析這份財務報表的主要指標

# 讀取簡報後請求改進建議
/read 產品介紹.pptx
這份簡報如何改進會更吸引人？
```

## 🔧 安裝需求

使用 Office 文件功能需要安裝相應的 Python 套件：

```bash
# Word 支援
pip install python-docx

# Excel 支援  
pip install openpyxl

# PowerPoint 支援
pip install python-pptx
```

或一次安裝所有套件：
```bash
pip install python-docx openpyxl python-pptx
```

## ⚡ 實際應用場景

### 📈 商業報告分析
- 讀取財務報表，請 AI 分析關鍵指標
- 處理客戶調查數據，生成洞察報告
- 分析競爭對手簡報內容

### 📚 學術研究
- 提取論文附錄中的數據表格
- 分析研究報告的結構和內容
- 整理參考文獻和研究資料

### 💼 日常辦公
- 快速瀏覽會議紀錄重點
- 提取合約文件關鍵條款
- 分析專案進度報告

## 🛠️ 技術特色

### 智能文字提取
- **Word**：保留段落結構，提取表格內容
- **Excel**：智能識別數據表格，支援多工作表
- **PowerPoint**：按投影片組織，提取文字和表格

### 錯誤處理
- 自動檢測文件格式
- 友善的錯誤提示
- 依賴套件安裝指引

### 性能優化
- 僅讀取文字內容，不載入格式化資訊
- 記憶體效率優化
- 支援大型文件處理

## 🔮 未來擴展

計劃中的功能增強：
- 支援更多 Office 格式 (.doc, .xls, .ppt)
- 圖片內容 OCR 識別
- 表格數據結構化分析
- 與 RAG 系統深度整合

---

**提示**：Office 文件支援讓 LocalLM CLI 成為您處理工作文檔的強大助手，結合 AI 對話功能，可以快速分析和理解複雜的商業文檔！