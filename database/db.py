import sqlite3
from datetime import datetime
import json

class InventoryDB:
    def __init__(self, db_path="data/inventory.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    product TEXT NOT NULL,
                    factors TEXT,
                    strategy TEXT,
                    logistics TEXT
                )
            """)
    
    def add_record(self, record_data: dict):
        """添加新记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO inventory_records 
                (timestamp, product, factors, strategy, logistics)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                record_data["product"],
                json.dumps(record_data["factors"], ensure_ascii=False),
                json.dumps(record_data["strategy"], ensure_ascii=False),
                json.dumps(record_data["logistics"], ensure_ascii=False)
            ))
    
    def add_records(self, records: list):
        """批量添加记录"""
        with sqlite3.connect(self.db_path) as conn:
            data_to_insert = [
                (
                    datetime.now().isoformat(),
                    record["product"],
                    json.dumps(record["factors"], ensure_ascii=False),
                    json.dumps(record["strategy"], ensure_ascii=False),
                    json.dumps(record["logistics"], ensure_ascii=False)
                )
                for record in records
            ]
            conn.executemany("""
                INSERT INTO inventory_records 
                (timestamp, product, factors, strategy, logistics)
                VALUES (?, ?, ?, ?, ?)
            """, data_to_insert)
    
    def get_recent_records(self, limit: int = 5):
        """获取最近的记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM inventory_records 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            records = []
            for row in cursor:
                records.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "product": row[2],
                    "factors": json.loads(row[3]),
                    "strategy": json.loads(row[4]),
                    "logistics": json.loads(row[5])
                })
            return records
    
    def search_records(self, query: str, limit: int = 3):
        """搜索相关记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM inventory_records 
                WHERE product LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{query}%", limit))
            
            records = []
            for row in cursor:
                records.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "product": row[2],
                    "factors": json.loads(row[3]),
                    "strategy": json.loads(row[4]),
                    "logistics": json.loads(row[5])
                })
            return records
