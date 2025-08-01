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
                        user_phone TEXT NOT NULL,
                        user_cep TEXT,
                        user_city TEXT,
                        user_address TEXT,
                        user_num TEXT,
                        user_profile_photo TEXT DEFAULT NULL
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
                            rep_address TEXT,
                            rep_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            rep_phone TEXT DEFAULT NULL,
                            rep_email TEXT DEFAULT NULL,
                            rep_resolved BOOLEAN DEFAULT 0,
                            rep_photo TEXT DEFAULT NULL,
                            rep_user_id INTEGER,
                            FOREIGN KEY (rep_user_id) REFERENCES tbUsers(user_id)
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
                            ong_cpf TEXT,
                            ong_cep TEXT,
                            ong_city TEXT,
                            ong_hood TEXT,
                            ong_address TEXT,
                            ong_num TEXT,
                            ong_desc TEXT,
                            ong_reportsResolved INTEGER DEFAULT 0,
                            ong_profile_photo TEXT DEFAULT NULL
                        );'''
            cur.execute(query)
            conn.commit()

    def createRescue(self):
        with self.connect() as conn:
            cur = conn.cursor()

            query = ''' CREATE TABLE IF NOT EXISTS tbRescues (
                            resc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            resc_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            resc_desc TEXT,
                            resc_photo TEXT,
                            resc_author TEXT,
                            resc_phone TEXT,
                            resc_cep TEXT,
                            resc_addr TEXT,
                            resc_num TEXT,
                            resc_resolved BOOLEAN DEFAULT 0,
                            resc_photo TEXT DEFAULT NULL,
                            resc_user_id INTEGER,
                            FOREIGN KEY (resc_user_id) REFERENCES tbUsers(user_id)
                    );'''
            cur.execute(query)
            conn.commit()

    def saveUser(self, name, email, password, phone, cep, city, addr, num):
        with self.connect() as conn:
            cur = conn.cursor()
            
            if self.getUser(email):
                return False
            else:
                query = '''INSERT INTO tbUsers (user_id, user_name, user_email, user_pass, user_phone, user_cep, user_city, user_address, user_num ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?);'''
                ph = PasswordHasher()
                password = ph.hash(password)
                cur.execute(query, (name, email, password, phone, cep, city, addr, num))
                conn.commit()
                return True

    def saveOng(self, name, phone, email, password, cpf, cep, city, hood, address, num, desc=None):
        with self.connect() as conn:
            cur = conn.cursor()
            
            if self.getOng(email):
                return False
            else:
                query = '''INSERT INTO tbOngs (ong_id, ong_name, ong_phone, ong_email, ong_pass, ong_cpf, ong_cep, ong_city, ong_hood, ong_address, ong_num, ong_desc) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'''
                ph = PasswordHasher()
                password = ph.hash(password)
                cur.execute(query, (name, phone, email, password, cpf, cep, city, hood, address, num, desc))
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
            try:
                if ph.verify(user[3], password):
                    return True
            except Exception as e:
                print(f"Erro ao verificar senha: {e}")
                return False
        return False
    
    def checkOng(self, email, password):
        ong = self.getOng(email)
        if ong:
            ph = PasswordHasher()
            try:
                if ph.verify(ong[4], password): 
                    return True
            except Exception as e:
                print(f"Erro ao verificar senha: {e}")
                return False
        return False 
            
    def updateUser(self, id, email=None, name=None, city=None):
        with self.connect() as conn:
            cur = conn.cursor()

            fields = []
            values = []

            if name:
                fields.append("user_name = ?")
                values.append(name)
            if city:
                fields.append("user_city = ?")
                values.append(city)
            if email:
                fields.append("user_email = ?")
                values.append(email)

            if not fields:
                return False  

            query = f"UPDATE tbUsers SET {', '.join(fields)} WHERE user_id = ?"
            values.append(id)  

            try:
                cur.execute(query, tuple(values))
                conn.commit()
                return True
            except Exception as e:
                print(f"Erro ao atualizar usuário: {e}")
                return False


    def saveReport(self, title, desc, city, date, phone, email=None, addr=None):
        if email == None:
            email = 'NULL'
        
        if addr == None:
            addr = 'NULL'

        date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')

        with self.connect() as conn:
            cur = conn.cursor()

            query = '''INSERT INTO tbReport (rep_id, rep_title, rep_desc, rep_city, rep_addr, rep_date, rep_phone, rep_email) VALUES (NULL,?, ?, ?, ?, ?, ?, ?);'''
            cur.execute(query, (title, desc, city, addr, date, phone, email))
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
                return res
            else:
                return False




