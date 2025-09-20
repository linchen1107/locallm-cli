# LocalLM CLI PowerShell 安裝腳本

Write-Host ""
Write-Host "  ╭─────────────────────────────────────────╮" -ForegroundColor Cyan
Write-Host "  │                                         │" -ForegroundColor Cyan
Write-Host "  │     🛠️  LocalLM CLI 安裝程式             │" -ForegroundColor Cyan
Write-Host "  │                                         │" -ForegroundColor Cyan
Write-Host "  ╰─────────────────────────────────────────╯" -ForegroundColor Cyan
Write-Host ""

# 獲取當前目錄
$LocalLMDir = $PSScriptRoot

Write-Host "  📁 LocalLM CLI 位置: " -NoNewline
Write-Host $LocalLMDir -ForegroundColor Yellow
Write-Host ""

# 檢查是否已經在 PATH 中
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -and $userPath.Split(';') -contains $LocalLMDir) {
    Write-Host "  ✓ LocalLM CLI 已在 PATH 中" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "  🔧 正在將 LocalLM CLI 加入使用者 PATH..." -ForegroundColor Yellow
    
    try {
        # 添加到使用者 PATH
        if ($userPath) {
            $newPath = $userPath + ";" + $LocalLMDir
        } else {
            $newPath = $LocalLMDir
        }
        
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        
        Write-Host "  ✓ 成功加入 PATH" -ForegroundColor Green
        Write-Host ""
        Write-Host "  ⚠️  請重新開啟 PowerShell 使變更生效" -ForegroundColor Yellow
        Write-Host ""
    }
    catch {
        Write-Host "  ✗ 加入 PATH 失敗: " -NoNewline -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host "  請手動添加以下路徑到系統 PATH:" -ForegroundColor Red
        Write-Host "  $LocalLMDir" -ForegroundColor Yellow
        Write-Host ""
    }
}

# 測試命令是否可用
Write-Host "  🧪 測試 locallm 命令..." -ForegroundColor Cyan
Write-Host ""

try {
    $batPath = Join-Path $LocalLMDir "locallm.bat"
    $testResult = & $batPath --help 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ locallm 命令可用" -ForegroundColor Green
        Write-Host ""
        Write-Host "  🎉 安裝完成！現在您可以在任意位置輸入 'locallm' 來啟動程式" -ForegroundColor Green
        Write-Host ""
        Write-Host "  使用範例:" -ForegroundColor Cyan
        Write-Host "    locallm              " -NoNewline
        Write-Host "啟動程式（使用預設模型）" -ForegroundColor Gray
        Write-Host "    locallm -m llama3.1  " -NoNewline
        Write-Host "使用指定模型啟動" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "  ⚠️  locallm 命令尚未可用" -ForegroundColor Yellow
        Write-Host "  請重新開啟 PowerShell 後嘗試" -ForegroundColor Yellow
        Write-Host ""
    }
}
catch {
    Write-Host "  ⚠️  測試命令時發生錯誤: " -NoNewline -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "  按任意鍵退出..."
try {
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} catch {
    Read-Host
}