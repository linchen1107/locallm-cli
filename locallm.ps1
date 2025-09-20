# LocalLM CLI 啟動腳本 (PowerShell)
# 此腳本允許在任意位置輸入 locallm 來啟動程式

# 獲取腳本所在目錄
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 執行 Python 程式，傳遞所有參數
& python "$ScriptDir\scripts\locallm_entry.py" @args