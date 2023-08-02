from flask import Flask

# Crea un'istanza dell'app Flask
app = Flask(__name__)

# Definisci una route per l'endpoint '/'
@app.route('/')
def hello_world():
    return 'Hello, World!'

# Avvia l'applicazione Flask
if __name__ == '__main__':
    app.run()
