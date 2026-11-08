# Git Publish V5 - Windows installer
# Requires Windows PowerShell 5.1 or newer.
# Launchers use a process-only policy flag; User/Machine policy is unchanged.

[CmdletBinding()]
param(
    [string]$BinDir = (Join-Path $HOME ".local\bin"),
    [switch]$NoPathUpdate,
    [string]$PythonPath = "",
    [string]$GitPath = "",
    [string]$GhPath = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

if ($env:OS -ne "Windows_NT") {
    throw "Bo cai nay chi danh cho Windows."
}

$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

$Entry = Join-Path $ProjectRoot "publish.py"

if (-not (Test-Path -LiteralPath $Entry -PathType Leaf)) {
    throw "Khong tim thay publish.py."
}

Write-Host "======================================"
Write-Host " Git Publish V5 - Windows Installer"
Write-Host "======================================"

. (Join-Path $PSScriptRoot "windows-common.ps1")
$python = Get-GpPython -PreferredPath $PythonPath
if (-not $python) { throw "Can Python 3.11-3.15. Chay setup.cmd de cai dependency voi xac nhan." }
$PythonExe = $python.Path
if (-not $python.Tested) { Write-Warning "Python $($python.Version): CHUA KIEM THU; 3.15 chua cong bo ho tro." }
foreach ($toolName in @("git", "gh")) {
    $selectedPath = if ($toolName -eq "git") { $GitPath } else { $GhPath }
    if ($selectedPath) { $tool = Test-GpTool $toolName $selectedPath }
    else { $tool = (Get-GpTool $toolName).Tool }
    if (-not $tool) { throw "Can $toolName tuong thich. Chay setup.cmd." }
    if ($toolName -eq "git") { $GitPath = $tool.Path } else { $GhPath = $tool.Path }
}
Assert-GpPlainPath $BinDir

$BinDir = [System.IO.Path]::GetFullPath($BinDir)
if ($BinDir.Contains(";")) {
    throw "Thu muc launcher khong duoc chua dau cham phay (PATH)."
}

if ((Test-Path -LiteralPath $BinDir) -and
    ((Get-Item -LiteralPath $BinDir -Force).Attributes -band
        [System.IO.FileAttributes]::ReparsePoint)) {
    throw "Thu muc launcher la reparse point. Da dung."
}

New-Item `
    -ItemType Directory `
    -Force `
    -Path $BinDir |
    Out-Null

$CmdPath = Join-Path $BinDir "publish.cmd"
$PsPath = Join-Path $BinDir "publish-runner.ps1"
$LegacyPsPath = Join-Path $BinDir "publish.ps1"

$Stamp = [Guid]::NewGuid().ToString("N")
$Backups = @{}

foreach ($target in @($CmdPath, $PsPath, $LegacyPsPath)) {
    if (Test-Path -LiteralPath $target) {
        $item = Get-Item -LiteralPath $target -Force
        if ($item.PSIsContainer -or
            ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
            throw "Launcher cu khong phai file thong thuong. Da dung."
        }
        $backup = "$target.backup.$Stamp.$PID"

        Copy-Item `
            -LiteralPath $target `
            -Destination $backup
        $Backups[$target] = $backup

        Write-Host "Backup: $backup"
    }
}

# Escape single quotes for PowerShell literals.
$SafePython = $PythonExe.Replace("'", "''")
$SafeEntry = $Entry.Replace("'", "''")
$SafeGitDir = ([IO.Path]::GetDirectoryName($GitPath)).Replace("'", "''")
$SafeGhDir = ([IO.Path]::GetDirectoryName($GhPath)).Replace("'", "''")

$RunnerTemplate = @'
$ErrorActionPreference = "Stop"
$python = '{0}'
$entry = '{1}'
$env:Path = '{2};{3};' + $env:Path

& $python -X utf8 $entry @args
exit $LASTEXITCODE
'@

$Runner = $RunnerTemplate -f `
    $SafePython, $SafeEntry, $SafeGitDir, $SafeGhDir

$Utf8Bom = New-Object System.Text.UTF8Encoding($true)

$Cmd = @'
@echo off
setlocal DisableDelayedExpansion
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish-runner.ps1" %*
exit /b %errorlevel%
'@

# Update the current user's PATH, not the machine PATH.
$UserPath = [Environment]::GetEnvironmentVariable(
    "Path", "User"
)

$AlreadyInPath = $false

foreach ($segment in ($UserPath -split ";")) {
    $expanded = [Environment]::ExpandEnvironmentVariables($segment.Trim().Trim('"'))
    if ($expanded.TrimEnd("\") -ieq $BinDir.TrimEnd("\")) {
        $AlreadyInPath = $true
        break
    }
}

$PsTemporary = Join-Path $BinDir ".publish-$Stamp.ps1.tmp"
$CmdTemporary = Join-Path $BinDir ".publish-$Stamp.cmd.tmp"
$Installed = @()
$PathUpdated = $false

try {
    [System.IO.File]::WriteAllText($PsTemporary, $Runner, $Utf8Bom)
    [System.IO.File]::WriteAllText($CmdTemporary, $Cmd, [System.Text.Encoding]::ASCII)
    Move-Item -LiteralPath $PsTemporary -Destination $PsPath -Force
    $Installed += $PsPath
    Move-Item -LiteralPath $CmdTemporary -Destination $CmdPath -Force
    $Installed += $CmdPath
    if ($Backups.ContainsKey($LegacyPsPath)) {
        $Installed += $LegacyPsPath
        Remove-Item -LiteralPath $LegacyPsPath -Force
    }

if (-not $NoPathUpdate -and -not $AlreadyInPath) {
    if ([string]::IsNullOrWhiteSpace($UserPath)) {
        $NewPath = $BinDir
    }
    else {
        $NewPath = "$UserPath;$BinDir"
    }

    [Environment]::SetEnvironmentVariable(
        "Path",
        $NewPath,
        "User"
    )
    $PathUpdated = $true

    Write-Host "Da them launcher vao User PATH."
}

$ProcessHasPath = @($env:Path -split ";" | Where-Object {
    $_.Trim().Trim('"').TrimEnd("\") -ieq $BinDir.TrimEnd("\")
}).Count -gt 0
if (-not $NoPathUpdate -and -not $ProcessHasPath) {
    $env:Path += ";$BinDir"
}
}
catch {
    foreach ($target in $Installed) {
        if ($Backups.ContainsKey($target)) {
            Copy-Item -LiteralPath $Backups[$target] -Destination $target -Force
        }
        else {
            Remove-Item -LiteralPath $target -Force
        }
    }
    if ($PathUpdated) {
        [Environment]::SetEnvironmentVariable("Path", $UserPath, "User")
    }
    throw
}
finally {
    foreach ($temporary in @($PsTemporary, $CmdTemporary)) {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

Write-Host ""
Write-Host "CAI DAT HOAN THANH"
Write-Host "Launcher: $CmdPath"
Write-Host ""
Write-Host "Mo Terminal moi, vao thu muc du an va chay:"
Write-Host "    publish"
Write-Host ""
Write-Host "Neu chua dang nhap GitHub:"
Write-Host "    gh auth login"
Write-Host ""
Write-Host "Git Publish 5.0.1: hay xac minh CI Windows truoc phat hanh."
