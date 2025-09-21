"""
加密存取工具
支援敏感文件的加密處理
"""

import os
import base64
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
import json
import time

# 可選依賴檢查
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

class EncryptionManager:
    """加密管理器"""
    
    def __init__(self):
        self.supported_formats = ['.txt', '.json', '.csv', '.py', '.md', '.xml', '.yml', '.yaml']
        self.key_service = "locallm_encryption"
        self.keyring_service = "locallm_cli"
        
    def check_dependencies(self) -> Dict[str, bool]:
        """檢查加密依賴"""
        return {
            'cryptography': HAS_CRYPTOGRAPHY,
            'keyring': HAS_KEYRING
        }
    
    def generate_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """從密碼生成加密密鑰"""
        if not HAS_CRYPTOGRAPHY:
            raise ImportError("cryptography 庫未安裝")
        
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def generate_random_key(self) -> bytes:
        """生成隨機加密密鑰"""
        if not HAS_CRYPTOGRAPHY:
            raise ImportError("cryptography 庫未安裝")
        
        return Fernet.generate_key()
    
    def save_key_to_keyring(self, key: bytes, key_name: str = "default") -> bool:
        """保存密鑰到系統密鑰環"""
        if not HAS_KEYRING:
            return False
        
        try:
            keyring.set_password(self.keyring_service, key_name, key.decode())
            return True
        except Exception:
            return False
    
    def load_key_from_keyring(self, key_name: str = "default") -> Optional[bytes]:
        """從系統密鑰環載入密鑰"""
        if not HAS_KEYRING:
            return None
        
        try:
            key_str = keyring.get_password(self.keyring_service, key_name)
            if key_str:
                return key_str.encode()
            return None
        except Exception:
            return None
    
    def encrypt_file(self, file_path: str, password: str = None, 
                    key: bytes = None, output_path: str = None) -> Dict[str, Any]:
        """加密文件"""
        if not HAS_CRYPTOGRAPHY:
            return {"error": "cryptography 庫未安裝，請安裝: pip install cryptography"}
        
        try:
            # 檢查文件是否存在
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            
            # 讀取文件內容
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 生成或使用提供的密鑰
            if key is None:
                if password:
                    key, salt = self.generate_key_from_password(password)
                else:
                    key = self.generate_random_key()
                    salt = None
            else:
                salt = None
            
            # 加密數據
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(file_data)
            
            # 準備輸出路徑
            if output_path is None:
                output_path = f"{file_path}.encrypted"
            
            # 保存加密文件
            with open(output_path, 'wb') as f:
                if salt:
                    f.write(b"SALT:" + salt + b"\n")
                f.write(encrypted_data)
            
            # 計算文件哈希
            original_hash = hashlib.sha256(file_data).hexdigest()
            encrypted_hash = hashlib.sha256(encrypted_data).hexdigest()
            
            return {
                "success": True,
                "original_file": file_path,
                "encrypted_file": output_path,
                "original_size": len(file_data),
                "encrypted_size": len(encrypted_data),
                "original_hash": original_hash,
                "encrypted_hash": encrypted_hash,
                "key_saved": self.save_key_to_keyring(key) if not password else False
            }
            
        except Exception as e:
            return {"error": f"加密失敗: {str(e)}"}
    
    def decrypt_file(self, encrypted_file_path: str, password: str = None,
                    key: bytes = None, output_path: str = None) -> Dict[str, Any]:
        """解密文件"""
        if not HAS_CRYPTOGRAPHY:
            return {"error": "cryptography 庫未安裝，請安裝: pip install cryptography"}
        
        try:
            # 檢查加密文件是否存在
            if not os.path.exists(encrypted_file_path):
                return {"error": f"加密文件不存在: {encrypted_file_path}"}
            
            # 讀取加密文件
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # 檢查是否有鹽值
            salt = None
            if encrypted_data.startswith(b"SALT:"):
                salt_end = encrypted_data.find(b"\n")
                if salt_end != -1:
                    salt = encrypted_data[5:salt_end]
                    encrypted_data = encrypted_data[salt_end + 1:]
            
            # 生成或使用提供的密鑰
            if key is None:
                if password:
                    if salt is None:
                        return {"error": "缺少鹽值，無法從密碼生成密鑰"}
                    key, _ = self.generate_key_from_password(password, salt)
                else:
                    # 嘗試從密鑰環載入
                    key = self.load_key_from_keyring()
                    if key is None:
                        return {"error": "需要提供密碼或密鑰"}
            
            # 解密數據
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # 準備輸出路徑
            if output_path is None:
                if encrypted_file_path.endswith('.encrypted'):
                    output_path = encrypted_file_path[:-10]  # 移除 .encrypted
                else:
                    output_path = f"{encrypted_file_path}.decrypted"
            
            # 保存解密文件
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            # 計算文件哈希
            decrypted_hash = hashlib.sha256(decrypted_data).hexdigest()
            
            return {
                "success": True,
                "encrypted_file": encrypted_file_path,
                "decrypted_file": output_path,
                "decrypted_size": len(decrypted_data),
                "decrypted_hash": decrypted_hash
            }
            
        except Exception as e:
            return {"error": f"解密失敗: {str(e)}"}
    
    def encrypt_text(self, text: str, password: str = None, key: bytes = None) -> Dict[str, Any]:
        """加密文本"""
        if not HAS_CRYPTOGRAPHY:
            return {"error": "cryptography 庫未安裝，請安裝: pip install cryptography"}
        
        try:
            # 生成或使用提供的密鑰
            if key is None:
                if password:
                    key, salt = self.generate_key_from_password(password)
                else:
                    key = self.generate_random_key()
                    salt = None
            else:
                salt = None
            
            # 加密文本
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(text.encode('utf-8'))
            
            # 編碼為 base64 字符串
            encrypted_text = base64.b64encode(encrypted_data).decode('utf-8')
            
            return {
                "success": True,
                "encrypted_text": encrypted_text,
                "salt": base64.b64encode(salt).decode('utf-8') if salt else None,
                "key_saved": self.save_key_to_keyring(key) if not password else False
            }
            
        except Exception as e:
            return {"error": f"文本加密失敗: {str(e)}"}
    
    def decrypt_text(self, encrypted_text: str, password: str = None,
                    key: bytes = None, salt: str = None) -> Dict[str, Any]:
        """解密文本"""
        if not HAS_CRYPTOGRAPHY:
            return {"error": "cryptography 庫未安裝，請安裝: pip install cryptography"}
        
        try:
            # 解碼 base64
            encrypted_data = base64.b64decode(encrypted_text.encode('utf-8'))
            
            # 生成或使用提供的密鑰
            if key is None:
                if password:
                    if salt:
                        salt_bytes = base64.b64decode(salt.encode('utf-8'))
                    else:
                        return {"error": "解密文本需要提供鹽值"}
                    key, _ = self.generate_key_from_password(password, salt_bytes)
                else:
                    # 嘗試從密鑰環載入
                    key = self.load_key_from_keyring()
                    if key is None:
                        return {"error": "需要提供密碼或密鑰"}
            
            # 解密文本
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            decrypted_text = decrypted_data.decode('utf-8')
            
            return {
                "success": True,
                "decrypted_text": decrypted_text
            }
            
        except Exception as e:
            return {"error": f"文本解密失敗: {str(e)}"}
    
    def create_encrypted_backup(self, file_path: str, password: str) -> Dict[str, Any]:
        """創建加密備份"""
        timestamp = int(time.time())
        backup_path = f"{file_path}.backup.{timestamp}.encrypted"
        
        result = self.encrypt_file(file_path, password, output_path=backup_path)
        
        if "success" in result:
            result["backup_path"] = backup_path
            result["timestamp"] = timestamp
        
        return result
    
    def batch_encrypt_files(self, file_paths: list, password: str = None) -> Dict[str, Any]:
        """批量加密文件"""
        if not HAS_CRYPTOGRAPHY:
            return {"error": "cryptography 庫未安裝，請安裝: pip install cryptography"}
        
        results = []
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            result = self.encrypt_file(file_path, password)
            results.append({
                "file_path": file_path,
                "result": result
            })
            
            if "success" in result:
                successful += 1
            else:
                failed += 1
        
        return {
            "total_files": len(file_paths),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    def batch_decrypt_files(self, encrypted_file_paths: list, password: str = None) -> Dict[str, Any]:
        """批量解密文件"""
        if not HAS_CRYPTOGRAPHY:
            return {"error": "cryptography 庫未安裝，請安裝: pip install cryptography"}
        
        results = []
        successful = 0
        failed = 0
        
        for file_path in encrypted_file_paths:
            result = self.decrypt_file(file_path, password)
            results.append({
                "file_path": file_path,
                "result": result
            })
            
            if "success" in result:
                successful += 1
            else:
                failed += 1
        
        return {
            "total_files": len(encrypted_file_paths),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    def verify_file_integrity(self, original_file: str, decrypted_file: str) -> Dict[str, Any]:
        """驗證文件完整性"""
        try:
            # 計算原始文件哈希
            with open(original_file, 'rb') as f:
                original_hash = hashlib.sha256(f.read()).hexdigest()
            
            # 計算解密文件哈希
            with open(decrypted_file, 'rb') as f:
                decrypted_hash = hashlib.sha256(f.read()).hexdigest()
            
            return {
                "original_hash": original_hash,
                "decrypted_hash": decrypted_hash,
                "integrity_verified": original_hash == decrypted_hash
            }
            
        except Exception as e:
            return {"error": f"完整性驗證失敗: {str(e)}"}
    
    def list_encrypted_files(self, directory: str) -> list:
        """列出目錄中的加密文件"""
        encrypted_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.encrypted'):
                    file_path = os.path.join(root, file)
                    encrypted_files.append(file_path)
        
        return encrypted_files
    
    def get_encryption_info(self, encrypted_file: str) -> Dict[str, Any]:
        """獲取加密文件信息"""
        try:
            if not os.path.exists(encrypted_file):
                return {"error": "文件不存在"}
            
            stat = os.stat(encrypted_file)
            
            # 讀取文件頭部檢查是否有鹽值
            with open(encrypted_file, 'rb') as f:
                header = f.read(100)  # 讀取前100字節
            
            has_salt = header.startswith(b"SALT:")
            
            return {
                "file_path": encrypted_file,
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "has_salt": has_salt,
                "encrypted": True
            }
            
        except Exception as e:
            return {"error": f"獲取加密信息失敗: {str(e)}"}

# 創建默認實例
default_encryption_manager = EncryptionManager()
