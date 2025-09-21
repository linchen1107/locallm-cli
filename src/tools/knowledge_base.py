#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知識庫管理工具
支持本地向量數據庫，構建個人知識庫
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

# 向量數據庫相關
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

# 文檔處理相關
try:
    import fitz  # PyMuPDF
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False

try:
    from docx import Document
    HAS_DOCX_SUPPORT = True
except ImportError:
    HAS_DOCX_SUPPORT = False

try:
    import pandas as pd
    HAS_CSV_SUPPORT = True
except ImportError:
    HAS_CSV_SUPPORT = False

# 文本處理
import re
from collections import defaultdict

class KnowledgeBase:
    """本地知識庫管理器"""
    
    def __init__(self, kb_path: str = "data/knowledge_base"):
        self.kb_path = Path(kb_path)
        self.kb_path.mkdir(parents=True, exist_ok=True)
        
        # 知識庫元數據文件
        self.metadata_file = self.kb_path / "metadata.json"
        self.documents_file = self.kb_path / "documents.json"
        
        # 設置日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化元數據
        self.metadata = self._load_metadata()
        self.documents = self._load_documents()
        
        # 初始化向量數據庫
        self.vector_db = None
        self._init_vector_db()
        
        # 支持的文檔類型
        self.supported_extensions = {
            '.txt': self._process_text_file,
            '.md': self._process_text_file,
            '.py': self._process_code_file,
            '.js': self._process_code_file,
            '.html': self._process_code_file,
            '.css': self._process_code_file,
            '.json': self._process_json_file,
            '.csv': self._process_csv_file,
            '.pdf': self._process_pdf_file,
            '.docx': self._process_docx_file,
        }
        
        # 設置日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _init_vector_db(self):
        """初始化向量數據庫"""
        if not HAS_CHROMADB:
            self.logger.warning("ChromaDB not available, using simple text search")
            return
        
        try:
            # 創建 ChromaDB 客戶端
            chroma_path = str(self.kb_path / "chroma_db")
            
            # 如果數據庫已存在且有問題，嘗試重置
            if os.path.exists(chroma_path):
                try:
                    self.vector_db = chromadb.PersistentClient(
                        path=chroma_path,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=False
                        )
                    )
                except Exception as reset_error:
                    self.logger.warning(f"Existing database has issues, resetting: {reset_error}")
                    # 刪除有問題的數據庫
                    import shutil
                    shutil.rmtree(chroma_path, ignore_errors=True)
                    # 重新創建
                    self.vector_db = chromadb.PersistentClient(
                        path=chroma_path,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True
                        )
                    )
            else:
                # 創建新的數據庫
                self.vector_db = chromadb.PersistentClient(
                    path=chroma_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            
            # 獲取或創建集合
            try:
                self.collection = self.vector_db.get_collection("knowledge_base")
            except Exception:
                self.collection = self.vector_db.create_collection(
                    name="knowledge_base",
                    metadata={"description": "LocalLM Knowledge Base"}
                )
                
        except Exception as e:
            self.logger.error(f"Failed to initialize vector database: {e}")
            self.vector_db = None
    
    def _load_metadata(self) -> Dict:
        """載入知識庫元數據"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load metadata: {e}")
        return {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_documents": 0,
            "total_chunks": 0,
            "version": "1.0"
        }
    
    def _save_metadata(self):
        """保存知識庫元數據"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
    
    def _load_documents(self) -> Dict:
        """載入文檔索引"""
        if self.documents_file.exists():
            try:
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load documents: {e}")
        return {}
    
    def _save_documents(self):
        """保存文檔索引"""
        try:
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save documents: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """計算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """將文本分割成塊"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 嘗試在句號或換行符處分割
            if end < len(text):
                # 向前查找合適的分割點
                for i in range(end, max(start + chunk_size // 2, end - 200), -1):
                    if text[i] in '。\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _process_text_file(self, file_path: str) -> List[Dict[str, Any]]:
        """處理文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = self._chunk_text(content)
            return [
                {
                    "content": chunk,
                    "metadata": {
                        "file_path": file_path,
                        "file_type": "text",
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        except Exception as e:
            self.logger.error(f"Failed to process text file {file_path}: {e}")
            return []
    
    def _process_code_file(self, file_path: str) -> List[Dict[str, Any]]:
        """處理代碼文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按函數或類分割代碼
            chunks = self._chunk_text(content, chunk_size=800, overlap=100)
            
            return [
                {
                    "content": chunk,
                    "metadata": {
                        "file_path": file_path,
                        "file_type": "code",
                        "language": Path(file_path).suffix[1:],
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        except Exception as e:
            self.logger.error(f"Failed to process code file {file_path}: {e}")
            return []
    
    def _process_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """處理JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 將JSON轉換為可讀文本
            content = json.dumps(data, indent=2, ensure_ascii=False)
            chunks = self._chunk_text(content, chunk_size=600, overlap=100)
            
            return [
                {
                    "content": chunk,
                    "metadata": {
                        "file_path": file_path,
                        "file_type": "json",
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        except Exception as e:
            self.logger.error(f"Failed to process JSON file {file_path}: {e}")
            return []
    
    def _process_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """處理CSV文件"""
        if not HAS_CSV_SUPPORT:
            return self._process_text_file(file_path)
        
        try:
            df = pd.read_csv(file_path)
            
            # 生成CSV摘要
            summary = f"CSV文件: {Path(file_path).name}\n"
            summary += f"行數: {len(df)}\n"
            summary += f"列數: {len(df.columns)}\n"
            summary += f"列名: {', '.join(df.columns)}\n\n"
            
            # 添加前幾行數據
            summary += "前5行數據:\n"
            summary += df.head().to_string()
            
            chunks = self._chunk_text(summary, chunk_size=800, overlap=100)
            
            return [
                {
                    "content": chunk,
                    "metadata": {
                        "file_path": file_path,
                        "file_type": "csv",
                        "rows": len(df),
                        "columns": len(df.columns),
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        except Exception as e:
            self.logger.error(f"Failed to process CSV file {file_path}: {e}")
            return []
    
    def _process_pdf_file(self, file_path: str) -> List[Dict[str, Any]]:
        """處理PDF文件"""
        if not HAS_PDF_SUPPORT:
            return []
        
        try:
            doc = fitz.open(file_path)
            content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                content += page.get_text()
            
            doc.close()
            
            chunks = self._chunk_text(content, chunk_size=1000, overlap=200)
            
            return [
                {
                    "content": chunk,
                    "metadata": {
                        "file_path": file_path,
                        "file_type": "pdf",
                        "total_pages": len(doc),
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        except Exception as e:
            self.logger.error(f"Failed to process PDF file {file_path}: {e}")
            return []
    
    def _process_docx_file(self, file_path: str) -> List[Dict[str, Any]]:
        """處理Word文件"""
        if not HAS_DOCX_SUPPORT:
            return []
        
        try:
            doc = Document(file_path)
            content = ""
            
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            
            chunks = self._chunk_text(content, chunk_size=1000, overlap=200)
            
            return [
                {
                    "content": chunk,
                    "metadata": {
                        "file_path": file_path,
                        "file_type": "docx",
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        except Exception as e:
            self.logger.error(f"Failed to process DOCX file {file_path}: {e}")
            return []
    
    def add_document(self, file_path: str) -> Dict[str, Any]:
        """添加文檔到知識庫"""
        file_path = Path(file_path).resolve()
        
        if not file_path.exists():
            return {"success": False, "error": f"文件不存在: {file_path}"}
        
        if file_path.suffix.lower() not in self.supported_extensions:
            return {"success": False, "error": f"不支持的文件類型: {file_path.suffix}"}
        
        # 檢查文件是否已經存在
        file_hash = self._get_file_hash(str(file_path))
        if file_hash in self.documents:
            return {"success": False, "error": f"文件已經存在於知識庫中: {file_path.name}"}
        
        # 處理文件
        processor = self.supported_extensions[file_path.suffix.lower()]
        chunks = processor(str(file_path))
        
        if not chunks:
            return {"success": False, "error": f"無法處理文件: {file_path.name}"}
        
        # 添加到向量數據庫
        if self.vector_db:
            try:
                # 準備數據
                documents = [chunk["content"] for chunk in chunks]
                metadatas = [chunk["metadata"] for chunk in chunks]
                ids = [f"{file_hash}_{i}" for i in range(len(chunks))]
                
                # 添加到集合
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            except Exception as e:
                self.logger.error(f"Failed to add to vector database: {e}")
                return {"success": False, "error": f"向量數據庫錯誤: {e}"}
        
        # 更新文檔索引
        self.documents[file_hash] = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "added_at": datetime.now().isoformat(),
            "chunks_count": len(chunks),
            "file_type": file_path.suffix.lower()
        }
        
        # 更新元數據
        self.metadata["total_documents"] += 1
        self.metadata["total_chunks"] += len(chunks)
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        # 保存數據
        self._save_documents()
        self._save_metadata()
        
        return {
            "success": True,
            "message": f"成功添加文檔: {file_path.name}",
            "chunks": len(chunks),
            "file_type": file_path.suffix.lower()
        }
    
    def add_directory(self, dir_path: str, pattern: str = "*") -> Dict[str, Any]:
        """批量添加目錄中的文件"""
        dir_path = Path(dir_path).resolve()
        
        if not dir_path.exists() or not dir_path.is_dir():
            return {"success": False, "error": f"目錄不存在: {dir_path}"}
        
        results = []
        total_added = 0
        total_errors = 0
        
        # 查找匹配的文件
        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                result = self.add_document(str(file_path))
                results.append({
                    "file": file_path.name,
                    "result": result
                })
                
                if result["success"]:
                    total_added += 1
                else:
                    total_errors += 1
        
        return {
            "success": True,
            "message": f"批量添加完成: {total_added} 個文件成功, {total_errors} 個錯誤",
            "total_added": total_added,
            "total_errors": total_errors,
            "results": results
        }
    
    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """查詢知識庫"""
        if not self.vector_db:
            return {"success": False, "error": "向量數據庫未初始化"}
        
        if not self.documents:
            return {"success": False, "error": "知識庫為空"}
        
        try:
            # 執行相似性搜索
            results = self.collection.query(
                query_texts=[question],
                n_results=top_k
            )
            
            # 格式化結果
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                formatted_results.append({
                    "rank": i + 1,
                    "content": doc,
                    "metadata": metadata,
                    "similarity": 1 - distance,  # 轉換為相似度
                    "file_name": metadata.get("file_path", "").split("/")[-1]
                })
            
            return {
                "success": True,
                "question": question,
                "results": formatted_results,
                "total_found": len(formatted_results)
            }
            
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return {"success": False, "error": f"查詢失敗: {e}"}
    
    def list_documents(self) -> Dict[str, Any]:
        """列出知識庫中的所有文檔"""
        if not self.documents:
            return {"success": True, "documents": [], "message": "知識庫為空"}
        
        doc_list = []
        for file_hash, doc_info in self.documents.items():
            doc_list.append({
                "file_name": doc_info["file_name"],
                "file_path": doc_info["file_path"],
                "file_type": doc_info["file_type"],
                "file_size": doc_info["file_size"],
                "added_at": doc_info["added_at"],
                "chunks_count": doc_info["chunks_count"]
            })
        
        # 按添加時間排序
        doc_list.sort(key=lambda x: x["added_at"], reverse=True)
        
        return {
            "success": True,
            "documents": doc_list,
            "total_documents": len(doc_list),
            "metadata": self.metadata
        }
    
    def delete_document(self, file_name: str) -> Dict[str, Any]:
        """從知識庫中刪除文檔"""
        # 查找文件
        file_hash = None
        for hash_key, doc_info in self.documents.items():
            if doc_info["file_name"] == file_name:
                file_hash = hash_key
                break
        
        if not file_hash:
            return {"success": False, "error": f"未找到文檔: {file_name}"}
        
        # 從向量數據庫中刪除
        if self.vector_db:
            try:
                # 查找所有相關的chunk IDs
                chunk_ids = [f"{file_hash}_{i}" for i in range(self.documents[file_hash]["chunks_count"])]
                self.collection.delete(ids=chunk_ids)
            except Exception as e:
                self.logger.error(f"Failed to delete from vector database: {e}")
        
        # 從文檔索引中刪除
        doc_info = self.documents.pop(file_hash)
        
        # 更新元數據
        self.metadata["total_documents"] -= 1
        self.metadata["total_chunks"] -= doc_info["chunks_count"]
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        # 保存數據
        self._save_documents()
        self._save_metadata()
        
        return {
            "success": True,
            "message": f"成功刪除文檔: {file_name}",
            "deleted_chunks": doc_info["chunks_count"]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取知識庫統計信息"""
        return {
            "success": True,
            "metadata": self.metadata,
            "total_documents": len(self.documents),
            "supported_types": list(self.supported_extensions.keys()),
            "vector_db_available": self.vector_db is not None
        }

# 創建默認實例
default_knowledge_base = KnowledgeBase()
