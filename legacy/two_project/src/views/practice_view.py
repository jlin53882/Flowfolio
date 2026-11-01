import flet as ft
import time
import threading
from datetime import date
from controllers.data_manager import DataManager

class PracticeView(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 20
        self.expand = True
        
        # --- 計時邏輯變數 ---
        self.total_seconds = 0      # 累計已完成的秒數
        self.current_start_time = 0 # 本次開始計時的時間點
        self.is_timing = False      # 是否正在計時中
        self.running = True         # 控制後台執行緒是否存活
        
        # --- UI 元件 ---
        self.piece_input = ft.TextField(
            label="1. 練習曲目 (必填)", 
            hint_text="輸入曲目後才能開始計時",
            on_change=self.validate_input
        )
        self.notes_input = ft.TextField(
            label="2. 練習心得", 
            multiline=True, 
            min_lines=3,
            hint_text="計時中或結束後可在此填寫心得..."
        )
        
        self.status_text = ft.Text("待機中", size=16, color=ft.Colors.GREY_500)
        self.timer_display = ft.Text("00:00:00", size=50, weight="bold", font_family="monospace")
        
        self.start_pause_btn = ft.ElevatedButton(
            "開始練習", 
            icon=ft.Icons.PLAY_ARROW, 
            bgcolor=ft.Colors.GREEN, 
            color=ft.Colors.WHITE,
            on_click=self.toggle_timer,
            width=150
        )
        
        self.stop_save_btn = ft.ElevatedButton(
            "結束並儲存", 
            icon=ft.Icons.SAVE, 
            bgcolor=ft.Colors.BLUE_700, 
            color=ft.Colors.WHITE,
            on_click=self.save_record,
            width=150,
            disabled=True
        )

        self.history_list = ft.ListView(expand=True, spacing=10)

        # --- 佈局 ---
        self.content = ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("練習計時器", size=24, weight="bold"),
                    ft.Container(
                        content=ft.Column([
                            self.status_text,
                            self.timer_display,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=30, 
                        border=ft.border.all(2, ft.Colors.BLUE_GREY_100), 
                        border_radius=20,
                        bgcolor=ft.Colors.WHITE,
                        width=350
                    ),
                    self.piece_input,
                    ft.Row([self.start_pause_btn, self.stop_save_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(),
                    self.notes_input,
                ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=1, padding=25, bgcolor=ft.Colors.GREY_50, border_radius=15
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("練習歷史", size=24, weight="bold"),
                    self.history_list
                ]), expand=1, padding=20
            )
        ])

    def did_mount(self):
        self.load_history()
        # 啟動後台計時更新執行緒
        self.running = True
        threading.Thread(target=self.update_timer_task, daemon=True).start()

    def will_unmount(self):
        # 離開頁面時停止執行緒
        self.running = False

    def show_snack_bar(self, message: str, color: str = ft.Colors.GREEN_600):
        """顯示提示通知"""
        snack = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
            action="知道了"
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def update_timer_task(self):
        """後台計時執行緒"""
        while self.running:
            if self.is_timing:
                elapsed = self.total_seconds + (time.time() - self.current_start_time)
                self.timer_display.value = self.format_time(elapsed)
                try:
                    self.update()
                except:
                    break
            time.sleep(0.1)

    def format_time(self, seconds):
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    def validate_input(self, e):
        if self.piece_input.value.strip():
            self.piece_input.error_text = None
            self.update()

    def toggle_timer(self, e):
        if not self.piece_input.value.strip():
            self.piece_input.error_text = "請先輸入曲目！"
            self.update()
            return

        if not self.is_timing:
            # 開始/繼續
            self.is_timing = True
            self.current_start_time = time.time()
            self.status_text.value = "計時中..."
            self.status_text.color = ft.Colors.GREEN_600
            self.start_pause_btn.text = "暫停練習"
            self.start_pause_btn.icon = ft.Icons.PAUSE
            self.start_pause_btn.bgcolor = ft.Colors.ORANGE_800
            self.stop_save_btn.disabled = False
        else:
            # 暫停
            self.is_timing = False
            self.total_seconds += (time.time() - self.current_start_time)
            self.status_text.value = "已暫停"
            self.status_text.color = ft.Colors.ORANGE_600
            self.start_pause_btn.text = "繼續練習"
            self.start_pause_btn.icon = ft.Icons.PLAY_ARROW
            self.start_pause_btn.bgcolor = ft.Colors.GREEN
        self.update()

    def save_record(self, e):
        # 結算時間
        if self.is_timing:
            self.total_seconds += (time.time() - self.current_start_time)
            self.is_timing = False

        duration_minutes = round(self.total_seconds / 60, 1)
        
        # 準備存檔資料
        new_record = {
            "date": date.today().strftime("%Y-%m-%d"),
            "piece": self.piece_input.value.strip(),
            "duration": max(duration_minutes, 0.1) if self.total_seconds > 0 else 0,
            "notes": self.notes_input.value or "無心得"
        }
        
        # 執行存檔
        DataManager.add_practice_record(new_record)
        
        # --- 提示通知：儲存成功 ---
        self.show_snack_bar(f"成功儲存：{new_record['piece']} 練習紀錄", color=ft.Colors.GREEN_700)
        
        # 重置 UI 狀態
        self.total_seconds = 0
        self.timer_display.value = "00:00:00"
        self.status_text.value = "待機中"
        self.status_text.color = ft.Colors.GREY_500
        self.piece_input.value = ""
        self.notes_input.value = ""
        self.start_pause_btn.text = "開始練習"
        self.start_pause_btn.icon = ft.Icons.PLAY_ARROW
        self.start_pause_btn.bgcolor = ft.Colors.GREEN
        self.stop_save_btn.disabled = True
        
        self.load_history()

    def load_history(self):
        all_data = DataManager.load_data().get("practice", [])
        self.history_list.controls.clear()
        # 使用 enumerate 獲取原始索引以便刪除
        for idx, item in reversed(list(enumerate(all_data))):
            self.history_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.BLUE),
                    title=ft.Text(f"{item['piece']} ({item['duration']} 分鐘)"),
                    subtitle=ft.Text(f"{item['date']} - {item['notes']}"),
                    trailing=ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE, 
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, i=idx: self.delete_record(i)
                    )
                )
            )
        self.update()

    def delete_record(self, index):
        # 執行刪除
        DataManager.delete_practice_record(index)
        
        # --- 提示通知：刪除成功 ---
        self.show_snack_bar("練習紀錄已永久刪除", color=ft.Colors.RED_700)
        
        self.load_history()