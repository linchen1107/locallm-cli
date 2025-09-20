from setuptools import setup, find_packages
import os

# 讀取專案根目錄的 README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'docs', 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "LocalLM CLI - 本地模型檔案操作工具"

# 讀取依賴需求
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return ['httpx>=0.24.0']

setup(
    name="locallm-cli",
    version="1.0.0",
    description="LocalLM CLI - 本地模型檔案操作工具",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="LocalLM Team",
    author_email="contact@locallm.dev",
    url="https://github.com/locallm/locallm-cli",
    
    # 套件設定
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Python 版本需求
    python_requires=">=3.8",
    
    # 依賴套件
    install_requires=read_requirements(),
    
    # 額外依賴
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio",
            "black",
            "flake8",
        ],
    },
    
    # 命令行腳本
    entry_points={
        "console_scripts": [
            "locallm=src.main:main",
        ],
    },
    
    # 分類標籤
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # 包含額外檔案
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.bat", "*.ps1"],
    },
    
    # 專案關鍵字
    keywords="cli ai local language-model file-management",
    
    # 專案 URLs
    project_urls={
        "Homepage": "https://github.com/locallm/locallm-cli",
        "Source": "https://github.com/locallm/locallm-cli",
        "Documentation": "https://github.com/locallm/locallm-cli/docs",
        "Bug Reports": "https://github.com/locallm/locallm-cli/issues",
    },
)