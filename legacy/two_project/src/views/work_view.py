import flet as ft
from controllers.data_manager import DataManager
from models.work import WorkRecord

class WorkView(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 20
        self.expand = True

        # --- 輸入欄位定義 ---
        self.name_input = ft.TextField(label="工作名稱", hint_text="例如：婚禮攝影")
        self.type_input = ft.Dropdown(
            label="類型",
            options=[
                ft.dropdown.Option("攝影"),
                ft.dropdown.Option("設計"),
                ft.dropdown.Option("活動"),
            ],
            value="攝影"
        )
        self.income_input = ft.TextField(label="收入金額", prefix_text="$ ", value="0")
        self.notes_input = ft.TextField(label="備註", multiline=True)

        # --- 表格定義 ---
        self.table = ft.DataTable(
            expand=True,
            columns=[
                ft.DataColumn(ft.Text("日期")),
                ft.DataColumn(ft.Text("工作名稱")),
                ft.DataColumn(ft.Text("類型")),
                ft.DataColumn(ft.Text("收入"), numeric=True),
                ft.DataColumn(ft.Text("操作")),
            ],
            rows=[]
        )

        self.content = ft.Column([
            ft.Text("工作紀錄管理", size=28, weight="bold"),
            ft.Row([
                ft.TextField(hint_text="搜尋紀錄...", expand=True, prefix_icon=ft.Icons.SEARCH),
                ft.ElevatedButton(
                    "新增紀錄", 
                    icon=ft.Icons.ADD, 
                    on_click=self.open_add_dialog
                ),
            ]),
            ft.Column([self.table], scroll=ft.ScrollMode.AUTO, expand=True)
        ])

    def did_mount(self):
        self.load_works()

    # --- 核心邏輯 ---

    def show_snack_bar(self, message: str, color: str = ft.Colors.GREEN_600):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=color)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def load_works(self):
        """從 DataManager 載入並顯示資料"""
        data = DataManager.load_data().get("works", [])
        self.table.rows.clear()
        
        for idx, item in enumerate(data):
            self.table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item.get("date", ""))),
                    ft.DataCell(ft.Text(item.get("name", ""))),
                    ft.DataCell(ft.Text(item.get("type", ""))),
                    ft.DataCell(ft.Text(f"{item.get('income', 0):,}")),
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda e, i=idx: self.delete_work(i)
                        )
                    ),
                ])
            )
        self.update()

    def open_add_dialog(self, e):
        """開啟新增視窗"""
        self.dialog = ft.AlertDialog(
            title=ft.Text("新增工作紀錄"),
            content=ft.Column([
                self.name_input,
                self.type_input,
                self.income_input,
                self.notes_input,
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("取消", on_click=lambda _: self.page.close(self.dialog)),
                ft.ElevatedButton("儲存", on_click=self.save_new_work),
            ],
        )
        self.page.open(self.dialog)

    def save_new_work(self, e):
        """驗證並儲存新紀錄"""
        if not self.name_input.value:
            self.name_input.error_text = "請輸入工作名稱"
            self.update()
            return

        # 建立物件並存檔
        new_record = WorkRecord(
            name=self.name_input.value,
            type_=self.type_input.value,
            income=float(self.income_input.value or 0),
            notes=self.notes_input.value
        )
        
        DataManager.add_work_record(new_record)
        
        # 清空欄位並關閉
        self.name_input.value = ""
        self.income_input.value = "0"
        self.notes_input.value = ""
        self.page.close(self.dialog)
        
        self.load_works()
        self.show_snack_bar("工作紀錄已新增！")

    def delete_work(self, index):
        """刪除紀錄邏輯 (需確認 DataManager 已有 delete_work_record)"""
        # 注意：需在 DataManager 補上此方法
        data = DataManager.load_data()
        if "works" in data:
            data["works"].pop(index)
            DataManager._save_to_file(data)
            self.load_works()
            self.show_snack_bar("紀錄已刪除", color=ft.Colors.RED_600)