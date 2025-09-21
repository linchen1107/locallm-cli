#!/usr/bin/env python3
"""
Git 集成管理模組
提供 Git 命令集成和智能提交信息生成功能
"""

import os
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import keyring
import requests

class GitManager:
    """Git 操作管理器"""
    
    def __init__(self):
        self.config_file = Path.home() / ".locallm" / "git_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """載入 Git 配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "profiles": {},
            "current_profile": None,
            "default_remote": "origin",
            "default_branch": "main"
        }
    
    def _save_config(self):
        """保存 Git 配置"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _run_git_command(self, args: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """執行 Git 命令"""
        try:
            cmd = ["git"] + args
            result = subprocess.run(
                cmd, 
                cwd=cwd or os.getcwd(),
                capture_output=True, 
                text=True, 
                encoding='utf-8'
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def status(self) -> str:
        """顯示 Git 狀態"""
        success, output = self._run_git_command(["status", "--porcelain"])
        if not success:
            return f"❌ Git 狀態檢查失敗: {output}"
        
        if not output.strip():
            return "✅ 工作目錄乾淨，沒有變更"
        
        # 解析狀態
        staged_files = []
        unstaged_files = []
        untracked_files = []
        
        for line in output.strip().split('\n'):
            if not line:
                continue
            status = line[:2]
            filename = line[3:]
            
            if status[0] != ' ':
                staged_files.append(filename)
            if status[1] != ' ':
                if status[1] == '?':
                    untracked_files.append(filename)
                else:
                    unstaged_files.append(filename)
        
        result = "📊 Git 狀態:\n"
        if staged_files:
            result += f"  📝 已暫存 ({len(staged_files)} 個文件):\n"
            for file in staged_files:
                result += f"    + {file}\n"
        
        if unstaged_files:
            result += f"  🔄 已修改 ({len(unstaged_files)} 個文件):\n"
            for file in unstaged_files:
                result += f"    ~ {file}\n"
        
        if untracked_files:
            result += f"  📄 未追蹤 ({len(untracked_files)} 個文件):\n"
            for file in untracked_files:
                result += f"    ? {file}\n"
        
        return result
    
    def add(self, files: List[str] = None) -> str:
        """添加文件到暫存區"""
        if files is None:
            files = ["."]
        
        success, output = self._run_git_command(["add"] + files)
        if success:
            return f"✅ 已添加 {len(files)} 個文件到暫存區"
        else:
            return f"❌ 添加文件失敗: {output}"
    
    def commit(self, message: str = None, auto_generate: bool = False) -> str:
        """提交變更"""
        if auto_generate or message == "auto":
            message = self._generate_commit_message()
        
        if not message:
            return "❌ 提交信息不能為空"
        
        success, output = self._run_git_command(["commit", "-m", message])
        if success:
            return f"✅ 提交成功: {message}"
        else:
            return f"❌ 提交失敗: {output}"
    
    def _generate_commit_message(self) -> str:
        """生成智能提交信息"""
        # 獲取變更統計
        success, diff_output = self._run_git_command(["diff", "--cached", "--stat"])
        if not success:
            return "feat: 更新代碼"
        
        # 分析變更內容
        success, diff_content = self._run_git_command(["diff", "--cached"])
        if not success:
            return "feat: 更新代碼"
        
        # 詳細的變更分析
        lines_added = len([line for line in diff_content.split('\n') if line.startswith('+')])
        lines_deleted = len([line for line in diff_content.split('\n') if line.startswith('-')])
        
        # 分析文件類型和變更模式
        files_changed = set()
        file_types = {}
        change_patterns = []
        
        for line in diff_output.split('\n'):
            if '|' in line:
                filename = line.split('|')[0].strip()
                files_changed.add(filename)
                ext = filename.split('.')[-1] if '.' in filename else 'unknown'
                file_types[ext] = file_types.get(ext, 0) + 1
        
        # 分析變更模式
        if 'feat' in diff_content.lower() or 'add' in diff_content.lower():
            change_patterns.append('feature')
        if 'fix' in diff_content.lower() or 'bug' in diff_content.lower():
            change_patterns.append('bugfix')
        if 'refactor' in diff_content.lower() or 'clean' in diff_content.lower():
            change_patterns.append('refactor')
        if 'test' in diff_content.lower():
            change_patterns.append('test')
        if 'doc' in diff_content.lower() or 'readme' in diff_content.lower():
            change_patterns.append('docs')
        
        # 智能生成提交信息
        if 'feature' in change_patterns:
            if '.py' in file_types:
                return "feat: 新增 Python 功能模組"
            elif '.js' in file_types or '.ts' in file_types:
                return "feat: 新增 JavaScript/TypeScript 功能"
            elif '.md' in file_types:
                return "feat: 新增文檔和說明"
            else:
                return "feat: 新增功能"
        elif 'bugfix' in change_patterns:
            return "fix: 修復問題"
        elif 'refactor' in change_patterns:
            return "refactor: 重構代碼結構"
        elif 'test' in change_patterns:
            return "test: 新增測試用例"
        elif 'docs' in change_patterns:
            return "docs: 更新文檔"
        elif lines_added > lines_deleted * 2:
            if '.py' in file_types:
                return "feat: 新增 Python 功能"
            elif '.md' in file_types:
                return "docs: 更新文檔"
            else:
                return "feat: 新增功能"
        elif lines_deleted > lines_added * 2:
            return "refactor: 清理和重構代碼"
        else:
            return "fix: 修復問題"
    
    def push(self, remote: Optional[str] = None, branch: Optional[str] = None) -> str:
        """推送到遠程倉庫"""
        remote = remote or self.config.get("default_remote", "origin")
        branch = branch or self.config.get("default_branch", "main")
        
        success, output = self._run_git_command(["push", remote, branch])
        if success:
            return f"✅ 已推送到 {remote}/{branch}"
        else:
            return f"❌ 推送失敗: {output}"
    
    def pull(self, remote: Optional[str] = None, branch: Optional[str] = None) -> str:
        """從遠程倉庫拉取"""
        remote = remote or self.config.get("default_remote", "origin")
        branch = branch or self.config.get("default_branch", "main")
        
        success, output = self._run_git_command(["pull", remote, branch])
        if success:
            return f"✅ 已從 {remote}/{branch} 拉取更新"
        else:
            return f"❌ 拉取失敗: {output}"
    
    def tag(self, tag_name: str) -> str:
        """創建標籤"""
        success, output = self._run_git_command(["tag", tag_name])
        if success:
            return f"✅ 已創建標籤: {tag_name}"
        else:
            return f"❌ 創建標籤失敗: {output}"
    
    def log(self, count: int = 10) -> str:
        """顯示提交歷史"""
        success, output = self._run_git_command(["log", f"--oneline", f"-{count}"])
        if success:
            return f"📋 最近 {count} 次提交:\n{output}"
        else:
            return f"❌ 獲取提交歷史失敗: {output}"
    
    def diff(self) -> str:
        """顯示變更差異"""
        success, output = self._run_git_command(["diff"])
        if success:
            if not output.strip():
                return "✅ 沒有未暫存的變更"
            return f"📊 變更差異:\n{output[:1000]}{'...' if len(output) > 1000 else ''}"
        else:
            return f"❌ 獲取變更差異失敗: {output}"
    
    def analyze_diff(self) -> str:
        """分析 diff 並提供智能建議"""
        success, diff_content = self._run_git_command(["diff"])
        if not success:
            return f"❌ 無法分析 diff: {diff_content}"
        
        if not diff_content.strip():
            return "✅ 沒有變更需要分析"
        
        # 分析變更統計
        lines_added = len([line for line in diff_content.split('\n') if line.startswith('+')])
        lines_deleted = len([line for line in diff_content.split('\n') if line.startswith('-')])
        
        # 分析文件變更
        files_changed = set()
        file_types = {}
        
        for line in diff_content.split('\n'):
            if line.startswith('diff --git'):
                filename = line.split()[-1]
                files_changed.add(filename)
                ext = filename.split('.')[-1] if '.' in filename else 'unknown'
                file_types[ext] = file_types.get(ext, 0) + 1
        
        # 生成分析報告
        analysis = "🔍 Diff 分析報告:\n"
        analysis += f"  📊 變更統計: +{lines_added} 行, -{lines_deleted} 行\n"
        analysis += f"  📁 影響文件: {len(files_changed)} 個\n"
        
        if file_types:
            analysis += "  📋 文件類型分布:\n"
            for ext, count in file_types.items():
                analysis += f"    • .{ext}: {count} 個文件\n"
        
        # 提供建議
        suggestions = []
        if lines_added > lines_deleted * 3:
            suggestions.append("💡 大量新增代碼，建議檢查是否需要添加測試")
        if lines_deleted > lines_added * 2:
            suggestions.append("💡 大量刪除代碼，建議確認沒有破壞現有功能")
        if '.py' in file_types and lines_added > 50:
            suggestions.append("💡 Python 文件變更較大，建議檢查代碼風格和文檔")
        if '.md' in file_types:
            suggestions.append("💡 文檔已更新，建議檢查格式和內容完整性")
        
        if suggestions:
            analysis += "\n  🎯 建議:\n"
            for suggestion in suggestions:
                analysis += f"    {suggestion}\n"
        
        return analysis


class GitHubAuth:
    """GitHub 認證管理"""
    
    def __init__(self):
        self.config_file = Path.home() / ".locallm" / "github_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """載入 GitHub 配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"profiles": {}, "current_profile": None}
    
    def _save_config(self):
        """保存 GitHub 配置"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def set_user(self, username: str) -> str:
        """設定 GitHub 用戶名"""
        profile_name = self.config.get("current_profile", "default")
        if profile_name not in self.config["profiles"]:
            self.config["profiles"][profile_name] = {}
        
        self.config["profiles"][profile_name]["username"] = username
        self._save_config()
        
        # 設定 Git 用戶名
        git_manager = GitManager()
        success, output = git_manager._run_git_command(["config", "user.name", username])
        if success:
            return f"✅ 已設定 GitHub 用戶名: {username}"
        else:
            return f"⚠️ GitHub 用戶名已保存，但 Git 設定失敗: {output}"
    
    def set_email(self, email: str) -> str:
        """設定 GitHub 郵箱"""
        profile_name = self.config.get("current_profile", "default")
        if profile_name not in self.config["profiles"]:
            self.config["profiles"][profile_name] = {}
        
        self.config["profiles"][profile_name]["email"] = email
        self._save_config()
        
        # 設定 Git 郵箱
        git_manager = GitManager()
        success, output = git_manager._run_git_command(["config", "user.email", email])
        if success:
            return f"✅ 已設定 GitHub 郵箱: {email}"
        else:
            return f"⚠️ GitHub 郵箱已保存，但 Git 設定失敗: {output}"
    
    def set_token(self, token: str) -> str:
        """設定 GitHub Personal Access Token"""
        profile_name = self.config.get("current_profile", "default")
        if profile_name not in self.config["profiles"]:
            self.config["profiles"][profile_name] = {}
        
        # 使用 keyring 安全存儲 token
        try:
            keyring.set_password("locallm-github", profile_name, token)
            self.config["profiles"][profile_name]["has_token"] = True
            self._save_config()
            return f"✅ 已安全保存 GitHub Token (配置檔: {profile_name})"
        except Exception as e:
            return f"❌ 保存 Token 失敗: {e}"
    
    def show_config(self) -> str:
        """顯示當前配置"""
        profile_name = self.config.get("current_profile", "default")
        profile = self.config["profiles"].get(profile_name, {})
        
        result = f"📋 GitHub 配置 (配置檔: {profile_name}):\n"
        result += f"  用戶名: {profile.get('username', '未設定')}\n"
        result += f"  郵箱: {profile.get('email', '未設定')}\n"
        result += f"  Token: {'已設定' if profile.get('has_token') else '未設定'}\n"
        
        return result
    
    def switch_profile(self, profile_name: str) -> str:
        """切換配置檔案"""
        if profile_name not in self.config["profiles"]:
            self.config["profiles"][profile_name] = {}
        
        self.config["current_profile"] = profile_name
        self._save_config()
        
        # 應用配置到 Git
        profile = self.config["profiles"][profile_name]
        git_manager = GitManager()
        
        if profile.get("username"):
            git_manager._run_git_command(["config", "user.name", profile["username"]])
        if profile.get("email"):
            git_manager._run_git_command(["config", "user.email", profile["email"]])
        
        return f"✅ 已切換到配置檔: {profile_name}"
    
    def logout(self) -> str:
        """登出當前帳號"""
        profile_name = self.config.get("current_profile", "default")
        
        # 清除 Token
        try:
            keyring.delete_password("locallm-github", profile_name)
        except:
            pass
        
        # 清除配置
        if profile_name in self.config["profiles"]:
            del self.config["profiles"][profile_name]
        
        self.config["current_profile"] = None
        self._save_config()
        
        return f"✅ 已登出配置檔: {profile_name}"


# 創建預設實例
default_git_manager = GitManager()
default_github_auth = GitHubAuth()
