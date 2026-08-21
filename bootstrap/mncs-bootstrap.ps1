# Minimal Windows bootstrap shim. Discovers Python before the richer mncs CLI.
# SPDX-License-Identifier: Apache-2.0

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsRemaining
)

$json = $ArgsRemaining -contains "--json"

function Emit-Message {
    param($Message, $PythonState, $Ok)
    if ($json) {
        $payload = @{
            ok = [bool]$Ok
            python = $PythonState
            message = $Message
            disclaimer = "This shim is operational only. It is not MNCS conformance, certification, or promotion."
        } | ConvertTo-Json -Compress
        Write-Output $payload
    }
    else {
        Write-Output $Message
    }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    Emit-Message "Python 3.11+ is not installed. Install Python, then re-run this shim or pip install the MNCS validator." "missing" $false
    exit 14
}

$mncs = Get-Command mncs -ErrorAction SilentlyContinue
if ($mncs) {
    & mncs bootstrap @ArgsRemaining
    exit $LASTEXITCODE
}

$here = Split-Path -Parent $PSScriptRoot
$cli = Join-Path $here "src\mncs_validator\cli.py"
if (Test-Path $cli) {
    $env:PYTHONPATH = (Join-Path $here "src") + $(if ($env:PYTHONPATH) { ";" + $env:PYTHONPATH } else { "" })
    & $python.Source -m mncs_validator bootstrap @ArgsRemaining
    exit $LASTEXITCODE
}

Emit-Message "Python is available, but the mncs CLI is not installed. pip install the MNCS validator, then re-run." "available" $false
exit 10
