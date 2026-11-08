function Send-FlowfolioWebhook {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$WebhookUrl,

        [Parameter(Mandatory = $true)]
        [string]$PublicUrl
    )

    if ([string]::IsNullOrWhiteSpace($WebhookUrl)) {
        return $false
    }

    try {
        $webhookUri = $null
        if (-not [Uri]::TryCreate($WebhookUrl, [UriKind]::Absolute, [ref]$webhookUri) -or $webhookUri.Scheme -notin @("http", "https")) {
            throw "FLOWFOLIO_WEBHOOK_URL 不是有效的 HTTP/HTTPS URL。"
        }

        $payload = [ordered]@{
            username = "Flowfolio"
            content = "🌐 Flowfolio 已啟動`n手機網址：$PublicUrl"
        } | ConvertTo-Json -Compress
        $body = [Text.Encoding]::UTF8.GetBytes($payload)
        $response = Invoke-WebRequest -Uri $WebhookUrl -Method Post -ContentType "application/json; charset=utf-8" -Body $body -UseBasicParsing -TimeoutSec 15
        if ([int]$response.StatusCode -lt 200 -or [int]$response.StatusCode -ge 300) {
            throw "webhook 回應 HTTP $([int]$response.StatusCode)。"
        }
        return $true
    } catch {
        Write-Warning "Flowfolio webhook 通知失敗，請檢查 FLOWFOLIO_WEBHOOK_URL 與網路連線。"
        return $false
    }
}
