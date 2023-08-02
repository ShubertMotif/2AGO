from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from datetime import timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'DATA', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SECRET_KEY'] = 'il_tuo_valore_segreto'


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

import os
database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')
print(database_path)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    photos = db.relationship('Photo', backref='user', lazy=True)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    price_eur = db.Column(db.Float, nullable=True)
    price_monero = db.Column(db.Float, nullable=True)
    province = db.Column(db.String(100), nullable=True)


def save_photo(file):
    filename = secure_filename(file.filename)
    file.save(f"{app.config['UPLOAD_FOLDER']}/{filename}")
    return filename

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    photos = db.session.query(Photo, User).join(User).order_by(Photo.id.desc()).all()
    photo_data = [(photo.filename, photo.title, photo.description, photo.id, user.username, photo.price_eur, photo.price_monero) for photo, user in photos]
    return render_template('index.html', photo_data=photo_data)


# Resto del codice...

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        photo = request.files['photo']
        price_eur = request.form['price_eur']
        price_monero = request.form['price_monero']
        province = request.form['province']

        if photo:
            filename = save_photo(photo)
            new_photo = Photo(filename=filename, title=title, description=description, user=current_user, price_eur=price_eur, price_monero=price_monero, province=province)
            db.session.add(new_photo)
            db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('dashboard.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user, remember=True)  # Imposta il flag "remember" a True per mantenere il cookie di sessione persistente
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Credenziali non valide')
    return render_template('login.html', error='')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Nome utente già registrato')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', error='')


@app.route('/photo/<int:photo_id>')
def photo_detail(photo_id):
    photo = Photo.query.get(photo_id)
    if photo:
        return render_template('photo_detail.html', photo=photo)
    else:
        return redirect(url_for('index'))


@app.route('/cerca', methods=['GET', 'POST'])
def cerca():
    if request.method == 'POST':
        search_text = request.form['search_text']
        photos = db.session.query(Photo, User).join(User).filter(
            db.or_(
                Photo.title.ilike(f'%{search_text}%'),
                Photo.description.ilike(f'%{search_text}%'),
                User.username.ilike(f'%{search_text}%')
            )
        ).order_by(Photo.id.desc()).all()
        return render_template('cerca.html', photos=photos, search_text=search_text)

    return render_template('cerca.html')


import requests

def get_xmr_price():
    url = 'https://api.binance.com/api/v3/ticker/price'
    params = {'symbol': 'XMRUSDT'}

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code == 200:
        price = float(data['price'])
        return price
    else:
        return None




if __name__ == '__main__':
    app.run(debug=True)
