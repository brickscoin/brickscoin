from flask import Flask, jsonify
import hashlib
import time
import json

app = Flask(__name__)

class Wallet:
    def __init__(self, name):
        self.name = name
        self.address = hashlib.sha256(name.encode()).hexdigest()[:20]
        self.balance = 0

class Block:
    def __init__(self, index, data, previous_hash):
        self.index = index
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.mine_block()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self):
        while True:
            hash_val = self.calculate_hash()
            if hash_val.startswith("00"):
                return hash_val
            self.nonce += 1

class BricksCoin:
    def __init__(self):
        self.chain = []
        self.wallets = {}
        self.transaction_history = []
        self.mining_reward = 10
        self.total_supply = 21000000
        self.circulating_supply = 0
        genesis = Block(0, "BRICKS Genesis Block", "0")
        self.chain.append(genesis)
        self.create_wallet("Rahul", 1000)
        self.create_wallet("Priya", 800)
        self.create_wallet("Amit", 600)

    def create_wallet(self, name, balance=0):
        w = Wallet(name)
        w.balance = balance
        self.wallets[name] = w
        self.circulating_supply += balance

    def send_bricks(self, sender, receiver, amount):
        if sender not in self.wallets or receiver not in self.wallets:
            return False
        if self.wallets[sender].balance < amount:
            return False
        self.wallets[sender].balance -= amount
        self.wallets[receiver].balance += amount
        tx = {"from": sender, "to": receiver, "amount": amount,
              "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        self.transaction_history.append(tx)
        block = Block(len(self.chain), str(tx), self.chain[-1].hash)
        self.chain.append(block)
        self.wallets[sender].balance += self.mining_reward
        self.circulating_supply += self.mining_reward
        return True

bricks = BricksCoin()

@app.route('/')
def home():
    return jsonify({
        "coin": "BRICKS Coin",
        "total_supply": "21,000,000 BRICKS",
        "circulating": bricks.circulating_supply,
        "total_blocks": len(bricks.chain),
        "total_wallets": len(bricks.wallets),
        "status": "BRICKS Coin is LIVE!"
    })

@app.route('/wallets')
def wallets():
    result = {}
    for name, w in bricks.wallets.items():
        result[name] = {
            "address": w.address,
            "balance": w.balance
        }
    return jsonify(result)

@app.route('/chain')
def chain():
    blocks = []
    for b in bricks.chain:
        blocks.append({
            "index": b.index,
            "data": b.data,
            "hash": b.hash[:20],
            "time": b.timestamp
        })
    return jsonify(blocks)

@app.route('/send/<sender>/<receiver>/<int:amount>')
def send(sender, receiver, amount):
    success = bricks.send_bricks(sender, receiver, amount)
    if success:
        return jsonify({"status": "Transaction Done!",
                       "from": sender, "to": receiver, "amount": amount})
    return jsonify({"status": "Transaction Failed!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
