@echo off
REM LocalLM CLI 全域啟動腳本
REM 此腳本允許在任意位置輸入 locallm 來啟動程式

REM 獲取腳本所在目錄
set SCRIPT_DIR=%~dp0

REM 執行 Python 程式，傳遞所有參數
python "%SCRIPT_DIR%scripts\locallm_entry.py" %*
exit /b

REM 防止顯示批次檔結束提示
exit /b