<#
.SYNOPSIS
    安全退出移动硬盘 - 自动关闭关联进程后弹出磁盘
.DESCRIPTION
    检测占用移动硬盘的进程，提供关闭选项，然后安全弹出
    用法: 双击 .bat 文件运行，或 PowerShell .\安全退出移动硬盘.ps1
#>

param(
    [string]$DriveLetter = ""
)

function Get-RemovableDrives {
    Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 }
}

function Get-ProcessesUsingDrive {
    param([string]$Drive)
    $results = @()
    Get-Process | ForEach-Object {
        try {
            $_.Modules | ForEach-Object {
                if ($_.FileName -like "$Drive*") {
                    $results += [PSCustomObject]@{
                        PID = $_.ProcessId
                        Process = $_.ProcessName
                        File = $_.FileName
                    }
                }
            }
        } catch {}
    }
    $results | Sort-Object Process -Unique
}

function Eject-Drive {
    param([string]$Drive)
    try {
        $shell = New-Object -ComObject Shell.Application
        $folder = $shell.Namespace(17)
        $item = $folder.ParseName("$Drive\\")
        if ($item) {
            $item.InvokeVerb("Eject")
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

# ---- MAIN ----
$host.UI.RawUI.WindowTitle = "安全退出移动硬盘"

$drives = Get-RemovableDrives
if ($drives.Count -eq 0) {
    Write-Host "未检测到可移动磁盘。" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

if ([string]::IsNullOrEmpty($DriveLetter)) {
    Write-Host "`n检测到以下可移动磁盘：" -ForegroundColor Cyan
    $i = 1
    $drives | ForEach-Object {
        $size = [math]::Round($_.Size / 1GB, 1)
        $free = [math]::Round($_.FreeSpace / 1GB, 1)
        $label = if ([string]::IsNullOrWhiteSpace($_.VolumeName)) { "(无卷标)" } else { $_.VolumeName }
        Write-Host (" [{0}] {1}  [{2}G / {3}G]  {4}") -f $i, $_.DeviceID, $free, $size, $label
        $i++
    }
    $sel = Read-Host "`n请选择要退出的磁盘编号"
    $target = $drives[[int]$sel - 1].DeviceID
} else {
    $target = $DriveLetter.ToUpper() + ":"
}

Write-Host ("`n选定磁盘: {0}") -f $target -ForegroundColor Yellow

# 检测占用进程
Write-Host "正在查找占用进程..." -NoNewline
$procs = Get-ProcessesUsingDrive -Drive $target
Write-Host "完成" -ForegroundColor Green

if ($procs.Count -gt 0) {
    Write-Host ("找到 {0} 个占用进程！") -f $procs.Count -ForegroundColor Red
    $procs | Format-Table PID, Process, File -AutoSize

    $ans = Read-Host "`n是否关闭这些进程? (y/n, 默认y)"
    if ($ans -ne "n") {
        $procs.PID | Select-Object -Unique | ForEach-Object {
            try { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } catch {}
        }
        Write-Host "进程已关闭。" -ForegroundColor Green
        Start-Sleep -Milliseconds 800
    }
} else {
    Write-Host "未找到占用进程，可直接安全退出。" -ForegroundColor Green
}

# 执行弹出
Write-Host "正在安全退出磁盘..." -NoNewline
$result = Eject-Drive -Drive $target
if ($result) {
    Write-Host "弹出成功！" -ForegroundColor Green
    Write-Host ("`n磁盘 {0} 可以安全拔出了。") -f $target -ForegroundColor Cyan
} else {
    Write-Host "弹出失败。" -ForegroundColor Red
    Write-Host "请手动：右键系统托盘 USB 图标 -> 弹出" -ForegroundColor Yellow
}

Read-Host "`n按回车退出"
