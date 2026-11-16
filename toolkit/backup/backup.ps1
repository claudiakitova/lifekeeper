# Nightly encrypted backup of a life archive with rclone (Windows). Setup: docs/backup.md.
#   powershell -ExecutionPolicy Bypass -File backup.ps1           # what the scheduled task runs every night
#   powershell -ExecutionPolicy Bypass -File backup.ps1 -DryRun   # show what would change, send nothing
# Each folder below is mirrored to <remote>:current/<name>. A file that changed or was deleted here isn't lost:
# its previous copy moves to <remote>:old/<date>/<name>, kept for $KeepDays days.
param([switch]$DryRun)
$ErrorActionPreference = "Stop"

# ---- edit these ----
$Remote = "archive-crypt"                                   # your rclone crypt remote (rclone config)
$Parts = [ordered]@{                                        # name in the backup = folder on this computer
    "exports" = Join-Path $env:USERPROFILE "my-archive\exports"   # the originals
    "derived" = Join-Path $env:USERPROFILE "my-archive\derived"   # catalog, timeline, corrections
}
$KeepDays = 30
$Rclone = "rclone"                                          # or the full path to rclone.exe
# --------------------

$logs = Join-Path $env:USERPROFILE "my-archive\backup-logs"
New-Item -ItemType Directory -Force $logs | Out-Null
$today = Get-Date -Format "yyyy-MM-dd"
$log = Join-Path $logs "$today.log"

# never sent: secrets, caches, system junk
$excludes = @("**/*token*", "**/*secret*", "**/*.key", "**/rclone.conf", "**/__pycache__/**", "**/node_modules/**",
              "~$*", "._*", "Thumbs.db", "desktop.ini", "backup-logs/**")
$filter = Join-Path $env:TEMP "archive-backup-excludes.txt"
$excludes | Set-Content -Encoding ascii $filter

foreach ($name in $Parts.Keys) {
    $source = $Parts[$name]
    if (-not (Test-Path $source)) { "skipped $name (not found: $source)" | Add-Content $log; continue }
    $arguments = @("sync", $source, "${Remote}:current/$name", "--backup-dir", "${Remote}:old/$today/$name", "--exclude-from", $filter,
                   "--transfers", "4", "--checkers", "8", "--fast-list", "--log-file", $log, "--log-level", "INFO")
    if ($DryRun) { $arguments += "--dry-run" }
    "=== $name ($source) $(Get-Date -Format s)" | Add-Content $log
    & $Rclone @arguments
    "=== $name finished with code $LASTEXITCODE $(Get-Date -Format s)" | Add-Content $log
}

# old copies are kept $KeepDays days, so the cloud doesn't fill up with every version forever
if (-not $DryRun) {
    $cutoff = (Get-Date).AddDays(-$KeepDays).ToString("yyyy-MM-dd")
    foreach ($day in (& $Rclone lsf --dirs-only "${Remote}:old" 2>$null)) {
        $day = $day.TrimEnd("/")
        if ($day -match '^\d{4}-\d{2}-\d{2}$' -and $day -lt $cutoff) {
            "=== removing old copies from $day" | Add-Content $log
            & $Rclone purge "${Remote}:old/$day" --log-file $log --log-level INFO
        }
    }
}
"=== all done $(Get-Date -Format s)" | Add-Content $log
