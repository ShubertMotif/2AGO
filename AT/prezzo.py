import time
import requests


def get_xmr_price():
    url = 'https://api.binance.com/api/v3/ticker/price'
    params = {'symbol': 'XMRUSDT'}
    response = requests.get(url, params=params, verify=True)

    if response.status_code == 200:
        data = response.json()
        price = float(data['price'])
        return price
    else:
        return None


def main():
    while True:
        price = get_xmr_price()
        if price is not None:
            print(f"Prezzo XMR: {price}")
        else:
            print("Impossibile ottenere il prezzo.")

        time.sleep(1)


if __name__ == "__main__":
    main()
