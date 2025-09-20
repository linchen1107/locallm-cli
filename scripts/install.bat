@echo off
REM LocalLM CLI 安裝腳本
REM 此腳本會將 LocalLM CLI 加入到系統 PATH 中

echo.
echo   ╭─────────────────────────────────────────╮
echo   │                                         │
echo   │     🛠️  LocalLM CLI 安裝程式             │
echo   │                                         │
echo   ╰─────────────────────────────────────────╯
echo.

REM 獲取當前目錄
set LOCALLM_DIR=%~dp0
set LOCALLM_DIR=%LOCALLM_DIR:~0,-1%

echo   📁 LocalLM CLI 位置: %LOCALLM_DIR%
echo.

REM 檢查是否已經在 PATH 中
echo %PATH% | findstr /i "%LOCALLM_DIR%" >nul
if %errorlevel%==0 (
    echo   ✓ LocalLM CLI 已在 PATH 中
    echo.
    goto :test_command
)

echo   🔧 正在將 LocalLM CLI 加入使用者 PATH...

REM 獲取目前的使用者 PATH
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set USER_PATH=%%B

REM 如果 PATH 不存在，創建一個新的
if not defined USER_PATH set USER_PATH=

REM 添加 LocalLM CLI 目錄到 PATH
if defined USER_PATH (
    set NEW_PATH=%USER_PATH%;%LOCALLM_DIR%
) else (
    set NEW_PATH=%LOCALLM_DIR%
)

REM 更新註冊表
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%NEW_PATH%" /f >nul

if %errorlevel%==0 (
    echo   ✓ 成功加入 PATH
    echo.
    echo   ⚠️  請重新開啟命令提示字元或 PowerShell 使變更生效
    echo.
) else (
    echo   ✗ 加入 PATH 失敗，請手動添加以下路徑到系統 PATH:
    echo   %LOCALLM_DIR%
    echo.
)

:test_command
echo   🧪 測試 locallm 命令...
echo.

REM 測試命令是否可用
call locallm.bat --help >nul 2>&1
if %errorlevel%==0 (
    echo   ✓ locallm 命令可用
    echo.
    echo   🎉 安裝完成！現在您可以在任意位置輸入 'locallm' 來啟動程式
    echo.
    echo   使用範例:
    echo     locallm              啟動程式（使用預設模型）
    echo     locallm -m llama3.1  使用指定模型啟動
    echo.
) else (
    echo   ⚠️  locallm 命令尚未可用
    echo   請重新開啟命令提示字元後嘗試
    echo.
)

echo   按任意鍵退出...
pause >nul