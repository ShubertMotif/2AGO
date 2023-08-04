import requests
import json

rpc_url = 'http://localhost:18082/json_rpc'  # Indirizzo del server JSON-RPC di Monero

def get_all_transfers(wallet_name, wallet_password):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "get_transfers",
        "params": {
            "in": True,
            "out": True,
            "pending": True,
            "account_index": 0,
            "subaddr_indices": [0],
            "wallet_name": wallet_name,
            "password": wallet_password
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            transfers = result["result"]["in"] + result["result"]["out"] + result["result"]["pending"]
            return transfers
        else:
            print("Error retrieving transfers:", result.get("error", {}).get("message"))
    else:
        print("Error retrieving transfers:", response.status_code)

# Esempio di utilizzo
wallet_name = "your_wallet_name"
wallet_password = "your_wallet_password"

transfers = get_all_transfers(wallet_name, wallet_password)

if transfers:
    for transfer in transfers:
        timestamp = transfer["timestamp"]
        amount = transfer["amount"] / 1e12
        tx_hash = transfer["txid"]
        print(f"Timestamp: {timestamp}")
        print(f"Amount: {amount} XMR")
        print(f"Transaction Hash: {tx_hash}")
        print()
else:
    print("No transfers found.")
