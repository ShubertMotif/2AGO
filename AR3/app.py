from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from datetime import timedelta
import os
import pyperclip, datetime
import requests
import json


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'DATA', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SECRET_KEY'] = 'il_tuo_valore_segreto'

rpc_url = "http://localhost:28080/json_rpc"
daemon_url = "XXX"
#"http://127.0.0.1:28081/json_rpc"

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
    monero_wallet = db.Column(db.String(255), nullable=True)  # Aggiunta del campo monero_wallet
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

    def __init__(self, prezzo_monero, utente, ):
        self.prezzo_monero = prezzo_monero
        self.utente = utente


def save_photo(file):
    filename = secure_filename(file.filename)
    file.save(f"{app.config['UPLOAD_FOLDER']}/{filename}")
    return filename

def set_rpc_daemon():
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "set_daemon",
        "params": {
            "address": daemon_url,
            "trusted": True
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))


def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    if not value or not isinstance(value, (int, float)):
        return ''  # In caso di valore mancante o non numerico, restituisci una stringa vuota
    return datetime.datetime.fromtimestamp(value).strftime(format)


app.jinja_env.filters['datetimeformat'] = datetimeformat

#set_rpc_daemon()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    photos = db.session.query(Photo, User).join(User).order_by(Photo.id.desc()).all()
    photo_data = [(photo.filename, photo.title, photo.description, photo.id, user.username, photo.price_eur, photo.price_monero) for photo, user in photos]

    # Ottieni il prezzo di XMR
    xmr_price = get_xmr_price()

    return render_template('index.html', photo_data=photo_data, xmr_price=xmr_price)



@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        photo = request.files['photo']
        price_eur = request.form['price_eur']
        province = request.form['province']

        if photo:
            filename = save_photo(photo)
            price_monero = float(price_eur) / get_xmr_price()
            new_photo = Photo(filename=filename, title=title, description=description, user=current_user,
                              price_eur=price_eur, price_monero=price_monero, province=province)

            # Genera un nuovo indirizzo Monero
            wallet_name = current_user.username
            wallet_password = current_user.password
            address = create_new_address(wallet_name, wallet_password)
            new_photo.monero_address = address

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

        # Crea un nuovo portafoglio Monero con username e password
        create_monero_wallet(username, password)

        # Ottieni il seed e l'indirizzo del portafoglio
        seed = get_wallet_mnemonic(username, password)
        address = show_wallet_address(username, password)

        # Salva le parole del seed nel database per l'utente
        seed_string = ' '.join(seed)
        new_user = User(username=username, password=password, monero_wallet=seed_string)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('portafoglio_monero'))

    return render_template('register.html', error='')


@app.route('/portafoglio_monero')
@login_required
def portafoglio_monero():
    # Apri il portafoglio Monero
    wallet_name = current_user.username
    wallet_password = current_user.password
    open_monero_wallet(wallet_name, wallet_password)

    # Ottieni il seed, l'indirizzo e i bilanci del portafoglio
    seed = get_wallet_mnemonic(wallet_name, wallet_password)
    address = show_wallet_address(wallet_name, wallet_password)
    balance, unlocked_balance = get_wallet_balance(wallet_name, wallet_password)

    xmr_price = get_xmr_price()
    balance_usd = "{:,.2f}".format(float(balance) * xmr_price) if xmr_price is not None else None

    return render_template('portafoglio_monero.html', address=address, seed=seed, balance=balance, unlocked_balance=unlocked_balance, balance_usd=balance_usd)


@app.route('/photo/<int:photo_id>')
def photo_detail(photo_id):
    photo = Photo.query.get(photo_id)
    if photo:
        return render_template('photo_detail.html', photo=photo, photo_id=photo_id)
    else:
        return redirect(url_for('index'))


@app.route('/conferma_trasazione/<int:photo_id>', methods=['GET'])
@login_required
def conferma_trasazione(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo:
        return redirect(url_for('index'))

    xmr_price = get_xmr_price()
    price_monero = photo.price_monero
    price_eur = photo.price_eur

    # Assicura che il prezzo in monero abbia al massimo 12 decimali
    max_decimal_digits = 12
    xmr_to_seller = round(price_monero * 0.99, max_decimal_digits)
    xmr_to_seller = min(xmr_to_seller, 1e12)  # Limita a un massimo di 12 decimali

    dollars_to_seller = round(xmr_to_seller * xmr_price, 2)

    xmr_commission = round(price_monero * 0.01, max_decimal_digits)
    xmr_commission = min(xmr_commission, 1e12)  # Limita a un massimo di 12 decimali

    dollars_commission = round(xmr_commission * xmr_price, 2)

    return render_template('conferma_trasazione.html', photo_id=photo_id, xmr_to_seller=xmr_to_seller,
                           dollars_to_seller=dollars_to_seller, xmr_commission=xmr_commission,
                           dollars_commission=dollars_commission)


@app.route('/send_transaction/<int:photo_id>', methods=['POST'])
@login_required
def send_transaction(photo_id):
    xmr_to_seller = float(request.form['xmr_to_seller'])
    dollars_to_seller = float(request.form['dollars_to_seller'])
    xmr_commission = float(request.form['xmr_commission'])
    dollars_commission = float(request.form['dollars_commission'])

    # Logica per inviare XMR alla commissione
    commission_address = "5AYG8XzTZapMNQNC1j3mCbemZ8VxCSHqYeWL5XTyynhk4yK44ytcLHFAFsJcD5m1LAh3JV3tHdk1BQjzefPyTxf7E3ie6Kn"  # Sostituisci con l'indirizzo della commissione
    commission_tx_hash = send_monero("wallet_name", "wallet_password", commission_address, xmr_commission)

    # Logica per inviare XMR al venditore
    photo = Photo.query.get(photo_id)
    seller_address = photo.monero_address  # Sostituisci con l'indirizzo del venditore
    seller_tx_hash = send_monero("wallet_name", "wallet_password", seller_address, xmr_to_seller)

    # Messaggi di conferma
    commission_message = f"Transazione commissione completata. Hash della transazione: {commission_tx_hash}"
    seller_message = f"Transazione al venditore completata. Hash della transazione: {seller_tx_hash}"

    return render_template('transaction_confirmed.html', photo_id=photo_id,
                           xmr_to_seller=xmr_to_seller, dollars_to_seller=dollars_to_seller,
                           xmr_commission=xmr_commission, dollars_commission=dollars_commission,
                           commission_message=commission_message, seller_message=seller_message)




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

@app.route('/copy_text', methods=['POST'])
def copy_text():
    text = request.form.get('text')
    if text:
        pyperclip.copy(text)
        return 'Testo copiato negli appunti'
    else:
        return 'Testo non fornito'


@app.route('/portafoglio_monero/send', methods=['POST'])
@login_required
def send_monero():
    wallet_name = current_user.username
    wallet_password = current_user.password
    destination_address = request.form['address']
    amount = float(request.form['amount'])

    # Apri il portafoglio Monero
    open_monero_wallet(wallet_name, wallet_password)

    # Invia Monero
    tx_hash = send_monero(wallet_name, wallet_password, destination_address, amount)

    if tx_hash:
        return render_template('send_success.html', address=destination_address, amount=amount, tx_hash=tx_hash)
    else:
        return render_template('send_error.html')


@app.route('/portafoglio_monero/send', methods=['GET'])
@login_required
def send_monero_form():
    return render_template('send_monero.html')

@app.route('/portafoglio_monero/transactions', methods=['GET'])
@login_required
def show_transactions():
    wallet_name = current_user.username
    wallet_password = current_user.password

    # Ottieni le transazioni
    transactions = get_transactions(wallet_name, wallet_password, rpc_url)

    if transactions is not None:
        return render_template('transactions.html', transactions=transactions)
    else:
        return render_template('error.html', message="Non è stato possibile ottenere le transazioni.")


@app.route('/converti_denaro_monero', methods=['GET', 'POST'])
@login_required
def converti_denaro_monero():
    if request.method == 'POST':
        prezzo_monero = float(request.form['prezzo_monero'])
        # Aggiungi qui la logica per salvare l'offerta nel database
        # Assumiamo che tu abbia un modello chiamato "Offerta" con i campi desiderati
        # E che tu abbia la connessione al database con SQLAlchemy

        # Esempio di salvataggio di un'offerta nel database
        nuova_offerta = Offerta(prezzo_monero=prezzo_monero, utente=current_user)
        db.session.add(nuova_offerta)
        db.session.commit()

    offerte = Offerta.query.all()
    return render_template('converti_denaro_monero.html', offerte=offerte)


@app.route('/pubblica_offerta', methods=['GET', 'POST'])
@login_required
def pubblica_offerta():
    if request.method == 'POST':
        prezzo_monero = float(request.form['prezzo_monero'])

        # Crea e salva l'offerta nel database
        nuova_offerta = Offerta(prezzo_monero=prezzo_monero, utente=current_user)
        db.session.add(nuova_offerta)
        db.session.commit()

        return redirect(url_for('pubblica_offerta'))

    return render_template('pubblica_offerta.html')



###########################################################
###########################################################
################################# MONERO ###################
#############################################################



def get_transactions(wallet_name, wallet_password, rpc_url):
    # Imposta gli headers della richiesta
    headers = {
        'Content-Type': 'application/json',
    }

    # Crea il body della richiesta
    data = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "get_transfers",
        "params": {
            "in": True,        # Include incoming transfers
            "out": True,       # Include outgoing transfers
            "pending": True,   # Include pending transfers
            "failed": True,    # Include failed transfers
            "pool": True       # Include transfers from the daemon's transaction pool
        }
    }

    # Effettua la richiesta
    response = requests.post(rpc_url, headers=headers, json=data, auth=(wallet_name, wallet_password))

    if response.status_code == 200:
        result = response.json().get('result', {})
        in_transactions = result.get('in', [])
        out_transactions = result.get('out', [])
        pending_transactions = result.get('pending', [])
        failed_transactions = result.get('failed', [])
        pool_transactions = result.get('pool', [])

        transactions = in_transactions + out_transactions + pending_transactions + failed_transactions + pool_transactions
        # Ordina le transazioni in ordine decrescente di timestamp (dalla più recente alla meno recente)
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)

        return transactions

    else:
        return None





def send_monero(wallet_name, wallet_password, destination_address, amount):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "transfer",
        "params": {
            "destinations": [
                {"amount": int(amount * 1e12), "address": destination_address}
            ],
            "get_tx_key": True
        }
    }

    auth = (wallet_name, wallet_password)
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload), auth=auth)
    response_json = response.json()

    if 'error' in response_json:
        print(f"Errore: {response_json['error']}")
        return None

    return response_json['result']['tx_hash']



def create_monero_wallet(wallet_name, wallet_password):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "create_wallet",
        "params": {
            "filename": wallet_name,
            "password": wallet_password,
            "language": "Italiano"
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            print("Wallet created successfully!")
        else:
            print("Error creating Monero wallet:", result.get("error", {}).get("message"))
    else:
        print("Error creating Monero wallet:", response.status_code)

def open_monero_wallet(wallet_name, wallet_password):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "open_wallet",
        "params": {
            "filename": wallet_name,
            "password": wallet_password
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            print("Wallet opened successfully!")
            mnemonic = get_wallet_mnemonic(wallet_name, wallet_password)

        else:
            print("Error opening Monero wallet:", result.get("error", {}).get("message"))
    else:
        print("Error opening Monero wallet:", response.status_code)

def get_wallet_mnemonic(wallet_name, wallet_password):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "query_key",
        "params": {
            "key_type": "mnemonic",
            "key_data": {"name": wallet_name, "password": wallet_password}
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            return result["result"]["key"]
        else:
            print("Error retrieving wallet mnemonic:", result.get("error", {}).get("message"))
    else:
        print("Error retrieving wallet mnemonic:", response.status_code)


def show_wallet_address(wallet_name, wallet_password):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "get_address",
        "params": {
            "account_index": 0,
            "address_index": 0,
            "wallet_name": wallet_name,
            "password": wallet_password
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            address = result["result"]["address"]
            print("Wallet address:", address)
            return address
        else:
            print("Error retrieving wallet address:", result.get("error", {}).get("message"))
    else:
        print("Error retrieving wallet address:", response.status_code)

def create_new_address(wallet_name, wallet_password):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "create_address",
        "params": {
            "account_index": 0,
            "wallet_name": wallet_name,
            "password": wallet_password
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            address = result["result"]["address"]
            return address
        else:
            print("Error creating new address:", result.get("error", {}).get("message"))
    else:
        print("Error creating new address:", response.status_code)


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


def get_wallet_balance(wallet_name, wallet_password):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "get_balance",
        "params": {
            "account_index": 0,
            "address_indices": [0],
            "wallet_name": wallet_name,
            "password": wallet_password
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            balance = result["result"]["balance"]
            unlocked_balance = result["result"]["unlocked_balance"]

            balance_xmr = balance / 10 ** 12
            formatted_balance = "{:.12f}".format(balance_xmr)

            unlocked_balance_xmr = unlocked_balance / 10 ** 12
            formatted_unlocked_balance = "{:.12f}".format(unlocked_balance_xmr)

            return formatted_balance, formatted_unlocked_balance
        else:
            print("Error retrieving wallet balance:", result.get("error", {}).get("message"))
    else:
        print("Error retrieving wallet balance:", response.status_code)

#######################################################
#######################################################
#######################################################


#ok
if __name__ == '__main__':
    app.run(debug=True)
