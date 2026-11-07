# ADR 004：私人與公開網路邊界

## 決定

FastAPI 只監聽 loopback。私人連線使用 Tailscale Serve；若使用者明確需要手機不安裝 Tailscale，則透過 `啟動Flowfolio公開網站.bat` 啟用 Tailscale Funnel。程式不自動修改 tailnet ACL、防火牆或電源政策；Funnel 不列為預設啟動流程。

## 原因

Tailscale Serve 能提供 tailnet 內 HTTPS，但「同一個 tailnet」不必然代表只有本人；Funnel 更會對公開網際網路開放。設備、ACL、帳號、公開網址流出與遺失裝置撤銷仍是使用者的部署責任。Flowfolio 目前沒有登入驗證，公開 Funnel 只適合在資料可公開時使用。

