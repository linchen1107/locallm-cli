"""
批量處理工具
支援一次處理多個文件的各種操作
"""

import os
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Callable, Optional, Union
from pathlib import Path
import time
from datetime import datetime

class BatchProcessor:
    """批量處理器"""
    
    def __init__(self):
        self.max_workers = 4  # 最大並發數
        self.supported_operations = [
            'read', 'analyze', 'convert', 'compress', 'extract', 'search', 'replace'
        ]
    
    def process_files(self, file_paths: List[str], operation: str, 
                     operation_func: Callable, **kwargs) -> Dict[str, Any]:
        """批量處理文件"""
        if not file_paths:
            return {"error": "沒有提供文件路徑"}
        
        if operation not in self.supported_operations:
            return {"error": f"不支援的操作: {operation}"}
        
        print(f"  🔄 開始批量{operation}處理...")
        print(f"  📁 文件數量: {len(file_paths)}")
        print(f"  ⚙️  並發數: {self.max_workers}")
        
        start_time = time.time()
        results = []
        
        # 使用線程池進行並發處理
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任務
            future_to_file = {
                executor.submit(self._process_single_file, file_path, operation_func, **kwargs): file_path
                for file_path in file_paths
            }
            
            # 收集結果
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append({
                        "file_path": file_path,
                        "success": True,
                        "result": result
                    })
                    print(f"  ✅ {file_path}")
                except Exception as e:
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": str(e)
                    })
                    print(f"  ❌ {file_path}: {str(e)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 統計結果
        successful = len([r for r in results if r["success"]])
        failed = len([r for r in results if not r["success"]])
        
        return {
            "operation": operation,
            "total_files": len(file_paths),
            "successful": successful,
            "failed": failed,
            "duration": duration,
            "results": results,
            "summary": f"成功: {successful}/{len(file_paths)}, 耗時: {duration:.2f}秒"
        }
    
    def _process_single_file(self, file_path: str, operation_func: Callable, **kwargs) -> Any:
        """處理單個文件"""
        try:
            return operation_func(file_path, **kwargs)
        except Exception as e:
            raise Exception(f"處理文件失敗: {str(e)}")
    
    def batch_read_files(self, file_paths: List[str], 
                        extract_images: bool = False) -> Dict[str, Any]:
        """批量讀取文件"""
        from .file_tools import default_file_tools
        
        def read_operation(file_path: str, **kwargs):
            return default_file_tools.read_file(file_path, **kwargs)
        
        return self.process_files(file_paths, 'read', read_operation)
    
    def batch_analyze_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """批量分析文件"""
        def analyze_operation(file_path: str, **kwargs):
            # 根據文件類型進行分析
            ext = Path(file_path).suffix.lower()
            
            if ext == '.py':
                return self._analyze_python_file(file_path)
            elif ext in ['.txt', '.md']:
                return self._analyze_text_file(file_path)
            elif ext == '.json':
                return self._analyze_json_file(file_path)
            elif ext == '.csv':
                return self._analyze_csv_file(file_path)
            else:
                return self._analyze_generic_file(file_path)
        
        return self.process_files(file_paths, 'analyze', analyze_operation)
    
    def batch_search_files(self, file_paths: List[str], 
                          search_term: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """批量搜索文件內容"""
        def search_operation(file_path: str, **kwargs):
            return self._search_in_file(file_path, search_term, case_sensitive)
        
        return self.process_files(file_paths, 'search', search_operation, 
                                search_term=search_term, case_sensitive=case_sensitive)
    
    def batch_replace_files(self, file_paths: List[str], 
                           old_text: str, new_text: str, 
                           backup: bool = True) -> Dict[str, Any]:
        """批量替換文件內容"""
        def replace_operation(file_path: str, **kwargs):
            return self._replace_in_file(file_path, old_text, new_text, backup)
        
        return self.process_files(file_paths, 'replace', replace_operation,
                                old_text=old_text, new_text=new_text, backup=backup)
    
    def batch_convert_files(self, file_paths: List[str], 
                           target_format: str) -> Dict[str, Any]:
        """批量轉換文件格式"""
        def convert_operation(file_path: str, **kwargs):
            return self._convert_file(file_path, target_format)
        
        return self.process_files(file_paths, 'convert', convert_operation,
                                target_format=target_format)
    
    def _analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """分析 Python 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            total_lines = len(lines)
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            code_lines = total_lines - comment_lines
            
            # 簡單的函數和類統計
            functions = content.count('def ')
            classes = content.count('class ')
            imports = content.count('import ') + content.count('from ')
            
            return {
                "type": "python",
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "complexity": "low" if functions < 10 else "medium" if functions < 50 else "high"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_text_file(self, file_path: str) -> Dict[str, Any]:
        """分析文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chars = len(content)
            words = len(content.split())
            lines = len(content.split('\n'))
            paragraphs = len([p for p in content.split('\n\n') if p.strip()])
            
            return {
                "type": "text",
                "characters": chars,
                "words": words,
                "lines": lines,
                "paragraphs": paragraphs,
                "avg_words_per_line": words / lines if lines > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_json_file(self, file_path: str) -> Dict[str, Any]:
        """分析 JSON 文件"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def count_keys(obj, prefix=""):
                if isinstance(obj, dict):
                    return {f"{prefix}{k}": len(v) if isinstance(v, (list, dict)) else 1 
                           for k, v in obj.items()}
                return {}
            
            key_counts = count_keys(data)
            
            return {
                "type": "json",
                "structure": type(data).__name__,
                "key_count": len(key_counts),
                "keys": list(key_counts.keys()),
                "size_bytes": os.path.getsize(file_path)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_csv_file(self, file_path: str) -> Dict[str, Any]:
        """分析 CSV 文件"""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            return {
                "type": "csv",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "data_types": df.dtypes.to_dict(),
                "missing_values": df.isnull().sum().to_dict()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_generic_file(self, file_path: str) -> Dict[str, Any]:
        """分析通用文件"""
        try:
            stat = os.stat(file_path)
            size = stat.st_size
            
            return {
                "type": "generic",
                "size_bytes": size,
                "size_mb": size / (1024 * 1024),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": Path(file_path).suffix
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _search_in_file(self, file_path: str, search_term: str, 
                       case_sensitive: bool = False) -> Dict[str, Any]:
        """在文件中搜索"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not case_sensitive:
                content_lower = content.lower()
                search_lower = search_term.lower()
                matches = content_lower.count(search_lower)
            else:
                matches = content.count(search_term)
            
            # 找到匹配的行
            lines = content.split('\n')
            matching_lines = []
            for i, line in enumerate(lines, 1):
                if (case_sensitive and search_term in line) or \
                   (not case_sensitive and search_term.lower() in line.lower()):
                    matching_lines.append({"line": i, "content": line.strip()})
            
            return {
                "matches": matches,
                "matching_lines": matching_lines[:10],  # 只返回前10行
                "total_matching_lines": len(matching_lines)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _replace_in_file(self, file_path: str, old_text: str, new_text: str, 
                        backup: bool = True) -> Dict[str, Any]:
        """替換文件內容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_text not in content:
                return {"replaced": 0, "message": "未找到要替換的文本"}
            
            # 創建備份
            if backup:
                backup_path = f"{file_path}.backup.{int(time.time())}"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 執行替換
            new_content = content.replace(old_text, new_text)
            replacements = content.count(old_text)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "replaced": replacements,
                "backup_created": backup,
                "backup_path": backup_path if backup else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _convert_file(self, file_path: str, target_format: str) -> Dict[str, Any]:
        """轉換文件格式"""
        # 這裡可以實現各種格式轉換
        # 目前只是一個示例框架
        return {
            "message": f"轉換到 {target_format} 格式的功能待實現",
            "source": file_path,
            "target_format": target_format
        }
    
    def get_file_list(self, directory: str, pattern: str = "*", 
                     recursive: bool = True) -> List[str]:
        """獲取文件列表"""
        try:
            path = Path(directory)
            if recursive:
                files = list(path.rglob(pattern))
            else:
                files = list(path.glob(pattern))
            
            return [str(f) for f in files if f.is_file()]
        except Exception as e:
            return []
    
    def create_batch_report(self, results: Dict[str, Any], 
                           output_file: str = None) -> str:
        """創建批量處理報告"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"batch_report_{timestamp}.txt"
        
        report = []
        report.append("=" * 60)
        report.append("批量處理報告")
        report.append("=" * 60)
        report.append(f"操作: {results['operation']}")
        report.append(f"總文件數: {results['total_files']}")
        report.append(f"成功: {results['successful']}")
        report.append(f"失敗: {results['failed']}")
        report.append(f"耗時: {results['duration']:.2f}秒")
        report.append("")
        
        # 詳細結果
        report.append("詳細結果:")
        report.append("-" * 40)
        for result in results['results']:
            status = "✅" if result['success'] else "❌"
            report.append(f"{status} {result['file_path']}")
            if not result['success']:
                report.append(f"   錯誤: {result['error']}")
            else:
                # 顯示部分結果信息
                if isinstance(result['result'], dict):
                    for key, value in list(result['result'].items())[:3]:
                        report.append(f"   {key}: {value}")
            report.append("")
        
        report_content = "\n".join(report)
        
        # 保存報告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_file

# 創建默認實例
default_batch_processor = BatchProcessor()
