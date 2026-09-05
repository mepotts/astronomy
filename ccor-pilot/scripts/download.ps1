$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Fixed allowlist: never interpret an empty fits.json as successful no-data.
$pilotRoot = Split-Path -Parent $PSScriptRoot
$rawRoot = Join-Path $pilotRoot 'data/raw'
$ledgerPath = Join-Path $pilotRoot 'data/download-ledger.json'
if (Test-Path -LiteralPath $ledgerPath) {
    throw 'Download ledger already exists; this single frozen attempt is not overwriteable.'
}
New-Item -ItemType Directory -Force -Path $rawRoot | Out-Null
$files = @(
    'CCOR2_1A_20260901T130014_V00_NC.fits',
    'CCOR2_1A_20260901T131514_V00_NC.fits',
    'CCOR2_1A_20260901T133014_V00_NC.fits',
    'CCOR2_1A_20260901T134514_V00_NC.fits'
)
foreach ($name in $files) {
    if (Test-Path -LiteralPath (Join-Path $rawRoot $name)) {
        throw "Existing raw frame prevents a new frozen attempt: $name"
    }
}
$ledger = [ordered]@{
    freeze_utc = [DateTime]::UtcNow.ToString('o')
    spec_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $pilotRoot 'SPEC-2026-09-05.md')).Hash.ToLowerInvariant()
    status = 'FROZEN_BEFORE_DOWNLOAD'
    max_frames = 4
    max_bytes_each = 12000000
    sources = @()
}
$ledger | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ledgerPath -Encoding utf8
foreach ($name in $files) {
    $uri = "https://services.swpc.noaa.gov/products/ccor2/fits/$name"
    $head = Invoke-WebRequest -Method Head -Uri $uri -TimeoutSec 30 -MaximumRedirection 0
    $expectedBytes = [long]($head.Headers['Content-Length'] | Select-Object -First 1)
    if ($expectedBytes -le 0 -or $expectedBytes -gt $ledger.max_bytes_each) {
        throw "Out-of-budget Content-Length for $name : $expectedBytes"
    }
    $path = Join-Path $rawRoot $name
    Invoke-WebRequest -Uri $uri -OutFile $path -TimeoutSec 60 -MaximumRedirection 0
    $actualBytes = (Get-Item -LiteralPath $path).Length
    if ($actualBytes -ne $expectedBytes -or $actualBytes -gt $ledger.max_bytes_each) {
        throw "Frame size does not match the preflight: $name"
    }
    $ledger.sources += [ordered]@{
        filename = $name
        url = $uri
        downloaded_utc = [DateTime]::UtcNow.ToString('o')
        bytes = $actualBytes
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    }
    $ledger.status = 'DOWNLOADING'
    $ledger | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ledgerPath -Encoding utf8
    Write-Output "Downloaded $name ($actualBytes bytes)"
}
$ledger.status = 'DOWNLOADED_FOUR_FROZEN_FRAMES'
$ledger | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ledgerPath -Encoding utf8
