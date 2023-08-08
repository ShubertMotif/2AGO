import requests

def get_xmr_price():
    # URL dell'API di CoinGecko per XMR/USD
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "monero",
        "vs_currencies": "usd"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        # Controllo se la richiesta ha avuto successo e se il prezzo è presente nella risposta
        if "monero" in data and "usd" in data["monero"]:
            price = data["monero"]["usd"]
            print(f"Prezzo di XMR/USD: ${price}")
        else:
            print("Impossibile ottenere il prezzo di XMR/USD.")
    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta: {e}")

if __name__ == "__main__":
    get_xmr_price()
