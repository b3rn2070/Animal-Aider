from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify
from db import db, saveUser, saveOng, saveReport, saveRescue, getUser, checkUser, getOng, showAllReports
from datetime import date as dt, timedelta
import secrets, requests, uuid, os
from werkzeug.utils import secure_filename

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

            if db.checkUser(email, password):
                user = db.getUser(email)

                session['logged'] = 1
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_email'] = email
                session['user_phone'] = user[4]
                session['user_cep'] = user[5]
                session['user_city'] = user[6]
                session['user_addr'] = user[7]

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

            if db.get(email):
                flash('Usuário já existe!', 'error')
                return redirect(url_for('register'))

            if not photo:
                photo = None
            
            if photo and checkExtension(photo.filename):

                extension = photo.filename.rsplit('.', 1)[1].lower()  # Obtém a extensão do arquivo
                new_filename = str(uuid.uuid4()) + '.' + extension  # Gera um UUID aleatório para o nome do arquivo
                print(new_filename)

                # Salva o arquivo com o novo nome
                try:
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                except Exception as e:
                    flash('Houve um erro. Tente Novamente', 'error')
                    print(e)
                    return redirect(url_for('register'))
                    
            if db.saveUser(name, email, password, phone, cep, city, addr, num, new_filename):
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
            phone = request.files['phone']
            photo = request.form.get('photo')
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

                if db.saveReport(title, desc, city, date, new_filename, photo, email, addr, userId):
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
    dados = db.showAllReports()
    return render_template('dados.html', dados=dados)

@app.route('/user', methods=['GET', 'POST'])
def user():
    if not session.get('logged'):
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    if session.get('ong_logged'):
        return redirect(url_for('index'))

    user = db.getUser(session.get('user_email'))
    id = session.get('user_id')

    if request.method == 'POST':
        if request.form.get('name') or request.form.get('city') or request.form.get('email'):
            name = request.form.get('name')
            city = request.form.get('city')
            email = request.form.get('email')
            phone = request.form.get('phone')
            photo = request.files['photo']

            if email != user[2] and db.checkUserExistence(email) == True:
                flash('Algum dado editado coincide com outro existente.', 'error')
                return redirect(url_for('user'))
            
            if photo != user and checkExtension(photo.filename):
                extension = photo.filename.rsplit('.', 1)[1].lower() 
                new_filename = str(uuid.uuid4()) + '.' + extension

                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
            else:
                flash('Extensão de arquivo não suportada', 'error')
                return redirect(url_for('user'))

            if db.updateUser(id, email, name, phone, new_filename):
                flash('Dados atualizados com sucesso!', 'success')
                session['user_email'] = email if email else user[2]
                session['user_name'] = name if name else user[1]
                session['logged'] = 1

                return redirect(url_for('user'))
            else:
                flash('Erro ao atualizar dados. Tente novamente.', 'error')

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

        if db.getOng(email):
            flash('Ong já existente', 'info')
            return redirect(url_for('index'))
        
        if photo and checkExtension(photo.filename):
            extension = photo.filename.rsplit('.', 1)[1].lower()  # Obtém a extensão do arquivo
            new_filename = str(uuid.uuid4()) + '.' + extension  # Gera um UUID aleatório para o nome do arquivo

            # Salva o arquivo com o novo nome
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

        if db.saveOng(name, phone, email, password, cpf, cep, city, hood, addr, num, new_filename, desc):
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

            if db.checkOng(email, password):
                ong = db.getOng(email)
                
                if ong: 
                    session['ong_logged'] = 1
                    session['ong_id'] = ong[0]
                    session['ong_email'] = email

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

    ong = db.getOng(session.get('ong_email'))

    if request.method == 'POST':
        if request.form.get('name') or request.form.get('city') or request.form.get('email') or request.form.get('desc'):
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            cpf = request.form.get('cpf')
            cep = request.form.get('cep')
            city = request.form.get('city')
            hood = request.form.get('hood')
            addr = request.form.get('addr')
            num = request.form.get('num')
            desc = request.form.get('desc')
            photo = request.form.get('photo')

            if ong[2] != email and db.getOng(email):
                flash('Algum dado editado coincide com outro existente.', 'error')
                return redirect(url_for('ong_profile'))

            if db.updateOng(ong[0], email, name, city, desc):
                flash('Dados atualizados com sucesso!', 'success')
                session['ong_email'] = email if email else ong[2]
                session['ong_name'] = name if name else ong[1]
                session['ong_city'] = city if city else ong[5]

                return redirect(url_for('ong_profile'))
            else:
                flash('Erro ao atualizar dados. Tente novamente.', 'error')

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

            if db.saveRescue(desc, author, phone, cep, city, addr, num, photo, userId):
                flash('Resgate registrado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Erro ao registrar resgate. Tente novamente.', 'error')
        else:
            flash('Preencha todos os campos do resgate.', 'error')

    return render_template('rescue.html')

if __name__ == "__main__":
    app.run(debug=True)