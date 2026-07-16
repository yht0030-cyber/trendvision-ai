# TrendVision AI - Deploy Script
param([switch]$Auto)
Write-Host "=== TrendVision AI - Deploy ===" -ForegroundColor Cyan
git status --short
if (-not $Auto) {
    $confirm = Read-Host "Confirm push? (y/n)"
    if ($confirm -ne "y") { exit }
}
git add -A
git commit -m "2026-07-16 19:00 - auto update"
git push origin main
Write-Host "=== Complete! ===" -ForegroundColor Green
