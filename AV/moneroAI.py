import requests
import json
import datetime

rpc_url = "http://localhost:28080/json_rpc"
daemon_url = "http://127.0.0.1:28081/json_rpc"

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

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            print("RPC daemon set successfully!")
        else:
            print("Error setting RPC daemon:", result.get("error", {}).get("message"))
    else:
        print("Error setting RPC daemon:", response.status_code)



def create_monero_wallet(wallet_name, wallet_password):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "create_wallet",
        "params": {
            "filename": wallet_name,
            "password": wallet_password,
            "language": "English"
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
            print("Mnemonic (seed words):", mnemonic)
            show_wallet_details(wallet_name, wallet_password)
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

def show_wallet_details(wallet_name, wallet_password):
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
            balance = result["result"]["balance"] / 1e12
            address = result["result"]["per_subaddress"][0]["address"]
            print("Wallet address:", address)
            print("Wallet balance:", balance, "XMR")
        else:
            print("Error retrieving wallet details:", result.get("error", {}).get("message"))
    else:
        print("Error retrieving wallet details:", response.status_code)

def send_xmr(wallet_name, wallet_password):
    address = input("Enter the recipient's Monero address: ")
    amount = float(input("Enter the amount of XMR to send: "))

    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "transfer",
        "params": {
            "destinations": [{"amount": int(amount * 1e12), "address": address}],
            "account_index": 0,
            "subaddr_indices": [0],
            "priority": 1,
            "ring_size": 11,
            "get_tx_key": True,
            "wallet_name": wallet_name,
            "password": wallet_password
        }
    }
    response = requests.post(rpc_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            tx_hash = result["result"]["tx_hash"]
            print("Transaction sent successfully. Transaction hash:", tx_hash)
        else:
            print("Error sending transaction:", result.get("error", {}).get("message"))
    else:
        print("Error sending transaction:", response.status_code)




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
            transfers = []
            transfers.extend(result["result"].get("in", []))
            transfers.extend(result["result"].get("out", []))
            transfers.extend(result["result"].get("pending", []))

            transfers = sorted(transfers, key=lambda x: x["timestamp"], reverse=True)

            print("All Transfers:")
            for transfer in transfers:
                timestamp = datetime.datetime.fromtimestamp(transfer["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
                amount = transfer["amount"] / 1e12
                tx_hash = transfer["txid"]
                if "type" in transfer:
                    transfer_type = transfer["type"]
                else:
                    transfer_type = "UNKNOWN"

                if transfer_type == "in":
                    transfer_type_label = "IN"
                elif transfer_type == "out":
                    transfer_type_label = "OUT"
                elif transfer_type == "pending":
                    transfer_type_label = "PENDING"
                else:
                    transfer_type_label = transfer_type

                print(f"{timestamp} - {transfer_type_label} - ({amount} XMR) - Transaction hash: {tx_hash}")
        else:
            print("Error retrieving transfers:", result.get("error", {}).get("message"))
    else:
        print("Error retrieving transfers:", response.status_code)

######################
#####################
#####################

while True:
    print("Menu:")
    print("1. Connect to RPC daemon")
    print("2. Open an existing wallet")
    print("3. Create a new wallet")
    print("5. Send XMR")
    print("6. Ottieni transazioni")
    print("4. Exit")
    choice = input("Enter your choice: ")

    if choice == "1":
        set_rpc_daemon()

    elif choice == "2":
        wallet_name = input("Enter the wallet name: ")
        wallet_password = input("Enter the wallet password: ")
        open_monero_wallet(wallet_name, wallet_password)

    elif choice == "3":
        wallet_name = input("Enter the wallet name: ")
        wallet_password = input("Enter the wallet password: ")
        create_monero_wallet(wallet_name, wallet_password)

    elif choice == "5":
        wallet_name = input("Enter the wallet name: ")
        wallet_password = input("Enter the wallet password: ")
        send_xmr(wallet_name, wallet_password)


    elif choice == "6":
        wallet_name = input("Enter the wallet name: ")
        wallet_password = input("Enter the wallet password: ")
        get_all_transfers(wallet_name, wallet_password)


    elif choice == "4":
        break

    else:
        print("Invalid choice. Please try again.")
