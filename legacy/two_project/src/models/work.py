from datetime import date

class WorkRecord:

# 修改 __init__
    def __init__(self, name, type_, date_str=None, hours=0, income=0, notes=""):
        self.name = name
        self.type = type_
        # 如果沒給日期，自動抓今天
        self.date = date_str if date_str else date.today().strftime("%Y-%m-%d")
        self.hours = float(hours)
        self.income = float(income)
        self.notes = notes

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,    # 存檔時去掉底線，方便 View 讀取
            "date": self.date,
            "hours": self.hours,
            "income": self.income,
            "notes": self.notes
        }