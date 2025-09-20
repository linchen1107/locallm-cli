#!/usr/bin/env python3
"""
RAG 核心功能模組
"""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# 檢查 RAG 依賴是否可用
HAS_RAG_SUPPORT = True
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
except ImportError as e:
    HAS_RAG_SUPPORT = False
    np = None
    SentenceTransformer = None
    chromadb = None
    Settings = None

logger = logging.getLogger(__name__)


class TextCleaner:
    """文字清理器"""
    
    def __init__(self):
        # 常見頁首頁尾模式
        self.header_patterns = [
            r'^第\s*\d+\s*頁',  # 第X頁
            r'^\d+\s*$',        # 純數字行
            r'^Page\s+\d+',     # Page X
            r'^-?\s*\d+\s*-?$', # -數字-
        ]
        
        self.footer_patterns = [
            r'第\s*\d+\s*頁\s*$',
            r'\d+\s*$',
            r'Page\s+\d+\s*$',
        ]
        
        # 編譯正則表達式
        self.header_regex = [re.compile(pattern, re.MULTILINE) for pattern in self.header_patterns]
        self.footer_regex = [re.compile(pattern, re.MULTILINE) for pattern in self.footer_patterns]
    
    def clean_text(self, text: str) -> str:
        """清理文字內容"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 跳過空行
            if not line:
                continue
            
            # 檢查是否為頁首頁尾
            is_header_footer = False
            for regex in self.header_regex + self.footer_regex:
                if regex.match(line):
                    is_header_footer = True
                    break
            
            if not is_header_footer:
                cleaned_lines.append(line)
        
        # 合併行並修復斷行
        cleaned_text = ' '.join(cleaned_lines)
        cleaned_text = self._fix_line_breaks(cleaned_text)
        
        return cleaned_text
    
    def _fix_line_breaks(self, text: str) -> str:
        """修復不正確的斷行"""
        # 修復中文斷行（移除不必要的空格）
        text = re.sub(r'([^\w\s])\s+([^\w\s])', r'\1\2', text)
        
        # 修復句子間的空格
        text = re.sub(r'\s+', ' ', text)
        
        # 修復標點符號前的空格
        text = re.sub(r'\s+([，。！？；：])', r'\1', text)
        
        return text.strip()


class TextChunker:
    """文字分割器"""
    
    def __init__(self, chunk_size: int = 500, overlap_size: int = 100):
        """
        初始化文字分割器
        
        Args:
            chunk_size: 分割片段大小
            overlap_size: 重疊區域大小
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        分割文字為片段
        
        Args:
            text: 要分割的文字
            metadata: 額外的元數據
            
        Returns:
            List[Dict]: 文字片段列表
        """
        if not text:
            return []
        
        # 首先按句子分割
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # 如果加入這個句子會超過chunk_size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # 保存當前chunk
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': len(chunks),
                    'chunk_size': current_length
                })
                
                chunks.append({
                    'text': current_chunk.strip(),
                    'metadata': chunk_metadata
                })
                
                # 開始新chunk，包含重疊部分
                if self.overlap_size > 0:
                    overlap_text = self._get_overlap_text(current_chunk, self.overlap_size)
                    current_chunk = overlap_text + " " + sentence
                    current_length = len(current_chunk)
                else:
                    current_chunk = sentence
                    current_length = sentence_length
            else:
                # 加入當前句子
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_length += sentence_length
        
        # 處理最後一個chunk
        if current_chunk:
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                'chunk_index': len(chunks),
                'chunk_size': len(current_chunk)
            })
            
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': chunk_metadata
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """將文字分割為句子"""
        # 中文句子分割模式
        sentence_pattern = r'[。！？；]+|\.+|\!+|\?+|;+'
        sentences = re.split(sentence_pattern, text)
        
        # 清理並過濾空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """獲取重疊文字"""
        if len(text) <= overlap_size:
            return text
        
        # 從結尾往前取overlap_size個字符
        overlap_text = text[-overlap_size:]
        
        # 嘗試在句子邊界處截斷
        sentence_end = max(
            overlap_text.rfind('。'),
            overlap_text.rfind('！'),
            overlap_text.rfind('？'),
            overlap_text.rfind('.'),
            overlap_text.rfind('!'),
            overlap_text.rfind('?')
        )
        
        if sentence_end > overlap_size // 2:  # 如果找到合適的句子邊界
            return overlap_text[sentence_end + 1:].strip()
        
        return overlap_text


class EmbeddingManager:
    """嵌入向量管理器"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化嵌入管理器
        
        Args:
            model_name: 句子嵌入模型名稱
        """
        if not HAS_RAG_SUPPORT:
            raise ImportError("嵌入功能需要安裝 sentence-transformers")
        
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加載嵌入模型"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"已加載嵌入模型: {self.model_name}")
        except Exception as e:
            logger.error(f"加載嵌入模型失敗: {e}")
            raise
    
    def encode(self, texts: List[str]):
        """
        編碼文字列表為嵌入向量
        
        Args:
            texts: 文字列表
            
        Returns:
            np.ndarray: 嵌入向量矩陣
        """
        if not texts:
            return np.array([])
        
        try:
            embeddings = self.model.encode(texts, show_progress_bar=True)
            return embeddings
        except Exception as e:
            logger.error(f"文字編碼失敗: {e}")
            return np.array([])
    
    def encode_single(self, text: str):
        """
        編碼單個文字為嵌入向量
        
        Args:
            text: 文字內容
            
        Returns:
            np.ndarray: 嵌入向量
        """
        try:
            embedding = self.model.encode([text])[0]
            return embedding
        except Exception as e:
            logger.error(f"單文字編碼失敗: {e}")
            return np.array([])


class VectorDatabase:
    """向量資料庫管理器"""
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        """
        初始化向量資料庫
        
        Args:
            persist_directory: 持久化存储目录
        """
        if not HAS_RAG_SUPPORT:
            raise ImportError("向量資料庫功能需要安裝 chromadb")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.collection_name = "pdf_documents"
        self.client = None
        self.collection = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化 ChromaDB 客戶端"""
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory)
            )
            self._ensure_collection()
            logger.info(f"向量資料庫初始化完成: {self.persist_directory}")
        except Exception as e:
            logger.error(f"向量資料庫初始化失敗: {e}")
            raise
    
    def _ensure_collection(self):
        """確保集合存在"""
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"使用現有集合: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "PDF 文檔向量存儲"}
            )
            logger.info(f"創建新集合: {self.collection_name}")
    
    def add_documents(self, chunks: List[Dict], embeddings):
        """
        添加文檔片段到向量資料庫
        
        Args:
            chunks: 文檔片段列表
            embeddings: 對應的嵌入向量
        """
        if len(chunks) != len(embeddings):
            raise ValueError("文檔片段數量與嵌入向量數量不匹配")
        
        # 準備數據
        ids = [f"chunk_{i}_{hash(chunk['text'])}" for i, chunk in enumerate(chunks)]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk.get('metadata', {}) for chunk in chunks]
        
        # 添加到集合
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings.tolist()
        )
        
        logger.info(f"添加 {len(chunks)} 個文檔片段到向量資料庫")
    
    def search(self, query_embedding, n_results: int = 5) -> Dict:
        """
        搜索相關文檔
        
        Args:
            query_embedding: 查詢向量
            n_results: 返回結果數量
            
        Returns:
            Dict: 搜索結果
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            # 將 QueryResult 轉換為標準 Dict 格式
            return {
                'documents': getattr(results, 'documents', results.get('documents', [])),
                'metadatas': getattr(results, 'metadatas', results.get('metadatas', [])),
                'distances': getattr(results, 'distances', results.get('distances', [])),
                'ids': getattr(results, 'ids', results.get('ids', []))
            }
        except Exception as e:
            logger.error(f"向量搜索失敗: {e}")
            return {
                'documents': [],
                'metadatas': [],
                'distances': [],
                'ids': []
            }
    
    def get_stats(self) -> Dict:
        """獲取資料庫統計信息"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"獲取統計信息失敗: {e}")
            return {}


# 導出主要類別
__all__ = [
    'TextCleaner', 
    'TextChunker', 
    'EmbeddingManager', 
    'VectorDatabase',
    'HAS_RAG_SUPPORT'
]