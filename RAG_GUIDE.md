# LocalLM CLI - RAG 功能使用指南

## 概述

LocalLM CLI 現在支援完整的 RAG（檢索增強生成）功能，可以處理 PDF 文件並提供智能文檔分析和問答服務。

## 功能特色

### 🎯 核心功能
- **PDF 文件讀取**: 支援多頁 PDF 文字提取
- **智能文字處理**: 自動清理頁首頁尾、修復斷行
- **文字分割**: 智能分割為語義片段，支援重疊處理
- **語義嵌入**: 使用 sentence-transformers 生成向量
- **向量資料庫**: ChromaDB 持久化存儲
- **語義搜索**: 基於相似度的文檔檢索
- **RAG 問答**: 結合搜索結果生成回答

### 📦 依賴套件
```bash
pip install sentence-transformers>=2.2.0
pip install chromadb>=0.4.0
pip install numpy>=2.3.0
pip install pymupdf>=1.23.0
```

## 使用方法

### 1. 基本 PDF 讀取
```bash
/read document.pdf
```
- 讀取並顯示 PDF 文件內容
- 支援多頁文檔
- 自動處理文字編碼

### 2. RAG 分析功能

#### 僅分析 PDF（建立向量資料庫）
```bash
/analyze document.pdf
```
**功能說明:**
- 讀取 PDF 內容
- 執行文字清理和預處理
- 分割為語義片段
- 生成嵌入向量
- 存入向量資料庫
- 顯示處理統計信息

**輸出示例:**
```
📖 正在讀取 PDF: document.pdf
🔧 初始化 RAG 處理器...
🔄 處理文字並建立向量資料庫...
✓ 處理完成:
  - 原始長度: 1250 字符
  - 清理後長度: 1180 字符
  - 分割片段: 5 個
  - 向量維度: 384

📊 向量資料庫統計:
  - 集合名稱: pdf_documents
  - 文檔數量: 5
  - 存儲路徑: data\chroma_db
```

#### 智能問答（RAG 檢索）
```bash
/analyze document.pdf "這份文件的主要內容是什麼？"
```
**功能說明:**
- 處理 PDF 並建立向量資料庫
- 對查詢進行語義編碼
- 搜索最相關的文檔片段
- 生成基於上下文的回答

**輸出示例:**
```
🔍 搜索查詢: 「這份文件的主要內容是什麼？」
📋 找到 3 個相關片段:
  1. 相似度: 0.892
     本文檔介紹了公司的年度財務報告，包含營收分析...
  2. 相似度: 0.847
     財務表現方面，本年度營收成長了 15%，主要來源於...
  3. 相似度: 0.823
     未來展望部分說明了公司的戰略規劃和發展方向...

🤖 基於文檔內容的回答:
──────────────────────────────────────────────────
基於文檔內容，關於「這份文件的主要內容是什麼？」的回答：

[片段 1] 本文檔介紹了公司的年度財務報告...
[片段 2] 財務表現方面，本年度營收成長了 15%...
[片段 3] 未來展望部分說明了公司的戰略規劃...

資料來源：document.pdf
共找到 3 個相關片段
──────────────────────────────────────────────────
```

## 技術架構

### RAG 處理流程
```
PDF 文件 → 文字提取 → 文字清理 → 分割片段 → 嵌入向量 → 向量資料庫
                                                      ↓
用戶查詢 → 查詢編碼 → 相似度搜索 → 檢索片段 → 生成回答
```

### 核心模組

#### 1. 文字清理器 (TextCleaner)
- 移除頁首頁尾
- 修復斷行問題
- 清理格式化文字

#### 2. 文字分割器 (TextChunker)
- 按語義分割文字
- 支援重疊處理
- 保留上下文連續性

#### 3. 嵌入管理器 (EmbeddingManager)
- 使用 sentence-transformers
- 支援多種預訓練模型
- 批次處理優化

#### 4. 向量資料庫 (VectorDatabase)
- ChromaDB 持久化存儲
- 支援相似度搜索
- 自動索引管理

### 配置選項

#### RAG 處理器參數
```python
processor = create_rag_processor(
    chunk_size=500,           # 分割片段大小
    overlap_size=100,         # 重疊區域大小
    embedding_model="all-MiniLM-L6-v2",  # 嵌入模型
    db_path="data/chroma_db"  # 資料庫路徑
)
```

#### 支援的嵌入模型
- `all-MiniLM-L6-v2` (預設): 輕量級，平衡效能
- `all-mpnet-base-v2`: 高品質，較大模型
- `paraphrase-multilingual-MiniLM-L12-v2`: 多語言支援

## 最佳實踐

### 1. 文檔準備
- 確保 PDF 文字可提取（非掃描版）
- 文檔結構清晰，避免過多格式化
- 建議文檔大小適中（< 10MB）

### 2. 查詢優化
- 使用具體、明確的問題
- 避免過於抽象的查詢
- 可以嘗試不同的問法

### 3. 效能調優
```python
# 小文檔配置
chunk_size=300, overlap_size=50

# 大文檔配置  
chunk_size=800, overlap_size=150

# 高精度配置
embedding_model="all-mpnet-base-v2"
```

## 故障排除

### 常見問題

#### 1. RAG 功能不可用
```
✗ RAG 功能不可用，請安裝依賴:
  pip install sentence-transformers chromadb
```

#### 2. PDF 讀取失敗
```
✗ PDF support not available
💡 Install PyMuPDF: pip install pymupdf
```

#### 3. 記憶體不足
- 減少 `chunk_size` 參數
- 使用較小的嵌入模型
- 分批處理大文檔

#### 4. 搜索結果不理想
- 調整查詢用詞
- 增加 `n_results` 參數
- 檢查文檔品質

### 除錯模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 進階功能

### 1. 程式化使用
```python
from rag import create_rag_processor
from tools import read_pdf

# 創建處理器
processor = create_rag_processor()

# 處理 PDF
pdf_content = read_pdf("document.pdf")
result = processor.process_pdf_text(pdf_content, "document.pdf")

# 搜索查詢
results = processor.search_documents("查詢內容", n_results=5)

# 生成回答
response = processor.generate_rag_response("問題", results)
```

### 2. 資料庫管理
```python
# 獲取統計
stats = processor.get_database_stats()

# 清空資料庫
processor.clear_database()
```

## 更新日誌

### v1.0.0 (2025-09-21)
- ✅ 完整 RAG 系統實現
- ✅ PDF 文字提取和處理
- ✅ 語義搜索和問答
- ✅ CLI 命令整合
- ✅ 向量資料庫持久化
- ✅ 多語言文字處理

## 授權

本專案採用 MIT 授權條款。