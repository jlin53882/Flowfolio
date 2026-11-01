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

        # 在 __init__ 中加入
        self.search_input = ft.TextField(
            label="搜尋作品", 
            hint_text="輸入項目名稱或內容...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search_change # 文字改變時自動觸發搜尋
        )
        
        # 確保圖片目錄存在
        self.image_dir = "data/picture"
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        self.temp_image_paths = []

        # --- 初始化元件 ---
        self.file_picker = ft.FilePicker(on_result=self.on_files_selected)
        
        # 修正 DatePicker：Flet 0.28.x 標準寫法
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
        # 務必將 DatePicker 加入 overlay
        self.page.overlay.extend([self.file_picker, self.date_picker])
        self.load_portfolio()
        self.page.update()

    def show_full_image(self, all_images, start_index):
        """顯示照片大圖彈窗，使用手動索引切換"""
        
        # 使用一個 list 來包裝 index，這樣在 inner function 才能修改它
        current_idx = [start_index]
        
        # 建立顯示圖片的元件
        image_display = ft.Image(
            src=all_images[current_idx[0]], 
            fit=ft.ImageFit.CONTAIN,
            expand=True
        )
        
        # 顯示頁數的文字
        counter_text = ft.Text(
            f"{current_idx[0] + 1} / {len(all_images)}", 
            color=ft.Colors.GREY_500
        )

        def update_viewer():
            image_display.src = all_images[current_idx[0]]
            counter_text.value = f"{current_idx[0] + 1} / {len(all_images)}"
            self.page.update()

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def go_next(e):
            if current_idx[0] < len(all_images) - 1:
                current_idx[0] += 1
                update_viewer()

        def go_prev(e):
            if current_idx[0] > 0:
                current_idx[0] -= 1
                update_viewer()

        dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Stack([
                    # 主要圖片顯示區
                    ft.Container(content=image_display, alignment=ft.alignment.center),
                    
                    # 左按鈕 (只有一張圖以上才顯示)
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_IOS_NEW,
                        bgcolor="#44000000",
                        icon_color="white",
                        left=0,
                        top=250,
                        on_click=go_prev,
                        visible=len(all_images) > 1
                    ),
                    
                    # 右按鈕
                    ft.IconButton(
                        icon=ft.Icons.ARROW_FORWARD_IOS,
                        bgcolor="#44000000",
                        icon_color="white",
                        right=0,
                        top=250,
                        on_click=go_next,
                        visible=len(all_images) > 1
                    ),
                ]),
                width=800,
                height=600,
            ),
            actions=[
                ft.Row([
                    counter_text,
                    ft.TextButton("關閉", on_click=close_dialog)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def show_message(self, text, color=ft.Colors.GREEN_600):
        """顯示提示通知"""
        snack = ft.SnackBar(content=ft.Text(text), bgcolor=color)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    # --- 日期處理邏輯 (修正重點) ---
    def open_date_picker(self, e):
        # Flet 0.28.x 使用 .open = True 而非 .pick_date()
        self.date_picker.open = True
        self.page.update()

    def on_date_change(self, e):
        if self.date_picker.value:
            self.selected_date = self.date_picker.value.strftime("%Y-%m-%d")
            self.date_text.value = self.selected_date
            self.update()

    # --- 圖片處理邏輯 ---
    def on_files_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                self.temp_image_paths.append(f.path)
                self.temp_preview_row.controls.append(
                    ft.Stack([
                        ft.Image(src=f.path, width=80, height=80, fit=ft.ImageFit.COVER, border_radius=5),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE, icon_size=15, bgcolor=ft.Colors.RED_400,
                            icon_color=ft.Colors.WHITE, right=-5, top=-5,
                            on_click=lambda _, p=f.path: self.remove_temp_img(p)
                        )
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

    # --- 儲存邏輯 ---
    def save_item(self, e):
        if not self.selected_date or not self.project_input.value:
            self.show_message("請填寫日期與項目名稱！", color=ft.Colors.RED_600)
            return

        saved_paths = []
        for p in self.temp_image_paths:
            ext = os.path.splitext(p)[1]
            new_name = f"{uuid.uuid4()}{ext}"
            dest = os.path.join(self.image_dir, new_name)
            shutil.copy(p, dest)
            saved_paths.append(dest)

        item = {
            "date": self.selected_date,
            "time": self.time_input.value,
            "project": self.project_input.value,
            "content": self.content_input.value,
            "images": saved_paths
        }
        DataManager.add_portfolio_item(item)
        
        # 儲存成功通知
        self.show_message(f"成功發佈：{self.project_input.value}")
        
        self.temp_image_paths = []
        self.temp_preview_row.controls.clear()
        self.project_input.value = ""
        self.content_input.value = ""
        self.time_input.value = ""
        self.date_text.value = "未選日期"
        self.selected_date = ""
        self.load_portfolio()

    # --- FB 風格佈局 (保持不變) ---
    def build_fb_layout(self, images):
        count = len(images)
        if count == 0: return ft.Container(height=0)

        # 輔助函數：現在需要知道 index
        def clickable_image(idx, expand=None, height=None, width=None):
            return ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda _: self.show_full_image(images, idx), # 傳入整組照片與當前索引值
                content=ft.Image(src=images[idx], fit=ft.ImageFit.COVER, height=height, width=width),
                expand=expand if expand else False
            )

        if count == 1: 
            return clickable_image(0, height=300, width=500)
        
        if count == 2:
            return ft.Row([
                clickable_image(0, expand=1, height=250),
                clickable_image(1, expand=1, height=250),
            ], spacing=2)
            
        if count == 3:
            return ft.Row([
                clickable_image(0, expand=2, height=300),
                ft.Column([
                    clickable_image(1, expand=1, width=150),
                    clickable_image(2, expand=1, width=150),
                ], spacing=2, expand=1)
            ], spacing=2, height=300)
            
        # 多圖佈局 (+N 模式)
        return ft.Column([
            clickable_image(0, height=200, width=500),
            ft.Row([
                clickable_image(1, expand=1, height=120),
                clickable_image(2, expand=1, height=120),
                ft.Stack([
                    clickable_image(3, expand=1, height=120),
                    ft.Container(
                        content=ft.Text(f"+{count-3}", color="white", size=20, weight="bold"),
                        bgcolor="black54", 
                        alignment=ft.alignment.center, 
                        expand=True,
                        # 點擊 +N 處，從第 4 張 (index 3) 開始看起
                        on_click=lambda _: self.show_full_image(images, 3), 
                    ) if count > 4 else ft.Container()
                ], expand=1)
            ], spacing=2)
        ], spacing=2)

    def load_portfolio(self):
        data = DataManager.load_data().get("portfolio", [])
        self.portfolio_grid.controls.clear()
        for i, item in enumerate(reversed(data)):
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
                                    on_click=lambda _, idx=i: self.delete_item(idx)
                                )
                            ),
                            # --- 修正處：將 ft.Padding 改為 ft.Container ---
                            ft.Container(
                                content=ft.Text(item['content']),
                                padding=ft.padding.only(left=15, right=15, bottom=10)
                            ),
                            # --------------------------------------------
                            img_layout
                        ], spacing=0),
                        padding=ft.padding.only(bottom=10)
                    )
                )
            )
        self.update()

    def delete_item(self, index):
        all_data = DataManager.load_data().get("portfolio", [])
        actual_index = len(all_data) - 1 - index
        DataManager.delete_portfolio_item(actual_index)
        # 刪除成功通知
        self.show_message("作品已刪除", color=ft.Colors.RED_700)
        self.load_portfolio()

    def build(self):
        left_panel = ft.Container(
            width=320, bgcolor=ft.Colors.WHITE, padding=20, border_radius=10,
            content=ft.Column([
                ft.Text("發佈新作品", size=20, weight="bold"),
                ft.Row([
                    # 修正處：改用 self.open_date_picker
                    ft.ElevatedButton("日期", on_click=self.open_date_picker), 
                    self.date_text
                ]),
                self.time_input,
                self.project_input,
                self.content_input,
                ft.ElevatedButton("選擇多張照片", icon=ft.Icons.ADD_A_PHOTO, on_click=lambda _: self.file_picker.pick_files(allow_multiple=True)),
                self.temp_preview_row,
                ft.ElevatedButton("發佈到作品集", width=300, bgcolor=ft.Colors.BLUE_600, color="white", on_click=self.save_item)
            ], scroll=ft.ScrollMode.AUTO)
        )

        self.content = ft.Row([
            left_panel,
            ft.Column([ft.Text("作品牆", size=20, weight="bold"), self.portfolio_grid], expand=True)
        ], spacing=20)
        return self