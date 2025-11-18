import os
import uuid
import logging
import secrets
import requests
from datetime import timedelta
from sqlalchemy import and_
from flask import (
    Flask, request, render_template, session,
    redirect, url_for, flash, jsonify
)
from extensions import db
from db import *


UPLOAD_FOLDER = 'src/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

random_key = secrets.token_hex(16)
app = Flask(__name__, template_folder="../templates", static_folder="../static")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animal_aider.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = random_key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

with app.app_context():
    db.create_all()

url_ibge = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/SP/municipios"
res = requests.get(url_ibge)
data = res.json()
cities = [cidade['nome'] for cidade in data]

def checkExtension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    if session.get('ong_logged') and request.method == 'GET':
        city = session.get('ong_city')

        reports = Report.query.filter(
            and_(
                Report.rep_city == city,
                Report.rep_status == 'pendente')
            ).all()
        
        rescues = Rescue.query.filter(
            and_(
                Rescue.resc_city == city,
                Rescue.resc_status == 'pendente'
            )
        ).all()  

        return render_template("ong_index.html", reports=reports, rescues=rescues)

    if session.get('logged') and request.method == 'GET':
        city = session.get('user_city')
        ongs = Ong.query.filter(Ong.ong_city.ilike(f'%{city}%')).all()
    else:
        ongs = Ong.query.all()

    return render_template("index.html", ongs=ongs)

@app.route("/accept_report/<int:report_id>", methods=['POST'])
def accept_report(report_id):
    if not session.get('ong_logged'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        report = Report.query.get_or_404(report_id)
        
        if report.rep_city != session.get('ong_city'):
            return jsonify({'success': False, 'message': 'Denúncia não pertence à sua cidade'}), 403
        
        report.rep_status = 'andamento'
        report.rep_ong_id = session.get('ong_id')
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Denúncia aceita com sucesso!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao aceitar denúncia: {str(e)}'}), 500

@app.route("/reject_report/<int:report_id>", methods=['POST'])
def reject_report(report_id):
    if not session.get('ong_logged'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        report = Report.query.get_or_404(report_id)
        
        if report.rep_city != session.get('ong_city'):
            return jsonify({'success': False, 'message': 'Denúncia não pertence à sua cidade'}), 403
        
        report.rep_status = 'rejeitado'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Denúncia rejeitada com sucesso!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao rejeitar denúncia: {str(e)}'}), 500

@app.route("/accept_rescue/<int:rescue_id>", methods=['POST'])
def accept_rescue(rescue_id):
    if not session.get('ong_logged'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        rescue = Rescue.query.get_or_404(rescue_id)
        
        if rescue.resc_city != session.get('ong_city'):
            return jsonify({'success': False, 'message': 'Resgate não pertence à sua cidade'}), 403
        
        rescue.resc_status = 'andamento'
        rescue.resc_ong_id = session.get('ong_id')
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Resgate aceito com sucesso!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao aceitar resgate: {str(e)}'}), 500

@app.route("/reject_rescue/<int:rescue_id>", methods=['POST'])
def reject_rescue(rescue_id):
    if not session.get('ong_logged'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    try:
        rescue = Rescue.query.get_or_404(rescue_id)
        
        if rescue.resc_city != session.get('ong_city'):
            return jsonify({'success': False, 'message': 'Resgate não pertence à sua cidade'}), 403
        
        rescue.resc_status = 'rejeitado'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Resgate rejeitado com sucesso!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao rejeitar resgate: {str(e)}'}), 500
    
@app.route('/delReport/<int:id>', methods=['POST'])
def delReport(id):
    user_id = session.get('user_id')

    if not user_id:
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': 'Usuário não autenticado.'})
        flash('Usuário não autenticado.', 'warning')
        return redirect(url_for('login'))

    report = Report.query.filter(
        and_(
            Report.rep_id == id,
            Report.rep_user_id == user_id
        )
    ).first()

    if report:
        db.session.delete(report)
        db.session.commit()
        message = 'Denúncia deletada com sucesso!'
        
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': True, 'message': message})
        
        flash(message, 'success')
    else:
        message = 'Denúncia não encontrada ou acesso negado.'
        
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': message})
        
        flash(message, 'danger')

    return redirect(url_for('user_reports'))  

@app.route('/delRescue/<int:id>', methods=['POST'])
def delRescue(id):
    user_id = session.get('user_id')

    if not user_id:
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': 'Usuário não autenticado.'})
        flash('Usuário não autenticado.', 'warning')
        return redirect(url_for('login'))

    rescue = Rescue.query.filter(
        and_(
            Rescue.resc_id == id, 
            Rescue.resc_user_id == user_id  
        )
    ).first()

    if rescue:
        db.session.delete(rescue)
        db.session.commit()
        message = 'Resgate deletado com sucesso!'
        
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': True, 'message': message})
        
        flash(message, 'success')
    else:
        message = 'Resgate não encontrado ou acesso negado.'
        
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': message})
        
        flash(message, 'error')

    return redirect(url_for('user_rescues'))
        

@app.route("/login", methods=['POST', 'GET'])
def login():
    if session.get('logged') or session.get('ong_logged'):
        flash('Você já está logado!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if request.form.get('email') and request.form.get('password'):
            email = request.form.get('email')
            password = request.form.get('password')

            if checkUser(email, password):
                user = getUser(email)

                session['logged'] = 1
                session['user_id'] = user.user_id
                session['user_name'] = user.user_name
                session['user_email'] = user.user_email
                session['user_phone'] = user.user_phone
                session['user_cep'] = user.user_cep
                session['user_city'] = user.user_city
                session['user_addr'] = user.user_address
                session['user_num'] = user.user_num

                flash('Login bem-sucedido!', 'success')
                return redirect(url_for('index'))
            else:
                flash('email e/ou senha inválidos', 'error')    
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route("/register", methods=['POST', 'GET'])
def register():
    if session.get('logged') or session.get('ong_logged'):
        flash('Você já está logado!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if request.form.get('email') and request.form.get('password') and request.form.get('city') and request.form.get('name') and request.form.get('phone'):
            email = request.form.get('email')
            password = request.form.get('password')
            city = request.form.get('city')
            name = request.form.get('name')
            phone = request.form.get('phone')
            cep = request.form.get('cep')
            addr = request.form.get('addr')
            num = request.form.get('num')
            photo = request.files['photo']

            if getUser(email):
                flash('Usuário já existe!', 'error')
                return redirect(url_for('register'))

            if not photo:
                new_filename = 'default_profile.jpg'
            elif photo and checkExtension(photo.filename):

                extension = photo.filename.rsplit('.', 1)[1].lower()  
                new_filename = str(uuid.uuid4()) + '.' + extension  
                try:
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                except Exception as e:
                    flash('Houve um erro. Tente Novamente', 'error')
                    print(e)
                    return redirect(url_for('register'))
                    
            if saveUser(name, email, password, phone, cep, city, addr, num, new_filename):
                flash('Usuário registrado com sucesso!', 'success')
                return redirect(url_for('login'))

        else:
            flash('Erro ao registrar usuário. Verifique os dados.', 'error')
    return render_template('register.html', cities=cities)

@app.route("/report", methods=['POST', 'GET'])
def report():
    hoje = dt.today()
    min_data = hoje - timedelta(days=2)
    max_data = hoje
    
    max_data_str = max_data.strftime('%Y-%m-%d')
    min_data_str = min_data.strftime('%Y-%m-%d')
    
    if session.get('ong_logged'):
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('report.html', 
                             min_data=min_data_str, 
                             max_data=max_data_str, 
                             cities=cities)
    
    try:
        required_fields = ['title', 'desc', 'date', 'city']
        missing_fields = [field for field in required_fields 
                         if not request.form.get(field, '').strip()]
        
        user_logged = session.get('logged')
        if not user_logged:
            if not request.form.get('phone', '').strip():
                missing_fields.append('phone')
        
        photo = request.files['photo']
        if not photo or not photo.filename:
            flash('A foto do avistamento é obrigatória.', 'error')
            return render_template('report.html', 
                                 min_data=min_data_str, 
                                 max_data=max_data_str, 
                                 cities=cities)
        
        if missing_fields:
            flash('Preencha todos os campos obrigatórios.', 'error')
            return render_template('report.html', 
                                 min_data=min_data_str, 
                                 max_data=max_data_str, 
                                 cities=cities)
        
        data = {
            'title': request.form.get('title').strip(),
            'desc': request.form.get('desc').strip(),
            'date': request.form.get('date').strip(),
            'city': request.form.get('city').strip(),
            'addr': request.form.get('addr', '').strip() or None,
        }
        
        if user_logged:
            data['email'] = session.get('user_email')
            data['phone'] = session.get('user_phone') 
            data['userId'] = session.get('user_id')
        else:
            data['email'] = request.form.get('email', '').strip() or None
            data['phone'] = request.form.get('phone', '').strip()
            data['userId'] = None
        
        photo_filename = None
        if photo and checkExtension(photo.filename):
            try:
                extension = photo.filename.rsplit('.', 1)[1].lower()
                photo_filename = str(uuid.uuid4()) + '.' + extension
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            except Exception as e:
                logging.error(f"Erro no upload: {e}")
                flash('Erro ao fazer upload da imagem.', 'error')
                return render_template('report.html', 
                                     min_data=min_data_str, 
                                     max_data=max_data_str, 
                                     cities=cities)
        else:
            flash('Formato de imagem inválido. Use apenas PNG, JPG, JPEG ou GIF.', 'error')
            return render_template('report.html', 
                                 min_data=min_data_str, 
                                 max_data=max_data_str, 
                                 cities=cities)
        
        if saveReport(
            title=data['title'],
            desc=data['desc'],
            city=data['city'],
            date=data['date'],
            phone=data['phone'],
            photo=photo_filename,
            email=data['email'],
            addr=data['addr'],
            userId=data['userId']
        ):
            if user_logged:
                flash('Relatório enviado com sucesso!', 'success')
            else:
                flash('Denúncia anônima enviada com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            if photo_filename:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                except:
                    pass
            flash('Erro ao salvar relatório. Tente novamente.', 'error')
    
    except Exception as e:
        logging.error(f"Erro na rota report: {e}")
        flash('Erro interno. Tente novamente.', 'error')
    
    return render_template('report.html', 
                         min_data=min_data_str, 
                         max_data=max_data_str, 
                         cities=cities)

@app.route('/ver_dados')
def ver_dados():
    dados = []
    dados = showAllReports()
    return render_template('dados.html', dados=dados)

@app.route('/user', methods=['GET', 'POST'])
def user():
    if not session.get('logged'):
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    if session.get('ong_logged'):
        return redirect(url_for('index'))

    user = User.query.filter_by(user_email=session.get('user_email')).first()
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')

    if request.method == 'POST':
        try:
            form_data = {
                'user_name': request.form.get('name'),
                'user_city': request.form.get('city'),
                'user_email': request.form.get('email'),
                'user_phone': request.form.get('phone'),
                'user_cep': request.form.get('cep'),
                'user_address': request.form.get('addr'),  
                'user_num': request.form.get('num')
            }
            
            form_data = {k: v for k, v in form_data.items() if v and v.strip()}
            
            if not form_data and 'photo' not in request.files:
                flash('Nenhum dado foi fornecido para atualização.', 'warning')
                return redirect(url_for('user'))
            
            if 'user_email' in form_data and form_data['user_email'] != user.user_email:
                existing_user = User.query.filter_by(user_email=form_data['user_email']).first()
                if existing_user:
                    flash('Este email já está sendo usado por outro usuário.', 'error')
                    return redirect(url_for('user'))
            
            new_filename = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename and checkExtension(photo.filename):
                    extension = photo.filename.rsplit('.', 1)[1].lower()
                    new_filename = str(uuid.uuid4()) + '.' + extension
                    
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    form_data['user_profile_photo'] = new_filename
                    
                    if user.user_profile_photo:
                        old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], user.user_profile_photo)
                        if os.path.exists(old_photo_path):
                            try:
                                os.remove(old_photo_path)
                            except:
                                pass  
                    
                elif photo and photo.filename: 
                    flash('Extensão de arquivo não suportada.', 'error')
                    return redirect(url_for('user'))
            
            result = updateUser(user_id, **form_data)
            
            if result['success']:
                if result.get('updated_fields'):
                    flash(f'Dados atualizados com sucesso! {result["message"]}', 'success')
                    
                    updated_fields = result['updated_fields']
                    if 'user_email' in updated_fields:
                        session['user_email'] = updated_fields['user_email']
                    if 'user_name' in updated_fields:
                        session['user_name'] = updated_fields['user_name']
                    if 'user_city' in updated_fields:
                        session['user_city'] = updated_fields['user_city']
                else:
                    flash('Nenhuma alteração foi necessária.', 'info')
            else:
                flash(f'Erro ao atualizar dados: {result.get("error", "Erro desconhecido")}', 'error')
                
        except Exception as e:
            flash(f'Erro interno: {str(e)}', 'error')
            
        return redirect(url_for('user'))

    return render_template('user.html', user=user, cidades=cities)

@app.route('/ong_register', methods=['GET', 'POST'])
def ong_register():
    if session.get('ong_logged') or session.get('logged'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        addr = request.form.get('addr')
        cep = request.form.get('cep')
        desc = request.form.get('desc')
        city = request.form.get('city')
        hood = request.form.get('hood')
        num = request.form.get('num')
        cpf = request.form.get('cpf')
        photo = request.files['photo']

        if not photo:
            photo = None

        if getOng(email):
            flash('Ong já existente', 'info')
            return redirect(url_for('index'))
        
        if not photo:
            new_filename = 'default_profile.jpg'
        elif photo and checkExtension(photo.filename):
            extension = photo.filename.rsplit('.', 1)[1].lower()  
            new_filename = str(uuid.uuid4()) + '.' + extension  

            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

        if saveOng(name, phone, email, password, cpf, cep, city, hood, addr, num, new_filename, desc):
            flash('Sucesso no cadastro.', 'info')
            return redirect(url_for('ong_login'))
        
        else:
            flash('Erro no cadastro.', 'info')
            return redirect(url_for('ong_register'))    
        
    return render_template('ong_register.html', cities=cities)

@app.route('/get_address/<cep>')
def get_address(cep):
    res = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
    if res.status_code == 200:
        data = res.json()
        if 'erro' in data:
            return jsonify({'erro': True})
        return jsonify(data)
    return jsonify({'erro': True})

@app.route('/ong_login', methods=['GET', 'POST'])
def ong_login():
    if session.get('ong_logged') or session.get('logged'):
        flash('Você já está logado!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if request.form.get('email') and request.form.get('password'):
            email = request.form.get('email')
            password = request.form.get('password')

            if checkOng(email, password):
                ong = getOng(email)
                
                if ong: 
                    session['ong_logged'] = 1
                    session['ong_id'] = ong.ong_id
                    session['ong_email'] = ong.ong_email
                    session['ong_city'] = ong.ong_city

                    flash('Login bem-sucedido!', 'success')
                return redirect(url_for('index'))
            else:
                flash('email e/ou senha inválidos', 'error')
    return render_template('ong_login.html')

@app.route('/ong_profile', methods=['GET', 'POST'])
def ong_profile():
    if session.get('logged'):
        return redirect(url_for('index'))

    if not session.get('ong_logged'):
        flash('Você precisa estar logado como ONG para acessar esta página.', 'error')
        return redirect(url_for('ong_login'))

    ong = Ong.query.filter_by(ong_email=session.get('ong_email')).first()
    if not ong:
        flash('ONG não encontrada.', 'error')
        return redirect(url_for('ong_login'))
    
    ong_id = session.get('ong_id')

    if request.method == 'POST':
        try:
            form_data = {
                'ong_name': request.form.get('name'),
                'ong_phone': request.form.get('phone'),
                'ong_email': request.form.get('email'),
                'ong_cpf': request.form.get('cpf'),
                'ong_cep': request.form.get('cep'),
                'ong_city': request.form.get('city'),
                'ong_hood': request.form.get('hood'),
                'ong_address': request.form.get('addr'),  
                'ong_num': request.form.get('num'),
                'ong_desc': request.form.get('desc')
            }
            
            form_data = {k: v for k, v in form_data.items() if v and v.strip()}
            
            if not form_data and 'photo' not in request.files:
                flash('Nenhum dado foi fornecido para atualização.', 'warning')
                return redirect(url_for('ong_profile'))
            
            if 'ong_email' in form_data and form_data['ong_email'] != ong.ong_email:
                existing_ong = Ong.query.filter_by(ong_email=form_data['ong_email']).first()
                if existing_ong:
                    flash('Este email já está sendo usado por outra ONG.', 'error')
                    return redirect(url_for('ong_profile'))
            
            new_filename = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename and checkExtension(photo.filename):
                    extension = photo.filename.rsplit('.', 1)[1].lower()
                    new_filename = str(uuid.uuid4()) + '.' + extension
                    
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    form_data['ong_profile_photo'] = new_filename
                    
                    if ong.ong_profile_photo:
                        old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], ong.ong_profile_photo)
                        if os.path.exists(old_photo_path):
                            try:
                                os.remove(old_photo_path)
                            except:
                                pass  
                    
                elif photo and photo.filename:  
                    flash('Extensão de arquivo não suportada.', 'error')
                    return redirect(url_for('ong_profile'))
            
           
            result = ong.safe_update(form_data)
            
            if result['success']:
                db.session.commit()
                
                if result.get('updated_fields'):
                    flash(f'Dados atualizados com sucesso! {result["total_changes"]} campo(s) alterado(s).', 'success')
                    
                    updated_fields = result['updated_fields']
                    if 'ong_email' in updated_fields:
                        session['ong_email'] = updated_fields['ong_email']
                    if 'ong_name' in updated_fields:
                        session['ong_name'] = updated_fields['ong_name']
                    if 'ong_city' in updated_fields:
                        session['ong_city'] = updated_fields['ong_city']
                else:
                    flash('Nenhuma alteração foi necessária.', 'info')
            else:
                flash('Nenhuma alteração foi detectada.', 'info')
                
        except Exception as e:
            db.session.rollback()  
            flash(f'Erro interno: {str(e)}', 'error')
            
        return redirect(url_for('ong_profile'))

    return render_template('ong_profile.html', cities=cities, ong=ong)

@app.route('/rescue', methods=['GET', 'POST'])
def rescue():
    if session.get('ong_logged'):
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('rescue.html', cities=cities)
    
    try:
        required_fields = ['desc', 'city', 'author']
        missing_fields = [field for field in required_fields 
                         if not request.form.get(field, '').strip()]
        
        user_logged = session.get('logged')
        if not user_logged:
            additional_required = ['author', 'phone']
            for field in additional_required:
                if not request.form.get(field, '').strip():
                    missing_fields.append(field)
        
        if missing_fields:
            flash('Preencha todos os campos obrigatórios.', 'error')
            return render_template('rescue.html', cities=cities)
        
        data = {
            'desc': request.form.get('desc').strip(),
            'city': request.form.get('city').strip(),
            'addr': request.form.get('address', '').strip() or None,
            'num': request.form.get('num', '').strip() or None,
            'cep': request.form.get('cep', '').strip() or None,
        }
        
        if user_logged:
            data['author'] = session.get('user_name') or session.get('user_email', 'Usuário Logado')
            data['phone'] = session.get('user_phone')
            data['userId'] = session.get('user_id')
        else:
            data['author'] = request.form.get('author').strip()
            data['phone'] = request.form.get('phone').strip()
            data['userId'] = None
        
        photo_filename = None
        photo = request.files['photo']
        
        if photo and photo.filename and checkExtension(photo.filename):
            try:
                extension = photo.filename.rsplit('.', 1)[1].lower()
                photo_filename = str(uuid.uuid4()) + '.' + extension
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            except Exception as e:
                logging.error(f"Erro no upload de foto do resgate: {e}")
                flash('Erro ao fazer upload da imagem.', 'error')
                return render_template('rescue.html', cities=cities)
        
        if saveRescue(
            desc=data['desc'],
            author=data['author'],
            phone=data['phone'],
            cep=data['cep'],
            city=data['city'],
            addr=data['addr'],
            num=data['num'],
            photo=photo_filename,
            userId=data['userId']
        ):
            if user_logged:
                flash('Resgate registrado com sucesso!', 'success')
            else:
                flash('Resgate anônimo registrado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            if photo_filename:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                except:
                    pass
            flash('Erro ao registrar resgate. Tente novamente.', 'error')
    
    except Exception as e:
        logging.error(f"Erro na rota rescue: {e}")
        flash('Erro interno. Tente novamente.', 'error')
    
    return render_template('rescue.html', cities=cities)

@app.route('/user_reports')
def user_reports():
    if not session.get('logged'):
        flash('Você precisa estar logado para ver suas denúncias.', 'error')
        return redirect(url_for('login'))
    
    if session.get('ong_logged'):
        return redirect(url_for('index'))
    
    try:
        user_id = session.get('user_id')
        
        reports = Report.query.filter_by(rep_user_id=user_id)\
                             .order_by(Report.rep_created_at.desc())\
                             .all()
        
        return render_template('user_reports.html', reports=reports)
    
    except Exception as e:
        logging.error(f"Erro ao carregar denúncias do usuário: {e}")
        flash('Erro ao carregar suas denúncias.', 'error')
        return redirect(url_for('index'))
    
@app.route('/user_rescues')
def user_rescues():
    if not session.get('logged'):
        flash('Você precisa estar logado para ver seus resgates.', 'error')
        return redirect(url_for('login'))
    
    if session.get('ong_logged'):
        return redirect(url_for('index'))
    
    try:
        user_id = session.get('user_id')
        
        rescues = Rescue.query.filter_by(resc_user_id=user_id)\
                             .order_by(Rescue.resc_created_at.desc())\
                             .all()
        
        return render_template('user_rescues.html', rescues=rescues)
    
    except Exception as e:
        logging.error(f"Erro ao carregar resgates do usuário: {e}")
        flash('Erro ao carregar seus resgates.', 'error')
        return redirect(url_for('index'))

@app.route('/ong_ongoing/<int:id>', methods=['GET', 'POST'])
def ong_ongoing(id):
    if session.get('logged'):
        flash('Você não pode acessar.', 'error')
        return redirect(url_for('index'))
    
    if not session.get('ong_logged'):
        return redirect(url_for('ong_login'))
    
    rescues = Rescue.query.filter(
        and_(
            Rescue.resc_ong_id == id,
            Rescue.resc_status == 'andamento'
        )
    )
    
    reports = Report.query.filter(
        and_(
            Report.rep_ong_id == id,
            Report.rep_status == 'andamento'
        )
    )

    if request.method == 'GET':
        return render_template('ong_ongoing.html', rescues=rescues, reports=reports)
    
@app.route('/finish_report/<int:id>', methods=['POST'])
def finish_report(id):
    ong_id = session.get('ong_id')

    if not ong_id:
        message = 'ONG não autenticada.'
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': message})
        flash(message, 'warning')
        return redirect(url_for('ong_login'))

    report = Report.query.filter(
        and_(
            Report.rep_id == id,
            Report.rep_ong_id == ong_id,
            Report.rep_status == 'andamento' 
        )
    ).first()

    if report:
        ong = Ong.query.get(ong_id)
        if ong:
            ong.ong_reportsResolved += 1

        report.rep_status = 'finalizado'
        db.session.commit()
        message = 'Denúncia finalizada com sucesso!'

        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': True, 'message': message})
        flash(message, 'success')

    else:
        message = 'Denúncia não encontrada, não pertence a esta ONG ou não pode ser finalizada.'
        
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': message})
        flash(message, 'danger')

    return redirect(url_for('ong_ongoing', id=ong_id))

@app.route('/finish_rescue/<int:id>', methods=['POST'])
def finish_rescue(id):
    ong_id = session.get('ong_id')

    if not ong_id:
        message = 'ONG não autenticada.'
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': message})
        flash(message, 'warning')
        return redirect(url_for('ong_login'))

    rescue = Rescue.query.filter(
        and_(
            Rescue.resc_id == id,
            Rescue.resc_ong_id == ong_id,
            Rescue.resc_status == 'andamento' 
        )
    ).first()

    if rescue:
        rescue.resc_status = 'finalizado'
        Ong.ong_rescuesResolved += 1
        db.session.commit()
        message = 'Resgate finalizado com sucesso!'
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': True, 'message': message})
        flash(message, 'success')
    else:
        message = 'Resgate não encontrado, não pertence a esta ONG ou não pode ser finalizado.'
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': message})
        flash(message, 'danger')

    return redirect(url_for('ong_ongoing', id=ong_id))

@app.route('/ong_events/<int:id>', methods=['GET', 'POST']) 
def ong_events(id): 
    if session.get('logged'): 
        flash('Você não pode acessar.', 'error') 
        return redirect(url_for('index')) 
    if not session.get('ong_logged'): 
        return redirect(url_for('ong_login')) 
    events = Events.query.filter(
        and_(
            Events.event_ong_id == id 
        )).all()
        
    if request.method == 'GET': 
        return render_template('ong_events.html', events=events) 
    
    if request.method == 'POST': 
        return render_template('ong_events.html', events=events)

@app.route('/create_event/<int:id>', methods=['GET', 'POST'])
def create_event(id):
    if not session.get('ong_logged') or session.get('ong_id') != id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('ong_login'))

    if request.method == 'POST':
        title = request.form.get('event_title')
        description = request.form.get('event_description')
        date_str = request.form.get('event_date')
        location = request.form.get('event_location')
        city = request.form.get('event_city')
        photo = request.files.get('event_photo')

        if not title or not date_str or not location:
            flash('Título, data e localização são obrigatórios.', 'error')
            return render_template('create_event.html', cities=cities)

        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            flash('Data inválida. Use o formato YYYY-MM-DD.', 'error')
            return render_template('create_event.html', cities=cities)

        photo_filename = None

        if photo and photo.filename and checkExtension(photo.filename):
            try:
                extension = photo.filename.rsplit('.', 1)[1].lower()
                photo_filename = f"{uuid.uuid4()}.{extension}"

                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            except Exception as e:
                logging.error(f"Erro no upload da foto do evento: {e}")
                flash('Erro ao fazer upload da imagem.', 'error')
                return render_template('create_event.html', cities=cities)

        try:
            new_event = Events(
                event_title=title,
                event_description=description,
                event_date=event_date,
                event_location=location,
                event_city=city,
                event_photo=photo_filename,
                event_ong_id=id
            )
            db.session.add(new_event)
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Erro ao salvar evento no banco: {e}")
            if photo_filename:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                except Exception as ex:
                    logging.error(f"Erro ao remover arquivo após falha no DB: {ex}")
            flash('Erro ao registrar evento. Tente novamente.', 'error')
            return render_template('create_event.html', cities=cities)

        flash('Evento criado com sucesso!', 'success')
        return redirect(url_for('ong_events', id=id, cities=cities))

    return render_template('create_event.html', cities=cities)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if not session.get('ong_logged'):
        flash('Você precisa estar logado como ONG.', 'error')
        return redirect(url_for('ong_login'))

    event = Events.query.get(event_id)

    if not event or event.event_ong_id != session.get('ong_id'):
        flash('Evento não encontrado ou acesso negado.', 'error')
        return redirect(url_for('ong_events', id=session.get('ong_id')))

    if event.event_photo:
        try:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], event.event_photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception as e:
            logging.error(f'Erro ao remover imagem do evento: {e}')

    try:
        db.session.delete(event)
        db.session.commit()
        flash('Evento excluído com sucesso.', 'success')
    except Exception as e:
        logging.error(f'Erro ao excluir evento: {e}')
        flash('Erro ao excluir o evento.', 'error')

    return redirect(url_for('ong_events', id=session.get('ong_id')))


if __name__ == "__main__":
    app.run(debug=True)