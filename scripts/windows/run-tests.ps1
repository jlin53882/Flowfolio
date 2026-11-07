param(
    [switch]$Serial
)

$pytestArguments = @("-n", "auto")
if ($Serial) {
    $pytestArguments = @("-n", "0")
    Write-Host "使用單程序模式執行後端測試。"
}
else {
    Write-Host "使用 pytest-xdist 平行執行後端測試。"
}

uv run pytest @pytestArguments
if ($LASTEXITCODE -ne 0) {
    throw "後端測試失敗，請查看上方輸出。"
}
