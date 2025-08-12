from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from argon2 import PasswordHasher

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'tbUsers'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String, nullable=False)
    user_email = db.Column(db.String, unique=True, nullable=False)
    user_pass = db.Column(db.String, nullable=False)
    user_phone = db.Column(db.String, nullable=False)
    user_cep = db.Column(db.String)
    user_city = db.Column(db.String)
    user_address = db.Column(db.String)
    user_num = db.Column(db.String)
    user_profile_photo = db.Column(db.String, default=None)

    def update_fields(self, **kwargs):
        """
        Atualiza apenas os campos fornecidos que são diferentes dos atuais
        """
        updated_fields = {}
        
        for field, new_value in kwargs.items():
            if hasattr(self, field) and new_value is not None:
                current_value = getattr(self, field)
                
                # Só atualiza se o valor for diferente
                if current_value != new_value and str(new_value).strip() != '':
                    setattr(self, field, new_value)
                    updated_fields[field] = new_value
        
        return updated_fields

    def safe_update(self, data_dict, allowed_fields=None):
        """
        Update seguro com lista de campos permitidos
        """
        if allowed_fields is None:
            allowed_fields = [
                'user_name', 'user_email', 'user_phone', 'user_cep',
                'user_city', 'user_address', 'user_num', 'user_profile_photo'
            ]
        
        # Filtra apenas campos permitidos e não vazios
        filtered_data = {k: v for k, v in data_dict.items() 
                        if k in allowed_fields and v is not None and str(v).strip() != ''}
        
        updated_fields = self.update_fields(**filtered_data)
        
        return {
            'success': len(updated_fields) > 0,
            'updated_fields': updated_fields,
            'total_changes': len(updated_fields)
        }

class Report(db.Model):
    __tablename__ = 'tbReport'
    rep_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rep_title = db.Column(db.String, nullable=False)
    rep_desc = db.Column(db.String)
    rep_city = db.Column(db.String)
    rep_address = db.Column(db.String)
    rep_date = db.Column(db.DateTime, default=datetime.utcnow)
    rep_phone = db.Column(db.String, default=None)
    rep_email = db.Column(db.String, default=None)
    rep_resolved = db.Column(db.Boolean, default=False)
    rep_photo = db.Column(db.String, default=None)
    rep_user_id = db.Column(db.Integer, db.ForeignKey('tbUsers.user_id'))

class Ong(db.Model):
    __tablename__ = 'tbOngs'
    ong_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ong_name = db.Column(db.String, nullable=False)
    ong_phone = db.Column(db.String)
    ong_email = db.Column(db.String, unique=True, nullable=False)
    ong_pass = db.Column(db.String, nullable=False)
    ong_cpf = db.Column(db.String)
    ong_cep = db.Column(db.String)
    ong_city = db.Column(db.String)
    ong_hood = db.Column(db.String)
    ong_address = db.Column(db.String)
    ong_num = db.Column(db.String)
    ong_desc = db.Column(db.String, default=None)
    ong_reportsResolved = db.Column(db.Integer, default=0)
    ong_rescuesResolved = db.Column(db.Integer, default=0)
    ong_profile_photo = db.Column(db.String, default=None)

class Rescue(db.Model):
    __tablename__ = 'tbRescues'
    resc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resc_date = db.Column(db.DateTime, default=datetime.utcnow)
    resc_desc = db.Column(db.String)
    resc_photo = db.Column(db.String)
    resc_author = db.Column(db.String)
    resc_phone = db.Column(db.String, default=None)
    resc_cep = db.Column(db.String)
    resc_city = db.Column(db.String)
    resc_addr = db.Column(db.String)
    resc_num = db.Column(db.String)
    resc_resolved = db.Column(db.Boolean, default=False)
    resc_user_id = db.Column(db.Integer, db.ForeignKey('tbUsers.user_id'))

# Funções de CRUD
def saveUser(name, email, password, phone, cep, city, addr, num, photo=None):
    if User.query.filter_by(user_email=email).first():
        return False
    ph = PasswordHasher()
    hashed_password = ph.hash(password)
    user = User(
        user_name=name,
        user_email=email,
        user_pass=hashed_password,
        user_phone=phone,
        user_cep=cep,
        user_city=city,
        user_address=addr,
        user_num=num,
        user_profile_photo=photo
    )
    db.session.add(user)
    db.session.commit()
    return True

def updateUser(user_id, **kwargs):
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'Usuário não encontrado'}
        
        result = user.safe_update(kwargs)
        
        if result['success']:
            db.session.commit()
            return {
                'success': True,
                'updated_fields': result['updated_fields'],
                'message': f"{result['total_changes']} campo(s) atualizado(s)"
            }
        else:
            return {
                'success': True,
                'message': 'Nenhuma alteração necessária',
                'updated_fields': {}
            }
            
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def saveOng(name, phone, email, password, cpf, cep, city, hood, address, num, photo=None, desc=None):
    if Ong.query.filter_by(ong_email=email).first():
        return False
    ph = PasswordHasher()
    hashed_password = ph.hash(password)
    ong = Ong(
        ong_name=name,
        ong_phone=phone,
        ong_email=email,
        ong_pass=hashed_password,
        ong_cpf=cpf,
        ong_cep=cep,
        ong_city=city,
        ong_hood=hood,
        ong_address=address,
        ong_num=num,
        ong_desc=desc,
        ong_profile_photo=photo
    )
    db.session.add(ong)
    db.session.commit()
    return True

def getUser(email):
    return User.query.filter_by(user_email=email).first()

def checkUser(email, password):
    user = getUser(email)
    if user:
        ph = PasswordHasher()
        try:
            if ph.verify(user.user_pass, password):
                return True
        except Exception as e:
            print(f"Erro ao verificar senha: {e}")
            return False
    return False

def checkOng(email, password):
    ong = getOng(email)
    if ong:
        ph = PasswordHasher()
        try:
            if ph.verify(ong.ong_pass, password):
                return True
        except Exception as e:
            print(f"Erro ao verificar senha: {e}")
            return False
    return False

def saveReport(title, desc, city, date, phone, photo=None, email=None, addr=None, userId=None):
    report = Report(
        rep_title=title,
        rep_desc=desc,
        rep_city=city,
        rep_address=addr,
        rep_date=datetime.strptime(date, '%Y-%m-%d'),
        rep_phone=phone,
        rep_email=email,
        rep_photo=photo,
        rep_user_id=userId
    )
    db.session.add(report)
    db.session.commit()
    return True

def saveRescue(desc, author, phone, cep, city, addr, num, photo=None, userId=None):
    rescue = Rescue(
        resc_desc=desc,
        resc_photo=photo,
        resc_author=author,
        resc_phone=phone,
        resc_cep=cep,
        resc_city=city,
        resc_addr=addr,
        resc_num=num,
        resc_user_id=userId
    )
    db.session.add(rescue)
    db.session.commit()
    return True

def showAllReports():
    return Report.query.all()

def showReportsByCity(city):
    return Report.query.filter_by(rep_city=city).all()

def showReportById(id):
    return Report.query.filter_by(rep_id=id).first()

def getAllRescues():
    return Rescue.query.all()

def getRescuesByCity(city):
    return Rescue.query.filter_by(resc_city=city).all()

def getRescueById(id):
    return Rescue.query.filter_by(resc_id=id).first()

def getAllOngs():
    return Ong.query.all()

def getOng(email):
    return Ong.query.filter_by(ong_email=email).first()