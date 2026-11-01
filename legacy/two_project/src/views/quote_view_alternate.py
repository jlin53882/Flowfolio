import flet as ft
import csv
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

class QuoteView(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 30
        self.expand = True
        self.current_price = 0
        
        # --- 輸入欄位 (左側控制區) ---
        self.client_name = ft.TextField(label="客戶名稱", value="貴業主", border_radius=10)
        self.project_name = ft.TextField(label="專案名稱", value="年度攝影服務專案", border_radius=10)
        
        self.hour_slider = ft.Slider(min=1, max=100, value=8, divisions=99, label="{value}小時", on_change=self.calculate)
        self.type_drop = ft.Dropdown(
            label="服務類型",
            options=[ft.dropdown.Option("攝影服務"), ft.dropdown.Option("平面設計"), ft.dropdown.Option("活動企劃")],
            value="攝影服務",
            on_change=self.calculate
        )
        self.hard_switch = ft.Switch(label="急件 / 高難度加成", value=False, on_change=self.calculate)
        
        self.price_display = ft.Text("$ 0", size=45, weight="bold", color=ft.Colors.BLUE_700)

        # --- 配置 UI 佈局 ---
        self.content = ft.Row([
            # 左側：控制面板
            ft.Container(
                content=ft.Column([
                    ft.Text("報價參數設定", size=24, weight="bold"),
                    self.client_name,
                    self.project_name,
                    ft.Divider(),
                    ft.Text("預估總工時"),
                    self.hour_slider,
                    self.type_drop,
                    self.hard_switch,
                    ft.Divider(),
                    ft.Text("建議報價總額", size=16),
                    self.price_display,
                ], spacing=20, scroll=ft.ScrollMode.AUTO),
                expand=1, padding=20, bgcolor=ft.Colors.GREY_50, border_radius=15
            ),
            
            # 右側：操作與導出
            ft.Container(
                content=ft.Column([
                    ft.Text("報價單導出選項", size=24, weight="bold"),
                    ft.Text("預覽資訊：", size=16, color=ft.Colors.GREY_700),
                    ft.Text(f"• 項目：{self.project_name.value}", size=14),
                    ft.Text("導出格式：", size=16, weight="bold"),
                    ft.ElevatedButton(
                        "導出專業 PDF 報價單", 
                        icon=ft.Icons.PICTURE_AS_PDF, 
                        on_click=self.export_pdf, 
                        height=50, width=300,
                        bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE
                    ),
                    ft.ElevatedButton(
                        "導出 Excel (CSV) 存檔", 
                        icon=ft.Icons.GRID_ON, 
                        on_click=self.export_excel,
                        height=50, width=300
                    ),
                    ft.Text("註：PDF 將包含您的 Logo 與詳細分項表", size=12, color=ft.Colors.GREY_500),
                ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
                expand=1, padding=40, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=15
            )
        ], spacing=30)
        
        self.calculate(None)

    def calculate(self, e):
        base_rate = 1200  # 提高基礎時薪
        base_total = self.hour_slider.value * base_rate
        multiplier = 1.3 if "攝影" in self.type_drop.value else 1.1 if "設計" in self.type_drop.value else 1.0
        if self.hard_switch.value: multiplier *= 1.5
            
        self.current_price = round(base_total * multiplier)
        self.price_display.value = f"$ {self.current_price:,}"
        try: self.update()
        except: pass

    def export_pdf(self, e):
        filename = f"報價單_{self.client_name.value}_{datetime.now().strftime('%m%d')}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        # 1. 註冊字體
        try:
            pdfmetrics.registerFont(TTFont('MSJH', 'C:/Windows/Fonts/msjh.ttc'))
            font_main = 'MSJH'
        except: font_main = 'Helvetica'

        # 2. 繪製 Logo (假設檔案為 logo.png)
        if os.path.exists("logo.png"):
            c.drawImage("logo.png", 50, height - 100, width=60, height=60, mask='auto')
        
        # 3. 標題與基本資訊
        c.setFont(font_main, 24)
        c.drawString(130, height - 80, "專案報價單 (Quotation)")
        
        c.setFont(font_main, 10)
        c.setFillColor(colors.grey)
        c.drawString(450, height - 60, f"編號：{datetime.now().strftime('%Y%m%d%H%M')}")
        c.drawString(450, height - 75, f"日期：{datetime.now().strftime('%Y-%m-%d')}")

        # 4. 客戶與專案資訊
        c.setFillColor(colors.black)
        c.setFont(font_main, 12)
        c.drawString(50, height - 150, f"致：{self.client_name.value}")
        c.drawString(50, height - 170, f"專案：{self.project_name.value}")

        # 5. 明細表格 (模擬 mtwmt 格式)
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(50, height - 190, 550, height - 190) # 表頭線
        
        c.setFont(font_main, 11)
        c.drawString(60, height - 210, "服務項目")
        c.drawString(300, height - 210, "預估工時")
        c.drawString(400, height - 210, "單價")
        c.drawString(480, height - 210, "合計")
        
        c.line(50, height - 220, 550, height - 220) # 表頭下線

        # 填入內容
        c.drawString(60, height - 245, f"{self.type_drop.value} - {self.project_name.value}")
        c.drawString(300, height - 245, f"{self.hour_slider.value} 小時")
        c.drawString(400, height - 245, "$ 1,200")
        c.drawString(480, height - 245, f"${self.current_price:,}")
        
        if self.hard_switch.value:
            c.setFont(font_main, 9)
            c.drawString(60, height - 260, "(包含急件加成費用)")

        # 6. 總計區塊
        c.line(350, height - 300, 550, height - 300)
        c.setFont(font_main, 16)
        c.drawString(350, height - 330, "總計金額 (TWD):")
        c.setFillColor(colors.blue)
        c.drawRightString(540, height - 330, f"$ {self.current_price:,}")

        # 7. 頁尾備註
        c.setFillColor(colors.black)
        c.setFont(font_main, 9)
        c.drawString(50, 100, "備註：")
        c.drawString(50, 85, "1. 本報價單自發出日起 7 天內有效。")
        c.drawString(50, 70, "2. 最終服務內容以合約簽訂為準。")

        c.save()
        self.notify(f"PDF 報價單已生成：{filename}")
        if os.name == 'nt': os.startfile(filename)

    def export_excel(self, e):
        filename = f"報價存檔_{self.client_name.value}.csv"
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["報價單資訊", "內容"])
            writer.writerow(["客戶", self.client_name.value])
            writer.writerow(["專案", self.project_name.value])
            writer.writerow(["類型", self.type_drop.value])
            writer.writerow(["總金額", self.current_price])
        self.notify(f"Excel 已存檔：{filename}")

    def notify(self, msg):
        self.page.overlay.append(ft.SnackBar(content=ft.Text(msg), open=True))
        self.page.update()