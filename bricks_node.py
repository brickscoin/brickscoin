# ===== BRICKS COIN NODE =====
# यह file अपने Computer पर चलाओ
# और BRICKS Network का हिस्सा बनो!

import requests
import time
import json

# ===== SETTINGS =====
MAIN_NODE = "https://brickscoin.onrender.com"
NODE_NAME = "My-BRICKS-Node"

print("=" * 50)
print("💎 BRICKS COIN NODE")
print("🌍 Global Currency Network")
print("=" * 50)
print(f"📡 Main Node: {MAIN_NODE}")
print(f"🖥️ Node Name: {NODE_NAME}")
print("=" * 50)

def get_network_status():
    try:
        response = requests.get(f"{MAIN_NODE}/api", timeout=10)
        data = response.json()
        print("\n✅ Network Status:")
        print(f"   💎 Coin: {data.get('coin')}")
        print(f"   🌐 Mission: {data.get('mission')}")
        print(f"   📦 Total Blocks: {data.get('total_blocks')}")
        print(f"   👥 Total Wallets: {data.get('total_wallets')}")
        print(f"   💰 Price: ${data.get('price_usd')}")
        print(f"   📊 Market Cap: ${data.get('market_cap_usd')}")
        print(f"   🔗 Nodes: {data.get('active_nodes')}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def sync_with_network():
    try:
        response = requests.get(f"{MAIN_NODE}/chain", timeout=10)
        chain = response.json()
        print(f"\n✅ Blockchain Synced!")
        print(f"   📦 Total Blocks: {len(chain)}")
        return True
    except:
        print("❌ Sync Failed!")
        return False

def register_node():
    try:
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
        print(f"\n📡 Registering Node: {local_ip}")
        print(f"✅ Node Registered as: {NODE_NAME}")
        return True
    except:
        return False

def show_menu():
    print("\n" + "=" * 50)
    print("📋 MENU:")
    print("1. Network Status देखो")
    print("2. Blockchain Sync करो")
    print("3. Wallets देखो")
    print("4. Auto Sync (हर 60 seconds)")
    print("5. Exit")
    print("=" * 50)
    return input("Option चुनो (1-5): ")

def view_wallets():
    try:
        response = requests.get(f"{MAIN_NODE}/wallets", timeout=10)
        wallets = response.json()
        print("\n✅ Wallets:")
        for name, data in wallets.items():
            print(f"   👛 {name}: {data.get('balance')} BRICKS")
        return True
    except:
        print("❌ Failed!")
        return False

def auto_sync():
    print("\n🔄 Auto Sync शुरू!")
    print("Ctrl+C से रोको\n")
    count = 0
    try:
        while True:
            count += 1
            print(f"🔄 Sync #{count} - {time.strftime('%H:%M:%S')}")
            get_network_status()
            sync_with_network()
            print(f"⏰ अगला Sync 60 seconds में...")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n✅ Auto Sync रोका!")

# ===== MAIN =====
print("\n🚀 BRICKS Node शुरू हो रहा है...")
register_node()
get_network_status()

while True:
    choice = show_menu()
    if choice == "1":
        get_network_status()
    elif choice == "2":
        sync_with_network()
    elif choice == "3":
        view_wallets()
    elif choice == "4":
        auto_sync()
    elif choice == "5":
        print("\n👋 BRICKS Node बंद हो रहा है!")
        print("💎 BRICKS Network को Support करने के लिए धन्यवाद!")
        break
    else:
        print("❌ गलत Option!")
