# Shared Windows dependency probes. Dot-sourcing this file performs no installation.
Set-StrictMode -Version 2.0

function Invoke-GpProcess {
    param([string]$File, [string[]]$Arguments = @(), [int]$TimeoutSeconds = 30)
    # ProcessStartInfo needs Windows command-line quoting on Windows PowerShell 5.1.
    $quoted = foreach ($argument in $Arguments) {
        '"' + [regex]::Replace([regex]::Replace($argument, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
    }
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $File
    $info.Arguments = $quoted -join ' '
    # Probes must never inherit repository redirection from the caller.
    foreach ($name in @('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR')) {
        $info.EnvironmentVariables.Remove($name)
    }
    $info.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $info.EnvironmentVariables['GH_PROMPT_DISABLED'] = '1'
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $info.StandardErrorEncoding = New-Object System.Text.UTF8Encoding($false)
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $process.Kill()
            throw "Timeout: $File"
        }
        [pscustomobject]@{ Code = $process.ExitCode; Output = $stdout.Result; Error = $stderr.Result }
    }
    finally { $process.Dispose() }
}

function Get-GpApplicationPaths {
    param([string[]]$Names)
    foreach ($name in $Names) {
        Get-Command -Name $name -CommandType Application -All -ErrorAction SilentlyContinue |
            ForEach-Object { $_.Source }
    }
}

function Get-GpPythonPaths {
    Get-GpApplicationPaths @('python', 'python3', 'python3.11', 'python3.12', 'python3.13', 'python3.14', 'python3.15')
    foreach ($launcher in @(Get-GpApplicationPaths @('py'))) {
        try {
            $listed = Invoke-GpProcess $launcher @('-0p')
            if ($listed.Code -eq 0) {
                foreach ($line in ($listed.Output -split "`r?`n")) {
                    if ($line -match '([A-Za-z]:\\.*?python(?:[0-9.]*)?\.exe)\s*$') { $Matches[1].Trim() }
                }
            }
        }
        catch { Write-Verbose $_ }
    }
    # PEP 514, per-user and machine, including 32-bit registrations.
    foreach ($root in @('HKCU:\Software\Python', 'HKLM:\Software\Python',
            'HKLM:\Software\WOW6432Node\Python', 'HKCU:\Software\WOW6432Node\Python')) {
        foreach ($company in @(Get-ChildItem -LiteralPath $root -ErrorAction SilentlyContinue)) {
            foreach ($tag in @(Get-ChildItem -LiteralPath $company.PSPath -ErrorAction SilentlyContinue)) {
                $key = Get-Item -LiteralPath ($tag.PSPath + '\InstallPath') -ErrorAction SilentlyContinue
                if ($key) {
                    $executable = $key.GetValue('ExecutablePath')
                    if ($executable) { $executable }
                    $directory = $key.GetValue('')
                    if ($directory) { Join-Path $directory 'python.exe' }
                }
            }
        }
    }
    foreach ($base in @($env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if ($base) {
            foreach ($pattern in @('Programs\Python\Python*\python.exe', 'Python*\python.exe')) {
                Get-Item -Path (Join-Path $base $pattern) -ErrorAction SilentlyContinue |
                    ForEach-Object { $_.FullName }
            }
        }
    }
}

function Test-GpPython {
    param([string]$Path)
    try {
        if (-not [IO.Path]::IsPathRooted($Path) -or $Path -match '\\WindowsApps\\') { return }
        $probe = 'import sys,json,os,subprocess,pathlib,hashlib,tempfile,urllib.parse,collections.abc; assert sys.version_info >= (3,11); print(json.dumps(dict(path=os.path.realpath(sys.executable),version=list(sys.version_info[:3]),release=sys.version_info.releaselevel)))'
        $result = Invoke-GpProcess $Path @('-I', '-X', 'utf8', '-c', $probe)
        if ($result.Code -ne 0) { return }
        $data = $result.Output | ConvertFrom-Json
        $version = [version]($data.version -join '.')
        if ($version.Major -ne 3 -or $version.Minor -lt 11 -or $version.Minor -gt 15 -or
                $data.release -ne 'final' -or -not [IO.Path]::IsPathRooted($data.path)) { return }
        # Evidence: the released V5 Windows CI used 3.14. Other minors need new CI evidence.
        [pscustomobject]@{ Path = $data.path; Version = $version; Tested = ($version.Minor -eq 14) }
    }
    catch { Write-Verbose "Python probe failed: $Path" }
}

function Get-GpPython {
    param([string]$PreferredPath = '')
    if ($PreferredPath) {
        $selected = Test-GpPython $PreferredPath
        if (-not $selected) { throw "Python da chon khong chay duoc hoac ngoai muc tieu 3.11-3.15: $PreferredPath" }
        return $selected
    }
    $candidates = @(foreach ($path in @(Get-GpPythonPaths | Sort-Object -Unique)) {
        Test-GpPython $path
    })
    $candidates | Sort-Object -Property @{ Expression = { $_.Tested }; Descending = $true },
        @{ Expression = { $_.Version }; Descending = $true }, Path | Select-Object -First 1
}

function Get-GpToolPaths {
    param([string]$Name)
    Get-GpApplicationPaths @($Name)
    $relative = if ($Name -eq 'git') { 'Git\cmd\git.exe' } else { 'GitHub CLI\gh.exe' }
    foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if ($base) { Join-Path $base $relative }
    }
    if ($env:LOCALAPPDATA) {
        Join-Path $env:LOCALAPPDATA ('Programs\' + $relative)
        Join-Path $env:LOCALAPPDATA ('Microsoft\WinGet\Links\' + $Name + '.exe')
    }
}

function Test-GpTool {
    param([string]$Name, [string]$Path)
    try {
        if (-not [IO.Path]::IsPathRooted($Path) -or [IO.Path]::GetDirectoryName($Path).Contains(';')) { return }
        $result = Invoke-GpProcess $Path @('--version')
        if ($result.Code -ne 0 -or $result.Output -notmatch '(\d+\.\d+(?:\.\d+)?)') { return }
        $version = [version]$Matches[1]
        if ($Name -eq 'git') {
            if ($version -lt [version]'2.23') { return }
            # Probe actual branch/pathspec/staging features in an isolated empty repository.
            $temporary = Join-Path ([IO.Path]::GetTempPath()) ('gitpublish-probe-' + [guid]::NewGuid().ToString('N'))
            try {
                $commands = @(
                    @('init', '--quiet', $temporary),
                    @('-C', $temporary, 'branch', '--show-current'),
                    @('-C', $temporary, 'add', '-A', '--', ':(literal)probe.txt'),
                    @('-C', $temporary, 'diff', '--cached', '--name-status', '--no-renames', '-z'),
                    @('-C', $temporary, 'ls-files', '-z', '--cached'))
                foreach ($arguments in $commands) {
                    $check = Invoke-GpProcess $Path $arguments
                    if ($check.Code -ne 0) { return }
                    if ($arguments[0] -eq 'init') {
                        [IO.File]::WriteAllText((Join-Path $temporary 'probe.txt'), 'offline feature probe')
                    }
                }
                $merge = Invoke-GpProcess $Path @('merge', '-h')
                if (($merge.Output + $merge.Error) -notmatch 'overwrite-ignore') { return }
            }
            finally {
                if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Recurse -Force }
            }
        }
        else {
            # Help is offline: no auth, repository creation, or API request.
            foreach ($spec in @(
                @{ Args = @('api', '--help'); Flags = @('--jq') },
                @{ Args = @('repo', 'create', '--help'); Flags = @('--private', '--public') },
                @{ Args = @('repo', 'view', '--help'); Flags = @('--json') },
                @{ Args = @('auth', 'status', '--help'); Flags = @('status') })) {
                $help = Invoke-GpProcess $Path $spec.Args
                if ($help.Code -ne 0) { return }
                foreach ($flag in $spec.Flags) {
                    if (-not ($help.Output + $help.Error).Contains($flag)) { return }
                }
            }
        }
        [pscustomobject]@{ Path = [IO.Path]::GetFullPath($Path); Version = $version; Name = $Name }
    }
    catch { Write-Verbose "Dependency probe failed: $Path" }
}

function Get-GpTool {
    param([string]$Name)
    $paths = @(Get-GpToolPaths $Name | Sort-Object -Unique | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
    foreach ($path in $paths) {
        $tool = Test-GpTool $Name $path
        if ($tool) { return [pscustomobject]@{ Name = $Name; State = 'compatible'; Tool = $tool } }
    }
    $state = if ($paths.Count) { 'incompatible' } else { 'missing' }
    [pscustomobject]@{ Name = $Name; State = $state; Tool = $null }
}

function Confirm-GpChange {
    param([string]$Message)
    (Read-Host "$Message [y/N]") -match '^(?i:y|yes)$'
}

function Update-GpProcessPath {
    # Preserve runner/venv PATH entries; pick up newly installed per-user tools.
    $env:Path = $env:Path + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') +
        ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
}

function Install-GpDependency {
    param([string]$Winget, [string]$Id, [string]$Action)
    $arguments = @($Action, '--id', $Id, '--exact', '--source', 'winget',
        '--accept-source-agreements', '--accept-package-agreements', '--disable-interactivity')
    if ($Id -like 'Python.Python.*') { $arguments += @('--scope', 'user', '--no-upgrade') }
    $result = Invoke-GpProcess $Winget $arguments 900
    if ($result.Code -ne 0) {
        throw "winget $Action $Id that bai (exit $($result.Code)). Kiem tra mang/nguon winget va chay lai setup.cmd. Khong go/ha cap dependency."
    }
    Update-GpProcessPath
}

function Resolve-GpDependencies {
    $python = Get-GpPython
    $git = Get-GpTool 'git'
    $gh = Get-GpTool 'gh'
    $winget = @(Get-GpApplicationPaths @('winget') | Select-Object -First 1)
    $wingetPath = $null
    if ($winget.Count) {
        try {
            $probe = Invoke-GpProcess $winget[0] @('--version')
            if ($probe.Code -eq 0 -and $probe.Output -match 'v?\d+\.\d+') { $wingetPath = $winget[0] }
        }
        catch { Write-Verbose $_ }
    }
    $pythonState = if ($python) { "$($python.Version), $($python.Path)" } else { 'missing compatible Python 3.11-3.15' }
    Write-Host "Python: $pythonState"
    Write-Host "Git: $($git.State) $($git.Tool)"
    Write-Host "gh: $($gh.State) $($gh.Tool)"
    Write-Host "winget available: $([bool]$wingetPath)"
    $changes = @()
    if (-not $python) { $changes += @{ Id = 'Python.Python.3.14'; Action = 'install' } }
    foreach ($tool in @($git, $gh)) {
        if ($tool.State -ne 'compatible') {
            $id = if ($tool.Name -eq 'git') { 'Git.Git' } else { 'GitHub.cli' }
            $action = if ($tool.State -eq 'missing') { 'install' } else { 'upgrade' }
            $changes += @{ Id = $id; Action = $action }
        }
    }
    if ($changes.Count -and -not $wingetPath) {
        throw 'Thieu winget hoat dong. Cai/cap nhat App Installer tu Microsoft Store: https://aka.ms/getwinget ; huong dan: https://learn.microsoft.com/windows/package-manager/winget/ . Sau do chay lai setup.cmd. Hoac cai Python/Git/gh thu cong tu python.org, git-scm.com, cli.github.com.'
    }
    # Obtain all approvals before the first package modification.
    foreach ($change in $changes) {
        if (-not (Confirm-GpChange "Cho phep winget $($change.Action) $($change.Id) tu nguon winget chinh thuc (chap nhan dieu khoan goi/nguon)?")) {
            throw "Da huy: dependency $($change.Id) chua tuong thich. Chua cai/cap nhat goi nao; publish can day du Python, Git va gh."
        }
    }
    foreach ($change in $changes) { Install-GpDependency $wingetPath $change.Id $change.Action }
    # Verify every dependency again; never trust the package manager exit code alone.
    $python = Get-GpPython
    $git = Get-GpTool 'git'
    $gh = Get-GpTool 'gh'
    if (-not $python -or $git.State -ne 'compatible' -or $gh.State -ne 'compatible') {
        throw 'Xac minh sau cai dat that bai. Kiem tra dependency va chay lai setup.cmd; launcher cu duoc giu nguyen.'
    }
    if (-not $python.Tested) {
        Write-Warning "Python $($python.Version): CHUA KIEM THU Windows voi Git Publish. 3.15 la thu nghiem, chua cong bo ho tro."
    }
    [pscustomobject]@{ Python = $python; Git = $git.Tool; Gh = $gh.Tool }
}

function Assert-GpPlainPath {
    param([string]$Path)
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $current" }
        }
        $parent = [IO.Path]::GetDirectoryName($current)
        if ($parent -eq $current) { break }
        $current = $parent
    }
}
