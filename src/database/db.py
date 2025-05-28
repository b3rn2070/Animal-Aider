import sqlite3 as sql
from datetime import datetime

class Database:
    def __init__(self, dbName):
        self.dbName = dbName
    
    def connect(self):
        return sql.connect(self.dbName)
    
    def createUser(self):
        with self.connect() as conn:
            cur = conn.cursor()

            query = '''CREATE TABLE IF NOT EXISTS tbUsers (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL UNIQUE,
                        user_pass TEXT NOT NULL,
                        user_city TEXT,
                        auth BOOLEAN DEFAULT 0
                    );'''
            cur.execute(query)
            conn.commit()
            conn.close()
    
    def createReport(self):
        with self.connect() as conn:
            cur = conn.cursor()

            query = '''CREATE TABLE IF NOT EXISTS tbReport (
                            rep_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rep_title TEXT NOT NULL,
                            rep_desc TEXT,
                            rep_region TEXT,
                            rep_anon BOOLEAN NOT NULL DEFAULT 0,
                            rep_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );'''
            cur.execute(query)
            conn.commit()
            conn.close()
        
    def createONG(self):
        with self.connect() as conn:
            cur = conn.cursor()

            query = '''CREATE TABLE IF NOT EXISTS tbOngs (
                            ong_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ong_name TEXT NOT NULL,
                            ong_phone TEXT,
                            ong_email TEXT NOT NULL UNIQUE,
                            ong_pass TEXT NOT NULL,
                            ong_address TEXT,
                            ong_cep TEXT,
                            ong_desc TEXT
                        );'''
            cur.execute(query)
            conn.commit()
            conn.close()

    def saveUser(self, email, password, city, auth=0):
        with self.connect() as conn:
            cur = conn.cursor()

            query = '''INSERT INTO tbUsers (*) VALUES (DEFAULT, ?, ?, ?, ?);'''
            cur.execute(query, (email, password, city, auth))
            conn.commit()
            conn.close()
            return True
            
    
    def getUser(self, email):
        with self.connect() as conn:
            cur = conn.cursor()

            query = "SELECT * FROM tbUsers WHERE user_email = ?"
            cur.execute(query, (email,))
            res = cur.fetchall()
            if res:
                return res
            else:
                return False
    
    def saveReport(self, title, desc, region, anon, date=None):
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with self.connect() as conn:
            cur = conn.cursor()

            query = '''INSERT INTO tbReports (*) VALUES(DEFAULT, ?, ?, ?, ?, ?);'''
            cur.execute(query, (title, desc, region, anon, date))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False



