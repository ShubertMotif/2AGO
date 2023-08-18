#!/bin/bash

while true; do
    # Controlla se il processo monero-wallet-rpc è in esecuzione
    if ps aux | grep -v grep | grep "monero-wallet-rpc" >/dev/null; then
        echo "Monero RPC is running."
    else
        echo "Monero RPC is not running. Starting..."
        ./monero-wallet-rpc --daemon-address stagenet.community.rino.io:38081 --wallet-dir wallet_python --rpc-bind-port 28080 --stagenet --disable-rpc-login &
    fi

    sleep 2  # Intervallo di controllo in secondi
done
