from flask import Flask, jsonify, render_template, request, abort
import hashlib
import time
import json
from functools import wraps

app = Flask(__name__)

# ===== RATE LIMITING =====
request_counts = {}
RATE_LIMIT = 30

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr
        now = time.time()
        if ip not in request_counts:
            request_counts[ip] = []
        request_counts[ip] = [t for t in request_counts[ip] if now - t < 60]
        if len(request_counts[ip]) >= RATE_LIMIT:
            return jsonify({"error": "Too many requests!"}), 429
        request_counts[ip].append(now)
        return f(*args, **kwargs)
    return decorated

# ===== WALLET =====
class Wallet:
    def __init__(self, name):
        self.name = name
        self.address = hashlib.sha256(name.encode()).hexdigest()[:20]
        self.balance = 0

# ===== BLOCK =====
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

# ===== BLOCKCHAIN =====
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
        if not name or len(name) > 50:
            return None
        name = name.strip()
        w = Wallet(name)
        w.balance = balance
        self.wallets[name] = w
        self.circulating_supply += balance
        return w

    def send_bricks(self, sender, receiver, amount):
        # Security Checks
        if not sender or not receiver or not amount:
            return False, "सब fields भरो!"
        if len(sender) > 50 or len(receiver) > 50:
            return False, "Invalid name!"
        if sender not in self.wallets:
            return False, f"{sender} की Wallet नहीं मिली!"
        if receiver not in self.wallets:
            return False, f"{receiver} की Wallet नहीं मिली!"
        try:
            amount = int(amount)
        except:
            return False, "Amount सही नहीं है!"
        if amount <= 0:
            return False, "Amount 0 से ज़्यादा होना चाहिए!"
        if amount > 10000:
            return False, "एक बार में 10000 से ज़्यादा नहीं!"
        if self.wallets[sender].balance < amount:
            return False, f"Balance कम है! सिर्फ {self.wallets[sender].balance} BRICKS हैं!"

        # Transaction
        self.wallets[sender].balance -= amount
        self.wallets[receiver].balance += amount
        tx = {
            "from": sender,
            "to": receiver,
            "amount": amount,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.transaction_history.append(tx)
        block = Block(len(self.chain), str(tx), self.chain[-1].hash)
        self.chain.append(block)
        self.wallets[sender].balance += self.mining_reward
        self.circulating_supply += self.mining_reward
        return True, "Transaction हो गई!"

    def is_valid(self):
        for i in range(1, len(self.chain)):
            if self.chain[i].previous_hash != self.chain[i-1].hash:
                return False
        return True

bricks = BricksCoin()

# ===== ROUTES =====
@app.route('/')
@rate_limit
def home():
    return render_template('index.html')

@app.route('/wallet')
@rate_limit
def wallet():
    return render_template('wallet.html')

@app.route('/api')
@rate_limit
def api():
    return jsonify({
        "coin": "BRICKS Coin",
        "total_supply": "21,000,000 BRICKS",
        "circulating": bricks.circulating_supply,
        "total_blocks": len(bricks.chain),
        "total_wallets": len(bricks.wallets),
        "blockchain_valid": bricks.is_valid(),
        "status": "BRICKS Coin is LIVE!"
    })

@app.route('/wallets')
@rate_limit
def wallets():
    result = {}
    for name, w in bricks.wallets.items():
        result[name] = {
            "address": w.address,
            "balance": w.balance
        }
    return jsonify(result)

@app.route('/chain')
@rate_limit
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

@app.route('/send/<sender>/<receiver>/<amount>')
@rate_limit
def send(sender, receiver, amount):
    success, msg = bricks.send_bricks(sender, receiver, amount)
    if success:
        return jsonify({
            "status": "Transaction Done!",
            "from": sender,
            "to": receiver,
            "amount": amount,
            "message": msg
        })
    return jsonify({"status": "Failed!", "message": msg}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Page नहीं मिली!"}), 404

@app.errorhandler(429)
def too_many(e):
    return jsonify({"error": "बहुत ज़्यादा requests!"}), 429

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error!"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
