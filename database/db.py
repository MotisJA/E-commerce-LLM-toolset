import sqlite3
from datetime import datetime
import json
import os

class InventoryDB:
    def __init__(self, db_path="data/inventory.db"):
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            # 删除旧表
            conn.execute("DROP TABLE IF EXISTS inventory_records")
            
            # 创建新表，添加字段长度限制
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL CHECK(length(timestamp) <= 50),
                    product TEXT NOT NULL CHECK(length(product) <= 100),
                    factors TEXT NOT NULL CHECK(length(factors) <= 1000),
                    strategy TEXT NOT NULL CHECK(length(strategy) <= 500),
                    logistics TEXT NOT NULL CHECK(length(logistics) <= 500)
                )
            """)
            
            # 创建索引优化查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_product 
                ON inventory_records(product)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON inventory_records(timestamp)
            """)
    
    def add_record(self, record_data: dict):
        """添加新记录，确保字段名匹配"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO inventory_records 
                (timestamp, product, factors, strategy, logistics)
                VALUES (?, ?, ?, ?, ?)
            """, (
                record_data.get("timestamp", datetime.now().isoformat()),
                record_data["product"],
                json.dumps(record_data.get("factors", {}), ensure_ascii=False),
                record_data.get("strategy", ""),
                record_data.get("logistics", "默认物流方案")
            ))
    
    def add_records(self, records: list):
        """批量添加记录"""
        with sqlite3.connect(self.db_path) as conn:
            data_to_insert = [
                (
                    record.get("timestamp", datetime.now().isoformat()),
                    record["product"],
                    json.dumps(record.get("factors", {}), ensure_ascii=False),
                    record.get("strategy", ""),
                    record.get("logistics", "")
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
                    "strategy": row[4],
                    "logistics": row[5]
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
                    "strategy": row[4],
                    "logistics": row[5]
                })
            return records
