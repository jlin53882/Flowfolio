# ADR 004：私人網路邊界

## 決定

FastAPI 只監聽 loopback，由使用者查證版本後設定 Tailscale Serve。程式不自動更改 tailnet ACL、不啟用 Funnel、不修改防火牆或電源政策。

## 原因

Tailscale Serve 能提供 tailnet 內 HTTPS，但「同一個 tailnet」不必然代表只有本人；設備、ACL、帳號與遺失裝置撤銷仍是使用者的部署責任。

