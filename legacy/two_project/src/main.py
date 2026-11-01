import flet as ft
from views.dashboard import DashboardView
from views.work_view import WorkView
from views.quote_view import QuoteView
from views.portfolio_view import PortfolioView
from views.practice_view import PracticeView

def main(page: ft.Page):
    page.title = "接案與練琴管理系統"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1100  # 稍微加寬，因為報價單現在是左右佈局
    page.window_height = 850
    
    # --- 1. 預先實例化 View (這樣切換分頁時，報價單輸入的內容不會消失) ---
    # 傳入 page 確保 QuoteView 內部的 SnackBar 和 PDF 功能可用
    views = {
        0: DashboardView(),
        1: WorkView(),
        2: QuoteView(page), # 關鍵：將 page 傳進去
        3: PortfolioView(),
        4: PracticeView(),
    }

    # 初始畫面設定
    content_area = ft.Container(content=views[0], expand=True)

    # --- 2. 優化切換邏輯 ---
    def nav_change(e):
        index = e.control.selected_index
        # 從預存的 dict 中抓取對應的 View
        content_area.content = views[index]
        page.update()

    # --- 3. 導航列 ---
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="總覽"),
            ft.NavigationBarDestination(icon=ft.Icons.LIST_ALT, label="工作紀錄"),
            ft.NavigationBarDestination(icon=ft.Icons.CALCULATE, label="報價估算"),
            ft.NavigationBarDestination(icon=ft.Icons.IMAGE, label="作品集"),
            ft.NavigationBarDestination(icon=ft.Icons.MUSIC_NOTE, label="練習紀錄"),
        ],
        on_change=nav_change,
        selected_index=0
    )

    page.add(content_area)

if __name__ == "__main__":
    ft.app(target=main)