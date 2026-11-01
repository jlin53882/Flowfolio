import flet as ft
from datetime import datetime
import os
import shutil
import uuid
from controllers.data_manager import DataManager

class PortfolioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 20
        self.expand = True

        # --- 修改重點：圖片目錄定位到 src/data/picture ---
        # DataManager.DATA_DIR 已經在 data_manager.py 定義為 src/data

        # --- 初始化搜尋欄 ---
        self.search_input = ft.TextField(
            label="搜尋作品", 
            hint_text="搜尋項目名稱或內容...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search_change, # 文字改變即時觸發
            expand=True
        )

        self.image_dir = os.path.join(DataManager.DATA_DIR, "picture")
        # 確保圖片目錄存在
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        
        # --- 暫存上傳圖片路徑 ---
        self.temp_image_paths = []

        # --- 初始化元件 ---
        self.file_picker = ft.FilePicker(on_result=self.on_files_selected)
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=lambda _: print("日曆已關閉")
        )
        
        self.selected_date = ""
        self.date_text = ft.Text("未選日期", size=14)
        self.time_input = ft.TextField(label="時間", hint_text="14:00", width=120)
        self.project_input = ft.TextField(label="項目名稱", hint_text="例如：鋼琴獨奏會")
        self.content_input = ft.TextField(label="內容簡述", multiline=True, min_lines=3)
        
        self.temp_preview_row = ft.Row(scroll=ft.ScrollMode.AUTO, height=100)
        
        self.portfolio_grid = ft.GridView(
            expand=1, runs_count=2, max_extent=500, spacing=20, run_spacing=20
        )

    def did_mount(self):
        self.page.overlay.extend([self.file_picker, self.date_picker])
        self.load_portfolio()
        self.page.update()

    # --- 搜尋功能邏輯 ---
    def on_search_change(self, e):
        self.load_portfolio()

    # --- 圖片檢視器邏輯 (手動切換版，確保穩定性) ---
    def show_full_image(self, all_images, start_index):
        current_idx = [start_index]
        image_display = ft.Image(src=all_images[current_idx[0]], fit=ft.ImageFit.CONTAIN, expand=True)
        counter_text = ft.Text(f"{current_idx[0] + 1} / {len(all_images)}", color=ft.Colors.GREY_500)

        def update_viewer():
            image_display.src = all_images[current_idx[0]]
            counter_text.value = f"{current_idx[0] + 1} / {len(all_images)}"
            self.page.update()

        def move_page(delta):
            new_idx = current_idx[0] + delta
            if 0 <= new_idx < len(all_images):
                current_idx[0] = new_idx
                update_viewer()

        dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Stack([
                    ft.Container(content=image_display, alignment=ft.alignment.center),
                    ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, left=0, top=250, bgcolor="#44000000", 
                                  icon_color="white", on_click=lambda _: move_page(-1), visible=len(all_images) > 1),
                    ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, right=0, top=250, bgcolor="#44000000", 
                                  icon_color="white", on_click=lambda _: move_page(1), visible=len(all_images) > 1),
                ]),
                width=800, height=600,
            ),
            actions=[ft.Row([counter_text, ft.TextButton("關閉", on_click=lambda _: setattr(dialog, "open", False) or self.page.update())], 
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN)],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    # --- 加載與排序邏輯 ---
    def load_portfolio(self):
        # 1. 取得原始資料
        data = DataManager.load_data().get("portfolio", [])
        
        # 2. 自動按日期排序：最新日期在前面
        data.sort(key=lambda x: (x.get("date", ""), x.get("time", "")), reverse=True)

        # 3. 執行關鍵字搜尋過濾
        search_query = self.search_input.value.lower()
        filtered_data = []
        for item in data:
            if search_query in item['project'].lower() or search_query in item['content'].lower():
                filtered_data.append(item)

        # 4. 渲染 UI
        self.portfolio_grid.controls.clear()
        for item in filtered_data:
            img_layout = self.build_fb_layout(item.get("images", []))
            self.portfolio_grid.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.PERSON),
                                title=ft.Text(item['project'], weight="bold"),
                                subtitle=ft.Text(f"{item['date']} {item['time']}"),
                                trailing=ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE, 
                                    icon_color=ft.Colors.RED_400,
                                    on_click=lambda _, it=item: self.delete_portfolio_item(it)
                                )
                            ),
                            ft.Container(content=ft.Text(item['content']), padding=ft.padding.only(left=15, right=15, bottom=10)),
                            img_layout
                        ], spacing=0),
                        padding=ft.padding.only(bottom=10)
                    )
                )
            )
        self.update()

    # --- 刪除邏輯 (改用內容比對，避免排序後 index 錯誤) ---
    def delete_portfolio_item(self, target_item):
        all_data = DataManager.load_data().get("portfolio", [])
        
        # 1. 執行邏輯刪除
        new_data = [i for i in all_data if not (
            i['project'] == target_item['project'] and 
            i['date'] == target_item['date'] and 
            i['time'] == target_item['time']
        )]
        
        # 2. 實體檔案刪除 (如果你想連圖片檔案都刪掉，解除下方註釋)
        # for img_path in target_item.get("images", []):
        #     if os.path.exists(img_path):
        #         os.remove(img_path)

        DataManager.save_all_portfolio(new_data) 
        self.show_message(f"🗑️ 已刪除作品：{target_item['project']}", color=ft.Colors.RED_700)
        self.load_portfolio()

    # --- 圖片佈局 (支援點擊索引) ---
    def build_fb_layout(self, images):
        count = len(images)
        if count == 0: return ft.Container(height=0)

        def clickable_image(idx, expand=None, height=None, width=None):
            return ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda _: self.show_full_image(images, idx),
                content=ft.Image(src=images[idx], fit=ft.ImageFit.COVER, height=height, width=width),
                expand=expand if expand else False
            )

        if count == 1: return clickable_image(0, height=300, width=500)
        if count == 2:
            return ft.Row([clickable_image(0, 1, 250), clickable_image(1, 1, 250)], spacing=2)
        if count == 3:
            return ft.Row([clickable_image(0, 2, 300), 
                           ft.Column([clickable_image(1, 1, 150), clickable_image(2, 1, 150)], spacing=2, expand=1)], 
                          spacing=2, height=300)
        
        return ft.Column([
            clickable_image(0, height=200, width=500),
            ft.Row([
                clickable_image(1, 1, 120),
                clickable_image(2, 1, 120),
                ft.Stack([
                    clickable_image(3, 1, 120),
                    ft.Container(
                        content=ft.Text(f"+{count-3}", color="white", size=20, weight="bold"),
                        bgcolor="black54", alignment=ft.alignment.center, expand=True,
                        on_click=lambda _: self.show_full_image(images, 3),
                    ) if count > 4 else ft.Container()
                ], expand=1)
            ], spacing=2)
        ], spacing=2)

    # --- 其他原有功能 ---
    def show_message(self, text, color=ft.Colors.GREEN_600):
        snack = ft.SnackBar(content=ft.Text(text), bgcolor=color)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def open_date_picker(self, e):
        self.date_picker.open = True
        self.page.update()

    def on_date_change(self, e):
        if self.date_picker.value:
            self.selected_date = self.date_picker.value.strftime("%Y-%m-%d")
            self.date_text.value = self.selected_date
            self.update()

    def on_files_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                self.temp_image_paths.append(f.path)
                self.temp_preview_row.controls.append(
                    ft.Stack([
                        ft.Image(src=f.path, width=80, height=80, fit=ft.ImageFit.COVER, border_radius=5),
                        ft.IconButton(ft.Icons.CLOSE, icon_size=15, bgcolor=ft.Colors.RED_400, 
                                      icon_color="white", right=-5, top=-5, on_click=lambda _, p=f.path: self.remove_temp_img(p))
                    ])
                )
            self.update()

    def remove_temp_img(self, path):
        self.temp_image_paths.remove(path)
        self.refresh_temp_preview()

    def refresh_temp_preview(self):
        self.temp_preview_row.controls.clear()
        for p in self.temp_image_paths:
            self.temp_preview_row.controls.append(
                ft.Stack([
                    ft.Image(src=p, width=80, height=80, fit=ft.ImageFit.COVER, border_radius=5),
                    ft.IconButton(ft.Icons.CLOSE, icon_size=15, bgcolor=ft.Colors.RED_400, on_click=lambda _, path=p: self.remove_temp_img(path))
                ])
            )
        self.update()

    def save_item(self, e):
        # 1. 檢查必填欄位
        if not self.selected_date or not self.project_input.value:
            self.show_message("❌ 請填寫日期與項目名稱！", color=ft.Colors.RED_600)
            return

        # 2. 處理圖片儲存
        saved_paths = []
        for p in self.temp_image_paths:
            ext = os.path.splitext(p)[1]
            new_name = f"{uuid.uuid4()}{ext}"
            dest = os.path.join(self.image_dir, new_name)
            shutil.copy(p, dest)
            saved_paths.append(dest)

        # 3. 建立資料物件
        item = {
            "date": self.selected_date, 
            "time": self.time_input.value,
            "project": self.project_input.value, 
            "content": self.content_input.value, 
            "images": saved_paths
        }

        # 4. 寫入資料庫/檔案
        DataManager.add_portfolio_item(item)
        
        # 5. --- 關鍵改進：先清空輸入框，再顯示提示與載入新資料 ---
        project_name = self.project_input.value # 暫存名稱用於提示訊息
        
        # 重置 UI 狀態
        self.temp_image_paths = []
        self.temp_preview_row.controls.clear()
        self.project_input.value = ""
        self.content_input.value = ""
        self.time_input.value = ""
        self.date_text.value = "未選日期"
        self.selected_date = ""

        # 6. 顯示成功提示
        self.show_message(f"✅ 成功發佈作品：{project_name}", color=ft.Colors.GREEN_600)
        
        # 7. 重新載入列表 (這會觸發你寫好的排序邏輯，讓新作品跳到最前面)
        self.load_portfolio()

    def build(self):
        left_panel = ft.Container(
            width=320, bgcolor=ft.Colors.WHITE, padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("發佈新作品", size=20, weight="bold"),
                ft.Row([ft.ElevatedButton("日期", on_click=self.open_date_picker), self.date_text]),
                self.time_input, self.project_input, self.content_input,
                ft.ElevatedButton("選擇多張照片", icon=ft.Icons.ADD_A_PHOTO, on_click=lambda _: self.file_picker.pick_files(allow_multiple=True)),
                self.temp_preview_row,
                ft.ElevatedButton("發佈到作品集", width=300, bgcolor=ft.Colors.BLUE_600, color="white", on_click=self.save_item)
            ], scroll=ft.ScrollMode.AUTO)
        )

        self.content = ft.Row([
            left_panel,
            ft.Column([
                ft.Row([ft.Text("作品牆", size=20, weight="bold"), self.search_input], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.portfolio_grid
            ], expand=True)
        ], spacing=20)
        return self