# RTLPlayground Argon 主题一键补丁管理工具
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       RTLPlayground 现代双主题一键补丁管理工具" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PatchFile = Join-Path $ScriptDir "argon_theme.patch"
$ResDir = Join-Path $ScriptDir "argon_theme"
$SimSrc = Join-Path $ScriptDir "sim_server.py"

# 检测目标仓库
$TargetDir = $args[0]

if ([string]::IsNullOrWhiteSpace($TargetDir)) {
    # 智能推断：检查上级目录是否包含 html\index.html
    $ParentDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path
    if (Test-Path (Join-Path $ParentDir "html\index.html")) {
        $DefaultDir = $ParentDir
    } else {
        $DefaultDir = (Get-Location).Path
    }

    Write-Host "请输入需要打补丁的目标仓库根目录：" -ForegroundColor Yellow
    Write-Host "[可以直接按回车使用默认路径: $DefaultDir]" -ForegroundColor Gray
    $UserInput = Read-Host "> "
    if ([string]::IsNullOrWhiteSpace($UserInput)) {
        $TargetDir = $DefaultDir
    } else {
        $TargetDir = $UserInput.Trim('"')
    }
} else {
    $TargetDir = $TargetDir.Trim('"')
}

$TargetDir = (Resolve-Path $TargetDir -ErrorAction SilentlyContinue).Path

if ([string]::IsNullOrWhiteSpace($TargetDir) -or -not (Test-Path (Join-Path $TargetDir "html"))) {
    Write-Host ""
    Write-Host "[错误] 在指定路径下未找到 html 目录！" -ForegroundColor Red
    Write-Host "目标路径: $TargetDir" -ForegroundColor DarkGray
    Write-Host "请确认您指定的是 RTLPlayground 仓库的根目录。" -ForegroundColor Red
    Write-Host ""
    Read-Host "按回车键退出..."
    exit 1
}

Write-Host ""
Write-Host "当前目标仓库: $TargetDir" -ForegroundColor Green
Write-Host ""

function Show-Menu {
    Write-Host "========================================================" -ForegroundColor DarkCyan
    Write-Host "请选择要执行的操作:"
    Write-Host "  1. [推荐] 一键应用 Argon 现代主题 (安全替换并自动生成 .bak 备份)" -ForegroundColor White
    Write-Host "  2. 使用 Git Patch 补丁应用 (适合干净的 Git 分支)" -ForegroundColor White
    Write-Host "  3. 一键还原官方原版 (从 .bak 备份恢复或 Git 还原)" -ForegroundColor White
    Write-Host "  4. 启动本地模拟服务器 (启动 Python 调试服务进行实时预览)" -ForegroundColor White
    Write-Host "  5. 退出" -ForegroundColor Gray
    Write-Host ""
}

function Do-CopyApply {
    Write-Host ""
    Write-Host "正在应用主题文件..." -ForegroundColor Cyan

    $SrcMainJs = Join-Path $ResDir "html\main.js"
    $SrcStyleCss = Join-Path $ResDir "html\style.css"

    if (-not (Test-Path $SrcMainJs) -or -not (Test-Path $SrcStyleCss)) {
        Write-Host "[错误] 补丁源文件缺失，请确保 tools/argon_theme/html/ 下存在 main.js 和 style.css！" -ForegroundColor Red
        return
    }

    $DstMainJs = Join-Path $TargetDir "html\main.js"
    $DstStyleCss = Join-Path $TargetDir "html\style.css"

    # 安全备份（仅当备份不存在时备份，保护初始官方原版）
    $BakMainJs = "$DstMainJs.bak"
    $BakStyleCss = "$DstStyleCss.bak"

    if ((Test-Path $DstMainJs) -and -not (Test-Path $BakMainJs)) {
        Write-Host "[备份] 正在备份原版 main.js -> main.js.bak ..." -ForegroundColor Gray
        Copy-Item $DstMainJs $BakMainJs -Force
    }
    if ((Test-Path $DstStyleCss) -and -not (Test-Path $BakStyleCss)) {
        Write-Host "[备份] 正在备份原版 style.css -> style.css.bak ..." -ForegroundColor Gray
        Copy-Item $DstStyleCss $BakStyleCss -Force
    }

    Write-Host "[应用] 正在复制 html/main.js ..." -ForegroundColor Green
    Copy-Item $SrcMainJs $DstMainJs -Force

    Write-Host "[应用] 正在复制 html/style.css ..." -ForegroundColor Green
    Copy-Item $SrcStyleCss $DstStyleCss -Force

    # 同步 sim_server.py
    if (Test-Path $SimSrc) {
        $DstTools = Join-Path $TargetDir "tools"
        if (-not (Test-Path $DstTools)) { New-Item -ItemType Directory -Path $DstTools -Force | Out-Null }
        $DstSim = Join-Path $DstTools "sim_server.py"
        Write-Host "[同步] 正在同步 tools/sim_server.py ..." -ForegroundColor Green
        Copy-Item $SimSrc $DstSim -Force
    }

    Write-Host ""
    Write-Host "[成功] Argon 现代双主题已成功应用到目标仓库！" -ForegroundColor Green
    Write-Host "官方原版文件已安全保存在 html/*.bak 中。" -ForegroundColor Cyan
    Write-Host ""
}

function Do-GitApply {
    Write-Host ""
    if (-not (Test-Path $PatchFile)) {
        Write-Host "[错误] 未找到补丁文件: $PatchFile" -ForegroundColor Red
        return
    }

    Push-Location $TargetDir
    try {
        Write-Host "正在检查 Git 补丁兼容性..." -ForegroundColor Cyan
        git apply --check $PatchFile 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "正在应用 Git 补丁..." -ForegroundColor Cyan
            git apply $PatchFile
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "[成功] Git 补丁应用成功！" -ForegroundColor Green
            } else {
                Write-Host ""
                Write-Host "[失败] Git 补丁应用失败。" -ForegroundColor Red
            }
        } else {
            Write-Host "[提示] 直接检测有微小差异，尝试 3-way merge 自动合并模式..." -ForegroundColor Yellow
            git apply -3 $PatchFile
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "[成功] 通过 3-way merge 成功合入补丁！" -ForegroundColor Green
            } else {
                Write-Host ""
                Write-Host "[失败] 补丁存在冲突。建议选择菜单 1 进行直接覆盖应用。" -ForegroundColor Red
            }
        }

        if (Test-Path $SimSrc) {
            $DstTools = Join-Path $TargetDir "tools"
            if (-not (Test-Path $DstTools)) { New-Item -ItemType Directory -Path $DstTools -Force | Out-Null }
            Copy-Item $SimSrc (Join-Path $DstTools "sim_server.py") -Force
        }
    } finally {
        Pop-Location
    }
    Write-Host ""
}

function Do-Restore {
    Write-Host ""
    Write-Host "正在尝试还原官方原版..." -ForegroundColor Cyan
    $Restored = $false

    $DstMainJs = Join-Path $TargetDir "html\main.js"
    $DstStyleCss = Join-Path $TargetDir "html\style.css"
    $BakMainJs = "$DstMainJs.bak"
    $BakStyleCss = "$DstStyleCss.bak"

    if (Test-Path $BakMainJs) {
        Write-Host "正在从 main.js.bak 恢复..." -ForegroundColor Gray
        Copy-Item $BakMainJs $DstMainJs -Force
        Remove-Item $BakMainJs -Force
        $Restored = $true
    }

    if (Test-Path $BakStyleCss) {
        Write-Host "正在从 style.css.bak 恢复..." -ForegroundColor Gray
        Copy-Item $BakStyleCss $DstStyleCss -Force
        Remove-Item $BakStyleCss -Force
        $Restored = $true
    }

    if (-not $Restored) {
        Push-Location $TargetDir
        try {
            Write-Host "未找到 .bak 备份文件，尝试通过 Git 恢复官方原版..." -ForegroundColor Gray
            git checkout -- html/main.js html/style.css 2>$null
            if ($LASTEXITCODE -eq 0) {
                $Restored = $true
            }
        } finally {
            Pop-Location
        }
    }

    if ($Restored) {
        Write-Host ""
        Write-Host "[成功] 目标仓库已完全恢复为官方原生纯净状态！" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[提示] 未能找到任何原版备份或 Git 历史，未能执行还原。" -ForegroundColor Yellow
    }
    Write-Host ""
}

function Do-RunServer {
    Write-Host ""
    $ServerScript = Join-Path $TargetDir "tools\sim_server.py"
    if (-not (Test-Path $ServerScript)) {
        $ServerScript = $SimSrc
    }

    if (-not (Test-Path $ServerScript)) {
        Write-Host "[错误] 未找到 sim_server.py 仿真服务脚本！" -ForegroundColor Red
        return
    }

    Write-Host "正在启动本地模拟服务器 (端口 8088)..." -ForegroundColor Green
    Write-Host "提示: 可在弹出的终端窗口按 Ctrl+C 关闭仿真服务。" -ForegroundColor Gray
    Write-Host ""

    Start-Process -FilePath "python" -ArgumentList "`"$ServerScript`"" -WindowStyle Normal
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:8088/"
}

while ($true) {
    Show-Menu
    $Choice = Read-Host "请输入选项数字 [1-5]，默认为 1"
    if ([string]::IsNullOrWhiteSpace($Choice)) { $Choice = "1" }

    switch ($Choice) {
        "1" { Do-CopyApply }
        "2" { Do-GitApply }
        "3" { Do-Restore }
        "4" { Do-RunServer }
        "5" { 
            Write-Host "已退出。" -ForegroundColor Gray
            exit 0 
        }
        Default {
            Write-Host "[无效选项] 请重新输入。" -ForegroundColor Red
        }
    }
    Write-Host ""
}
