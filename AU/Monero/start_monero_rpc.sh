#!/bin/bash

while true; do
    # Controlla se Monero RPC è in esecuzione
    if ! pgrep -x "monero-wallet-rpc" > /dev/null; then
        echo "Monero RPC is not running. Starting..."
        ./monero-wallet-rpc --daemon-address stagenet.community.rino.io:38081 --wallet-dir wallet_python --rpc-bind-port 28080 --stagenet --disable-rpc-login &
        sleep 5
    else
        echo "Monero RPC is already running."
    fi

    sleep 1  # Intervallo di controllo in secondi
done
