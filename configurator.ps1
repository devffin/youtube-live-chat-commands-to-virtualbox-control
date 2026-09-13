$ErrorActionPreference = 'Stop'
$configPath = Join-Path $PSScriptRoot 'config.json'

function Read-Config {
    if (Test-Path $configPath) {
        return (Get-Content -Raw -Path $configPath | ConvertFrom-Json)
    }

    return [pscustomobject]@{
        vm_name = 'Windows10'
        video_id = 'LIVE_ID'
        allowed_users = @()
        Cust_plgs = [pscustomobject]@{}
    }
}

function Read-Value {
    param([string]$Label, [string]$Current)
    $value = Read-Host "$Label [$Current]"
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $Current
    }
    return $value.Trim()
}

function Read-Multiline {
    param([string]$Label, [string[]]$Current)
    Write-Host "`n$Label"
    Write-Host '(One value per line, blank line to finish.)'
    if ($Current.Count -gt 0) {
        Write-Host "Current values: $($Current -join ', ')"
    }
    $values = @()
    while ($true) {
        $line = Read-Host '>'
        if ([string]::IsNullOrWhiteSpace($line)) {
            break
        }
        $values += $line.Trim()
    }
    return $values
}

function Save-Config {
    param($Config)
    $json = $Config | ConvertTo-Json -Depth 10
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($configPath, $json, $utf8NoBom)
}

try {
    $config = Read-Config
    $vmName = [string]$config.vm_name
    $videoId = [string]$config.video_id
    $allowedUsers = @($config.allowed_users | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $pluginsJson = if ($config.Cust_plgs) { $config.Cust_plgs | ConvertTo-Json -Depth 5 } else { '{}' }

    while ($true) {
        Clear-Host
        Write-Host '========================================' -ForegroundColor Cyan
        Write-Host ' Youtube2Box - Configuration JSON (TUI)' -ForegroundColor Cyan
        Write-Host '========================================' -ForegroundColor Cyan
        Write-Host "`nFile: $configPath"
        Write-Host "`n[1] VM name         : $vmName"
        Write-Host "[2] Live video ID   : $videoId"
        Write-Host "[3] Allowed users   : $(if ($allowedUsers.Count) { $allowedUsers -join ', ' } else { '(all)' })"
        Write-Host "[4] Plugins JSON    : $($pluginsJson -replace '\s+', ' ' | Select-Object -First 1)"
        Write-Host "`n[S] Save            [Q] Quit without saving"

        $choice = (Read-Host '`nChoice').Trim().ToUpperInvariant()
        switch ($choice) {
            '1' { $vmName = Read-Value 'VM name' $vmName }
            '2' { $videoId = Read-Value 'YouTube live ID' $videoId }
            '3' { $allowedUsers = @(Read-Multiline 'Allowed users' $allowedUsers) }
            '4' {
                Write-Host "`nPaste the plugin JSON on one line."
                Write-Host 'Example: {"!key":["BadKeyboards","press"]}'
                $candidate = Read-Host 'JSON'
                if (-not [string]::IsNullOrWhiteSpace($candidate)) {
                    try {
                        $null = $candidate | ConvertFrom-Json
                        $pluginsJson = $candidate
                    } catch {
                        Write-Host "Invalid JSON: $($_.Exception.Message)" -ForegroundColor Red
                        Read-Host 'Press Enter to continue'
                    }
                }
            }
            'S' {
                if ([string]::IsNullOrWhiteSpace($vmName) -or [string]::IsNullOrWhiteSpace($videoId)) {
                    Write-Host 'The VM name and live ID are required.' -ForegroundColor Red
                    Read-Host 'Press Enter to continue'
                    continue
                }
                $configToSave = [ordered]@{
                    vm_name = $vmName
                    video_id = $videoId
                    allowed_users = $allowedUsers
                    Cust_plgs = ($pluginsJson | ConvertFrom-Json)
                }
                Save-Config $configToSave
                Write-Host "Configuration saved to $configPath" -ForegroundColor Green
                Read-Host 'Press Enter to exit'
                exit 0
            }
            'Q' { exit 0 }
            default { Write-Host 'Invalid choice.' -ForegroundColor Yellow; Start-Sleep -Seconds 1 }
        }
    }
} catch {
    Write-Host "Configurator error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
