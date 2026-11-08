# One-click bootstrap: dependency consent, immutable application copy, existing installer.
[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'GitPublish'),
    [string]$BinDir = (Join-Path $HOME '.local\bin'),
    [switch]$NoPathUpdate
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
. (Join-Path $PSScriptRoot 'windows-common.ps1')

function Install-GpApplication {
    param([string]$SourceRoot, [string]$DestinationRoot, [string]$LauncherDir, $Dependencies,
        [switch]$SkipPathUpdate)
    $DestinationRoot = [IO.Path]::GetFullPath($DestinationRoot)
    Assert-GpPlainPath $DestinationRoot
    Assert-GpPlainPath $LauncherDir
    # A separate directory per attempt preserves all previous code/configuration.
    $release = Join-Path $DestinationRoot ('releases\5.0.1-' + [guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($release)
    $files = @('publish.py', 'installers\install.ps1', 'installers\windows-common.ps1')
    $files += @('__init__.py', 'cli.py', 'config.py', 'git.py', 'github.py',
        'security.py', 'file_picker.py', 'ui.py', 'clipboard.py') | ForEach-Object { 'src\gitpublish\' + $_ }
    foreach ($relative in $files) {
        $source = Join-Path $SourceRoot $relative
        Assert-GpPlainPath $source
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Thieu source: $relative" }
        $destination = Join-Path $release $relative
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
        Copy-Item -LiteralPath $source -Destination $destination
    }
    $state = [ordered]@{
        version = '5.0.1'; python = $Dependencies.Python.Path
        pythonVersion = [string]$Dependencies.Python.Version; pythonTested = $Dependencies.Python.Tested
        git = $Dependencies.Git.Path; gh = $Dependencies.Gh.Path
    } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $release 'install-state.json'), $state,
        (New-Object System.Text.UTF8Encoding($true)))
    & (Join-Path $release 'installers\install.ps1') -BinDir $LauncherDir -NoPathUpdate:$SkipPathUpdate `
        -PythonPath $Dependencies.Python.Path -GitPath $Dependencies.Git.Path -GhPath $Dependencies.Gh.Path
    Write-Host "Application: $release"
    Write-Host 'Mo Terminal moi va chay publish trong thu muc du an.'
    $release
}

function Invoke-GpSetup {
    if ($env:OS -ne 'Windows_NT') { throw 'Bo cai nay chi danh cho Windows.' }
    $dependencies = Resolve-GpDependencies
    Install-GpApplication -SourceRoot (Split-Path $PSScriptRoot -Parent) -DestinationRoot $InstallRoot `
        -LauncherDir $BinDir -Dependencies $dependencies -SkipPathUpdate:$NoPathUpdate
}

# Allow tests to dot-source functions without executing setup.
if ($MyInvocation.InvocationName -ne '.') {
    try { Invoke-GpSetup | Out-Host }
    catch { Write-Error $_; exit 1 }
}
