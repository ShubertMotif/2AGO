import os
import schedule
import time
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'DATA', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'il_tuo_valore_segreto'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    monero_wallet = db.Column(db.String(255), nullable=True)
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
    monero_address = db.Column(db.String(255), nullable=True)

class Offerta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prezzo_monero = db.Column(db.Float, nullable=False)
    utente_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    utente = db.relationship('User', backref='offerte')

    def __init__(self, prezzo_monero, utente):
        self.prezzo_monero = prezzo_monero
        self.utente = utente

def get_xmr_price():
    url = 'https://api.binance.com/api/v3/ticker/price'
    params = {'symbol': 'XMRUSDT'}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        price = float(data['price'])
        return price
    else:
        return None

def update_monero_prices():
    with app.app_context():
        photos = Photo.query.all()
        xmr_price = get_xmr_price()  # Ottieni il prezzo di Monero (XMR)
        for photo in photos:
            price_eur = photo.price_eur
            price_monero = price_eur / xmr_price
            photo.price_monero = price_monero
        db.session.commit()
        print(f"Ho aggiornato il database. Prezzo XMRUSDT = {xmr_price}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Schedula l'esecuzione di update_monero_prices() ogni minuto
    schedule.every(1).minutes.do(update_monero_prices)

    while True:
        schedule.run_pending()
        time.sleep(1)
