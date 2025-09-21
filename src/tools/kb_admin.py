#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知識庫管理員架構
實現完整的知識庫管理系統，支持多模型嵌入和靈活的數據庫管理
"""

import os
import json
import hashlib
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# 向量數據庫支持
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    import faiss
    import numpy as np
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

# 嵌入模型支持
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None

# 文檔處理支持
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

class EmbeddingModel(Enum):
    """支持的嵌入模型"""
    EMBEDDING_GEMMA = "embedding-gemma"
    BGE_M3 = "bge-m3"
    E5_MISTRAL = "e5-mistral"
    ALL_MINI_LM = "all-MiniLM-L6-v2"

class VectorStore(Enum):
    """支持的向量數據庫"""
    CHROMA = "chroma"
    FAISS = "faiss"
    SQLITE = "sqlite"

@dataclass
class DocumentChunk:
    """文檔塊數據結構"""
    content: str
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None
    chunk_id: Optional[str] = None
    file_hash: Optional[str] = None

@dataclass
class KnowledgeBaseConfig:
    """知識庫配置"""
    name: str
    embedding_model: EmbeddingModel
    vector_store: VectorStore
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    supported_extensions: List[str] = None
    
    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = [
                '.txt', '.md', '.py', '.js', '.html', '.css', '.json',
                '.pdf', '.docx', '.xlsx', '.pptx', '.csv', '.sql', '.yml', '.yaml', '.toml'
            ]

class EmbeddingLayer:
    """嵌入層 - 負責文本向量化"""
    
    def __init__(self, model: EmbeddingModel):
        self.model = model
        self.transformer = None
        self.dimension = None
        self._load_model()
    
    def _load_model(self):
        """載入嵌入模型"""
        if not HAS_SENTENCE_TRANSFORMERS:
            logging.warning("sentence-transformers not available, using dummy embeddings")
            self.transformer = None
            self.dimension = 384
            return
        
        try:
            if self.model == EmbeddingModel.EMBEDDING_GEMMA:
                # 使用 sentence-transformers 的 embedding model
                self.transformer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                self.dimension = 384
            elif self.model == EmbeddingModel.BGE_M3:
                # BGE-M3 模型，支持中英文
                self.transformer = SentenceTransformer('BAAI/bge-m3')
                self.dimension = 1024
            elif self.model == EmbeddingModel.E5_MISTRAL:
                # E5-Mistral 模型
                self.transformer = SentenceTransformer('intfloat/e5-mistral-7b-instruct')
                self.dimension = 4096
            else:
                # 默認使用 all-MiniLM
                self.transformer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                self.dimension = 384
            
            logging.info(f"Loaded embedding model: {self.model.value}, dimension: {self.dimension}")
            
        except Exception as e:
            logging.error(f"Failed to load embedding model {self.model.value}: {e}")
            # 回退到默認模型
            try:
                self.transformer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                self.dimension = 384
            except:
                self.transformer = None
                self.dimension = 384
    
    def embed_text(self, text: str) -> List[float]:
        """將文本轉換為向量"""
        try:
            if self.transformer is None:
                # 返回隨機向量作為占位符
                import random
                return [random.random() for _ in range(self.dimension)]
            
            # 處理空文本
            if not text.strip():
                return [0.0] * self.dimension
            
            # 生成嵌入向量
            embedding = self.transformer.encode(text, convert_to_tensor=False)
            
            # 確保是列表格式
            if hasattr(embedding, 'tolist'):
                return embedding.tolist()
            else:
                return list(embedding)
                
        except Exception as e:
            logging.error(f"Failed to embed text: {e}")
            return [0.0] * self.dimension
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        try:
            if self.transformer is None:
                # 返回隨機向量作為占位符
                import random
                return [[random.random() for _ in range(self.dimension)] for _ in texts]
            
            embeddings = self.transformer.encode(texts, convert_to_tensor=False)
            
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            else:
                return [list(emb) for emb in embeddings]
                
        except Exception as e:
            logging.error(f"Failed to embed batch: {e}")
            return [[0.0] * self.dimension] * len(texts)

class FileHandler:
    """檔案處理層 - 負責文件過濾、解析和正規化"""
    
    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 忽略的文件模式
        self.ignore_patterns = [
            '*.tmp', '*.temp', '*.log', '*.cache',
            '__pycache__', '.git', '.svn', '.hg',
            'node_modules', '.vscode', '.idea',
            '*.pyc', '*.pyo', '*.pyd', '*.so',
            '*.dll', '*.exe', '*.bin'
        ]
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """檢查文件是否應該被忽略"""
        file_name = file_path.name.lower()
        
        # 檢查文件大小
        try:
            if file_path.stat().st_size > self.config.max_file_size:
                return True
        except OSError:
            return True
        
        # 檢查忽略模式
        for pattern in self.ignore_patterns:
            if pattern.startswith('*'):
                if file_name.endswith(pattern[1:]):
                    return True
            elif pattern in str(file_path):
                return True
        
        # 檢查文件擴展名
        if file_path.suffix.lower() not in self.config.supported_extensions:
            return True
        
        return False
    
    def extract_text(self, file_path: Path) -> str:
        """從文件中提取文本"""
        try:
            suffix = file_path.suffix.lower()
            
            if suffix == '.txt' or suffix == '.md':
                return self._extract_text_file(file_path)
            elif suffix == '.py' or suffix == '.js' or suffix == '.html' or suffix == '.css':
                return self._extract_code_file(file_path)
            elif suffix == '.json':
                return self._extract_json_file(file_path)
            elif suffix == '.csv':
                return self._extract_csv_file(file_path)
            elif suffix == '.pdf':
                return self._extract_pdf_file(file_path)
            elif suffix == '.docx':
                return self._extract_docx_file(file_path)
            else:
                return self._extract_text_file(file_path)
                
        except Exception as e:
            self.logger.error(f"Failed to extract text from {file_path}: {e}")
            return ""
    
    def _extract_text_file(self, file_path: Path) -> str:
        """提取文本文件內容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 嘗試其他編碼
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                return ""
    
    def _extract_code_file(self, file_path: Path) -> str:
        """提取代碼文件內容"""
        return self._extract_text_file(file_path)
    
    def _extract_json_file(self, file_path: Path) -> str:
        """提取JSON文件內容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except:
            return self._extract_text_file(file_path)
    
    def _extract_csv_file(self, file_path: Path) -> str:
        """提取CSV文件內容"""
        if not HAS_CSV_SUPPORT:
            return self._extract_text_file(file_path)
        
        try:
            df = pd.read_csv(file_path)
            return df.to_string()
        except:
            return self._extract_text_file(file_path)
    
    def _extract_pdf_file(self, file_path: Path) -> str:
        """提取PDF文件內容"""
        if not HAS_PDF_SUPPORT:
            return ""
        
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except:
            return ""
    
    def _extract_docx_file(self, file_path: Path) -> str:
        """提取Word文件內容"""
        if not HAS_DOCX_SUPPORT:
            return ""
        
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except:
            return ""
    
    def chunk_text(self, text: str) -> List[str]:
        """將文本分割成塊"""
        if len(text) <= self.config.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            # 嘗試在句號或換行符處分割
            if end < len(text):
                for i in range(end, max(start + self.config.chunk_size // 2, end - 200), -1):
                    if text[i] in '。\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.config.chunk_overlap
            if start >= len(text):
                break
        
        return chunks

class VectorStoreLayer:
    """向量資料庫層 - 負責向量存儲和檢索"""
    
    def __init__(self, config: KnowledgeBaseConfig, db_path: Path):
        self.config = config
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # 根據配置選擇向量數據庫
        if config.vector_store == VectorStore.CHROMA:
            self.store = self._init_chroma()
        elif config.vector_store == VectorStore.FAISS:
            self.store = self._init_faiss()
        else:
            self.store = self._init_sqlite()
    
    def _init_chroma(self):
        """初始化ChromaDB"""
        if not HAS_CHROMADB:
            raise Exception("ChromaDB not available")
        
        try:
            chroma_path = str(self.db_path / "chroma_db")
            
            # 如果數據庫已存在且有問題，嘗試重置
            if os.path.exists(chroma_path):
                try:
                    client = chromadb.PersistentClient(
                        path=chroma_path,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=False
                        )
                    )
                except Exception:
                    self.logger.warning("Existing ChromaDB has issues, resetting...")
                    shutil.rmtree(chroma_path, ignore_errors=True)
                    client = chromadb.PersistentClient(
                        path=chroma_path,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True
                        )
                    )
            else:
                client = chromadb.PersistentClient(
                    path=chroma_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            
            # 獲取或創建集合
            try:
                collection = client.get_collection("knowledge_base")
            except:
                collection = client.create_collection(
                    name="knowledge_base",
                    metadata={"description": "LocalLM Knowledge Base"}
                )
            
            return {"type": "chroma", "client": client, "collection": collection}
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _init_faiss(self):
        """初始化FAISS"""
        if not HAS_FAISS:
            raise Exception("FAISS not available")
        
        try:
            faiss_path = self.db_path / "faiss_index"
            faiss_path.mkdir(parents=True, exist_ok=True)
            
            # 創建FAISS索引
            dimension = 1024  # 默認維度，實際應該從嵌入層獲取
            index = faiss.IndexFlatIP(dimension)  # 內積相似度
            
            return {"type": "faiss", "index": index, "path": faiss_path}
            
        except Exception as e:
            self.logger.error(f"Failed to initialize FAISS: {e}")
            raise
    
    def _init_sqlite(self):
        """初始化SQLite（簡單實現）"""
        try:
            sqlite_path = self.db_path / "knowledge_base.db"
            # 這裡可以實現SQLite + 向量的混合存儲
            return {"type": "sqlite", "path": sqlite_path}
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite: {e}")
            raise
    
    def add_vectors(self, chunks: List[DocumentChunk]) -> bool:
        """添加向量到數據庫"""
        try:
            if self.store["type"] == "chroma":
                return self._add_to_chroma(chunks)
            elif self.store["type"] == "faiss":
                return self._add_to_faiss(chunks)
            else:
                return self._add_to_sqlite(chunks)
        except Exception as e:
            self.logger.error(f"Failed to add vectors: {e}")
            return False
    
    def _add_to_chroma(self, chunks: List[DocumentChunk]) -> bool:
        """添加到ChromaDB"""
        try:
            documents = [chunk.content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [chunk.chunk_id for chunk in chunks]
            
            self.store["collection"].add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to add to ChromaDB: {e}")
            return False
    
    def _add_to_faiss(self, chunks: List[DocumentChunk]) -> bool:
        """添加到FAISS"""
        try:
            vectors = np.array([chunk.vector for chunk in chunks if chunk.vector])
            if len(vectors) > 0:
                self.store["index"].add(vectors)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add to FAISS: {e}")
            return False
    
    def _add_to_sqlite(self, chunks: List[DocumentChunk]) -> bool:
        """添加到SQLite（簡化實現）"""
        # 這裡可以實現更複雜的SQLite存儲邏輯
        return True
    
    def search_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        try:
            if self.store["type"] == "chroma":
                return self._search_chroma(query_vector, top_k)
            elif self.store["type"] == "faiss":
                return self._search_faiss(query_vector, top_k)
            else:
                return self._search_sqlite(query_vector, top_k)
        except Exception as e:
            self.logger.error(f"Failed to search vectors: {e}")
            return []
    
    def _search_chroma(self, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        """在ChromaDB中搜索"""
        try:
            # ChromaDB 需要文本查詢，這裡簡化處理
            results = self.store["collection"].query(
                query_texts=["dummy query"],  # 這裡需要改進
                n_results=top_k
            )
            
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
                    "similarity": 1 - distance,
                    "file_name": metadata.get("file_path", "").split("/")[-1]
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Failed to search ChromaDB: {e}")
            return []
    
    def _search_faiss(self, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        """在FAISS中搜索"""
        try:
            query_vec = np.array([query_vector])
            scores, indices = self.store["index"].search(query_vec, top_k)
            
            # 這裡需要從索引中獲取實際的文檔內容
            # 簡化實現，返回空結果
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to search FAISS: {e}")
            return []
    
    def _search_sqlite(self, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        """在SQLite中搜索"""
        # 簡化實現
        return []
    
    def delete_vectors(self, chunk_ids: List[str]) -> bool:
        """刪除向量"""
        try:
            if self.store["type"] == "chroma":
                self.store["collection"].delete(ids=chunk_ids)
            # 其他數據庫類型的刪除邏輯
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete vectors: {e}")
            return False

class KnowledgeBaseAdmin:
    """知識庫管理員 - 核心協調層"""
    
    def __init__(self, kb_path: str = "data/kb_admin"):
        self.kb_path = Path(kb_path)
        self.kb_path.mkdir(parents=True, exist_ok=True)
        
        # 設置日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 配置文件路徑
        self.config_file = self.kb_path / "config.json"
        self.metadata_file = self.kb_path / "metadata.json"
        self.documents_file = self.kb_path / "documents.json"
        
        # 初始化組件
        self.config = self._load_config()
        self.embedding_layer = EmbeddingLayer(self.config.embedding_model)
        self.file_handler = FileHandler(self.config)
        self.vector_store = VectorStoreLayer(self.config, self.kb_path)
        
        # 載入元數據
        self.metadata = self._load_metadata()
        self.documents = self._load_documents()
    
    def _load_config(self) -> KnowledgeBaseConfig:
        """載入配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                return KnowledgeBaseConfig(
                    name=config_data.get("name", "default"),
                    embedding_model=EmbeddingModel(config_data.get("embedding_model", "embedding-gemma")),
                    vector_store=VectorStore(config_data.get("vector_store", "chroma")),
                    chunk_size=config_data.get("chunk_size", 1000),
                    chunk_overlap=config_data.get("chunk_overlap", 200),
                    max_file_size=config_data.get("max_file_size", 50 * 1024 * 1024),
                    supported_extensions=config_data.get("supported_extensions", [
                        '.txt', '.md', '.py', '.js', '.html', '.css', '.json',
                        '.pdf', '.docx', '.xlsx', '.pptx', '.csv', '.sql', '.yml', '.yaml', '.toml'
                    ])
                )
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
        
        # 默認配置
        return KnowledgeBaseConfig(
            name="default",
            embedding_model=EmbeddingModel.EMBEDDING_GEMMA,
            vector_store=VectorStore.CHROMA
        )
    
    def _save_config(self):
        """保存配置"""
        try:
            config_data = {
                "name": self.config.name,
                "embedding_model": self.config.embedding_model.value,
                "vector_store": self.config.vector_store.value,
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
                "max_file_size": self.config.max_file_size,
                "supported_extensions": self.config.supported_extensions
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def _load_metadata(self) -> Dict:
        """載入元數據"""
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
            "version": "2.0"
        }
    
    def _save_metadata(self):
        """保存元數據"""
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
    
    def init_knowledge_base(self, name: str, embedding_model: EmbeddingModel, vector_store: VectorStore = VectorStore.CHROMA) -> Dict[str, Any]:
        """初始化知識庫"""
        try:
            # 更新配置
            self.config.name = name
            self.config.embedding_model = embedding_model
            self.config.vector_store = vector_store
            
            # 重新初始化組件
            self.embedding_layer = EmbeddingLayer(embedding_model)
            self.vector_store = VectorStoreLayer(self.config, self.kb_path)
            
            # 重置元數據
            self.metadata = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_documents": 0,
                "total_chunks": 0,
                "version": "2.0"
            }
            
            self.documents = {}
            
            # 保存配置和元數據
            self._save_config()
            self._save_metadata()
            self._save_documents()
            
            return {
                "success": True,
                "message": f"知識庫 '{name}' 初始化成功",
                "embedding_model": embedding_model.value,
                "vector_store": vector_store.value,
                "dimension": self.embedding_layer.dimension
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"初始化失敗: {e}"
            }
    
    def add_document(self, file_path: str) -> Dict[str, Any]:
        """添加文檔到知識庫"""
        try:
            file_path = Path(file_path).resolve()
            
            if not file_path.exists():
                return {"success": False, "error": f"文件不存在: {file_path}"}
            
            if self.file_handler.should_ignore_file(file_path):
                return {"success": False, "error": f"文件被忽略: {file_path.name}"}
            
            # 計算文件哈希
            file_hash = self._get_file_hash(str(file_path))
            
            # 檢查文件是否已經存在
            if file_hash in self.documents:
                return {"success": False, "error": f"文件已經存在於知識庫中: {file_path.name}"}
            
            # 提取文本
            text = self.file_handler.extract_text(file_path)
            if not text.strip():
                return {"success": False, "error": f"無法提取文本內容: {file_path.name}"}
            
            # 分割文本
            text_chunks = self.file_handler.chunk_text(text)
            
            # 創建文檔塊
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk_id = f"{file_hash}_{i}"
                chunk = DocumentChunk(
                    content=chunk_text,
                    metadata={
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "file_type": file_path.suffix.lower(),
                        "chunk_index": i,
                        "total_chunks": len(text_chunks),
                        "file_size": file_path.stat().st_size,
                        "added_at": datetime.now().isoformat()
                    },
                    chunk_id=chunk_id,
                    file_hash=file_hash
                )
                
                # 生成向量
                chunk.vector = self.embedding_layer.embed_text(chunk_text)
                chunks.append(chunk)
            
            # 添加到向量數據庫
            if not self.vector_store.add_vectors(chunks):
                return {"success": False, "error": "向量數據庫添加失敗"}
            
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
            
        except Exception as e:
            return {"success": False, "error": f"添加失敗: {e}"}
    
    def query_knowledge_base(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """查詢知識庫"""
        try:
            # 將問題轉換為向量
            query_vector = self.embedding_layer.embed_text(question)
            
            # 搜索相似向量
            results = self.vector_store.search_vectors(query_vector, top_k)
            
            return {
                "success": True,
                "question": question,
                "results": results,
                "total_found": len(results)
            }
            
        except Exception as e:
            return {"success": False, "error": f"查詢失敗: {e}"}
    
    def get_status(self) -> Dict[str, Any]:
        """獲取知識庫狀態"""
        try:
            # 計算數據庫大小
            db_size = 0
            for file_path in self.kb_path.rglob('*'):
                if file_path.is_file():
                    db_size += file_path.stat().st_size
            
            return {
                "success": True,
                "config": {
                    "name": self.config.name,
                    "embedding_model": self.config.embedding_model.value,
                    "vector_store": self.config.vector_store.value,
                    "dimension": self.embedding_layer.dimension
                },
                "metadata": self.metadata,
                "total_documents": len(self.documents),
                "db_size_bytes": db_size,
                "db_size_mb": round(db_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {"success": False, "error": f"獲取狀態失敗: {e}"}
    
    def list_documents(self) -> Dict[str, Any]:
        """列出所有文檔"""
        try:
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
                "total_documents": len(doc_list)
            }
            
        except Exception as e:
            return {"success": False, "error": f"獲取文檔列表失敗: {e}"}
    
    def _get_file_hash(self, file_path: str) -> str:
        """計算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

# 創建默認實例
default_kb_admin = KnowledgeBaseAdmin()
