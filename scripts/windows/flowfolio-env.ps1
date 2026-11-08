function Import-FlowfolioEnv {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    $envPath = Join-Path $Root ".env"
    if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
        return
    }

    foreach ($line in Get-Content -LiteralPath $envPath -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith("#")) {
            continue
        }

        if ($trimmed -notmatch '^(?:export\s+)?(?<Name>FLOWFOLIO_[A-Za-z0-9_]*)\s*=\s*(?<Value>.*)$') {
            continue
        }

        $name = $Matches.Name
        $value = $Matches.Value.Trim()
        $isQuoted = $false
        if ($value.Length -ge 2) {
            $first = $value.Substring(0, 1)
            $last = $value.Substring($value.Length - 1, 1)
            if (($first -eq '"' -and $last -eq '"') -or ($first -eq "'" -and $last -eq "'")) {
                $isQuoted = $true
                $value = $value.Substring(1, $value.Length - 2)
            }
        }
        if (-not $isQuoted) {
            $value = [regex]::Replace($value, '\s+#.*$', '').TrimEnd()
        }

        # Match Pydantic Settings: an existing process variable wins over .env.
        if ($null -eq [Environment]::GetEnvironmentVariable($name, [EnvironmentVariableTarget]::Process)) {
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

function Get-FlowfolioSettings {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
    Import-FlowfolioEnv -Root $resolvedRoot

    $environment = [Environment]::GetEnvironmentVariable("FLOWFOLIO_ENV", [EnvironmentVariableTarget]::Process)
    if ([string]::IsNullOrWhiteSpace($environment)) {
        $environment = [Environment]::GetEnvironmentVariable("FLOWFOLIO_ENVIRONMENT", [EnvironmentVariableTarget]::Process)
    }
    if ([string]::IsNullOrWhiteSpace($environment)) {
        $environment = "development"
    }

    $dataDirValue = [Environment]::GetEnvironmentVariable("FLOWFOLIO_DATA_DIR", [EnvironmentVariableTarget]::Process)
    if ([string]::IsNullOrWhiteSpace($dataDirValue)) {
        $dataDirValue = "data"
    }
    if ([IO.Path]::IsPathRooted($dataDirValue)) {
        $dataDir = [IO.Path]::GetFullPath($dataDirValue)
    } else {
        $dataDir = [IO.Path]::GetFullPath((Join-Path $resolvedRoot $dataDirValue))
    }

    $hostValue = [Environment]::GetEnvironmentVariable("FLOWFOLIO_HOST", [EnvironmentVariableTarget]::Process)
    if ([string]::IsNullOrWhiteSpace($hostValue)) {
        $hostValue = "127.0.0.1"
    }

    $portValue = [Environment]::GetEnvironmentVariable("FLOWFOLIO_PORT", [EnvironmentVariableTarget]::Process)
    $port = 8000
    if (-not [string]::IsNullOrWhiteSpace($portValue)) {
        try {
            $port = [int]$portValue.Trim()
        } catch {
            throw "FLOWFOLIO_PORT 必須是 1 到 65535 的整數。"
        }
    }
    if ($port -lt 1 -or $port -gt 65535) {
        throw "FLOWFOLIO_PORT 必須是 1 到 65535 的整數。"
    }

    $funnelPortValue = [Environment]::GetEnvironmentVariable("FLOWFOLIO_FUNNEL_PORT", [EnvironmentVariableTarget]::Process)
    $funnelPort = 10000
    if (-not [string]::IsNullOrWhiteSpace($funnelPortValue)) {
        try {
            $funnelPort = [int]$funnelPortValue.Trim()
        } catch {
            throw "FLOWFOLIO_FUNNEL_PORT 必須是 443、8443 或 10000。"
        }
    }
    if (@(443, 8443, 10000) -notcontains $funnelPort) {
        throw "FLOWFOLIO_FUNNEL_PORT 必須是 443、8443 或 10000。"
    }

    $webhookUrl = [Environment]::GetEnvironmentVariable("FLOWFOLIO_WEBHOOK_URL", [EnvironmentVariableTarget]::Process)

    $localHost = $hostValue
    if ($localHost -in @("0.0.0.0", "::", "[::]")) {
        $localHost = "127.0.0.1"
    }
    $urlHost = if ($localHost.Contains(":") -and -not $localHost.StartsWith("[")) {
        "[$localHost]"
    } else {
        $localHost
    }

    [pscustomobject]@{
        Root = $resolvedRoot
        Environment = $environment
        DataDir = $dataDir
        Host = $hostValue
        Port = $port
        FunnelPort = $funnelPort
        WebhookUrl = $webhookUrl
        LocalHost = $localHost
        LocalHealthUrl = "http://{0}:{1}/health" -f $urlHost, $port
    }
}

function Get-FlowfolioFunnelStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$TailscalePath
    )

    try {
        $jsonLines = & $TailscalePath funnel status --json 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $jsonLines) {
            return $null
        }
        return (($jsonLines -join [Environment]::NewLine) | ConvertFrom-Json)
    } catch {
        return $null
    }
}

function Get-FlowfolioFunnelEndpoint {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Status,

        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    if (-not $Status.Web) {
        return $null
    }

    return @($Status.Web.PSObject.Properties | Where-Object { $_.Name -like "*:$Port" } | Select-Object -First 1)
}

function Get-FlowfolioFunnelPublicUrl {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Status,

        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $endpoint = Get-FlowfolioFunnelEndpoint -Status $Status -Port $Port
    if (-not $endpoint) {
        return $null
    }

    $funnelSuffix = ":$Port"
    $funnelHost = $endpoint.Name.Substring(0, $endpoint.Name.Length - $funnelSuffix.Length)
    $portSuffix = if ($Port -eq 443) { "" } else { $funnelSuffix }
    return "https://$funnelHost$portSuffix"
}

function Get-FlowfolioLocalHealthUrl {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Settings,

        [int]$Port = 0
    )

    $effectivePort = if ($Port -gt 0) { $Port } else { $Settings.Port }
    $urlHost = $Settings.LocalHost
    if ($urlHost.Contains(":") -and -not $urlHost.StartsWith("[")) {
        $urlHost = "[$urlHost]"
    }
    return "http://{0}:{1}/health" -f $urlHost, $effectivePort
}
