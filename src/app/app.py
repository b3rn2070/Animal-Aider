from flask import Flask, request, render_template, session, redirect, url_for, flash
from db import Database
from datetime import date as dt, timedelta
from dotenv import load_dotenv
import os

app = Flask(__name__, template_folder="../templates")

load_dotenv()
db = Database('site.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


db.createONG()
db.createUser()
db.createReport()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    if session.get('logged'):
        flash('Você já está logado!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if request.form.get('email') and request.form.get('password'):
            email = request.form.get('email')
            password = request.form.get('password')

            if db.checkUser(email, password) == True:
                user = db.getUser(email)
                session['logged'] = 1
                session['user_email'] = email
                session['user_name'] = user[1]
                session['user_id'] = user[0]
                session['city'] = user[4]
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
    if session.get('logged'):
        flash('Você já está logado!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if request.form.get('email') and request.form.get('password') and request.form.get('city') and request.form.get('name'):
            email = request.form.get('email')
            password = request.form.get('password')
            city = request.form.get('city')
            name = request.form.get('name')

            if db.getUser(email):
                flash('Usuário já existe!', 'error')
                return redirect(url_for('register'))
                
            if db.saveUser(name, email, password, city):
                flash('Usuário registrado com sucesso!', 'success')
                return redirect(url_for('login'))
        else:
            flash('Erro ao registrar usuário. Verifique os dados.', 'error')
    return render_template('register.html')

@app.route("/report", methods=['POST', 'GET'])
def report():
    hoje = dt.today()
    min_data = hoje - timedelta(days=20)
    max_data = hoje + timedelta(days=20)

    if request.method == 'POST':
        if request.form.get('email') == None:
            email = 'NULL'
        else:
            email = request.form.get('email')

        if request.form.get('title') and request.form.get('desc') and request.form.get('date') and request.form.get('city'):
            title = request.form.get('title')
            desc = request.form.get('desc')
            date = request.form.get('date')
            email = request.form.get('email')
            city = request.form.get('city')


            if db.saveReport(title, desc, city, date, email):
                flash('Relatório enviado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Erro ao enviar relatório. Tente novamente.', 'error')
        else:
            flash('Preencha todos os campos do relatório.', 'error')

    return render_template('report.html', min_data=min_data.isoformat(), max_data=max_data.isoformat())

@app.route('/ver_dados')
def ver_dados():
    dados = db.showOngs() # Exemplo com SQLAlchemy
    return render_template('dados.html', dados=dados)

@app.route('/user', methods=['GET', 'POST'])
def user():
    if not session.get('logged'):
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))

    email = session.get('user_email')
    user = db.getUser(email)
    id = session.get('user_id')


    if request.method == 'POST':
        if request.form.get('name') or request.form.get('city') or request.form.get('email'):
            name = request.form.get('name')
            city = request.form.get('city')
            email = request.form.get('email')

            if name == user[1]:
                name = None
            if city == user[4]:
                city = None
            if email == user[2]:
                email = None
            if not name and not city and not email:
                flash('Nenhum dado foi alterado.', 'info')
                return redirect(url_for('user'))
            elif db.updateUser(id, email, name, city):
                flash('Dados atualizados com sucesso!', 'success')
                session['user_email'] = email if email else user[2]
                session['user_name'] = name if name else user[1]
                session['user_city'] = city if city else user[4]
                return redirect(url_for('user'))
            else:
                flash('Erro ao atualizar dados. Tente novamente.', 'error')

    return render_template('user.html', user=user)

@app.route('/ong_register', methods=['GET', 'POST'])
def ong_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        addr = request.form.get('addr')
        cep = request.form.get('cep')
        desc = request.form.get('desc')
        cep = request.form.get('cep')
        phone_dono = request.form.get('phone_dono')
        name_dono = request.form.get('name_dono')
        cpf = request.form.get('cpf')

        if db.getOng(email):
            flash('Ong já existente', 'info')
            return redirect(url_for('index'))
        if db.saveOng(name, phone, email, password, addr, cep, name_dono, phone_dono, cpf, desc):
            flash('Sucesso no cadastro.', 'info')
            return redirect(url_for('index'))
        else:
            flash('Erro no cadastro.', 'info')
            return redirect(url_for('index'))    
        
    return render_template('ong_register.html')


if __name__ == "__main__":
    app.run(debug=True)