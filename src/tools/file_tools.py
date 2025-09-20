"""
檔案操作核心工具模組
提供讀取、寫入、編輯檔案的核心功能
"""

import os
from pathlib import Path
from typing import Optional

# PDF 相關導入（可選依賴）
try:
    import fitz  # PyMuPDF
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False


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

    def read_pdf(self, file_path: str, use_ocr: bool = False) -> str:
        """
        讀取 PDF 檔案內容並提取文字
        
        Args:
            file_path: PDF 檔案路徑
            use_ocr: 是否強制使用 OCR（適用於掃描型 PDF）
            
        Returns:
            str: 提取的文字內容
            
        Raises:
            FileNotFoundError: 檔案不存在
            ValueError: 不是 PDF 檔案或 PDF 讀取失敗
            ImportError: PyMuPDF 未安裝
        """
        if not HAS_PDF_SUPPORT:
            raise ImportError("PDF 支援需要安裝 PyMuPDF。請執行: pip install pymupdf")
        
        resolved_path = self._resolve_path(file_path)
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"檔案不存在: {resolved_path}")
        
        if not resolved_path.is_file():
            raise ValueError(f"路徑不是檔案: {resolved_path}")
        
        if resolved_path.suffix.lower() != '.pdf':
            raise ValueError(f"檔案不是 PDF 格式: {resolved_path}")
        
        try:
            # 使用 PyMuPDF 讀取 PDF
            pdf_document = fitz.open(str(resolved_path))
            text_content = ""
            low_text_pages = []  # 記錄文字內容較少的頁面
            
            # 逐頁提取文字
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_header = f"--- 第 {page_num + 1} 頁 ---\n"
                
                # 使用 get_text() 方法提取文字
                page_text = getattr(page, 'get_text', lambda: "")()
                
                # 檢查文字內容是否充足
                if len(page_text.strip()) < 50:  # 文字內容較少，可能需要 OCR
                    low_text_pages.append(page_num)
                
                if use_ocr or (len(page_text.strip()) < 50):
                    # 嘗試使用 OCR
                    ocr_text = self._try_ocr_on_page(str(resolved_path), page_num)
                    if ocr_text and len(ocr_text.strip()) > len(page_text.strip()):
                        page_text = ocr_text
                        page_header += "[OCR] "
                
                text_content += page_header + page_text + "\n\n"
            
            pdf_document.close()
            
            # 如果整體文字內容很少，提示可能需要 OCR
            if not text_content.strip() or len(text_content.strip()) < 100:
                if low_text_pages:
                    ocr_hint = f"\n\n（注意：第 {', '.join(str(p+1) for p in low_text_pages)} 頁文字內容較少，"
                    ocr_hint += "可能是掃描型 PDF，建議使用 OCR 功能提取文字）"
                    text_content += ocr_hint
                else:
                    text_content = "（此 PDF 文件沒有可提取的文字內容，可能是圖片格式的 PDF，建議使用 OCR 功能）"
            
            return text_content.strip()
            
        except Exception as e:
            raise ValueError(f"PDF 讀取失敗: {e}")
    
    def _try_ocr_on_page(self, pdf_path: str, page_num: int) -> str:
        """
        嘗試對 PDF 頁面使用 OCR
        
        Args:
            pdf_path: PDF 檔案路徑
            page_num: 頁面編號
            
        Returns:
            str: OCR 提取的文字，失敗則返回空字串
        """
        try:
            from .ocr_tools import create_ocr_processor
            
            ocr_processor = create_ocr_processor()
            if ocr_processor:
                return ocr_processor.extract_text_from_pdf_page(pdf_path, page_num)
        except ImportError:
            pass  # OCR 不可用，靜默忽略
        except Exception:
            pass  # OCR 失敗，靜默忽略
        
        return ""
    
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

def read_pdf(file_path: str, use_ocr: bool = False) -> str:
    """讀取 PDF 檔案內容"""
    return default_file_tools.read_pdf(file_path, use_ocr)