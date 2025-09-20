#!/usr/bin/env python3
"""
RAG PDF 處理器 - 整合所有 RAG 功能的主要類別
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

try:
    from .rag_core import TextCleaner, TextChunker, EmbeddingManager, VectorDatabase, HAS_RAG_SUPPORT
except ImportError:
    from rag_core import TextCleaner, TextChunker, EmbeddingManager, VectorDatabase, HAS_RAG_SUPPORT

logger = logging.getLogger(__name__)


class PDFRAGProcessor:
    """PDF RAG 處理器主類別"""
    
    def __init__(self, 
                 chunk_size: int = 500,
                 overlap_size: int = 100,
                 embedding_model: str = "all-MiniLM-L6-v2",
                 db_path: str = "data/chroma_db"):
        """
        初始化 PDF RAG 處理器
        
        Args:
            chunk_size: 文字分割大小
            overlap_size: 重疊區域大小
            embedding_model: 嵌入模型名稱
            db_path: 向量資料庫路徑
        """
        if not HAS_RAG_SUPPORT:
            raise ImportError("RAG 功能需要安裝額外依賴: pip install sentence-transformers chromadb")
        
        self.text_cleaner = TextCleaner()
        self.text_chunker = TextChunker(chunk_size, overlap_size)
        self.embedding_manager = EmbeddingManager(embedding_model)
        self.vector_db = VectorDatabase(db_path)
        
        logger.info("PDF RAG 處理器初始化完成")
    
    def process_pdf_text(self, pdf_text: str, pdf_path: str) -> Dict[str, Any]:
        """
        處理 PDF 文字並存入向量資料庫
        
        Args:
            pdf_text: PDF 文字內容
            pdf_path: PDF 文件路徑
            
        Returns:
            Dict: 處理結果統計
        """
        logger.info(f"開始處理 PDF: {pdf_path}")
        
        # 1. 清理文字
        cleaned_text = self.text_cleaner.clean_text(pdf_text)
        logger.info(f"文字清理完成，原始長度: {len(pdf_text)}, 清理後長度: {len(cleaned_text)}")
        
        # 2. 分割文字
        metadata = {
            'source': pdf_path,
            'file_name': Path(pdf_path).name,
            'processed_at': str(datetime.now())
        }
        
        chunks = self.text_chunker.chunk_text(cleaned_text, metadata)
        logger.info(f"文字分割完成，共 {len(chunks)} 個片段")
        
        # 3. 生成嵌入向量
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_manager.encode(chunk_texts)
        
        # 4. 存入向量資料庫
        self.vector_db.add_documents(chunks, embeddings)
        
        result = {
            'pdf_path': pdf_path,
            'original_length': len(pdf_text),
            'cleaned_length': len(cleaned_text),
            'chunk_count': len(chunks),
            'embedding_dimension': embeddings.shape[1] if len(embeddings) > 0 else 0,
            'status': 'success'
        }
        
        logger.info(f"PDF 處理完成: {result}")
        return result
    
    def search_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相關文檔片段
        
        Args:
            query: 搜索查詢
            n_results: 返回結果數量
            
        Returns:
            List[Dict]: 搜索結果列表
        """
        logger.info(f"搜索查詢: '{query}'")
        
        # 編碼查詢
        query_embedding = self.embedding_manager.encode_single(query)
        
        # 搜索向量資料庫
        search_results = self.vector_db.search(query_embedding, n_results)
        
        # 格式化結果
        formatted_results = []
        if search_results and 'documents' in search_results:
            documents = search_results['documents'][0] if search_results['documents'] else []
            metadatas = search_results['metadatas'][0] if search_results.get('metadatas') else []
            distances = search_results['distances'][0] if search_results.get('distances') else []
            
            for i, doc in enumerate(documents):
                result = {
                    'text': doc,
                    'metadata': metadatas[i] if i < len(metadatas) else {},
                    'similarity_score': 1 - distances[i] if i < len(distances) else 0.0,
                    'rank': i + 1
                }
                formatted_results.append(result)
        
        logger.info(f"搜索完成，返回 {len(formatted_results)} 個結果")
        return formatted_results
    
    def generate_rag_response(self, query: str, context_results: List[Dict[str, Any]]) -> str:
        """
        基於搜索結果生成 RAG 回答
        
        Args:
            query: 用戶查詢
            context_results: 搜索得到的上下文
            
        Returns:
            str: 格式化的回答
        """
        if not context_results:
            return "抱歉，沒有找到相關的文檔內容來回答您的問題。"
        
        # 構建上下文
        context_texts = []
        sources = set()
        
        for result in context_results:
            context_texts.append(result['text'])
            metadata = result.get('metadata', {})
            if 'file_name' in metadata:
                sources.add(metadata['file_name'])
        
        context = "\n\n".join([f"[片段 {i+1}] {text}" for i, text in enumerate(context_texts)])
        
        # 格式化回答（這裡是簡化版，實際應該調用 LLM）
        response = f"""基於文檔內容，關於「{query}」的回答：

{context}

資料來源：{', '.join(sources) if sources else '未知'}
共找到 {len(context_results)} 個相關片段"""
        
        return response
    
    def get_database_stats(self) -> Dict[str, Any]:
        """獲取資料庫統計信息"""
        return self.vector_db.get_stats()
    
    def clear_database(self) -> bool:
        """清空向量資料庫"""
        try:
            # 重新創建集合（等於清空）
            self.vector_db.client.delete_collection(self.vector_db.collection_name)
            self.vector_db._ensure_collection()
            logger.info("向量資料庫已清空")
            return True
        except Exception as e:
            logger.error(f"清空資料庫失敗: {e}")
            return False


# 便捷函數
def create_rag_processor(**kwargs) -> PDFRAGProcessor:
    """創建 RAG 處理器實例"""
    return PDFRAGProcessor(**kwargs)


def is_rag_available() -> bool:
    """檢查 RAG 功能是否可用"""
    return HAS_RAG_SUPPORT


__all__ = ['PDFRAGProcessor', 'create_rag_processor', 'is_rag_available']