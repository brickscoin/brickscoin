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

# ===== DATABASE MODELS =====
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
    staked = db.Column(db.Integer, default=0)
    reward_points = db.Column(db.Integer, default=0)
    language = db.Column(db.String(10), default="hi")

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

class MarketplaceDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(500))
    seller = db.Column(db.String(50))
    buyer = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Integer)
    status = db.Column(db.String(20), default="available")
    timestamp = db.Column(db.String(50))

class StakeDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    stake_time = db.Column(db.String(50))
    status = db.Column(db.String(20), default="active")

class LoanDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.String(20), unique=True)
    borrower = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    interest = db.Column(db.Float)
    due_date = db.Column(db.String(50))
    status = db.Column(db.String(20), default="active")
    timestamp = db.Column(db.String(50))

class VoteDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vote_id = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    creator = db.Column(db.String(50))
    yes_votes = db.Column(db.Integer, default=0)
    no_votes = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="active")
    timestamp = db.Column(db.String(50))

class GameDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.String(50))
    game = db.Column(db.String(50))
    score = db.Column(db.Integer)
    reward = db.Column(db.Integer)
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

# ===== MULTI LANGUAGE =====
MESSAGES = {
    "hi": {
        "tx_done": "✅ Transaction हो गई!",
        "tx_failed": "❌ Transaction Failed!",
        "wrong_key": "❌ Wrong Private Key!",
        "low_balance": "❌ Balance कम है!",
        "staked": "✅ BRICKS Stake हो गए!",
        "reward": "✅ Reward मिला!",
        "loan": "✅ Loan मिला!",
        "game_play": "🎮 Game खेला!",
        "vote_cast": "✅ Vote दे दिया!",
    },
    "en": {
        "tx_done": "✅ Transaction Done!",
        "tx_failed": "❌ Transaction Failed!",
        "wrong_key": "❌ Wrong Private Key!",
        "low_balance": "❌ Low Balance!",
        "staked": "✅ BRICKS Staked!",
        "reward": "✅ Reward Received!",
        "loan": "✅ Loan Granted!",
        "game_play": "🎮 Game Played!",
        "vote_cast": "✅ Vote Cast!",
    },
    "zh": {
        "tx_done": "✅ 交易完成!",
        "tx_failed": "❌ 交易失败!",
        "wrong_key": "❌ 错误的私钥!",
        "low_balance": "❌ 余额不足!",
        "staked": "✅ 已质押!",
        "reward": "✅ 已获得奖励!",
        "loan": "✅ 贷款已批准!",
        "game_play": "🎮 游戏完成!",
        "vote_cast": "✅ 投票完成!",
    },
    "ru": {
        "tx_done": "✅ Транзакция выполнена!",
        "tx_failed": "❌ Ошибка транзакции!",
        "wrong_key": "❌ Неверный ключ!",
        "low_balance": "❌ Недостаточно средств!",
        "staked": "✅ BRICKS застейканы!",
        "reward": "✅ Награда получена!",
        "loan": "✅ Кредит одобрен!",
        "game_play": "🎮 Игра сыграна!",
        "vote_cast": "✅ Голос подан!",
    }
}

# ===== WALLET =====
class Wallet:
    def __init__(self, name):
        self.name = name
        self.address = hashlib.sha256(name.encode()).hexdigest()[:20]
        self.balance = 0
        self.staked = 0
        self.reward_points = 0
        self.language = "hi"
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

# ===== MARKETPLACE ITEM =====
class MarketItem:
    def __init__(self, name, description, seller, price):
        self.name = name
        self.description = description
        self.seller = seller
        self.buyer = None
        self.price = price
        self.status = "available"
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.item_id = hashlib.sha256(
            (name + seller + self.timestamp).encode()
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
        ).hexdigest()[:10]# ===== BLOCKCHAIN =====
class BricksCoin:
    def __init__(self):
        self.chain = []
        self.wallets = {}
        self.transaction_history = []
        self.contracts = []
        self.nfts = []
        self.marketplace = []
        self.loans = []
        self.votes = []
        self.mining_reward = 10
        self.total_supply = 21000000
        self.circulating_supply = 0
        self.staking_rate = 0.05
        self.bank_reserve = 100000
        self.transaction_fee = 0
        genesis = Block(0, "BRICKS Genesis Block - Global Currency", "0")
        self.chain.append(genesis)
        self._load_wallets()
        self._load_nfts()
        self._load_marketplace()
        self._load_votes()
        self._load_loans()

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
                    wallet.staked = w.staked
                    wallet.reward_points = w.reward_points
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

    def _load_marketplace(self):
        with app.app_context():
            saved = MarketplaceDB.query.all()
            for m in saved:
                item = MarketItem(m.name, m.description, m.seller, m.price)
                item.item_id = m.item_id
                item.buyer = m.buyer
                item.status = m.status
                item.timestamp = m.timestamp
                self.marketplace.append(item)

    def _load_votes(self):
        with app.app_context():
            saved = VoteDB.query.all()
            for v in saved:
                self.votes.append({
                    "vote_id": v.vote_id,
                    "title": v.title,
                    "description": v.description,
                    "creator": v.creator,
                    "yes_votes": v.yes_votes,
                    "no_votes": v.no_votes,
                    "status": v.status,
                    "timestamp": v.timestamp
                })

    def _load_loans(self):
        with app.app_context():
            saved = LoanDB.query.all()
            for l in saved:
                self.loans.append({
                    "loan_id": l.loan_id,
                    "borrower": l.borrower,
                    "amount": l.amount,
                    "interest": l.interest,
                    "due_date": l.due_date,
                    "status": l.status,
                    "timestamp": l.timestamp
                })

    def create_wallet(self, name, balance=0, language="hi"):
        if not name or len(name) > 50:
            return None
        w = Wallet(name)
        w.balance = balance
        w.language = language
        self.wallets[name] = w
        self.circulating_supply += balance
        with app.app_context():
            existing = WalletDB.query.filter_by(name=name).first()
            if not existing:
                db_wallet = WalletDB(
                    name=name,
                    address=w.address,
                    balance=balance,
                    language=language
                )
                db.session.add(db_wallet)
                db.session.commit()
        return w

    def save_wallet(self, name):
        with app.app_context():
            w = WalletDB.query.filter_by(name=name).first()
            if w:
                w.balance = self.wallets[name].balance
                w.staked = self.wallets[name].staked
                w.reward_points = self.wallets[name].reward_points
                db.session.commit()

    def get_msg(self, name, key):
        lang = self.wallets[name].language if name in self.wallets else "hi"
        return MESSAGES.get(lang, MESSAGES["hi"]).get(key, key)

    def send_bricks(self, sender, receiver, amount, private_key=""):
        if sender not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if receiver not in self.wallets:
            return False, "Receiver नहीं मिला!"
        if self.wallets[sender].private_key != private_key:
            return False, self.get_msg(sender, "wrong_key")
        try:
            amount = int(amount)
        except:
            return False, "Amount सही नहीं!"
        if amount <= 0:
            return False, "Amount 0 से ज़्यादा होना चाहिए!"
        if self.wallets[sender].balance < amount:
            return False, self.get_msg(sender, "low_balance")

        # ZERO FEES - Global Currency Feature
        self.wallets[sender].balance -= amount
        self.wallets[receiver].balance += amount
        self.wallets[sender].reward_points += 5

        tx = {
            "from": sender,
            "to": receiver,
            "amount": amount,
            "fee": 0,
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
        return True, self.get_msg(sender, "tx_done")

    def stake_bricks(self, name, amount, private_key):
        if name not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[name].private_key != private_key:
            return False, self.get_msg(name, "wrong_key")
        try:
            amount = int(amount)
        except:
            return False, "Amount सही नहीं!"
        if self.wallets[name].balance < amount:
            return False, self.get_msg(name, "low_balance")

        self.wallets[name].balance -= amount
        self.wallets[name].staked += amount
        self.save_wallet(name)

        with app.app_context():
            db_stake = StakeDB(
                wallet=name,
                amount=amount,
                stake_time=time.strftime("%Y-%m-%d %H:%M:%S"),
                status="active"
            )
            db.session.add(db_stake)
            db.session.commit()

        return True, f"✅ {amount} BRICKS Stake! रोज़ {int(amount * self.staking_rate)} BRICKS मिलेंगे!"

    def claim_stake_reward(self, name, private_key):
        if name not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[name].private_key != private_key:
            return False, self.get_msg(name, "wrong_key")
        if self.wallets[name].staked == 0:
            return False, "कोई Stake नहीं है!"

        reward = int(self.wallets[name].staked * self.staking_rate)
        self.wallets[name].balance += reward
        self.wallets[name].reward_points += 10
        self.circulating_supply += reward
        self.save_wallet(name)
        return True, f"✅ {reward} BRICKS Reward मिला!"

    def unstake_bricks(self, name, private_key):
        if name not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[name].private_key != private_key:
            return False, self.get_msg(name, "wrong_key")
        if self.wallets[name].staked == 0:
            return False, "कोई Stake नहीं!"

        amount = self.wallets[name].staked
        self.wallets[name].balance += amount
        self.wallets[name].staked = 0
        self.save_wallet(name)
        return True, f"✅ {amount} BRICKS Unstake!"

    def claim_reward(self, name, private_key):
        if name not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[name].private_key != private_key:
            return False, self.get_msg(name, "wrong_key")
        if self.wallets[name].reward_points < 100:
            return False, f"100 points चाहिए! अभी {self.wallets[name].reward_points} हैं!"

        bricks_reward = self.wallets[name].reward_points // 10
        self.wallets[name].balance += bricks_reward
        self.wallets[name].reward_points = 0
        self.circulating_supply += bricks_reward
        self.save_wallet(name)
        return True, f"✅ {bricks_reward} BRICKS Reward!"

    def create_vote(self, creator, title, description, private_key):
        if creator not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[creator].private_key != private_key:
            return False, self.get_msg(creator, "wrong_key")

        vote_id = hashlib.sha256(
            (creator + title + time.strftime("%Y-%m-%d %H:%M:%S")).encode()
        ).hexdigest()[:10]

        vote = {
            "vote_id": vote_id,
            "title": title,
            "description": description,
            "creator": creator,
            "yes_votes": 0,
            "no_votes": 0,
            "status": "active",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.votes.append(vote)

        with app.app_context():
            db_vote = VoteDB(
                vote_id=vote_id,
                title=title,
                description=description,
                creator=creator,
                status="active",
                timestamp=vote["timestamp"]
            )
            db.session.add(db_vote)
            db.session.commit()

        return True, f"✅ Vote बन गया! ID: {vote_id}"

    def cast_vote(self, vote_id, voter, choice, private_key):
        if voter not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[voter].private_key != private_key:
            return False, self.get_msg(voter, "wrong_key")

        for vote in self.votes:
            if vote["vote_id"] == vote_id:
                if vote["status"] != "active":
                    return False, "Vote बंद है!"
                if choice.lower() == "yes":
                    vote["yes_votes"] += 1
                else:
                    vote["no_votes"] += 1

                self.wallets[voter].reward_points += 5
                self.save_wallet(voter)

                with app.app_context():
                    db_vote = VoteDB.query.filter_by(vote_id=vote_id).first()
                    if db_vote:
                        db_vote.yes_votes = vote["yes_votes"]
                        db_vote.no_votes = vote["no_votes"]
                        db.session.commit()

                return True, f"✅ Vote! Yes:{vote['yes_votes']} No:{vote['no_votes']}"
        return False, "Vote नहीं मिला!"

    def play_game(self, player, private_key):
        if player not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[player].private_key != private_key:
            return False, self.get_msg(player, "wrong_key")

        score = random.randint(1, 100)
        reward = score // 10

        self.wallets[player].balance += reward
        self.wallets[player].reward_points += score
        self.circulating_supply += reward
        self.save_wallet(player)

        with app.app_context():
            db_game = GameDB(
                player=player,
                game="BRICKS-Game",
                score=score,
                reward=reward,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            db.session.add(db_game)
            db.session.commit()

        return True, f"🎮 Score:{score} Reward:{reward} BRICKS!"

    def take_loan(self, borrower, amount, private_key):
        if borrower not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[borrower].private_key != private_key:
            return False, self.get_msg(borrower, "wrong_key")
        try:
            amount = int(amount)
        except:
            return False, "Amount सही नहीं!"
        if amount > 1000:
            return False, "1000 से ज़्यादा नहीं!"
        if amount > self.bank_reserve:
            return False, "Bank Reserve कम है!"

        loan_id = hashlib.sha256(
            (borrower + str(amount) + time.strftime("%Y-%m-%d %H:%M:%S")).encode()
        ).hexdigest()[:10]

        self.wallets[borrower].balance += amount
        self.bank_reserve -= amount
        self.circulating_supply += amount

        loan = {
            "loan_id": loan_id,
            "borrower": borrower,
            "amount": amount,
            "interest": 0.10,
            "due_date": "30 days",
            "status": "active",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.loans.append(loan)

        with app.app_context():
            db_loan = LoanDB(
                loan_id=loan_id,
                borrower=borrower,
                amount=amount,
                interest=0.10,
                due_date="30 days",
                status="active",
                timestamp=loan["timestamp"]
            )
            db.session.add(db_loan)
            db.session.commit()

        self.save_wallet(borrower)
        return True, f"✅ {amount} BRICKS Loan! 10% Interest 30 दिन!"

    def repay_loan(self, loan_id, borrower, private_key):
        if borrower not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[borrower].private_key != private_key:
            return False, self.get_msg(borrower, "wrong_key")

        for loan in self.loans:
            if loan["loan_id"] == loan_id:
                if loan["status"] == "repaid":
                    return False, "Loan पहले ही चुका दिया!"

                repay = int(loan["amount"] * 1.10)
                if self.wallets[borrower].balance < repay:
                    return False, f"{repay} BRICKS चाहिए!"

                self.wallets[borrower].balance -= repay
                self.bank_reserve += repay
                loan["status"] = "repaid"

                with app.app_context():
                    db_loan = LoanDB.query.filter_by(loan_id=loan_id).first()
                    if db_loan:
                        db_loan.status = "repaid"
                        db.session.commit()

                self.save_wallet(borrower)
                return True, f"✅ Loan चुका दिया! {repay} BRICKS!"
        return False, "Loan नहीं मिला!"

    def create_nft(self, name, description, creator, price, private_key):
        if creator not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[creator].private_key != private_key:
            return False, self.get_msg(creator, "wrong_key")

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

        return True, f"✅ NFT बना! ID:{nft.nft_id}"

    def buy_nft(self, nft_id, buyer, private_key):
        if buyer not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[buyer].private_key != private_key:
            return False, self.get_msg(buyer, "wrong_key")

        for n in self.nfts:
            if n.nft_id == nft_id:
                if n.owner == buyer:
                    return False, "पहले से तुम्हारी है!"
                if self.wallets[buyer].balance < n.price:
                    return False, self.get_msg(buyer, "low_balance")

                self.wallets[buyer].balance -= n.price
                self.wallets[n.owner].balance += n.price
                old_owner = n.owner
                n.owner = buyer

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
                return True, f"✅ NFT खरीदी!"
        return False, "NFT नहीं मिली!"

    def list_item(self, seller, name, description, price, private_key):
        if seller not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[seller].private_key != private_key:
            return False, self.get_msg(seller, "wrong_key")
        try:
            price = int(price)
        except:
            return False, "Price सही नहीं!"

        item = MarketItem(name, description, seller, price)
        self.marketplace.append(item)

        with app.app_context():
            db_item = MarketplaceDB(
                item_id=item.item_id,
                name=item.name,
                description=item.description,
                seller=item.seller,
                price=item.price,
                status="available",
                timestamp=item.timestamp
            )
            db.session.add(db_item)
            db.session.commit()

        return True, f"✅ Listed! ID:{item.item_id}"

    def buy_item(self, item_id, buyer, private_key):
        if buyer not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if self.wallets[buyer].private_key != private_key:
            return False, self.get_msg(buyer, "wrong_key")

        for i in self.marketplace:
            if i.item_id == item_id:
                if i.status == "sold":
                    return False, "पहले ही बिक गई!"
                if i.seller == buyer:
                    return False, "अपनी Item नहीं!"
                if self.wallets[buyer].balance < i.price:
                    return False, self.get_msg(buyer, "low_balance")

                self.wallets[buyer].balance -= i.price
                self.wallets[i.seller].balance += i.price
                i.buyer = buyer
                i.status = "sold"

                with app.app_context():
                    db_item = MarketplaceDB.query.filter_by(item_id=item_id).first()
                    if db_item:
                        db_item.buyer = buyer
                        db_item.status = "sold"
                        db.session.commit()

                self.save_wallet(buyer)
                self.save_wallet(i.seller)
                return True, f"✅ खरीद ली!"
        return False, "Item नहीं मिली!"

    def create_contract(self, creator, receiver, amount, condition, private_key):
        if creator not in self.wallets:
            return False, "Wallet नहीं मिली!"
        if receiver not in self.wallets:
            return False, "Receiver नहीं मिला!"
        if self.wallets[creator].private_key != private_key:
            return False, self.get_msg(creator, "wrong_key")
        try:
            amount = int(amount)
        except:
            return False, "Amount सही नहीं!"
        if self.wallets[creator].balance < amount:
            return False, self.get_msg(creator, "low_balance")

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

        return True, f"✅ Contract! ID:{contract.contract_id}"

    def execute_contract(self, contract_id, private_key):
        for contract in self.contracts:
            if contract.contract_id == contract_id:
                if contract.status == "executed":
                    return False, "Already executed!"
                if self.wallets[contract.creator].private_key != private_key:
                    return False, "❌ Wrong Key!"

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

                return True, "✅ Contract Execute!"
        return False, "Contract नहीं मिला!"

    # ===== AI SYSTEM =====
    def ai_predict_price(self):
        history = price_system.price_history
        if len(history) > 1:
            trend = history[-1] - history[0]
            if trend > 0:
                prediction = "📈 Price बढ़ेगी!"
                advice = "💡 अभी Buy करो!"
                action = "BUY"
            else:
                prediction = "📉 Price घटेगी!"
                advice = "💡 Hold करो!"
                action = "HOLD"
        else:
            prediction = "📊 Data कम है"
            advice = "💡 Wait करो!"
            action = "WAIT"

        return {
            "current_price": price_system.current_price,
            "prediction": prediction,
            "advice": advice,
            "action": action,
            "confidence": f"{random.randint(60, 95)}%",
            "global_impact": "🌍 Dollar से compare: BRICKS बढ़ रही है!"
        }

    def ai_analyze_wallet(self, name):
        if name not in self.wallets:
            return None
        w = self.wallets[name]
        total_value = w.balance + w.staked
        advice = ""
        if w.balance > 500:
            advice = "💡 Stake करो — ज़्यादा कमाओ!"
        elif w.staked > 0:
            advice = "💡 Reward Claim करो!"
        elif w.balance < 100:
            advice = "💡 Game खेलो — Balance बढ़ाओ!"
        else:
            advice = "💡 NFT या Market में invest करो!"

        return {
            "wallet": name,
            "balance": w.balance,
            "staked": w.staked,
            "reward_points": w.reward_points,
            "total_value": total_value,
            "nfts": len(w.nfts),
            "advice": advice,
            "global_rank": f"Top {random.randint(1, 100)}% BRICKS holders!"
        }

    def ai_global_analysis(self):
        return {
            "mission": "🌍 Dollar को Replace करना!",
            "current_users": len(self.wallets),
            "total_transactions": len(self.transaction_history),
            "total_value_locked": self.circulating_supply,
            "vs_dollar": "BRICKS Zero Fees | Dollar High Fees",
            "vs_bitcoin": "BRICKS Fast | Bitcoin Slow",
            "advantage": "✅ Multi Language ✅ Zero Fees ✅ Fast ✅ Smart Contracts ✅ NFT ✅ Bank",
            "prediction": f"📈 {random.randint(100, 1000)}% Growth Expected!",
            "countries_targeting": ["🇮🇳 India", "🇷🇺 Russia", "🇨🇳 China", "🇧🇷 Brazil", "🇿🇦 South Africa"]
        }

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
        "coin": "BRICKS Coin 💎",
        "mission": "🌍 Global Currency - Dollar Alternative",
        "total_supply": "21,000,000 BRICKS",
        "circulating": bricks.circulating_supply,
        "total_blocks": len(bricks.chain),
        "total_wallets": len(bricks.wallets),
        "total_contracts": len(bricks.contracts),
        "total_nfts": len(bricks.nfts),
        "total_market_items": len(bricks.marketplace),
        "total_votes": len(bricks.votes),
        "total_loans": len(bricks.loans),
        "bank_reserve": bricks.bank_reserve,
        "transaction_fee": "0 BRICKS (Zero Fee!)",
        "blockchain_valid": bricks.is_valid(),
        "price_usd": round(price_system.current_price, 6),
        "market_cap_usd": price_system.get_market_cap(bricks.circulating_supply),
        "price_history": price_system.price_history,
        "languages": ["Hindi", "English", "Chinese", "Russian"],
        "status": "🚀 BRICKS Coin is LIVE! Global Currency!"
    })

@app.route('/wallets')
@rate_limit
def wallets():
    result = {}
    for name, w in bricks.wallets.items():
        result[name] = {
            "address": w.address,
            "balance": w.balance,
            "staked": w.staked,
            "reward_points": w.reward_points,
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
        return jsonify({"status": "✅", "message": msg, "fee": "0 BRICKS"})
    return jsonify({"status": "❌", "message": msg}), 400

@app.route('/stake/<name>/<amount>/<private_key>')
@rate_limit
def stake(name, amount, private_key):
    success, msg = bricks.stake_bricks(name, amount, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/stake/claim/<name>/<private_key>')
@rate_limit
def claim_stake(name, private_key):
    success, msg = bricks.claim_stake_reward(name, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/stake/unstake/<name>/<private_key>')
@rate_limit
def unstake(name, private_key):
    success, msg = bricks.unstake_bricks(name, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/reward/claim/<name>/<private_key>')
@rate_limit
def claim_reward(name, private_key):
    success, msg = bricks.claim_reward(name, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/vote/create/<creator>/<title>/<description>/<private_key>')
@rate_limit
def create_vote(creator, title, description, private_key):
    success, msg = bricks.create_vote(creator, title, description, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/vote/cast/<vote_id>/<voter>/<choice>/<private_key>')
@rate_limit
def cast_vote(vote_id, voter, choice, private_key):
    success, msg = bricks.cast_vote(vote_id, voter, choice, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/votes')
@rate_limit
def votes():
    return jsonify(bricks.votes)

@app.route('/game/play/<player>/<private_key>')
@rate_limit
def play_game(player, private_key):
    success, msg = bricks.play_game(player, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/bank/loan/<borrower>/<amount>/<private_key>')
@rate_limit
def take_loan(borrower, amount, private_key):
    success, msg = bricks.take_loan(borrower, amount, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/bank/repay/<loan_id>/<borrower>/<private_key>')
@rate_limit
def repay_loan(loan_id, borrower, private_key):
    success, msg = bricks.repay_loan(loan_id, borrower, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/bank/loans')
@rate_limit
def loans():
    return jsonify(bricks.loans)

@app.route('/ai/predict')
@rate_limit
def ai_predict():
    return jsonify(bricks.ai_predict_price())

@app.route('/ai/analyze/<name>')
@rate_limit
def ai_analyze(name):
    result = bricks.ai_analyze_wallet(name)
    if result:
        return jsonify(result)
    return jsonify({"error": "Wallet नहीं मिली!"}), 404

@app.route('/ai/global')
@rate_limit
def ai_global():
    return jsonify(bricks.ai_global_analysis())

@app.route('/market/list/<seller>/<name>/<description>/<price>/<private_key>')
@rate_limit
def list_item(seller, name, description, price, private_key):
    success, msg = bricks.list_item(seller, name, description, price, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/market/buy/<item_id>/<buyer>/<private_key>')
@rate_limit
def buy_item(item_id, buyer, private_key):
    success, msg = bricks.buy_item(item_id, buyer, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/market')
@rate_limit
def market():
    result = []
    for item in bricks.marketplace:
        result.append({
            "id": item.item_id,
            "name": item.name,
            "description": item.description,
            "seller": item.seller,
            "buyer": item.buyer,
            "price": item.price,
            "status": item.status,
            "time": item.timestamp
        })
    return jsonify(result)

@app.route('/nft/create/<creator>/<name>/<description>/<int:price>/<private_key>')
@rate_limit
def create_nft(creator, name, description, price, private_key):
    success, msg = bricks.create_nft(name, description, creator, price, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/nft/buy/<nft_id>/<buyer>/<private_key>')
@rate_limit
def buy_nft(nft_id, buyer, private_key):
    success, msg = bricks.buy_nft(nft_id, buyer, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

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
    return jsonify({"status": "✅" if success else "❌", "message": msg})

@app.route('/contract/execute/<contract_id>/<private_key>')
@rate_limit
def execute_contract(contract_id, private_key):
    success, msg = bricks.execute_contract(contract_id, private_key)
    return jsonify({"status": "✅" if success else "❌", "message": msg})

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

@app.route('/wallet/create/<name>/<language>')
@rate_limit
def create_wallet_api(name, language):
    if language not in ["hi", "en", "zh", "ru"]:
        language = "hi"
    w = bricks.create_wallet(name, 100, language)
    if w:
        return jsonify({
            "status": "✅ Wallet बनी!",
            "name": name,
            "address": w.address,
            "balance": w.balance,
            "private_key": w.private_key,
            "language": language
        })
    return jsonify({"status": "❌ Failed!"}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Page नहीं मिली!"}), 404

@app.errorhandler(429)
def too_many(e):
    return jsonify({"error": "Too many requests!"}), 429

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error!"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
