my_freelance_app/
├── .venv/                # uv 虛擬環境
├── assets/               # 存放作品集圖片、圖示
├── data/                 # 存放 JSON 或 SQLite 資料庫檔案
├── src/
│   ├── __init__.py
│   ├── main.py           # 程式入口點
│   ├── models/           # 底層資料結構 (你提供的 class)
│   │   ├── work.py
│   │   ├── portfolio.py
│   │   └── course.py
│   ├── views/            # 不同的 UI 頁面
│   │   ├── dashboard.py  # 儀表板 (收入統計)
│   │   ├── work_view.py  # 工作紀錄介面
│   │   ├── quote_view.py # 報價計算器介面
│   │   └── practice_view.py
│   └── components/       # 共用組件 (導覽列、自訂卡片)
│       └── nav_bar.py
├── pyproject.toml        # uv 設定檔
└── README.md

本資料夾是重構時保留的唯讀參考副本。原本名稱含 `copy` 的三個檔案已改成能表達用途的 `*_alternate.py`，用來保留不同實作版本，不把模糊的複製檔名帶進正式程式碼。
