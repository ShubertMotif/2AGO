from monero.wallet import Wallet
from monero.seed import Seed

from monero.backends.jsonrpc import JSONRPCWallet

w = Wallet(JSONRPCWallet(port=28080))
s=Seed()
print(s.phrase)
print(w.address())

print(w.balance())

print(len(w.accounts))

print(w.accounts[0].addresses())

w.new_address()


print(w.accounts[0].addresses())
