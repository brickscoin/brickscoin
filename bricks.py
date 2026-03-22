import hashlib
import time
import json

print("=" * 45)
print("   💎 BRICKS COIN - FINAL VERSION 💎")
print("   🚀 Complete Cryptocurrency!")
print("=" * 45)

class Wallet:
    def __init__(self, name):
        self.name = name
        self.address = hashlib.sha256(name.encode()).hexdigest()[:20]
        self.balance = 0

    def show(self):
        print(f"\n👛 Name    : {self.name}")
        print(f"   Address : {self.address}")
        print(f"   Balance : {self.balance} BRICKS 💎")

class Block:
    def __init__(self, index, transactions, previous_hash, miner):
        self.index = index
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.miner = miner
        self.nonce = 0
        self.hash = self.mine_block()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self):
        print(f"\n⛏️  Block #{self.index} Mine हो रहा है", end="")
        while True:
            hash_val = self.calculate_hash()
            if hash_val.startswith("00"):
                print(f" ✅ Done!")
                return hash_val
            self.nonce += 1
            if self.nonce % 500 == 0:
                print(".", end="")

class BricksCoin:
    def __init__(self):
        self.chain = []
        self.wallets = {}
        self.transaction_history = []
        self.mining_reward = 10
        self.total_supply = 21000000
        self.circulating_supply = 0
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, "BRICKS Genesis Block", "0", "System")
        self.chain.append(genesis)
        print("\n🎉 BRICKS Coin Blockchain शुरू हुई!")
        print(f"💰 Total Supply : {self.total_supply:,} BRICKS")

    def create_wallet(self, name, initial_balance=0):
        wallet = Wallet(name)
        wallet.balance = initial_balance
        self.wallets[name] = wallet
        self.circulating_supply += initial_balance
        print(f"\n✅ Wallet बनी → {name}")
        print(f"   Address : {wallet.address}")
        print(f"   Balance : {wallet.balance} BRICKS")
        return wallet

    def send_bricks(self, sender, receiver, amount, miner):
        if sender not in self.wallets:
            print(f"❌ {sender} की Wallet नहीं मिली!")
            return False
        if receiver not in self.wallets:
            print(f"❌ {receiver} की Wallet नहीं मिली!")
            return False
        sender_wallet = self.wallets[sender]
        receiver_wallet = self.wallets[receiver]
        if sender_wallet.balance < amount:
            print(f"❌ Balance कम है!")
            return False
        tx = {
            "from": sender,
            "to": receiver,
            "amount": amount,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.transaction_history.append(tx)
        data = f"{sender} ne {receiver} ko {amount} BRICKS bheje"
        prev_hash = self.chain[-1].hash
        new_block = Block(len(self.chain), data, prev_hash, miner)
        self.chain.append(new_block)
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount
        if miner in self.wallets:
            self.wallets[miner].balance += self.mining_reward
            self.circulating_supply += self.mining_reward
        print(f"✅ {sender} → {receiver} → {amount} BRICKS")
        print(f"🏆 {miner} को {self.mining_reward} BRICKS Reward!")
        return True

    def is_valid(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i-1]
            if curr.previous_hash != prev.hash:
                return False
        return True

    def show_chain(self):
        print("\n" + "=" * 45)
        print("   💎 BRICKS Blockchain")
        print("=" * 45)
        for block in self.chain:
            print(f"\n🔷 Block #{block.index}")
            print(f"   📦 Data  : {str(block.transactions)[:30]}...")
            print(f"   ⛏️  Miner : {block.miner}")
            print(f"   🔐 Hash  : {block.hash[:25]}...")

    def show_all_wallets(self):
        print("\n" + "=" * 45)
        print("   👛 सभी Wallets")
        print("=" * 45)
        for wallet in self.wallets.values():
            wallet.show()

    def show_stats(self):
        print("\n" + "=" * 45)
        print("   📊 BRICKS Coin Statistics")
        print("=" * 45)
        print(f"\n💰 Total Supply    : {self.total_supply:,} BRICKS")
        print(f"🔄 Circulating     : {self.circulating_supply:,} BRICKS")
        print(f"📦 Total Blocks    : {len(self.chain)}")
        print(f"📜 Total Transactions : {len(self.transaction_history)}")
        print(f"👛 Total Wallets   : {len(self.wallets)}")
        if self.is_valid():
            print(f"\n🔐 Blockchain : 100% Valid ✅")

bricks = BricksCoin()

bricks.create_wallet("Rahul", 1000)
bricks.create_wallet("Priya", 800)
bricks.create_wallet("Amit", 600)
bricks.create_wallet("Neha", 400)

bricks.send_bricks("Rahul", "Priya", 200, "Rahul")
bricks.send_bricks("Priya", "Amit", 150, "Priya")
bricks.send_bricks("Amit", "Neha", 100, "Amit")
bricks.send_bricks("Neha", "Rahul", 50, "Neha")

bricks.show_chain()
bricks.show_all_wallets()
bricks.show_stats()

print("\n" + "=" * 45)
print("🎉 BRICKS Coin Successfully Launch!")
print("💎 Welcome to BRICKS Cryptocurrency!")
print("🚀 Made with ❤️  by BRICKS Team!")
print("=" * 45)
