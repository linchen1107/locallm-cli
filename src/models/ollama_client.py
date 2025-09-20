"""
Ollama 本地模型客戶端
提供與本地 Ollama 服務通信的功能，支援流式輸出
"""

import json
import httpx
from typing import List, Dict, Generator, Optional


class OllamaClient:
    """Ollama 客戶端類"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        初始化 Ollama 客戶端
        
        Args:
            base_url: Ollama 服務的基礎 URL
        """
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)
    
    def list_models(self) -> List[Dict]:
        """
        列出可用的模型
        
        Returns:
            List[Dict]: 模型列表
        """
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            print(f"取得模型列表失敗: {e}")
            return []
    
    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
        """
        使用流式輸出與模型對話
        
        Args:
            model: 模型名稱
            messages: 對話訊息列表
            **kwargs: 其他參數（如 temperature, top_p 等）
            
        Yields:
            str: 模型回應的每個 token
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs
        }
        
        try:
            with self.client.stream(
                "POST", 
                f"{self.base_url}/api/chat",
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                if content:
                                    yield content
                            
                            # 檢查是否結束
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPStatusError as e:
            yield f"\n[錯誤] HTTP 錯誤: {e.response.status_code}"
        except httpx.ConnectError:
            yield f"\n[錯誤] 無法連接到 Ollama 服務 ({self.base_url})"
        except Exception as e:
            yield f"\n[錯誤] 未知錯誤: {e}"
    
    def chat(self, model: str, messages: List[Dict], **kwargs) -> str:
        """
        與模型對話（非流式）
        
        Args:
            model: 模型名稱
            messages: 對話訊息列表
            **kwargs: 其他參數
            
        Returns:
            str: 完整的模型回應
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        try:
            response = self.client.post(
                f"{self.base_url}/api/chat",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except httpx.HTTPStatusError as e:
            return f"[錯誤] HTTP 錯誤: {e.response.status_code}"
        except httpx.ConnectError:
            return f"[錯誤] 無法連接到 Ollama 服務 ({self.base_url})"
        except Exception as e:
            return f"[錯誤] 未知錯誤: {e}"
    
    def is_available(self) -> bool:
        """
        檢查 Ollama 服務是否可用
        
        Returns:
            bool: 服務是否可用
        """
        try:
            response = self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except:
            return False
    
    def __del__(self):
        """清理資源"""
        if hasattr(self, 'client'):
            self.client.close()


# 創建預設實例
default_ollama_client = OllamaClient()

# 提供便捷的函數介面
def chat_stream(model: str, messages: List[Dict], **kwargs) -> Generator[str, None, None]:
    """流式對話"""
    yield from default_ollama_client.chat_stream(model, messages, **kwargs)

def chat(model: str, messages: List[Dict], **kwargs) -> str:
    """非流式對話"""
    return default_ollama_client.chat(model, messages, **kwargs)

def list_models() -> List[Dict]:
    """列出可用模型"""
    return default_ollama_client.list_models()

def is_available() -> bool:
    """檢查服務是否可用"""
    return default_ollama_client.is_available()
