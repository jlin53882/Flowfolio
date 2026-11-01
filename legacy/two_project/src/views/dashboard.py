import flet as ft
from datetime import datetime
from controllers.data_manager import DataManager
from models.work import WorkRecord

class DashboardView(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 20
        self.expand = True
        
        # --- 狀態變數 ---
        self.selected_date = datetime.now()
        
        # --- 統計數據變數 (動態更新用) ---
        self.monthly_income_text = ft.Text("$ 0", size=22, weight="bold")
        self.monthly_hours_text = ft.Text("0 hrs", size=22, weight="bold")
        self.today_status_text = ft.Text("0 %", size=22, weight="bold")
        
        # --- UI 組件 ---
        self.selected_date_text = ft.Text(
            f"選定日期：{self.selected_date.strftime('%Y-%m-%d')}", 
            size=16, weight="bold"
        )
        
        self.date_picker = ft.DatePicker(
            on_change=self.handle_date_change,
            first_date=datetime(2023, 1, 1),
            last_date=datetime(2026, 12, 31),
        )

        self.daily_events = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
        self.summary_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

        # --- 新增排程彈窗欄位 ---
        self.type_dropdown = ft.Dropdown(
            label="類型",
            options=[
                ft.dropdown.Option("待辦事項"),
                ft.dropdown.Option("工作"),
                ft.dropdown.Option("練習")
            ],
            value="待辦事項",
            on_change=self.on_type_change
        )
        self.title_input = ft.TextField(label="標題 / 名稱")
        self.time_input = ft.TextField(label="時間", value="12:00")
        self.location_input = ft.TextField(label="地點")
        self.value_input = ft.TextField(label="金額 / 分鐘", value="0", visible=False)

        # --- 佈局 ---
        self.content = ft.Row([
            ft.Column([
                ft.Text("歡迎回來，今日進度", size=28, weight="bold"),
                self.create_stat_cards(),
                ft.Text("當日快速摘要", size=20, weight="bold"),
                ft.Container(
                    content=self.summary_list,
                    padding=15, bgcolor=ft.Colors.GREY_50, border_radius=15, expand=True
                ),
            ], expand=2, spacing=20),
            
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("行程檢視", size=20, weight="bold"),
                        ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.BLUE, on_click=self.open_add_dialog)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.ElevatedButton("選擇日期", icon=ft.Icons.CALENDAR_MONTH, on_click=lambda _: self.page.open(self.date_picker)),
                    self.selected_date_text,
                    ft.Divider(),
                    self.daily_events,
                ], spacing=15),
                padding=20, bgcolor=ft.Colors.WHITE, border_radius=15, expand=1,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
            )
        ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)

    def create_stat_card(self, title, control, icon, color):
        return ft.Card(content=ft.Container(content=ft.Column([
            ft.Icon(icon, color=color, size=30),
            ft.Text(title, size=14, color=ft.Colors.GREY_700),
            control, # 這裡傳入動態的 Text 組件
        ], horizontal_alignment="center"), padding=15, width=160))

    def create_stat_cards(self):
        return ft.Row([
            self.create_stat_card("本月收入", self.monthly_income_text, ft.Icons.ATTACH_MONEY, ft.Colors.GREEN),
            self.create_stat_card("工時總計", self.monthly_hours_text, ft.Icons.TIMER, ft.Colors.BLUE),
            self.create_stat_card("今日完成率", self.today_status_text, ft.Icons.FACT_CHECK, ft.Colors.PURPLE),
        ], wrap=True)

    def did_mount(self):
        if self.page:
            if self.date_picker not in self.page.overlay:
                self.page.overlay.append(self.date_picker)
            self.refresh_all_data()

    def calculate_stats(self, all_data):
        """計算並更新統計卡片的數值"""
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        today_str = self.selected_date.strftime("%Y-%m-%d")

        total_income = 0
        total_minutes = 0 # 假設我們從工作紀錄或練習紀錄中換算
        
        # 1. 計算本月收入與工時 (從 works)
        for w in all_data.get("works", []):
            if w.get('date', '').startswith(current_month):
                total_income += float(w.get('income', 0))
                # 這裡假設每筆工作紀錄如果你有 duration 欄位可以加總，
                # 若無，我們先以練習時長作為範例加總
        
        for p in all_data.get("practice", []):
            if p.get('date', '').startswith(current_month):
                total_minutes += float(p.get('duration', 0))

        # 2. 計算今日完成率 (從所有類別的 completed 狀態)
        today_total = 0
        today_done = 0
        for cat in ["todos", "works", "practice"]:
            for item in all_data.get(cat, []):
                if item.get('date') == today_str:
                    today_total += 1
                    if item.get('completed', False):
                        today_done += 1
        
        completion_rate = int((today_done / today_total * 100)) if today_total > 0 else 0

        # 更新 UI 文字
        self.monthly_income_text.value = f"$ {total_income:,.0f}"
        self.monthly_hours_text.value = f"{total_minutes / 60:.1f} hrs"
        self.today_status_text.value = f"{completion_rate} %"

    def refresh_all_data(self):
        all_data = DataManager.load_data()
        self.calculate_stats(all_data) # 每次整理資料時重新計算統計
        
        date_str = self.selected_date.strftime('%Y-%m-%d')
        self.daily_events.controls.clear()
        self.summary_list.controls.clear()
        found = False

        def add_item_ui(title, subtitle, icon, color, category, idx, is_completed=False):
            style = ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH, color=ft.Colors.GREY_400) if is_completed else None
            
            # 右側清單
            self.daily_events.controls.append(
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.CHECK_CIRCLE if is_completed else ft.Icons.RADIO_BUTTON_UNCHECKED, # 已修正拼字
                        icon_color=ft.Colors.GREEN if is_completed else ft.Colors.GREY_300,
                        icon_size=20,
                        on_click=lambda _: self.toggle_complete(category, idx)
                    ),
                    ft.Column([
                        ft.Text(title, size=14, style=style, weight="w500"),
                        ft.Text(subtitle, size=11, color=ft.Colors.GREY_500) if not is_completed else ft.Container()
                    ], expand=True, spacing=0),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=ft.Colors.RED_200, 
                                  on_click=lambda _: self.delete_item(category, idx))
                ])
            )

            # 左側摘要
            self.summary_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.VerticalDivider(width=4, color=color if not is_completed else ft.Colors.GREY_300),
                        ft.Column([
                            ft.Text(title, weight="bold", size=14, style=style),
                            ft.Text(subtitle, size=12, color=ft.Colors.GREY_600),
                        ], spacing=2, expand=True),
                    ]),
                    padding=10, bgcolor=ft.Colors.WHITE, border_radius=8, opacity=0.6 if is_completed else 1
                )
            )

        # 顯示資料邏輯... (待辦、工作、練習)
        for cat, icon, color, label in [("todos", ft.Icons.LIST, ft.Colors.PINK, "待辦"), 
                                         ("works", ft.Icons.WORK, ft.Colors.AMBER, "工作"), 
                                         ("practice", ft.Icons.MUSIC_NOTE, ft.Colors.BLUE, "練習")]:
            for i, item in enumerate(all_data.get(cat, [])):
                if item.get('date') == date_str:
                    is_done = item.get('completed', False)
                    title = f"{label}: {item.get('title', item.get('name', item.get('piece', '未命名')))}"
                    sub = f"{item.get('time', '')} {item.get('location', '')}" if cat=="todos" else f"${item.get('income',0)}" if cat=="works" else f"{item.get('duration',0)} min"
                    add_item_ui(title, sub, icon, color, cat, i, is_done)
                    found = True

        if not found:
            self.daily_events.controls.append(ft.Text("本日無行程", italic=True, color=ft.Colors.GREY_400))
        self.update()

    def toggle_complete(self, category, index):
        data = DataManager.load_data()
        data[category][index]['completed'] = not data[category][index].get('completed', False)
        DataManager._save_to_file(data)
        self.refresh_all_data()

    def delete_item(self, category, index):
        data = DataManager.load_data()
        data[category].pop(index)
        DataManager._save_to_file(data)
        self.refresh_all_data()

    def handle_date_change(self, e):
        if e.control.value:
            self.selected_date = e.control.value
            self.selected_date_text.value = f"選定日期：{self.selected_date.strftime('%Y-%m-%d')}"
            self.refresh_all_data()

    # --- 新增彈窗與儲存邏輯 ---
    def open_add_dialog(self, e):
        self.add_dialog = ft.AlertDialog(
            title=ft.Text(f"新增行程 ({self.selected_date.strftime('%Y-%m-%d')})"),
            content=ft.Column([self.type_dropdown, self.title_input, self.time_input, self.location_input, self.value_input], tight=True),
            actions=[ft.TextButton("取消", on_click=lambda _: self.page.close(self.add_dialog)),
                     ft.ElevatedButton("儲存", on_click=self.save_new_event)]
        )
        self.page.open(self.add_dialog)

    def on_type_change(self, e):
        v = self.type_dropdown.value
        self.time_input.visible = self.location_input.visible = (v == "待辦事項")
        self.value_input.visible = (v != "待辦事項")
        self.update()

    def save_new_event(self, e):
        d = self.selected_date.strftime('%Y-%m-%d')
        v = self.type_dropdown.value
        if v == "待辦事項":
            DataManager.add_todo_record({"date": d, "title": self.title_input.value, "time": self.time_input.value, "location": self.location_input.value, "completed": False})
        elif v == "工作":
            DataManager.add_work_record(WorkRecord(name=self.title_input.value, type_="一般", date_str=d, income=float(self.value_input.value or 0)))
        elif v == "練習":
            DataManager.add_practice_record({"date": d, "piece": self.title_input.value, "duration": float(self.value_input.value or 0), "notes": "總覽新增", "completed": False})
        self.page.close(self.add_dialog)
        self.refresh_all_data()