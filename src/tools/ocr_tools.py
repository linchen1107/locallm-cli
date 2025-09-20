#!/usr/bin/env python3
"""
OCR 支援模組
提供掃描型 PDF 文件的光學字符識別功能
"""

import logging
from pathlib import Path
from typing import Optional, Union
import tempfile
import os

# 檢查 OCR 相關依賴
HAS_OCR_SUPPORT = True
OCR_ERROR_MSG = ""

try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
except ImportError as e:
    HAS_OCR_SUPPORT = False
    OCR_ERROR_MSG = f"OCR 依賴未安裝: {e}"
    # 創建 Image 占位符
    Image = None
    pytesseract = None
    fitz = None

logger = logging.getLogger(__name__)


class OCRProcessor:
    """OCR 處理器類別"""
    
    def __init__(self, 
                 language: str = 'eng+chi_tra',
                 tesseract_cmd: Optional[str] = None):
        """
        初始化 OCR 處理器
        
        Args:
            language: OCR 語言設定 (例如: 'eng', 'chi_tra', 'eng+chi_tra')
            tesseract_cmd: Tesseract 執行檔路徑
        """
        if not HAS_OCR_SUPPORT:
            raise ImportError(f"OCR 功能不可用: {OCR_ERROR_MSG}")
        
        self.language = language
        
        # 設定 Tesseract 路徑
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif os.name == 'nt':  # Windows
            # 常見的 Windows Tesseract 安裝路徑
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe'
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        
        self._test_ocr()
    
    def _test_ocr(self):
        """測試 OCR 功能是否正常"""
        try:
            # 創建一個小的測試圖片
            test_image = Image.new('RGB', (100, 50), color='white')
            pytesseract.image_to_string(test_image, lang=self.language)
            logger.info("OCR 功能測試成功")
        except Exception as e:
            logger.error(f"OCR 功能測試失敗: {e}")
            raise RuntimeError(f"OCR 初始化失敗: {e}")
    
    def extract_text_from_image(self, image) -> str:
        """
        從圖片中提取文字
        
        Args:
            image: 圖片路徑或 PIL Image 物件
            
        Returns:
            str: 提取的文字內容
        """
        try:
            if isinstance(image, (str, Path)):
                image = Image.open(image)
            
            # 使用 Tesseract 進行 OCR
            text = pytesseract.image_to_string(image, lang=self.language)
            return text.strip()
            
        except Exception as e:
            logger.error(f"圖片 OCR 失敗: {e}")
            return ""
    
    def extract_text_from_pdf_page(self, pdf_path, page_num: int) -> str:
        """
        從 PDF 頁面提取文字（使用 OCR）
        
        Args:
            pdf_path: PDF 文件路徑
            page_num: 頁面編號（從 0 開始）
            
        Returns:
            str: 提取的文字內容
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            # 將頁面轉換為圖片
            pix = getattr(page, 'get_pixmap', lambda: None)()
            if pix is None:
                return ""
            img_data = pix.tobytes("png")
            
            # 保存為臨時圖片文件
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file.write(img_data)
                temp_path = temp_file.name
            
            try:
                # 對圖片進行 OCR
                image = Image.open(temp_path)
                text = self.extract_text_from_image(image)
                return text
            finally:
                # 清理臨時文件
                os.unlink(temp_path)
                doc.close()
                
        except Exception as e:
            logger.error(f"PDF 頁面 OCR 失敗: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path) -> str:
        """
        從整個 PDF 文件提取文字（使用 OCR）
        
        Args:
            pdf_path: PDF 文件路徑
            
        Returns:
            str: 提取的文字內容
        """
        try:
            doc = fitz.open(pdf_path)
            all_text = []
            
            logger.info(f"開始 OCR 處理 PDF: {pdf_path}，共 {len(doc)} 頁")
            
            for page_num in range(len(doc)):
                logger.info(f"正在處理第 {page_num + 1} 頁...")
                
                # 首先嘗試直接提取文字
                page = doc[page_num]
                text = getattr(page, 'get_text', lambda: "")() or ""
                
                # 如果直接提取的文字很少或為空，使用 OCR
                if len(text.strip()) < 50:  # 閾值可調整
                    logger.info(f"第 {page_num + 1} 頁文字較少，使用 OCR")
                    ocr_text = self.extract_text_from_pdf_page(pdf_path, page_num)
                    if ocr_text:
                        text = ocr_text
                
                if text.strip():
                    all_text.append(f"--- 第 {page_num + 1} 頁 ---\n{text}")
            
            doc.close()
            return "\n\n".join(all_text)
            
        except Exception as e:
            logger.error(f"PDF OCR 處理失敗: {e}")
            return ""


def create_ocr_processor(**kwargs) -> Optional[OCRProcessor]:
    """
    創建 OCR 處理器實例
    
    Args:
        **kwargs: OCRProcessor 的參數
        
    Returns:
        OCRProcessor 實例，如果不可用則返回 None
    """
    if not HAS_OCR_SUPPORT:
        logger.warning(f"OCR 功能不可用: {OCR_ERROR_MSG}")
        return None
    
    try:
        return OCRProcessor(**kwargs)
    except Exception as e:
        logger.error(f"OCR 處理器創建失敗: {e}")
        return None


def is_ocr_available() -> bool:
    """檢查 OCR 功能是否可用"""
    return HAS_OCR_SUPPORT


def get_ocr_installation_instructions() -> str:
    """獲取 OCR 安裝說明"""
    instructions = """
OCR 功能需要安裝以下依賴：

1. Python 套件：
   pip install pytesseract pillow

2. Tesseract OCR 引擎：
   
   Windows:
   - 下載: https://github.com/UB-Mannheim/tesseract/wiki
   - 安裝到預設路徑 (C:\\Program Files\\Tesseract-OCR\\)
   
   macOS:
   brew install tesseract

   Ubuntu/Debian:
   sudo apt-get install tesseract-ocr tesseract-ocr-chi-tra

3. 語言包（可選）：
   - 中文繁體: tesseract-ocr-chi-tra
   - 中文簡體: tesseract-ocr-chi-sim
   - 其他語言請參考 Tesseract 官方文檔

安裝完成後重新啟動程式即可使用 OCR 功能。
"""
    return instructions


__all__ = [
    'OCRProcessor',
    'create_ocr_processor',
    'is_ocr_available',
    'get_ocr_installation_instructions',
    'HAS_OCR_SUPPORT'
]