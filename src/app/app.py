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

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animal_aider.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = random_key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicializa o SQLAlchemy com o app Flask
db.init_app(app)

# Cria as tabelas no banco de dados
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
        ).all()  # ← Adicione .all() aqui

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
        
        # Verificar se a denúncia é da mesma cidade da ONG
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
        
        # Verificar se a denúncia é da mesma cidade da ONG
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
        
        # Verificar se o resgate é da mesma cidade da ONG
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
        
        # Verificar se o resgate é da mesma cidade da ONG
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

    return redirect(url_for('user_reports'))  # ou a rota apropriada para onde redirecionar

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
            Rescue.resc_id == id,  # Note: mudei de rep_id para resc_id
            Rescue.resc_user_id == user_id  # Note: mudei de rep_user_id para resc_user_id
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

@app.route("/register", methods=['POST', 'GET']) #colocar forma de enviar a foto depois
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

                extension = photo.filename.rsplit('.', 1)[1].lower()  # Obtém a extensão do arquivo
                new_filename = str(uuid.uuid4()) + '.' + extension  # Gera um UUID aleatório para o nome do arquivo
                # Salva o arquivo com o novo nome
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
    # Cache das datas
    hoje = dt.today()
    min_data = hoje - timedelta(days=2)
    max_data = hoje
    
    # Formatar datas para o HTML
    max_data_str = max_data.strftime('%Y-%m-%d')
    min_data_str = min_data.strftime('%Y-%m-%d')
    
    # Redirect para ONGs logadas
    if session.get('ong_logged'):
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('report.html', 
                             min_data=min_data_str, 
                             max_data=max_data_str, 
                             cities=cities)
    
    # Processar POST
    try:
        # Validação de campos obrigatórios básicos
        required_fields = ['title', 'desc', 'date', 'city']
        missing_fields = [field for field in required_fields 
                         if not request.form.get(field, '').strip()]
        
        # Verificar se usuário está logado para validar telefone
        user_logged = session.get('logged')
        if not user_logged:
            # Para usuários não logados, telefone é obrigatório
            if not request.form.get('phone', '').strip():
                missing_fields.append('phone')
        
        # Verificar se foto é obrigatória (conforme formulário)
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
        
        # Extração e limpeza dos dados
        data = {
            'title': request.form.get('title').strip(),
            'desc': request.form.get('desc').strip(),
            'date': request.form.get('date').strip(),
            'city': request.form.get('city').strip(),
            'addr': request.form.get('addr', '').strip() or None,
        }
        
        # Dados específicos por tipo de usuário
        if user_logged:
            # Usuário logado - dados vêm da sessão
            data['email'] = session.get('user_email')
            data['phone'] = session.get('user_phone') 
            data['userId'] = session.get('user_id')
        else:
            # Usuário anônimo - dados vêm do formulário
            data['email'] = request.form.get('email', '').strip() or None
            data['phone'] = request.form.get('phone', '').strip()
            data['userId'] = None
        
        # Processamento de foto (obrigatória)
        photo_filename = None
        if photo and checkExtension(photo.filename):
            try:
                extension = photo.filename.rsplit('.', 1)[1].lower()
                photo_filename = str(uuid.uuid4()) + '.' + extension
                
                # Cria diretório se não existir
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
        
        # Salvar no banco
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
            # Remove arquivo se salvamento falhou
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

#lembrar de tirar isso depois
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

    # Busca o usuário pelo SQLAlchemy (mais eficiente)
    user = User.query.filter_by(user_email=session.get('user_email')).first()
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')

    if request.method == 'POST':
        try:
            # Coleta os dados do formulário (mapeando os nomes corretos)
            form_data = {
                'user_name': request.form.get('name'),
                'user_city': request.form.get('city'),
                'user_email': request.form.get('email'),
                'user_phone': request.form.get('phone'),
                'user_cep': request.form.get('cep'),
                'user_address': request.form.get('addr'),  # 'addr' no form -> 'user_address' no banco
                'user_num': request.form.get('num')
            }
            
            # Remove valores vazios
            form_data = {k: v for k, v in form_data.items() if v and v.strip()}
            
            # Verifica se há dados para atualizar
            if not form_data and 'photo' not in request.files:
                flash('Nenhum dado foi fornecido para atualização.', 'warning')
                return redirect(url_for('user'))
            
            # Validação de email único (só se email foi alterado)
            if 'user_email' in form_data and form_data['user_email'] != user.user_email:
                existing_user = User.query.filter_by(user_email=form_data['user_email']).first()
                if existing_user:
                    flash('Este email já está sendo usado por outro usuário.', 'error')
                    return redirect(url_for('user'))
            
            # Processamento da foto
            new_filename = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename and checkExtension(photo.filename):
                    extension = photo.filename.rsplit('.', 1)[1].lower()
                    new_filename = str(uuid.uuid4()) + '.' + extension
                    
                    # Salva a nova foto
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    form_data['user_profile_photo'] = new_filename
                    
                    # Remove a foto antiga se existir
                    if user.user_profile_photo:
                        old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], user.user_profile_photo)
                        if os.path.exists(old_photo_path):
                            try:
                                os.remove(old_photo_path)
                            except:
                                pass  # Se não conseguir deletar, continua
                    
                elif photo and photo.filename:  # Se tem arquivo mas extensão inválida
                    flash('Extensão de arquivo não suportada.', 'error')
                    return redirect(url_for('user'))
            
            # Atualiza o usuário com os dados coletados
            result = updateUser(user_id, **form_data)
            
            if result['success']:
                if result.get('updated_fields'):
                    flash(f'Dados atualizados com sucesso! {result["message"]}', 'success')
                    
                    # Atualiza a sessão se necessário
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
            extension = photo.filename.rsplit('.', 1)[1].lower()  # Obtém a extensão do arquivo
            new_filename = str(uuid.uuid4()) + '.' + extension  # Gera um UUID aleatório para o nome do arquivo

            # Salva o arquivo com o novo nome
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

    # Busca a ONG pelo SQLAlchemy (mais eficiente)
    ong = Ong.query.filter_by(ong_email=session.get('ong_email')).first()
    if not ong:
        flash('ONG não encontrada.', 'error')
        return redirect(url_for('ong_login'))
    
    ong_id = session.get('ong_id')

    if request.method == 'POST':
        try:
            # Coleta os dados do formulário (mapeando os nomes corretos)
            form_data = {
                'ong_name': request.form.get('name'),
                'ong_phone': request.form.get('phone'),
                'ong_email': request.form.get('email'),
                'ong_cpf': request.form.get('cpf'),
                'ong_cep': request.form.get('cep'),
                'ong_city': request.form.get('city'),
                'ong_hood': request.form.get('hood'),
                'ong_address': request.form.get('addr'),  # 'addr' no form -> 'ong_address' no banco
                'ong_num': request.form.get('num'),
                'ong_desc': request.form.get('desc')
            }
            
            # Remove valores vazios
            form_data = {k: v for k, v in form_data.items() if v and v.strip()}
            
            # Verifica se há dados para atualizar
            if not form_data and 'photo' not in request.files:
                flash('Nenhum dado foi fornecido para atualização.', 'warning')
                return redirect(url_for('ong_profile'))
            
            # Validação de email único (só se email foi alterado)
            if 'ong_email' in form_data and form_data['ong_email'] != ong.ong_email:
                existing_ong = Ong.query.filter_by(ong_email=form_data['ong_email']).first()
                if existing_ong:
                    flash('Este email já está sendo usado por outra ONG.', 'error')
                    return redirect(url_for('ong_profile'))
            
            # Processamento da foto
            new_filename = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename and checkExtension(photo.filename):
                    extension = photo.filename.rsplit('.', 1)[1].lower()
                    new_filename = str(uuid.uuid4()) + '.' + extension
                    
                    # Salva a nova foto
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    form_data['ong_profile_photo'] = new_filename
                    
                    # Remove a foto antiga se existir
                    if ong.ong_profile_photo:
                        old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], ong.ong_profile_photo)
                        if os.path.exists(old_photo_path):
                            try:
                                os.remove(old_photo_path)
                            except:
                                pass  # Se não conseguir deletar, continua
                    
                elif photo and photo.filename:  # Se tem arquivo mas extensão inválida
                    flash('Extensão de arquivo não suportada.', 'error')
                    return redirect(url_for('ong_profile'))
            
            # Atualiza a ONG usando o método safe_update
            result = ong.safe_update(form_data)
            
            if result['success']:
                # Salva no banco
                db.session.commit()
                
                if result.get('updated_fields'):
                    flash(f'Dados atualizados com sucesso! {result["total_changes"]} campo(s) alterado(s).', 'success')
                    
                    # Atualiza a sessão se necessário
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
            db.session.rollback()  # Reverte mudanças em caso de erro
            flash(f'Erro interno: {str(e)}', 'error')
            
        return redirect(url_for('ong_profile'))

    return render_template('ong_profile.html', cities=cities, ong=ong)

@app.route('/rescue', methods=['GET', 'POST'])
def rescue():
    # Redirect para ONGs logadas
    if session.get('ong_logged'):
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('rescue.html', cities=cities)
    
    # Processar POST
    try:
        # Validação de campos obrigatórios básicos
        required_fields = ['desc', 'city', 'author']
        missing_fields = [field for field in required_fields 
                         if not request.form.get(field, '').strip()]
        
        # Verificar se usuário está logado para validar campos adicionais
        user_logged = session.get('logged')
        if not user_logged:
            # Para usuários não logados, campos adicionais são obrigatórios
            additional_required = ['author', 'phone']
            for field in additional_required:
                if not request.form.get(field, '').strip():
                    missing_fields.append(field)
        
        if missing_fields:
            flash('Preencha todos os campos obrigatórios.', 'error')
            return render_template('rescue.html', cities=cities)
        
        # Extração e limpeza dos dados
        data = {
            'desc': request.form.get('desc').strip(),
            'city': request.form.get('city').strip(),
            'addr': request.form.get('address', '').strip() or None,
            'num': request.form.get('num', '').strip() or None,
            'cep': request.form.get('cep', '').strip() or None,
        }
        
        # Dados específicos por tipo de usuário
        if user_logged:
            # Usuário logado - dados vêm da sessão (assumindo que existam na sessão)
            data['author'] = session.get('user_name') or session.get('user_email', 'Usuário Logado')
            data['phone'] = session.get('user_phone')
            data['userId'] = session.get('user_id')
        else:
            # Usuário anônimo - dados vêm do formulário
            data['author'] = request.form.get('author').strip()
            data['phone'] = request.form.get('phone').strip()
            data['userId'] = None
        
        # Processamento de foto (opcional)
        photo_filename = None
        photo = request.files['photo']
        
        if photo and photo.filename and checkExtension(photo.filename):
            try:
                extension = photo.filename.rsplit('.', 1)[1].lower()
                photo_filename = str(uuid.uuid4()) + '.' + extension
                
                # Cria diretório se não existir
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            except Exception as e:
                logging.error(f"Erro no upload de foto do resgate: {e}")
                flash('Erro ao fazer upload da imagem.', 'error')
                return render_template('rescue.html', cities=cities)
        
        # Salvar no banco
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
            # Remove arquivo se salvamento falhou
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

# Rota para listar denúncias do usuário
@app.route('/user_reports')
def user_reports():
    # Verificar se usuário está logado
    if not session.get('logged'):
        flash('Você precisa estar logado para ver suas denúncias.', 'error')
        return redirect(url_for('login'))
    
    # Redirect para ONGs logadas
    if session.get('ong_logged'):
        return redirect(url_for('index'))
    
    try:
        user_id = session.get('user_id')
        
        # Buscar denúncias do usuário ordenadas por data (mais recentes primeiro)
        reports = Report.query.filter_by(rep_user_id=user_id)\
                             .order_by(Report.rep_created_at.desc())\
                             .all()
        
        return render_template('user_reports.html', reports=reports)
    
    except Exception as e:
        logging.error(f"Erro ao carregar denúncias do usuário: {e}")
        flash('Erro ao carregar suas denúncias.', 'error')
        return redirect(url_for('index'))
    
# Rota para listar resgates do usuário
@app.route('/user_rescues')
def user_rescues():
    # Verificar se usuário está logado
    if not session.get('logged'):
        flash('Você precisa estar logado para ver seus resgates.', 'error')
        return redirect(url_for('login'))
    
    # Redirect para ONGs logadas
    if session.get('ong_logged'):
        return redirect(url_for('index'))
    
    try:
        user_id = session.get('user_id')
        
        # Buscar resgates do usuário ordenados por data (mais recentes primeiro)
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
    # Pegar o ID da ONG da sessão (não do usuário)
    ong_id = session.get('ong_id')

    if not ong_id:
        message = 'ONG não autenticada.'
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': message})
        flash(message, 'warning')
        return redirect(url_for('ong_login'))

    # Buscar denúncia que pertence a esta ONG e está aceita
    report = Report.query.filter(
        and_(
            Report.rep_id == id,
            Report.rep_ong_id == ong_id,
            Report.rep_status == 'andamento'  # Só pode finalizar se estiver aceita
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
    # Pegar o ID da ONG da sessão (não do usuário)
    ong_id = session.get('ong_id')

    if not ong_id:
        message = 'ONG não autenticada.'
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': message})
        flash(message, 'warning')
        return redirect(url_for('ong_login'))

    # Buscar resgate que pertence a esta ONG e está aceito
    rescue = Rescue.query.filter(
        and_(
            Rescue.resc_id == id,
            Rescue.resc_ong_id == ong_id,
            Rescue.resc_status == 'andamento'  # Só pode finalizar se estiver aceito
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

        # Tratamento do upload da foto, seguindo seu padrão
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
            # Remove foto salva caso falhe o commit
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

    # Apagar a imagem se houver
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