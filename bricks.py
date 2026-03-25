from flask_sqlalchemy import SQLAlchemy
import os
from flask import Flask, jsonify, render_template, request
import hashlib
import time
import json
from functools import wraps
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bricks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ===== DATABASE =====
class TransactionDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50))
    receiver = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    timestamp = db.Column(db.String(50))

class WalletDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    address = db.Column(db.String(50))
    balance = db.Column(db.Integer, default=0)

class SmartContractDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.String(50))
    receiver = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    condition = db.Column(db.String(200))
    status = db.Column(db.String(20), default="pending")
    timestamp = db.Column(db.String(50))

class NFTDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nft_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(500))
    creator = db.Column(db.String(50))
    owner = db.Column(db.String(50))
    price = db.Column(db.Integer)
    timestamp = db.Column(db.String(50))

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
        self.private_key = hashlib.sha256(
            (name + "BRICKS_SECRET_2026").encode()
        ).hexdigest()[:16]
        self.nfts = []

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
            if hash_val.startswith("000"):
                return hash_val
            self.nonce += 1

# ===== NFT =====
class NFT:
    def __init__(self, name, description, creator, price):
        self.name = name
        self.description = description
        self.creator = creator
        self.owner = creator
        self.price = price
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.nft_id = hashlib.sha256(
            (name + creator + self.timestamp).encode()
        ).hexdigest()[:10]

# ===== SMART CONTRACT =====
class SmartContract:
    def __init__(self, creator, receiver, amount, condition):
        self.creator = creator
        self.receiver = receiver
        self.amount = amount
        self.condition = condition
        self.status = "pending"
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.contract_id = hashlib.sha256(
            (creator + receiver + str(amount) + self.timestamp).encode()
        ).hexdigest()[:10]

# ===== BLOCKCHAIN =====
class BricksCoin:
    def __init__(self):
        self.chain = []
        self.wallets = {}
        self.transaction_history = []
        self.contracts = []
        self.nfts = []
        self.mining_reward = 10
        self.total_supply = 21000000
        self.circulating_supply = 0
        genesis = Block(0, "BRICKS Genesis Block", "0")
        self.chain.append(genesis)
        self._load_wallets()
        self._load_nfts()

    def _load_wallets(self):
        with app.app_context():
            saved = WalletDB.query.all()
            if not saved:
                self.create_wallet("Rahul", 1000)
                self.create_wallet("Priya", 800)
                self.create_wallet("Amit", 600)
            else:
                for w in saved:
                    wallet = Wallet(w.name)
                    wallet.balance = w.balance
                    self.wallets[w.name] = wallet
                    self.circulating_supply += w.balance

    def _load_nfts(self):
        with app.app_context():
            saved = NFTDB.query.all()
            for n in saved:
                nft = NFT(n.name, n.description, n.creator, n.price)
                nft.nft_id = n.nft_id
                nft.owner = n.owner
                nft.timestamp = n.timestamp
                self.nfts.append(nft)
                if n.owner in self.wallets:
                    self.wallets[n.owner].nfts.append(nft.nft_id)

    def create_wallet(self, name, balance=0):
        if not name or len(name) > 50:
            return None
        w = Wallet(name)
        w.balance = balance
        self.wallets[name] = w
        self.circulating_supply += balance
        with app.app_context():
            existing = WalletDB.query.filter_by(name=name).first()
            if not existing:
                db_wallet = WalletDB(name=name, address=w.address, balance=balance)
                db.session.add(db_wallet)
                db.session.commit()
        return w

    def save_wallet(self, name):
        with app.app_context():
            w = WalletDB.query.filter_by(name=name).first()
            if w:
                w.balance = self.wallets[name].balance
                db.session.commit()

    def send_bricks(self, sender, receiver, amount, private_key=""):
        if not sender or not receiver or not amount:
            return False, "सब fields भरो!"
        if sender not in self.wallets:
            return False, f"{sender} की Wallet नहीं मिली!"
        if receiver not in self.wallets:
            return False, f"{receiver} की Wallet नहीं मिली!"
        if self.wallets[sender].private_key != private_key:
            return False, "❌ Wrong Private Key!"
        try:
            amount = int(amount)
        except:
            return False, "Amount सही नहीं है!"
        if amount <= 0:
            return False, "Amount 0 से ज़्यादा होना चाहिए!"
        if amount > 10000:
            return False, "एक बार में 10000 से ज़्यादा नहीं!"
        if self.wallets[sender].balance < amount:
            return False, "Balance कम है!"

        self.wallets[sender].balance -= amount
        self.wallets[receiver].balance += amount

        tx = {
            "from": sender,
            "to": receiver,
            "amount": amount,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.transaction_history.append(tx)

        with app.app_context():
            db_tx = TransactionDB(
                sender=sender,
                receiver=receiver,
                amount=amount,
                timestamp=tx["time"]
            )
            db.session.add(db_tx)
            db.session.commit()

        block = Block(len(self.chain), str(tx), self.chain[-1].hash)
        self.chain.append(block)
        self.wallets[sender].balance += self.mining_reward
        self.circulating_supply += self.mining_reward

        self.save_wallet(sender)
        self.save_wallet(receiver)
        return True, "Transaction हो गई!"

    def create_nft(self, name, description, creator, price, private_key):
        if creator not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[creator].private_key != private_key:
            return False, "❌ Wrong Private Key!"
        if not name or len(name) > 100:
            return False, "NFT नाम सही नहीं!"

        nft = NFT(name, description, creator, price)
        self.nfts.append(nft)
        self.wallets[creator].nfts.append(nft.nft_id)

        with app.app_context():
            db_nft = NFTDB(
                nft_id=nft.nft_id,
                name=nft.name,
                description=nft.description,
                creator=nft.creator,
                owner=nft.owner,
                price=nft.price,
                timestamp=nft.timestamp
            )
            db.session.add(db_nft)
            db.session.commit()

        return True, f"✅ NFT बन गया! ID: {nft.nft_id}"

    def buy_nft(self, nft_id, buyer, private_key):
        if buyer not in self.wallets:
            return False, "Buyer Wallet नहीं मिली!"
        if self.wallets[buyer].private_key != private_key:
            return False, "❌ Wrong Private Key!"

        nft = None
        for n in self.nfts:
            if n.nft_id == nft_id:
                nft = n
                break

        if not nft:
            return False, "NFT नहीं मिली!"
        if nft.owner == buyer:
            return False, "यह NFT पहले से तुम्हारी है!"
        if self.wallets[buyer].balance < nft.price:
            return False, "Balance कम है!"

        self.wallets[buyer].balance -= nft.price
        self.wallets[nft.owner].balance += nft.price

        old_owner = nft.owner
        nft.owner = buyer

        if nft_id in self.wallets[old_owner].nfts:
            self.wallets[old_owner].nfts.remove(nft_id)
        self.wallets[buyer].nfts.append(nft_id)

        with app.app_context():
            db_nft = NFTDB.query.filter_by(nft_id=nft_id).first()
            if db_nft:
                db_nft.owner = buyer
                db.session.commit()

        self.save_wallet(buyer)
        self.save_wallet(old_owner)
        return True, f"✅ NFT खरीद ली! {nft.price} BRICKS दिए!"

    def create_contract(self, creator, receiver, amount, condition, private_key):
        if creator not in self.wallets:
            return False, "Creator Wallet नहीं मिली!"
        if receiver not in self.wallets:
            return False, "Receiver Wallet नहीं मिली!"
        if self.wallets[creator].private_key != private_key:
            return False, "❌ Wrong Private Key!"
        try:
            amount = int(amount)
        except:
            return False, "Amount सही नहीं है!"
        if self.wallets[creator].balance < amount:
            return False, "Balance कम है!"

        contract = SmartContract(creator, receiver, amount, condition)
        self.contracts.append(contract)
        self.wallets[creator].balance -= amount
        self.save_wallet(creator)

        with app.app_context():
            db_contract = SmartContractDB(
                creator=creator,
                receiver=receiver,
                amount=amount,
                condition=condition,
                status="pending",
                timestamp=contract.timestamp
            )
            db.session.add(db_contract)
            db.session.commit()

        return True, f"✅ Contract बन गया! ID: {contract.contract_id}"

    def execute_contract(self, contract_id, private_key):
        for contract in self.contracts:
            if contract.contract_id == contract_id:
                if contract.status == "executed":
                    return False, "Contract already executed!"
                if self.wallets[contract.creator].private_key != private_key:
                    return False, "❌ Wrong Private Key!"

                self.wallets[contract.receiver].balance += contract.amount
                self.save_wallet(contract.receiver)
                contract.status = "executed"

                with app.app_context():
                    db_c = SmartContractDB.query.filter_by(
                        creator=contract.creator,
                        timestamp=contract.timestamp
                    ).first()
                    if db_c:
                        db_c.status = "executed"
                        db.session.commit()

                return True, f"✅ Contract Execute हो गया!"
        return False, "Contract नहीं मिला!"

    def is_valid(self):
        for i in range(1, len(self.chain)):
            if self.chain[i].previous_hash != self.chain[i-1].hash:
                return False
        return True

# ===== PRICE SYSTEM =====
class PriceSystem:
    def __init__(self):
        self.current_price = 0.001
        self.price_history = [0.001]

    def update_price(self, buy_pressure=True):
        change = random.uniform(0.00001, 0.0001)
        if buy_pressure:
            self.current_price += change
        else:
            self.current_price -= change
        if self.current_price < 0.0001:
            self.current_price = 0.0001
        self.price_history.append(round(self.current_price, 6))
        if len(self.price_history) > 20:
            self.price_history.pop(0)

    def get_market_cap(self, circulating):
        return round(self.current_price * circulating, 4)

with app.app_context():
    db.create_all()

bricks = BricksCoin()
price_system = PriceSystem()

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
    price_system.update_price()
    return jsonify({
        "coin": "BRICKS Coin",
        "total_supply": "21,000,000 BRICKS",
        "circulating": bricks.circulating_supply,
        "total_blocks": len(bricks.chain),
        "total_wallets": len(bricks.wallets),
        "total_contracts": len(bricks.contracts),
        "total_nfts": len(bricks.nfts),
        "blockchain_valid": bricks.is_valid(),
        "price_usd": round(price_system.current_price, 6),
        "market_cap_usd": price_system.get_market_cap(bricks.circulating_supply),
        "price_history": price_system.price_history,
        "status": "BRICKS Coin is LIVE!"
    })

@app.route('/wallets')
@rate_limit
def wallets():
    result = {}
    for name, w in bricks.wallets.items():
        result[name] = {
            "address": w.address,
            "balance": w.balance,
            "private_key": w.private_key,
            "nfts": w.nfts
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

@app.route('/send/<sender>/<receiver>/<amount>/<private_key>')
@rate_limit
def send(sender, receiver, amount, private_key):
    success, msg = bricks.send_bricks(sender, receiver, amount, private_key)
    if success:
        return jsonify({
            "status": "Transaction Done!",
            "from": sender,
            "to": receiver,
            "amount": amount,
            "message": msg
        })
    return jsonify({"status": "Failed!", "message": msg}), 400

@app.route('/nft/create/<creator>/<name>/<description>/<int:price>/<private_key>')
@rate_limit
def create_nft(creator, name, description, price, private_key):
    success, msg = bricks.create_nft(name, description, creator, price, private_key)
    if success:
        return jsonify({"status": "NFT बन गया!", "message": msg})
    return jsonify({"status": "Failed!", "message": msg}), 400

@app.route('/nft/buy/<nft_id>/<buyer>/<private_key>')
@rate_limit
def buy_nft(nft_id, buyer, private_key):
    success, msg = bricks.buy_nft(nft_id, buyer, private_key)
    if success:
        return jsonify({"status": "NFT खरीद ली!", "message": msg})
    return jsonify({"status": "Failed!", "message": msg}), 400

@app.route('/nfts')
@rate_limit
def nfts():
    result = []
    for n in bricks.nfts:
        result.append({
            "id": n.nft_id,
            "name": n.name,
            "description": n.description,
            "creator": n.creator,
            "owner": n.owner,
            "price": n.price,
            "time": n.timestamp
        })
    return jsonify(result)

@app.route('/contract/create/<creator>/<receiver>/<amount>/<condition>/<private_key>')
@rate_limit
def create_contract(creator, receiver, amount, condition, private_key):
    success, msg = bricks.create_contract(creator, receiver, amount, condition, private_key)
    if success:
        return jsonify({"status": "Contract बन गया!", "message": msg})
    return jsonify({"status": "Failed!", "message": msg}), 400

@app.route('/contract/execute/<contract_id>/<private_key>')
@rate_limit
def execute_contract(contract_id, private_key):
    success, msg = bricks.execute_contract(contract_id, private_key)
    if success:
        return jsonify({"status": "Contract Execute हो गया!", "message": msg})
    return jsonify({"status": "Failed!", "message": msg}), 400

@app.route('/contracts')
@rate_limit
def contracts():
    result = []
    for c in bricks.contracts:
        result.append({
            "id": c.contract_id,
            "creator": c.creator,
            "receiver": c.receiver,
            "amount": c.amount,
            "condition": c.condition,
            "status": c.status,
            "time": c.timestamp
        })
    return jsonify(result)

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
