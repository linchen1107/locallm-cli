"""
檔案分類工具
支援按作者、檔案類型等多種方式進行智能分類
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime
import chardet
import mimetypes


class FileClassifier:
    """檔案分類器"""
    
    # 檔案類型映射
    FILE_TYPE_CATEGORIES = {
        # 程式碼檔案
        'programming': {
            'extensions': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt'],
            'folder_name': '程式碼檔案'
        },
        # 文件檔案
        'documents': {
            'extensions': ['.docx', '.doc', '.pdf', '.txt', '.rtf'],
            'folder_name': '文件檔案'
        },
        # 簡報檔案
        'presentations': {
            'extensions': ['.pptx', '.ppt', '.key'],
            'folder_name': '簡報檔案'
        },
        # 試算表檔案
        'spreadsheets': {
            'extensions': ['.xlsx', '.xls', '.csv'],
            'folder_name': '試算表檔案'
        },
        # 標記語言檔案
        'markup': {
            'extensions': ['.md', '.html', '.htm', '.xml'],
            'folder_name': '標記語言檔案'
        },
        # 資料檔案
        'data': {
            'extensions': ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'],
            'folder_name': '資料檔案'
        },
        # 圖片檔案
        'images': {
            'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'folder_name': '圖片檔案'
        },
        # 影片檔案
        'videos': {
            'extensions': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            'folder_name': '影片檔案'
        },
        # 音訊檔案
        'audio': {
            'extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
            'folder_name': '音訊檔案'
        },
        # 壓縮檔案
        'archives': {
            'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'folder_name': '壓縮檔案'
        }
    }
    
    # 內容分類關鍵詞
    CONTENT_CATEGORIES = {
        'API文檔': {
            'keywords': ['api', 'endpoint', 'request', 'response', 'json', 'http', 'rest', 'swagger', 'postman'],
            'patterns': [r'GET\s+/', r'POST\s+/', r'PUT\s+/', r'DELETE\s+/', r'@app\.route', r'@api\.route']
        },
        '配置檔案': {
            'keywords': ['config', 'setting', 'environment', 'env', 'production', 'development', 'dependencies', 'scripts'],
            'patterns': [r'^\s*[A-Z_]+\s*=', r'^\s*\[.*\]', r'host\s*:', r'port\s*:', r'database\s*:', r'"name"\s*:', r'"version"\s*:', r'"scripts"\s*:']
        },
        '測試檔案': {
            'keywords': ['test', 'unittest', 'pytest', 'jest', 'mocha', 'spec', 'mock'],
            'patterns': [r'def test_', r'it\(', r'describe\(', r'@Test', r'assert', r'expect\(']
        },
        '資料庫相關': {
            'keywords': ['database', 'sql', 'query', 'table', 'schema', 'migration', 'model'],
            'patterns': [r'CREATE TABLE', r'SELECT.*FROM', r'INSERT INTO', r'UPDATE.*SET', r'class.*Model']
        },
        '前端UI': {
            'keywords': ['component', 'react', 'vue', 'angular', 'css', 'html', 'style', 'template'],
            'patterns': [r'<template>', r'<style>', r'className=', r'v-if=', r'@Component']
        },
        '後端邏輯': {
            'keywords': ['server', 'controller', 'service', 'middleware', 'router', 'handler', 'fastapi', 'flask', 'django'],
            'patterns': [r'class.*Controller', r'@app\.', r'app\.use', r'express\(', r'Flask\(', r'FastAPI\(', r'from fastapi']
        },
        '文檔說明': {
            'keywords': ['readme', 'doc', 'guide', 'tutorial', 'instruction', 'manual', 'help'],
            'patterns': [r'^#+\s', r'##\s', r'###\s', r'\*\*.*\*\*', r'`.*`']
        },
        '腳本工具': {
            'keywords': ['script', 'tool', 'utility', 'automation', 'build', 'deploy'],
            'patterns': [r'#!/.*', r'if __name__ == "__main__"', r'npm run', r'python.*\.py']
        },
        '數據分析': {
            'keywords': ['pandas', 'numpy', 'matplotlib', 'data', 'analysis', 'visualization', 'chart'],
            'patterns': [r'import pandas', r'import numpy', r'plt\.', r'df\.', r'\.csv', r'\.plot\(']
        },
        '機器學習': {
            'keywords': ['tensorflow', 'pytorch', 'sklearn', 'model', 'train', 'predict', 'neural'],
            'patterns': [r'import torch', r'from sklearn', r'model\.fit', r'model\.predict', r'Sequential\(']
        }
    }
    
    def __init__(self, base_directory: Optional[str] = None):
        """
        初始化檔案分類器
        
        Args:
            base_directory: 基礎目錄，如果不指定則使用當前目錄
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        
    def extract_author_from_filename(self, filename: str) -> Optional[str]:
        """
        從檔案名稱中提取作者資訊
        
        支援的格式：
        - 作者_標題.ext
        - 作者-標題.ext
        - [作者]標題.ext
        - (作者)標題.ext
        - 作者 標題.ext
        """
        name_without_ext = Path(filename).stem
        
        # 常見的作者分隔模式
        patterns = [
            r'^([^_]+)_',  # 作者_標題
            r'^([^-]+)-',  # 作者-標題
            r'^\[([^\]]+)\]',  # [作者]標題
            r'^\(([^\)]+)\)',  # (作者)標題
            r'^([^ ]+) ',  # 作者 標題（空格分隔）
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name_without_ext)
            if match:
                author = match.group(1).strip()
                # 過濾掉太短或看起來不像作者名稱的結果
                if len(author) >= 2 and not author.isdigit():
                    return author
        
        return None
    
    def get_file_category(self, filename: str) -> Tuple[str, str]:
        """
        根據檔案副檔名確定檔案類別
        
        Returns:
            (category_key, folder_name) 元組
        """
        ext = Path(filename).suffix.lower()
        
        for category, info in self.FILE_TYPE_CATEGORIES.items():
            if ext in info['extensions']:
                return category, info['folder_name']
        
        return 'others', '其他檔案'
    
    def analyze_file_content(self, file_path: Path) -> Tuple[str, float]:
        """
        分析檔案內容並確定最可能的分類
        
        Returns:
            (category_name, confidence_score) 元組
        """
        try:
            # 檢查檔案大小，避免處理過大的檔案
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                return "大型檔案", 0.5
            
            # 嘗試檢測檔案編碼
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)  # 讀取前8KB進行編碼檢測
                encoding_info = chardet.detect(raw_data)
                encoding = encoding_info.get('encoding', 'utf-8')
            
            # 讀取檔案內容
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
            except:
                # 如果仍然無法讀取，嘗試UTF-8
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            # 如果檔案為空或太短，返回未知
            if len(content.strip()) < 10:
                return "空檔案", 0.3
            
            # 分析內容
            content_lower = content.lower()
            scores = {}
            
            for category, rules in self.CONTENT_CATEGORIES.items():
                score = 0
                total_possible = len(rules['keywords']) + len(rules['patterns'])
                
                # 關鍵詞匹配
                for keyword in rules['keywords']:
                    if keyword in content_lower:
                        score += 1
                
                # 正則表達式匹配
                for pattern in rules['patterns']:
                    if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                        score += 1
                
                # 計算信心分數 (0-1)
                confidence = score / total_possible if total_possible > 0 else 0
                if confidence > 0:
                    scores[category] = confidence
            
            # 返回最高分的分類
            if scores:
                best_category = max(scores.keys(), key=lambda k: scores[k])
                best_score = scores[best_category]
                return best_category, best_score
            else:
                return "其他內容", 0.1
                
        except Exception as e:
            return f"分析錯誤: {str(e)}", 0.0
    
    def classify_files_by_author(self, directory: Optional[str] = None, target_dir: Optional[str] = None) -> Dict[str, List[str]]:
        """
        按作者分類檔案
        
        Args:
            directory: 要分類的目錄，預設為base_directory
            target_dir: 目標分類目錄，預設為directory/按作者分類
            
        Returns:
            分類結果字典 {作者: [檔案列表]}
        """
        if directory is None:
            directory_path = self.base_directory
        else:
            directory_path = Path(directory)
            
        if target_dir is None:
            target_dir_path = directory_path / "按作者分類"
        else:
            target_dir_path = Path(target_dir)
            
        # 建立目標目錄
        target_dir_path.mkdir(exist_ok=True)
        
        # 分類結果
        classification = {}
        unknown_author_files = []
        
        # 掃描所有檔案
        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.parent == directory_path:
                filename = file_path.name
                author = self.extract_author_from_filename(filename)
                
                if author:
                    if author not in classification:
                        classification[author] = []
                    classification[author].append(filename)
                else:
                    unknown_author_files.append(filename)
        
        # 如果有無法識別作者的檔案，歸類到"未知作者"
        if unknown_author_files:
            classification["未知作者"] = unknown_author_files
            
        # 建立作者資料夾並移動檔案
        for author, files in classification.items():
            author_dir = target_dir_path / self._sanitize_folder_name(author)
            author_dir.mkdir(exist_ok=True)
            
            for filename in files:
                src_path = directory_path / filename
                dst_path = author_dir / filename
                try:
                    shutil.move(str(src_path), str(dst_path))
                    print(f"移動檔案: {filename} -> {author_dir}")
                except Exception as e:
                    print(f"移動檔案失敗 {filename}: {e}")
        
        return classification
    
    def classify_files_by_type(self, directory: Optional[str] = None, target_dir: Optional[str] = None) -> Dict[str, List[str]]:
        """
        按檔案類型分類檔案
        
        Args:
            directory: 要分類的目錄，預設為base_directory
            target_dir: 目標分類目錄，預設為directory/按類型分類
            
        Returns:
            分類結果字典 {類型: [檔案列表]}
        """
        if directory is None:
            directory_path = self.base_directory
        else:
            directory_path = Path(directory)
            
        if target_dir is None:
            target_dir_path = directory_path / "按類型分類"
        else:
            target_dir_path = Path(target_dir)
            
        # 建立目標目錄
        target_dir_path.mkdir(exist_ok=True)
        
        # 分類結果
        classification = {}
        
        # 掃描所有檔案
        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.parent == directory_path:
                filename = file_path.name
                category_key, folder_name = self.get_file_category(filename)
                
                if folder_name not in classification:
                    classification[folder_name] = []
                classification[folder_name].append(filename)
        
        # 建立類型資料夾並移動檔案
        for folder_name, files in classification.items():
            type_dir = target_dir_path / folder_name
            type_dir.mkdir(exist_ok=True)
            
            for filename in files:
                src_path = directory_path / filename
                dst_path = type_dir / filename
                try:
                    shutil.move(str(src_path), str(dst_path))
                    print(f"移動檔案: {filename} -> {type_dir}")
                except Exception as e:
                    print(f"移動檔案失敗 {filename}: {e}")
        
        return classification
    
    def classify_files_mixed(self, directory: Optional[str] = None, target_dir: Optional[str] = None) -> Dict[str, Dict[str, List[str]]]:
        """
        混合分類：先按作者，再按類型
        
        Returns:
            分類結果字典 {作者: {文件類型: [檔案列表]}}
        """
        if directory is None:
            directory_path = self.base_directory
        else:
            directory_path = Path(directory)
            
        if target_dir is None:
            target_dir_path = directory_path / "混合分類"
        else:
            target_dir_path = Path(target_dir)
            
        # 建立目標目錄
        target_dir_path.mkdir(exist_ok=True)
        
        # 分類結果
        classification = {}
        
        # 掃描所有檔案
        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.parent == directory_path:
                filename = file_path.name
                author = self.extract_author_from_filename(filename) or "未知作者"
                category_key, folder_name = self.get_file_category(filename)
                
                if author not in classification:
                    classification[author] = {}
                if folder_name not in classification[author]:
                    classification[author][folder_name] = []
                    
                classification[author][folder_name].append(filename)
        
        # 建立資料夾結構並移動檔案
        for author, type_dict in classification.items():
            author_dir = target_dir_path / self._sanitize_folder_name(author)
            author_dir.mkdir(exist_ok=True)
            
            for folder_name, files in type_dict.items():
                type_dir = author_dir / folder_name
                type_dir.mkdir(exist_ok=True)
                
                for filename in files:
                    src_path = directory_path / filename
                    dst_path = type_dir / filename
                    try:
                        shutil.move(str(src_path), str(dst_path))
                        print(f"移動檔案: {filename} -> {type_dir}")
                    except Exception as e:
                        print(f"移動檔案失敗 {filename}: {e}")
        
        return classification
    
    def classify_files_by_content(self, directory: Optional[str] = None, target_dir: Optional[str] = None, min_confidence: float = 0.3) -> Dict[str, List[str]]:
        """
        按檔案內容分類檔案
        
        Args:
            directory: 要分類的目錄，預設為base_directory
            target_dir: 目標分類目錄，預設為directory/按內容分類
            min_confidence: 最小信心分數，低於此分數的檔案會被歸類為"未分類"
            
        Returns:
            分類結果字典 {內容類型: [檔案列表]}
        """
        if directory is None:
            directory_path = self.base_directory
        else:
            directory_path = Path(directory)
            
        if target_dir is None:
            target_dir_path = directory_path / "按內容分類"
        else:
            target_dir_path = Path(target_dir)
            
        # 建立目標目錄
        target_dir_path.mkdir(exist_ok=True)
        
        # 分類結果
        classification = {}
        
        print("  🔍 正在分析檔案內容...")
        
        # 掃描所有檔案
        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.parent == directory_path:
                filename = file_path.name
                
                # 跳過隱藏檔案和系統檔案
                if filename.startswith('.') or filename.startswith('~'):
                    continue
                
                # 分析內容
                category, confidence = self.analyze_file_content(file_path)
                
                # 如果信心分數太低，歸類為未分類
                if confidence < min_confidence:
                    category = "未分類"
                
                print(f"    📄 {filename} -> {category} (信心度: {confidence:.2f})")
                
                if category not in classification:
                    classification[category] = []
                classification[category].append(filename)
        
        # 建立內容分類資料夾並移動檔案
        for category, files in classification.items():
            category_dir = target_dir_path / self._sanitize_folder_name(category)
            category_dir.mkdir(exist_ok=True)
            
            for filename in files:
                src_path = directory_path / filename
                dst_path = category_dir / filename
                try:
                    shutil.move(str(src_path), str(dst_path))
                    print(f"移動檔案: {filename} -> {category_dir}")
                except Exception as e:
                    print(f"移動檔案失敗 {filename}: {e}")
        
        return classification
    
    def preview_classification(self, directory: Optional[str] = None, mode: str = "author", min_confidence: float = 0.3) -> Dict:
        """
        預覽分類結果，不實際移動檔案
        
        Args:
            directory: 要分類的目錄
            mode: 分類模式 ("author", "type", "mixed", "content")
            min_confidence: 內容分類的最小信心分數
        """
        if directory is None:
            directory_path = self.base_directory
        else:
            directory_path = Path(directory)
        
        classification = {}
        
        # 掃描所有檔案
        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.parent == directory_path:
                filename = file_path.name
                
                # 跳過隱藏檔案
                if filename.startswith('.') or filename.startswith('~'):
                    continue
                
                if mode == "author":
                    author = self.extract_author_from_filename(filename) or "未知作者"
                    if author not in classification:
                        classification[author] = []
                    classification[author].append(filename)
                    
                elif mode == "type":
                    category_key, folder_name = self.get_file_category(filename)
                    if folder_name not in classification:
                        classification[folder_name] = []
                    classification[folder_name].append(filename)
                    
                elif mode == "content":
                    category, confidence = self.analyze_file_content(file_path)
                    if confidence < min_confidence:
                        category = "未分類"
                    
                    if category not in classification:
                        classification[category] = []
                    classification[category].append(f"{filename} (信心度: {confidence:.2f})")
                    
                elif mode == "mixed":
                    author = self.extract_author_from_filename(filename) or "未知作者"
                    category_key, folder_name = self.get_file_category(filename)
                    
                    if author not in classification:
                        classification[author] = {}
                    if folder_name not in classification[author]:
                        classification[author][folder_name] = []
                    classification[author][folder_name].append(filename)
        
        return classification
    
    def _sanitize_folder_name(self, name: str) -> str:
        """清理資料夾名稱，移除不允許的字元"""
        # Windows 不允許的字元
        invalid_chars = r'<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    def get_classification_summary(self, classification: Dict) -> str:
        """
        生成分類摘要報告
        """
        summary = []
        summary.append(f"分類摘要報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("=" * 50)
        
        if isinstance(next(iter(classification.values())), list):
            # 簡單分類 (作者或類型)
            total_files = sum(len(files) for files in classification.values())
            summary.append(f"總共檔案數: {total_files}")
            summary.append(f"分類數量: {len(classification)}")
            summary.append("")
            
            for category, files in classification.items():
                summary.append(f"📁 {category} ({len(files)} 個檔案)")
                for file in sorted(files):
                    summary.append(f"   - {file}")
                summary.append("")
        else:
            # 混合分類
            total_files = sum(sum(len(files) for files in type_dict.values()) 
                            for type_dict in classification.values())
            summary.append(f"總共檔案數: {total_files}")
            summary.append(f"作者數量: {len(classification)}")
            summary.append("")
            
            for author, type_dict in classification.items():
                author_files = sum(len(files) for files in type_dict.values())
                summary.append(f"👤 {author} ({author_files} 個檔案)")
                for folder_name, files in type_dict.items():
                    summary.append(f"   📁 {folder_name} ({len(files)} 個檔案)")
                    for file in sorted(files):
                        summary.append(f"      - {file}")
                summary.append("")
        
        return "\n".join(summary)