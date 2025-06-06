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
                            rep_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_email TEXT DEFAULT NULL
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
                            ong_desc TEXT,
                            ong_owner TEXT,
                            ong_phone_owner TEXT,
                            ong_cpf_owner TEXT
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
    
    def saveOng(self, name, phone, email, password, address, cep, owner, phone_owner, cpf, desc=None):
        with self.connect() as conn:
            cur = conn.cursor()
            
            if self.getOng(email):
                return False
            else:
                query = '''INSERT INTO tbOngs (ong_id, ong_name, ong_phone, ong_email, ong_pass, ong_address, ong_cep, ong_desc, ong_owner, ong_phone_owner, ong_cpf_owner) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?);'''
                ph = PasswordHasher()
                password = ph.hash(password)
                cur.execute(query, (name, phone, email, password, address, cep, desc, owner, phone_owner, cpf,))
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
            
    def updateUser(self, id, email, name=None, city=None):
        with self.connect() as conn:
            cur = conn.cursor()

            if name:
                query = "UPDATE tbUsers SET user_name = ? WHERE user_email = ?"
                cur.execute(query, (name, email))
            if city:
                query = "UPDATE tbUsers SET user_city = ? WHERE user_email = ?"
                cur.execute(query, (city, email))
            if email:
                query = "UPDATE tbUsers SET user_email = ? WHERE user_id = ?"
                cur.execute(query, (email, id))
            
            if conn.commit():
                return True
            else:
                return False
    
    def saveReport(self, title, desc, city, date=None, email=None):
        if email == None:
            email = 'NULL'

        date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')

        with self.connect() as conn:
            cur = conn.cursor()

            query = '''INSERT INTO tbReport (rep_id, rep_title, rep_desc, rep_city, rep_date, user_email) VALUES (NULL,?, ?, ?, ?, ?);'''
            cur.execute(query, (title, desc, city, date, email))
            if conn.commit():
                return True
            else:
                return False
    
    def showReports(self):
        with self.connect() as conn:
            cur = conn.cursor()

            query = "SELECT * FROM tbReport"
            cur.execute(query)
            res = cur.fetchall()
            return res
        
    def showOngs(self):
        with self.connect() as conn:
            cur = conn.cursor()

            query = "SELECT * FROM tbOngs WHERE 1 = 1"
            cur.execute(query)
            res = cur.fetchall()
            return res
        
    def getOng(self, email):
        with self.connect() as conn:
            cur = conn.cursor()

            query = "SELECT * FROM tbOngs WHERE ong_email = ?"
            cur.execute(query, (email,))
            res = cur.fetchone()
            if res:
                return res, True
            else:
                return False




