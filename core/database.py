import sqlite3
from datetime import datetime
from typing import List, Dict

class Database:
    def __init__(self, db_path: str = "data/tracking.db"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracked_coins (
                coin_id TEXT PRIMARY KEY,
                entry_price REAL NOT NULL,
                start_time TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                notified_3_5 BOOLEAN DEFAULT 0,
                notified_5 BOOLEAN DEFAULT 0
            )
        """)
        self.conn.commit()

    def add_tracking(self, coin_id: str, price: float, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO tracked_coins VALUES (?, ?, ?, ?, 0, 0)",
            (coin_id, price, datetime.now().isoformat(), user_id)
        )
        self.conn.commit()

    def get_active_trackings(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tracked_coins")
        return cursor.fetchall()
