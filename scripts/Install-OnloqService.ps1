# Onloq Service Installation Script for Windows
# This PowerShell script sets up Onloq to run automatically at startup

param(
    [string]$InstallPath = (Get-Location).Path,
    [string]$SummaryTime = "20:00",
    [switch]$Force
)

Write-Host "🔧 Setting up Onloq for automatic operation..." -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "⚠️  This script requires administrator privileges for Task Scheduler access." -ForegroundColor Yellow
    Write-Host "💡 Re-run as administrator or use the manual startup method." -ForegroundColor Yellow
}

# Create startup task
$taskName = "OnloqAutoLogger"
$pythonPath = (Get-Command python).Source
$scriptPath = Join-Path $InstallPath "main.py"
$workingDir = $InstallPath

Write-Host "📁 Install path: $InstallPath" -ForegroundColor Green
Write-Host "🐍 Python path: $pythonPath" -ForegroundColor Green
Write-Host "⏰ Summary time: $SummaryTime" -ForegroundColor Green

# Configure auto-summarization
Write-Host "🤖 Configuring auto-summarization..." -ForegroundColor Yellow
& python "$scriptPath" auto --enable --time $SummaryTime

if ($isAdmin) {
    # Remove existing task if it exists
    if ($Force -or (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) {
        Write-Host "🗑️  Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    }

    # Create new scheduled task
    Write-Host "📅 Creating scheduled task..." -ForegroundColor Yellow
    
    $action = New-ScheduledTaskAction -Execute $pythonPath -Argument "$scriptPath run --daemon" -WorkingDirectory $workingDir
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    $task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Onloq Privacy-First Activity Logger"
    
    Register-ScheduledTask -TaskName $taskName -InputObject $task

    Write-Host "✅ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host "🚀 Onloq will start automatically at login" -ForegroundColor Green
} else {
    # Create startup registry entry (user-level)
    Write-Host "📝 Adding to user startup..." -ForegroundColor Yellow
    
    $startupPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    $command = "`"$pythonPath`" `"$scriptPath`" run --daemon"
    
    Set-ItemProperty -Path $startupPath -Name "Onloq" -Value $command
    
    Write-Host "✅ Added to user startup registry!" -ForegroundColor Green
    Write-Host "🚀 Onloq will start automatically at login" -ForegroundColor Green
}

# Create quick access shortcuts
Write-Host "🔗 Creating shortcuts..." -ForegroundColor Yellow

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Onloq Status.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonPath
$shortcut.Arguments = "`"$scriptPath`" status"
$shortcut.WorkingDirectory = $InstallPath
$shortcut.Description = "Check Onloq Status"
$shortcut.Save()

Write-Host "🖥️  Desktop shortcut created: Onloq Status.lnk" -ForegroundColor Green

# Test notification system
Write-Host "🔔 Testing notification system..." -ForegroundColor Yellow
& python "$scriptPath" notify --test

Write-Host ""
Write-Host "🎉 Onloq automation setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 What happens next:" -ForegroundColor Cyan
Write-Host "   • Onloq will start automatically at login" -ForegroundColor White
Write-Host "   • Daily summaries will be generated at $SummaryTime" -ForegroundColor White
Write-Host "   • Desktop notifications will alert you when summaries are ready" -ForegroundColor White
Write-Host "   • All data stays private on your machine" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Quick commands:" -ForegroundColor Cyan
Write-Host "   • Check status: python main.py status" -ForegroundColor White
Write-Host "   • View schedule: python main.py schedule" -ForegroundColor White
Write-Host "   • Manual summary: python main.py summarize" -ForegroundColor White
Write-Host ""
Write-Host "🔄 To start now, run: python main.py run" -ForegroundColor Yellow
