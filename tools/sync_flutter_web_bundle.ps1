param(
    [string]$SourceDir,
    [string]$DestinationDir
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pluginRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path

if ([string]::IsNullOrWhiteSpace($SourceDir)) {
    $SourceDir = Join-Path $pluginRoot "..\friendeck-web"
}
$SourceDir = (Resolve-Path $SourceDir).Path

if ([string]::IsNullOrWhiteSpace($DestinationDir)) {
    $DestinationDir = Join-Path $pluginRoot "defaults\remote_web_ui"
}

$requiredItems = @(
    "index.html",
    "main.dart.js",
    "flutter.js",
    "flutter_bootstrap.js",
    "flutter_service_worker.js",
    "manifest.json",
    "version.json",
    "favicon.png",
    "assets",
    "canvaskit",
    "icons"
)

foreach ($item in $requiredItems) {
    $sourcePath = Join-Path $SourceDir $item
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "Missing required Flutter web artifact: $sourcePath"
    }
}

if (Test-Path -LiteralPath $DestinationDir) {
    Remove-Item -LiteralPath $DestinationDir -Recurse -Force
}
New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null

foreach ($item in $requiredItems) {
    $sourcePath = Join-Path $SourceDir $item
    $destPath = Join-Path $DestinationDir $item
    Copy-Item -LiteralPath $sourcePath -Destination $destPath -Recurse -Force
}

# Optional marker file from Flutter build output.
$buildIdPath = Join-Path $SourceDir ".last_build_id"
if (Test-Path -LiteralPath $buildIdPath) {
    Copy-Item -LiteralPath $buildIdPath -Destination (Join-Path $DestinationDir ".last_build_id") -Force
}

foreach ($item in $requiredItems) {
    $destPath = Join-Path $DestinationDir $item
    if (-not (Test-Path -LiteralPath $destPath)) {
        throw "Bundle verification failed. Missing: $destPath"
    }
}

Write-Host "Flutter web bundle synced successfully."
Write-Host "Source: $SourceDir"
Write-Host "Destination: $DestinationDir"
