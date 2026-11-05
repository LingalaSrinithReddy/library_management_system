import sqlite3
import csv
import json

class Database:
    def __init__(self, db_name="library.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        pass  # tables will be added in the next step
    
    def close(self):
        self.conn.close()