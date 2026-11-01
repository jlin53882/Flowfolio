import flet as ft
import csv
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# =========================
# 單一報價項目 Row 組件
# =========================
class QuoteItemRow(ft.Row):
    def __init__(self, on_delete, on_change):
        super().__init__()
        self.on_delete = on_delete
        self.on_change = on_change

        self.desc = ft.TextField(label="項目名稱", expand=3, dense=True, on_change=self.on_change)
        self.unit_price = ft.TextField(label="單價", expand=1, dense=True, value="0", text_align=ft.TextAlign.RIGHT, on_change=self.on_change)
        self.qty = ft.TextField(label="數量", expand=1, dense=True, value="1", text_align=ft.TextAlign.RIGHT, on_change=self.on_change)
        self.subtotal_text = ft.Text("$ 0", width=90, text_align=ft.TextAlign.RIGHT, weight="bold")

        self.controls = [
            self.desc, self.unit_price, self.qty, self.subtotal_text,
            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=lambda _: self.on_delete(self)),
        ]

    def get_subtotal(self):
        try:
            # 移除逗號並轉換數字
            price = float(self.unit_price.value.replace(",", "").strip() or 0)
            qty = float(self.qty.value.strip() or 0)
            subtotal = price * qty
            self.subtotal_text.value = f"$ {subtotal:,.0f}"
            return subtotal
        except ValueError:
            return 0

# =========================
# 報價主畫面容器
# =========================
class QuoteView(ft.Container):

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.padding = 30
        self.expand = True

        # --- 1. 初始化資料元件 ---
        self.client_name = ft.TextField(label="客戶名稱", value="貴業主", expand=True)
        self.quote_no = ft.TextField(label="報價單編號", value=datetime.now().strftime("%Y%m%d%H%M"), expand=True)

        self.tax_rate = ft.Dropdown(
            label="稅率設定",
            options=[
                ft.dropdown.Option("0", "不計稅"),
                ft.dropdown.Option("0.05", "營業稅 (5%)"),
            ],
            value="0",
            width=160,
            on_change=self.update_totals,
        )

        self.deposit_rate = ft.Slider(
            min=0,
            max=1,
            value=0.3,
            divisions=10,
            label="訂金比例: {value}",
            on_change=self.update_totals,
        )

        # 費用顯示
        self.subtotal_display = ft.Text("$ 0")
        self.tax_display = ft.Text("$ 0")
        self.total_display = ft.Text("$ 0", size=22, weight="bold", color=ft.Colors.BLUE_700)
        self.deposit_display = ft.Text("$ 0")
        self.balance_display = ft.Text("$ 0")

        # 項目列表
        self.items_column = ft.Column(spacing=10)
        self.items_column.controls.append(QuoteItemRow(self.delete_item, self.update_totals))

        # 結算卡片
        self.summary_card = ft.Column(
            [
                self._summary_row("項目小計", self.subtotal_display),
                self._summary_row("稅額 (VAT)", self.tax_display),
                self._summary_row("總計金額", self.total_display, big=True),
                ft.Divider(),
                self._summary_row("需付訂金", self.deposit_display),
                self._summary_row("剩餘尾款", self.balance_display),
            ],
            spacing=10,
        )

        # --- 2. UI 佈局（已避開 Flet 28.3 bug） ---
        self.content = ft.Row(
            [
                # 左側：報價編輯
                ft.Column(
                    [
                        ft.Text("報價單內容編輯", size=24, weight="bold"),
                        ft.Row([self.client_name, self.quote_no]),
                        ft.Divider(),
                        ft.Row(
                            [
                                ft.Text("服務項目明細", size=18, weight="w500"),
                                ft.ElevatedButton("新增項目", icon=ft.Icons.ADD, on_click=self.add_item),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            content=self.items_column,
                            padding=15,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=10,
                            bgcolor=ft.Colors.WHITE,
                        ),
                    ],
                    expand=2,
                    scroll=ft.ScrollMode.AUTO,
                ),

                # 右側：結算與輸出
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("費用結算", size=24, weight="bold"),
                            ft.Text("稅率與訂金設定", size=14, color=ft.Colors.GREY_600),
                            self.tax_rate,
                            self.deposit_rate,
                            ft.Container(
                                content=self.summary_card,
                                padding=25,
                                bgcolor=ft.Colors.BLUE_GREY_50,
                                border_radius=15,
                            ),
                            ft.Divider(),

                            # 兩個按鈕
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [ft.Icon(ft.Icons.PICTURE_AS_PDF), ft.Text("生成專業 PDF 報價單", weight="bold")],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                on_click=self.export_pdf,
                                width=350,
                                height=50,
                                bgcolor=ft.Colors.BLUE_900,
                                color=ft.Colors.WHITE,
                            ),

                            ft.OutlinedButton(
                                content=ft.Row(
                                    [ft.Icon(ft.Icons.FILE_DOWNLOAD), ft.Text("導出 Excel (CSV) 存檔")],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                on_click=self.export_excel,
                                width=350,
                                height=50,
                            ),
                            # 底部緩衝，避免捲動到底部時太擠
                            ft.Container(height=10),
                        ],
                        spacing=15,
                        scroll=ft.ScrollMode.AUTO, # 關鍵：內容超出時自動產生捲軸
                    ),
                    expand=1, # 保持佔據剩餘寬度
                    padding=ft.padding.only(right=10), # 給捲軸留一點寬度，避免擋到按鈕邊緣
                ),
            ],
            spacing=30,
        )

        # 初始計算
        self.update_totals(None)

    # =========================
    # 工具函數
    # =========================

    def _summary_row(self, title, value_control, big=False):
        return ft.Row(
            [
                ft.Text(title, size=18 if big else 14, weight="bold" if big else None),
                value_control,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def add_item(self, e):
        self.items_column.controls.append(QuoteItemRow(self.delete_item, self.update_totals))
        self.update_totals(None)

    def delete_item(self, row):
        if len(self.items_column.controls) > 1:
            self.items_column.controls.remove(row)
            self.update_totals(None)

    def update_totals(self, e):
        if not self.items_column.controls:
            return

        subtotal = sum(item.get_subtotal() for item in self.items_column.controls)
        tax = subtotal * float(self.tax_rate.value)
        total = subtotal + tax
        deposit = total * self.deposit_rate.value
        balance = total - deposit

        self.subtotal_display.value = f"$ {subtotal:,.0f}"
        self.tax_display.value = f"$ {tax:,.0f}"
        self.total_display.value = f"$ {total:,.0f}"
        self.deposit_display.value = f"$ {deposit:,.0f}"
        self.balance_display.value = f"$ {balance:,.0f}"

        try:
            self.update()
        except:
            pass


    def show_snack(self, message, color=ft.Colors.GREEN_600):
        if self.page:
            snack = ft.SnackBar(content=ft.Text(message), bgcolor=color)
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

    def export_pdf(self, e):
        """完全復刻 mtwmt 專業報價單格式"""
        print("開始生成 PDF...")
        try:
            # 檔案名稱處理
            safe_name = "".join([c for c in self.client_name.value if c.isalnum()]).strip() or "Client"
            filename = f"Quotation_{safe_name}_{datetime.now().strftime('%m%d')}.pdf"
            
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # 字型設定
            font_path = "C:/Windows/Fonts/msjh.ttc" # Windows
            if not os.path.exists(font_path): font_path = "/System/Library/Fonts/STHeiti Light.ttc" # Mac
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont("MSJH", font_path))
                font_name = "MSJH"
            else:
                font_name = "Helvetica"

            # --- 繪製頁面內容 ---
            # 1. Header & Logo
            if os.path.exists("logo.png"):
                c.drawImage("logo.png", 50, height-80, width=50, height=50, mask='auto')
            
            c.setFont(font_name, 24)
            c.drawString(120, height-70, "專案報價單")
            
            c.setFont(font_name, 10)
            c.setFillColor(colors.grey)
            c.drawString(450, height-60, f"單號: {self.quote_no.value}")
            c.drawString(450, height-75, f"日期: {datetime.now().strftime('%Y-%m-%d')}")

            # 2. 客戶資訊
            c.setFillColor(colors.black)
            c.setFont(font_name, 12)
            c.drawString(50, height-130, f"致客戶：{self.client_name.value}")
            
            # 3. 表格表頭
            y = height - 160
            c.setStrokeColor(colors.black)
            c.setLineWidth(1)
            c.line(50, y, 550, y)
            c.setFont(font_name, 11)
            c.drawString(60, y-20, "服務項目與說明")
            c.drawString(320, y-20, "數量")
            c.drawString(400, y-20, "單價")
            c.drawString(480, y-20, "小計")
            c.line(50, y-30, 550, y-30)

            # 4. 表格明細
            y -= 50
            for item in self.items_column.controls:
                c.setFont(font_name, 10)
                c.drawString(60, y, item.desc.value or "服務項目")
                c.drawString(320, y, item.qty.value)
                c.drawString(400, y, f"${float(item.unit_price.value):,.0f}")
                c.drawString(480, y, item.subtotal_text.value)
                y -= 25
                # 自動換頁判斷
                if y < 150:
                    c.showPage()
                    y = height - 50

            # 5. 結算區 (小計/稅額/總計)
            c.line(350, y, 550, y)
            y -= 25
            c.setFont(font_name, 10)
            c.drawString(360, y, f"小計 (Subtotal):")
            c.drawRightString(540, y, self.subtotal_display.value)
            y -= 20
            c.drawString(360, y, f"稅額 (VAT {int(float(self.tax_rate.value)*100)}%):")
            c.drawRightString(540, y, self.tax_display.value)
            y -= 30
            c.setFont(font_name, 14)
            c.setFillColor(colors.blue)
            c.drawString(360, y, "總計 (Total TWD):")
            c.drawRightString(540, y, self.total_display.value)

            # 6. 支付條件
            c.setFillColor(colors.black)
            c.setFont(font_name, 10)
            c.drawString(50, y, f"● 預付訂金：{self.deposit_display.value}")
            c.drawString(50, y-18, f"● 完工尾款：{self.balance_display.value}")

            c.save()
            self.show_snack(f"PDF 報價單已成功生成：{filename}")
            self.page.run_thread(lambda: self.page.run_thread(lambda: self.page.run_thread(lambda: os.startfile(filename)))) # 自動開啟

        except Exception as ex:
            print(f"PDF 錯誤: {ex}")
            self.show_snack(f"PDF 失敗: {ex}", color=ft.Colors.RED_400)

    def export_excel(self, e):
        """導出 CSV 存檔"""
        try:
            filename = f"Quote_{self.client_name.value}.csv"
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["報價項目", "單價", "數量", "小計"])
                for item in self.items_column.controls:
                    writer.writerow([item.desc.value, item.unit_price.value, item.qty.value, item.subtotal_text.value])
                writer.writerow([])
                writer.writerow(["總計金額", self.total_display.value])
            self.show_snack(f"CSV 已導出：{filename}")
            self.page.run_thread(lambda: self.page.run_thread(lambda: os.startfile(filename)))
        except Exception as ex:
            self.show_snack(f"CSV 錯誤: {ex}", color=ft.Colors.RED_400)