import json
import os
from models.work import WorkRecord
from pathlib import Path

class DataManager:
    # 1. 取得當前檔案 (data_manager.py) 的絕對路徑
    # 2. .parent 是 controllers, .parent.parent 是 src
    BASE_SRC_DIR = Path(__file__).resolve().parent.parent
    
    # 3. 定位到 src/data/records.json
    DATA_DIR = os.path.join(BASE_SRC_DIR, "data")
    DATA_PATH = os.path.join(DATA_DIR, "records.json")

    @classmethod
    def _ensure_data_dir(cls):
        """確保 src/data 資料夾與 records.json 存在"""
        # 如果 src/data 不存在就建立
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)
            
        if not os.path.exists(cls.DATA_PATH):
            with open(cls.DATA_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "works": [], 
                    "practice": [], 
                    "portfolio": [],
                    "todos": []
                }, f, indent=4, ensure_ascii=False)

    @classmethod
    def load_data(cls):
        """讀取 JSON 檔案"""
        cls._ensure_data_dir()
        try:
            with open(cls.DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"works": [], "practice": [], "portfolio": [], "todos": []}

    @classmethod
    def _save_to_file(cls, data):
        """存檔至 src/data/records.json"""
        cls._ensure_data_dir()
        with open(cls.DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    # --- 工作紀錄 (Works) 相關 ---
    @classmethod
    def add_work_record(cls, record: WorkRecord):
        data = cls.load_data()
        data["works"].append(record.to_dict())
        cls._save_to_file(data)

    @classmethod
    def get_all_works(cls):
        return cls.load_data().get("works", [])

    # --- 練習紀錄 (Practice) 相關 ---
    @classmethod
    def add_practice_record(cls, record_dict):
        """新增練習紀錄"""
        data = cls.load_data()
        if "practice" not in data:
            data["practice"] = []
        data["practice"].append(record_dict)
        cls._save_to_file(data)

    @classmethod
    def delete_practice_record(cls, index):
        """根據索引刪除練習紀錄"""
        data = cls.load_data()
        if "practice" in data and 0 <= index < len(data["practice"]):
            data["practice"].pop(index)
            cls._save_to_file(data)

    # --- 作品集 (Portfolio) 相關 ---
    @classmethod
    def save_all_portfolio(cls, new_data):
        """
        [重要] 用於覆蓋整個 portfolio 列表
        當進行刪除、搜尋後重新排序等操作時使用
        """
        data = cls.load_data()
        data["portfolio"] = new_data
        cls._save_to_file(data)


    @classmethod
    def add_portfolio_item(cls, item_dict):
        """新增作品項目"""
        data = cls.load_data()
        if "portfolio" not in data:
            data["portfolio"] = []
        data["portfolio"].append(item_dict)
        cls._save_to_file(data)

    @classmethod
    def delete_portfolio_item(cls, index):
        """根據索引刪除作品項目"""
        data = cls.load_data()
        if "portfolio" in data and 0 <= index < len(data["portfolio"]):
            data["portfolio"].pop(index)
            cls._save_to_file(data)

    @classmethod
    def delete_work_record(cls, index):
        data = cls.load_data()
        if "works" in data and 0 <= index < len(data["works"]):
            data["works"].pop(index)
            cls._save_to_file(data)

    @classmethod
    def _ensure_data_dir(cls):
        # ... 前面的程式碼保持不變
        if not os.path.exists(cls.DATA_PATH):
            with open(cls.DATA_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "works": [], 
                    "practice": [], 
                    "portfolio": [],
                    "todos": []  # 新增這一行
                }, f, indent=4, ensure_ascii=False)

    @classmethod
    def add_todo_record(cls, todo_dict):
        """新增待辦事項"""
        data = cls.load_data()
        if "todos" not in data: data["todos"] = []
        data["todos"].append(todo_dict)
        cls._save_to_file(data)