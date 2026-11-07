# Git Publish V5 - Windows installer
# Requires Windows PowerShell 5.1 or newer.
# No execution-policy changes are made by this installer or its launchers.

[CmdletBinding()]
param(
    [string]$BinDir = (Join-Path $HOME ".local\bin"),
    [switch]$NoPathUpdate
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

foreach ($tool in @("git", "gh")) {
    $found = Get-Command `
        -Name $tool `
        -CommandType Application `
        -ErrorAction SilentlyContinue

    if (-not $found) {
        throw "Thieu $tool. Hay cai dat truoc."
    }

    Write-Host "OK: $tool"
}

$PythonExe = $null
$PrefixLiteral = "@()"

foreach ($candidate in @("py", "python3", "python")) {
    $command = Get-Command `
        -Name $candidate `
        -CommandType Application `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if (-not $command) {
        continue
    }

    $prefix = @()

    if ($candidate -eq "py") {
        $prefix = @("-3")
    }

    try {
        & $command.Source @prefix -c `
            "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" `
            *> $null

        if ($LASTEXITCODE -eq 0) {
            $PythonExe = $command.Source

            if ($candidate -eq "py") {
                $PrefixLiteral = '@("-3")'
            }

            break
        }
    }
    catch {
        continue
    }
}

if (-not $PythonExe) {
    throw "Yeu cau Python 3.10 tro len."
}

Write-Host "OK: Python 3"

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
$PsPath = Join-Path $BinDir "publish.ps1"

$Stamp = [Guid]::NewGuid().ToString("N")
$Backups = @{}

foreach ($target in @($CmdPath, $PsPath)) {
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

$RunnerTemplate = @'
$ErrorActionPreference = "Stop"
$python = '{0}'
$entry = '{1}'
$prefix = {2}

& $python @prefix -X utf8 $entry @args
exit $LASTEXITCODE
'@

$Runner = $RunnerTemplate -f `
    $SafePython, $SafeEntry, $PrefixLiteral

$Utf8Bom = New-Object System.Text.UTF8Encoding($true)

$Cmd = @'
@echo off
setlocal DisableDelayedExpansion
powershell.exe -NoProfile -File "%~dp0publish.ps1" %*
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
Write-Host "V5 RC: CHUA KIEM THU TREN WINDOWS thuc te."
