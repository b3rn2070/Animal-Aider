from flask import Flask, request, render_template, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from db import Database

app = Flask(__name__, template_folder="../templates")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = Database('site.db')
app.secret_key = 'your_secret_key'

db.createONG()
db.createUser()
db.createReport()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        if request.form.get('email') and request.form.get('password'):
            email = request.form.get('email')
            password = request.form.get('password')

            if db.checkUser(email, password) == True:
                user = db.getUser(email)
                session['logged'] = 1
                session['user_email'] = email
                session['user'] = user[1]
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

if __name__ == "__main__":
    app.run(debug=True)