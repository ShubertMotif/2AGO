print("Ciao Piromalli")

import time
import requests

def get_bitcoin_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    response = requests.get(url, params=params)
    data = response.json()
    bitcoin_price = data["bitcoin"]["usd"]
    return bitcoin_price

while True:
    bitcoin_price = get_bitcoin_price()
    print(f"Prezzo di Bitcoin: ${bitcoin_price}")
    time.sleep(5)
