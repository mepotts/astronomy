# Header-only follow-up; never modifies the original frozen attempt.
# At most four 64-KiB range responses plus two bounded XML inventories.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$target = Join-Path $root 'data/raw/unblock-20260906'
if (Test-Path -LiteralPath $target) { throw 'Refusing to overwrite a recorded probe' }
New-Item -ItemType Directory -Path $target | Out-Null
$base = 'https://archive.data.noaa.gov/satellite-spaceweather'
$prefix = 'SWFO/SOLAR-1/CCOR-2/ccor2-l1a_science/2026/09/01/'
$records = @()
foreach ($entry in @(
    @{name='docs.xml'; prefix='SWFO/docs/CCOR/'; max=50},
    @{name='day.xml'; prefix=$prefix; max=100}
)) {
    $url = "$base`?list-type=2&prefix=$([uri]::EscapeDataString($entry.prefix))&max-keys=$($entry.max)"
    $path = Join-Path $target $entry.name
    $response = Invoke-WebRequest $url -OutFile $path -PassThru -TimeoutSec 20
    [xml]$listing = Get-Content -LiteralPath $path -Raw
    if ($listing.ListBucketResult.IsTruncated -ne 'false') { throw 'Incomplete inventory' }
    $records += @{url=$url; file=$entry.name; status=[int]$response.StatusCode;
        retrieved_utc=[datetime]::UtcNow.ToString('o');
        bytes=(Get-Item -LiteralPath $path).Length;
        sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
[xml]$day = Get-Content -LiteralPath (Join-Path $target 'day.xml') -Raw
foreach ($time in @('130014','131514','133014','134514')) {
    $matches = @($day.ListBucketResult.Contents | Where-Object {
        $_.Key -match "s20260901T${time}Z_.*_pub[.]fits$"
    })
    if ($matches.Count -ne 1) { throw "Ambiguous or missing timestamp $time" }
    $item = $matches[0]
    $url = "$base/$($item.Key)"
    $path = Join-Path $target "$time.prefix"
    $response = Invoke-WebRequest $url -Headers @{Range='bytes=0-65535'} -OutFile $path -PassThru -TimeoutSec 20
    if ($response.StatusCode -ne 206 -or (Get-Item -LiteralPath $path).Length -ne 65536) {
        throw 'Server did not honor the bounded range request; do not continue'
    }
    if ([string]$response.Headers['Content-Range'] -ne "bytes 0-65535/$($item.Size)") {
        throw 'Range identity mismatch'
    }
    $records += @{url=$url; file="$time.prefix"; status=206;
        content_range=[string]$response.Headers['Content-Range'];
        retrieved_utc=[datetime]::UtcNow.ToString('o'); bytes=65536;
        sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$ledger = @{purpose='Separate header-only retrospective preflight, not a recovery attempt';
    script_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();
    records=$records}
$ledger | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $target 'ledger.json') -Encoding utf8
$ledger | ConvertTo-Json -Depth 6
