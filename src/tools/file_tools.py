"""
檔案操作核心工具模組
提供讀取、寫入、編輯檔案的核心功能
"""

import os
from pathlib import Path
from typing import Optional


class FileTools:
    """檔案操作工具類"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化檔案工具
        
        Args:
            base_path: 基礎路徑，如果未提供則使用當前工作目錄
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        
    def get_current_path(self) -> str:
        """取得目前的工作路徑"""
        return str(self.base_path.absolute())
    
    def _resolve_path(self, file_path: str) -> Path:
        """
        解析檔案路徑，處理相對路徑和絕對路徑
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            Path: 解析後的完整路徑
        """
        path = Path(file_path)
        if path.is_absolute():
            return path
        else:
            return self.base_path / path
    
    def read_file(self, file_path: str) -> str:
        """
        讀取指定路徑的檔案內容
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            str: 檔案內容
            
        Raises:
            FileNotFoundError: 檔案不存在
            PermissionError: 沒有讀取權限
            UnicodeDecodeError: 檔案編碼問題
        """
        resolved_path = self._resolve_path(file_path)
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"檔案不存在: {resolved_path}")
        
        if not resolved_path.is_file():
            raise ValueError(f"路徑不是檔案: {resolved_path}")
        
        try:
            # 嘗試使用 UTF-8 編碼讀取
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            try:
                # 如果 UTF-8 失敗，嘗試使用系統預設編碼
                with open(resolved_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                return content
            except UnicodeDecodeError:
                # 最後嘗試使用 latin-1 編碼（幾乎不會失敗）
                with open(resolved_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                return content
    
    def write_file(self, file_path: str, content: str) -> None:
        """
        將內容寫入指定檔案（覆蓋模式）
        
        Args:
            file_path: 檔案路徑
            content: 要寫入的內容
            
        Raises:
            PermissionError: 沒有寫入權限
            OSError: 其他系統錯誤
        """
        resolved_path = self._resolve_path(file_path)
        
        # 確保父目錄存在
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(resolved_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def edit_file(self, file_path: str, new_content: str) -> None:
        """
        編輯檔案內容（覆蓋模式）
        這個函數在語義上與 write_file 相同，但用於明確表示是在編輯現有檔案
        
        Args:
            file_path: 檔案路徑
            new_content: 新的檔案內容
            
        Raises:
            PermissionError: 沒有寫入權限
            OSError: 其他系統錯誤
        """
        self.write_file(file_path, new_content)
    
    def file_exists(self, file_path: str) -> bool:
        """
        檢查檔案是否存在
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            bool: 檔案是否存在
        """
        resolved_path = self._resolve_path(file_path)
        return resolved_path.exists() and resolved_path.is_file()
    
    def list_files(self, directory: str = ".", pattern: str = "*") -> list:
        """
        列出目錄中的檔案
        
        Args:
            directory: 目錄路徑，預設為當前目錄
            pattern: 檔案模式，預設為所有檔案
            
        Returns:
            list: 檔案路徑列表
        """
        resolved_path = self._resolve_path(directory)
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"目錄不存在: {resolved_path}")
        
        if not resolved_path.is_dir():
            raise ValueError(f"路徑不是目錄: {resolved_path}")
        
        files = []
        for file_path in resolved_path.glob(pattern):
            if file_path.is_file():
                files.append(str(file_path.relative_to(self.base_path)))
        
        return sorted(files)
    
    def get_file_info(self, file_path: str) -> dict:
        """
        取得檔案資訊
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            dict: 檔案資訊字典
        """
        resolved_path = self._resolve_path(file_path)
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"檔案不存在: {resolved_path}")
        
        stat = resolved_path.stat()
        
        return {
            'path': str(resolved_path),
            'name': resolved_path.name,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'is_file': resolved_path.is_file(),
            'is_dir': resolved_path.is_dir(),
            'extension': resolved_path.suffix
        }


# 創建預設實例
default_file_tools = FileTools()

# 提供便捷的函數介面
def read_file(file_path: str) -> str:
    """讀取檔案內容"""
    return default_file_tools.read_file(file_path)

def write_file(file_path: str, content: str) -> None:
    """寫入檔案內容"""
    default_file_tools.write_file(file_path, content)

def edit_file(file_path: str, new_content: str) -> None:
    """編輯檔案內容"""
    default_file_tools.edit_file(file_path, new_content)

def file_exists(file_path: str) -> bool:
    """檢查檔案是否存在"""
    return default_file_tools.file_exists(file_path)

def list_files(directory: str = ".", pattern: str = "*") -> list:
    """列出目錄中的檔案"""
    return default_file_tools.list_files(directory, pattern)

def get_current_path() -> str:
    """取得目前工作路徑"""
    return default_file_tools.get_current_path()