import sqlite3 as sql
from datetime import datetime
from argon2 import PasswordHasher

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
                        user_name TEXT NOT NULL,
                        user_email TEXT NOT NULL UNIQUE,
                        user_pass TEXT NOT NULL,
                        user_city TEXT
                    );'''
            cur.execute(query)
            conn.commit()
            
    
    def createReport(self):
        with self.connect() as conn:
            cur = conn.cursor()

            query = '''CREATE TABLE IF NOT EXISTS tbReport (
                            rep_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            rep_title TEXT NOT NULL,
                            rep_desc TEXT,
                            rep_city TEXT,
                            rep_anon BOOLEAN NOT NULL DEFAULT 0,
                            rep_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER DEFAULT NULL
                        );'''
            cur.execute(query)
            conn.commit()
            
        
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

    def saveUser(self, name, email, password, city):
        with self.connect() as conn:
            cur = conn.cursor()
            
            if self.getUser(email):
                return False
            else:
                query = '''INSERT INTO tbUsers (user_id, user_name, user_email, user_pass, user_city) VALUES (NULL, ?, ?, ?, ?);'''
                ph = PasswordHasher()
                password = ph.hash(password)
                cur.execute(query, (name, email, password, city))
                conn.commit()
                return True
    
    def getUser(self, email):
        with self.connect() as conn:
            cur = conn.cursor()

            query = "SELECT * FROM tbUsers WHERE user_email = ?"
            cur.execute(query, (email,))
            res = cur.fetchone()
            if res:
                return res
            else:
                return False
    
    def checkUser(self, email, password):
        user = self.getUser(email)
        if user:
            ph = PasswordHasher()
            if ph.verify(user[3], password):
                return True
            else:
                return False
    
    def saveReport(self, title, desc, city, anon, date=None):
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with self.connect() as conn:
            cur = conn.cursor()

            query = '''INSERT INTO tbReports (rep_title, rep_desc, rep_city, rep_anon, rep_date) VALUES(DEFAULT, ?, ?, ?, ?);'''
            cur.execute(query, (title, desc, city, anon, date))
            conn.commit()
            if cur.rowcount > 0:
                return True
            else:
                return False



