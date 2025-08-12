from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify
from extensions import db
from db import *
from datetime import date as dt, timedelta
import secrets, requests, uuid, os

UPLOAD_FOLDER = 'src/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif'}

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
    if session.get('ong_logged'):
        return render_template("ong_index.html")
    else:
        return render_template("index.html")

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
                photo = None
            
            if photo and checkExtension(photo.filename):

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

@app.route("/report", methods=['POST', 'GET']) #lembrar de colocar forma de enviar a foto depois
def report():
    hoje = dt.today()
    min_data = hoje - timedelta(days=2)
    max_data = hoje

    if session.get('ong_logged'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        if request.form.get('title') and request.form.get('desc') and request.form.get('date') and request.form.get('city'):
            title = request.form.get('title')
            desc = request.form.get('desc')
            date = request.form.get('date')
            email = request.form.get('email')
            city = request.form.get('city')
            addr = request.form.get('addr')
            phone = request.form.get('phone')
            photo = request.files('photo')
            userId = request.form.get('userId')
            
            if not userId:
                userId = None
            if not email:
                email = None
            if not addr:
                addr = None


            if photo and checkExtension(photo.filename):

                extension = photo.filename.rsplit('.', 1)[1].lower()  # Obtém a extensão do arquivo
                new_filename = str(uuid.uuid4()) + '.' + extension  # Gera um UUID aleatório para o nome do arquivo

                # Salva o arquivo com o novo nome
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

                if saveReport(title, desc, city, date, phone, new_filename, email, addr, userId):
                    flash('Relatório enviado com sucesso!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Erro ao enviar relatório. Tente novamente.', 'error')
        else:
            flash('Preencha todos os campos do relatório.', 'error')

    return render_template('report.html', min_data=min_data.isoformat(), max_data=max_data.isoformat(), cities=cities)

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
        
        if photo and checkExtension(photo.filename):
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
        
    return render_template('ong_register.html')

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
        if request.form.get('email') and request.form.get('pass'):
            email = request.form.get('email')
            password = request.form.get('pass')

            if checkOng(email, password):
                ong = getOng(email)
                
                if ong: 
                    session['ong_logged'] = 1
                    session['ong_id'] = ong.ong_id
                    session['ong_email'] = ong.ong_email

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
    if session.get('ong_logged'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        if  request.form.get('desc') and request.form.get('city'): 
            desc = request.form.get('desc')
            city = request.form.get('city')
            addr = request.form.get('address')
            num = request.form.get('num')
            phone = request.form.get('phone')
            author = request.form.get('author')
            userId = request.form.get('userId')
            cep = request.form.get('cep')
            photo = request.form.get('photo')
            
            if not photo:
                photo = None

            if saveRescue(desc, author, phone, cep, city, addr, num, photo, userId):
                flash('Resgate registrado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Erro ao registrar resgate. Tente novamente.', 'error')
        else:
            flash('Preencha todos os campos do resgate.', 'error')

    return render_template('rescue.html')

if __name__ == "__main__":
    app.run(debug=True)