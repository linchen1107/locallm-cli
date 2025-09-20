#!/usr/bin/env python3
"""
RAG (檢索增強生成) 功能模組

提供 PDF 文件的文字提取、清理、分割、向量化和檢索功能。
"""

from .rag_core import (
    TextCleaner,
    TextChunker, 
    EmbeddingManager,
    VectorDatabase,
    HAS_RAG_SUPPORT
)

from .pdf_processor import (
    PDFRAGProcessor,
    create_rag_processor,
    is_rag_available
)

__all__ = [
    # 核心類別
    'TextCleaner',
    'TextChunker', 
    'EmbeddingManager',
    'VectorDatabase',
    
    # PDF 處理器
    'PDFRAGProcessor',
    
    # 便捷函數
    'create_rag_processor',
    'is_rag_available',
    
    # 狀態檢查
    'HAS_RAG_SUPPORT'
]