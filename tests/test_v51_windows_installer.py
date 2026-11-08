"""Windows setup tests: mocked package operations, never real system installs.

Behavioral tests execute PowerShell when available; Windows CI runs both shells.
Ubuntu without PowerShell reports these cases as skipped, not verified.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / 'installers/windows-common.ps1'
SETUP = ROOT / 'installers/setup-windows.ps1'


def test_setup_is_packaged_and_uses_only_process_policy():
    setup = (ROOT / 'setup.cmd').read_text()
    assert 'DisableDelayedExpansion' in setup
    assert '"%~dp0installers\\setup-windows.ps1"' in setup
    assert '-ExecutionPolicy Bypass' in setup
    for path in (COMMON, SETUP, ROOT / 'installers/install.ps1'):
        assert 'Set-ExecutionPolicy' not in path.read_text()
    source = COMMON.read_text()
    assert "'Python.Python.3.14'" in source
    assert "'Git.Git'" in source and "'GitHub.cli'" in source
    assert "'--source', 'winget'" in source
    assert "'--no-upgrade'" in source
    assert 'auth login' not in source


@pytest.fixture(params=['powershell', 'pwsh'])
def ps(request):
    if os.name != 'nt':
        pytest.skip('Windows dependency mocks require Windows path semantics')
    shell = shutil.which(request.param)
    if not shell:
        pytest.skip(f'{request.param} unavailable; mocked Windows behavior NOT TESTED')
    return shell


def run_ps(ps, tmp_path, body):
    script = tmp_path / 'mock scenario.ps1'
    script.write_text(
        "$ErrorActionPreference = 'Stop'\n"
        ". $env:GP_COMMON\n"
        "function Assert($condition, $message = 'assertion failed') { if (-not $condition) { throw $message } }\n"
        + body, encoding='utf-8-sig')
    result = subprocess.run(
        [ps, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
        env={**os.environ, 'GP_COMMON': str(COMMON), 'GP_SETUP': str(SETUP), 'GP_SOURCE': str(ROOT), 'GP_PYTHON': sys.executable},
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


# Fake every OS/package-manager boundary before running dependency orchestration.
MOCKS = r'''
$script:installs = @()
$script:approvals = @()
$script:pythonMissing = $false
$script:gitState = 'compatible'
$script:ghState = 'compatible'
$script:wingetMissing = $false
$script:refuse = $false
$script:failInstall = $false
$script:verifyFail = $false
$script:phase = 0
function Get-GpPython {
    if ($script:pythonMissing -and ($script:phase -eq 0 -or $script:verifyFail)) { return }
    [pscustomobject]@{ Path = 'C:\Python314\python.exe'; Version = [version]'3.14.4'; Tested = $true }
}
function Get-GpTool($Name) {
    $state = if ($Name -eq 'git') { $script:gitState } else { $script:ghState }
    if ($script:phase -gt 0 -and -not $script:verifyFail) { $state = 'compatible' }
    [pscustomobject]@{ Name = $Name; State = $state; Tool = [pscustomobject]@{ Path = "C:\Tools\$Name.exe"; Version = [version]'99.1' } }
}
function Get-GpApplicationPaths($Names) { if (-not $script:wingetMissing) { 'C:\winget.exe' } }
function Invoke-GpProcess { [pscustomobject]@{ Code = 0; Output = 'v1.12'; Error = '' } }
function Confirm-GpChange($Message) { $script:approvals += $Message; -not $script:refuse }
function Install-GpDependency($Winget, $Id, $Action) {
    $script:installs += "$Action/$Id"
    if ($script:failInstall) { throw 'offline winget error' }
    $script:phase = 1
}
'''


@pytest.mark.parametrize('scenario,arrange,expected', [
    ('ready', '', []),
    ('python missing', '$script:pythonMissing = $true', ['install/Python.Python.3.14']),
    ('git missing', "$script:gitState = 'missing'", ['install/Git.Git']),
    ('gh missing', "$script:ghState = 'missing'", ['install/GitHub.cli']),
    ('git incompatible', "$script:gitState = 'incompatible'", ['upgrade/Git.Git']),
    ('gh incompatible', "$script:ghState = 'incompatible'", ['upgrade/GitHub.cli']),
    ('all missing', "$script:pythonMissing = $true; $script:gitState = 'missing'; $script:ghState = 'missing'",
     ['install/Python.Python.3.14', 'install/Git.Git', 'install/GitHub.cli']),
    ('winget unnecessary', '$script:wingetMissing = $true', []),
])
def test_dependency_plan(ps, tmp_path, scenario, arrange, expected):
    expected_ps = ','.join("'" + value + "'" for value in expected)
    run_ps(ps, tmp_path, MOCKS + arrange + f'''
$result = Resolve-GpDependencies
Assert ($result.Python.Path -eq 'C:\\Python314\\python.exe')
Assert (($script:installs -join ',') -eq (@({expected_ps}) -join ',')) '{scenario}'
Assert ($script:approvals.Count -eq $script:installs.Count)
''')


@pytest.mark.parametrize('arrange,install_count,message', [
    ('$script:pythonMissing = $true; $script:refuse = $true', 0, 'Da huy'),
    ('$script:pythonMissing = $true; $script:wingetMissing = $true', 0, 'App Installer'),
    ('$script:pythonMissing = $true; $script:failInstall = $true', 1, 'offline winget'),
    ('$script:pythonMissing = $true; $script:verifyFail = $true', 1, 'Xac minh'),
])
def test_dependency_failures_stop_safely(ps, tmp_path, arrange, install_count, message):
    run_ps(ps, tmp_path, MOCKS + arrange + f'''
$caught = $false
try {{ Resolve-GpDependencies | Out-Null }} catch {{ $caught = $true; Assert ($_.Exception.Message.Contains('{message}')) $_ }}
Assert $caught
Assert ($script:installs.Count -eq {install_count})
''')


@pytest.mark.parametrize('versions,expected', [
    (['3.11.9', '3.13.2', '3.14.4'], '3.14.4'),
    (['3.15.0', '3.14.4'], '3.14.4'),
    (['3.11.9', '3.13.2'], '3.13.2'),
    (['3.15.0'], '3.15.0'),
    (['3.16.0', '3.10.9'], None),
])
def test_python_selection_checks_real_probe_results(ps, tmp_path, versions, expected):
    # Real Test-GpPython + sorting, only discovery/process execution mocked.
    mapping = {f'C:\\Python{i}\\python.exe': version for i, version in enumerate(versions)}
    run_ps(ps, tmp_path, '''
$script:versions = ConvertFrom-Json @'
''' + json.dumps(mapping) + '''
'@
function Get-GpPythonPaths { $script:versions.PSObject.Properties.Name }
function Invoke-GpProcess($File, $Arguments) {
    Assert ($Arguments -contains '-I')
    $version = $script:versions.$File.Split('.') | ForEach-Object { [int]$_ }
    [pscustomobject]@{ Code = 0; Error = ''; Output = (@{ path = $File; version = @($version); release = 'final' } | ConvertTo-Json -Compress) }
}
$result = Get-GpPython
''' + (f"Assert ([string]$result.Version -eq '{expected}')\n" if expected else 'Assert ($null -eq $result)\n')
        + ("Assert (-not $result.Tested)\n" if expected == '3.15.0' else ''))


@pytest.mark.parametrize('code,release', [(1, 'final'), (0, 'alpha')])
def test_python_broken_or_prerelease_rejected(ps, tmp_path, code, release):
    run_ps(ps, tmp_path, f'''
function Invoke-GpProcess {{ [pscustomobject]@{{ Code = {code}; Output = '{{"path":"C:\\\\Python\\\\python.exe","version":[3,15,0],"release":"{release}"}}'; Error = '' }} }}
Assert ($null -eq (Test-GpPython 'C:\\Python\\python.exe'))
''')


def test_winget_exact_commands_and_failure(ps, tmp_path):
    run_ps(ps, tmp_path, r'''
$script:calls = @()
$script:fail = $false
function Invoke-GpProcess($File, $Arguments, $TimeoutSeconds) {
    $script:calls += ,$Arguments
    [pscustomobject]@{ Code = $(if ($script:fail) { 1 } else { 0 }); Output = ''; Error = 'network failure' }
}
function Update-GpProcessPath {}
Install-GpDependency 'mock-winget' 'Python.Python.3.14' 'install'
Install-GpDependency 'mock-winget' 'Git.Git' 'upgrade'
Assert ($script:calls[0] -contains '--no-upgrade')
Assert ($script:calls[0] -contains 'user')
Assert ($script:calls[1][0] -eq 'upgrade')
Assert (-not ($script:calls[1] -contains '--no-upgrade'))
foreach ($argsList in $script:calls) {
    Assert ($argsList -contains '--exact')
    Assert ($argsList -contains 'winget')
    Assert (-not ($argsList -contains '--all'))
}
$script:fail = $true
$caught = $false
try { Install-GpDependency 'mock-winget' 'GitHub.cli' 'install' } catch { $caught = $true }
Assert $caught
''')


def test_install_twice_unicode_preserves_old_data_and_pins_python(ps, tmp_path):
    if os.name != 'nt':
        pytest.skip('Windows paths and native launchers required')
    run_ps(ps, tmp_path, r'''
. $env:GP_SETUP
$work = Join-Path $PSScriptRoot "ứng dụng có khoảng trắng [1] 'quote"
$bin = Join-Path $work 'bin'
$root = Join-Path $work 'stable'
[void][IO.Directory]::CreateDirectory($root)
[void][IO.Directory]::CreateDirectory($bin)
[IO.File]::WriteAllText((Join-Path $root 'config.json'), 'old config')
[IO.File]::WriteAllText((Join-Path $bin 'publish.ps1'), 'old launcher')
$python = Get-GpPython -PreferredPath $env:GP_PYTHON
Assert ($null -ne $python)
$dependencies = [pscustomobject]@{ Python = $python; Git = (Get-GpTool 'git').Tool; Gh = (Get-GpTool 'gh').Tool }
Assert ($null -ne $dependencies.Git)
Assert ($null -ne $dependencies.Gh)
$first = Install-GpApplication $env:GP_SOURCE $root $bin $dependencies -SkipPathUpdate
$second = Install-GpApplication $env:GP_SOURCE $root $bin $dependencies -SkipPathUpdate
Assert ($first -ne $second)
Assert (Test-Path -LiteralPath (Join-Path $first 'publish.py'))
Assert ([IO.File]::ReadAllText((Join-Path $root 'config.json')) -eq 'old config')
Assert (-not (Test-Path -LiteralPath (Join-Path $bin 'publish.ps1')))
Assert (@(Get-ChildItem -LiteralPath $bin -Filter 'publish.ps1.backup.*').Count -eq 1)
$runner = Join-Path $bin 'publish-runner.ps1'
$text = [IO.File]::ReadAllText($runner)
Assert ($text.Contains($python.Path.Replace("'", "''")))
Assert (-not $text.Contains('py -3'))
$state = Get-Content -LiteralPath (Join-Path $second 'install-state.json') -Raw | ConvertFrom-Json
Assert ($state.python -eq $python.Path)
# A harmless entry proves actual interpreter selection/argument forwarding/exit code.
[IO.File]::WriteAllText((Join-Path $second 'publish.py'), "import sys`nprint(sys.executable)`nprint(sys.argv[1])`nsys.exit(7)`n", (New-Object Text.UTF8Encoding($false)))
$launch = Invoke-GpProcess 'powershell.exe' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $runner, 'đối số có khoảng trắng')
Assert ($launch.Code -eq 7) $launch.Error
Assert ($launch.Output.Contains($python.Path))
Assert ($launch.Output.Contains('đối số có khoảng trắng'))
''')


def test_py_launcher_and_registry_discovery(ps, tmp_path):
    run_ps(ps, tmp_path, r'''
function Get-GpApplicationPaths($Names) { if ($Names -contains 'py') { 'C:\py.exe' } }
function Invoke-GpProcess($File, $Arguments) {
    Assert ($Arguments[0] -eq '-0p')
    [pscustomobject]@{ Code = 0; Output = " -V:3.14 * C:\Python có khoảng trắng\python.exe`n -V:3.15 C:\Python315\python.exe"; Error = '' }
}
function Get-ChildItem {
    param($LiteralPath, $ErrorAction)
    if ($LiteralPath -eq 'HKCU:\Software\Python') { [pscustomobject]@{ PSPath = 'mock-company' } }
    if ($LiteralPath -eq 'mock-company') { [pscustomobject]@{ PSPath = 'mock-tag' } }
}
function Get-Item {
    param($LiteralPath, $Path, $ErrorAction)
    if ($LiteralPath -eq 'mock-tag\InstallPath') {
        $key = New-Object PSObject
        $key | Add-Member ScriptMethod GetValue { param($name) if ($name -eq 'ExecutablePath') { 'C:\Registry Python\python.exe' } }
        $key
    }
}
$paths = @(Get-GpPythonPaths)
Assert ($paths -contains 'C:\Python có khoảng trắng\python.exe')
Assert ($paths -contains 'C:\Python315\python.exe')
Assert ($paths -contains 'C:\Registry Python\python.exe')
''')


@pytest.mark.parametrize('broken', [False, True])
def test_future_gh_version_requires_actual_features(ps, tmp_path, broken):
    run_ps(ps, tmp_path, r'''
function Invoke-GpProcess($File, $Arguments) {
    if ($Arguments[0] -eq '--version') { $output = 'gh version 99.0.0' }
    else { $output = '--jq --private --public --json status' }
''' + ("    if ($Arguments[0] -eq 'api') { $output = 'old api with no jq' }\n" if broken else '') + r'''
    [pscustomobject]@{ Code = 0; Output = $output; Error = '' }
}
$tool = Test-GpTool 'gh' 'C:\Tools\gh.exe'
''' + ('Assert ($null -eq $tool)' if broken else "Assert ($tool.Version -eq [version]'99.0.0')"))


def test_all_permissions_precede_any_install(ps, tmp_path):
    run_ps(ps, tmp_path, MOCKS + r'''
$script:pythonMissing = $true
$script:gitState = 'missing'
function Confirm-GpChange($Message) {
    $script:approvals += $Message
    Assert ($script:installs.Count -eq 0)
    return $script:approvals.Count -lt 2
}
$caught = $false
try { Resolve-GpDependencies | Out-Null } catch { $caught = $true }
Assert $caught
Assert ($script:installs.Count -eq 0)
''')
