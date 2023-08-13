import requests
import json

def send_monero(wallet_name, wallet_password, destination_addresses, amounts):
    headers = {"Content-Type": "application/json"}
    destinations = [{"amount": int(amount * 1e12), "address": address} for amount, address in zip(amounts, destination_addresses)]
    print("destinations", destinations)
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "transfer",
        "params": {
            "destinations": destinations,
            "account_index": 0,
            "subaddr_indices": [0],
            "priority": 1,
            "ring_size": 11,
            "get_tx_key": True,
            "wallet_name": wallet_name,
            "password": wallet_password
        }
    }

    rpc_url = "http://localhost:28080/json_rpc"  # Inserisci l'URL corretto per il tuo nodo Monero RPC

    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            tx_hash = result["result"]["tx_hash"]
            return tx_hash
        else:
            print("Error sending transaction:", result.get("error", {}).get("message"))
    else:
        print("Error sending transaction:", response.status_code)

def main():
    wallet_name = input("Enter your wallet name: ")
    wallet_password = input("Enter your wallet password: ")

    destination_addresses = []
    amounts = []

    while True:
        address = input("Enter the recipient's Monero address (or type 'done' to finish): ")
        if address.lower() == 'done':
            break

        amount = float(input("Enter the amount of XMR to send: "))

        destination_addresses.append(address)
        amounts.append(amount)

    if not destination_addresses or not amounts:
        print("No transaction data provided.")
        return

    tx_hashes = send_monero(wallet_name, wallet_password, destination_addresses, amounts)

    if tx_hashes:
        print("Transaction hashes:", tx_hashes)

if __name__ == "__main__":
    main()
