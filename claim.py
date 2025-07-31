import base64
import json
import time
import requests
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder

RPC = "https://octra.network"

# === Load addresses and private keys ===
with open("address.txt") as f:
    addresses = [line.strip() for line in f if line.strip()]

with open("pvt.txt") as f:
    priv_keys = [line.strip() for line in f if line.strip()]

if len(addresses) != len(priv_keys):
    raise ValueError("❌ address.txt and pvt.txt must have same number of lines")

# === Load contract interface ===
with open("exec_interface.json") as f:
    interface = json.load(f)

contract = interface["contract"]
method = interface["methods"][0]["name"]

print(f"Using contract: {contract}, method: {method}")
print(f"Loaded {len(addresses)} wallets")

def api_call(method_type, url, data=None, retries=3):
    headers = {"Content-Type": "application/json"}
    for attempt in range(1, retries + 1):
        try:
            if method_type == "GET":
                r = requests.get(url, headers=headers, timeout=30)
            else:
                r = requests.post(url, headers=headers, json=data, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"⚠️ API call failed ({attempt}/{retries}): {e}")
            time.sleep(2)
    raise RuntimeError(f"API call failed after {retries} retries: {url}")

for addr, priv_b64 in zip(addresses, priv_keys):
    print(f"\n🔑 Processing wallet: {addr}")
    sk_bytes = base64.b64decode(priv_b64)
    sk = SigningKey(sk_bytes)
    vk = sk.verify_key

    # === Get nonce ===
    bal_resp = api_call("GET", f"{RPC}/balance/{addr}")
    nonce = bal_resp["nonce"]
    print(f"Nonce: {nonce}")

    timestamp = round(time.time(), 6)
    tx = {
        "from": addr,
        "to_": contract,
        "amount": "0",
        "nonce": nonce + 1,
        "ou": "1",
        "timestamp": timestamp
    }

    # Strict ordering for signing
    blob = '{{"from":"{}","to_":"{}","amount":"{}","nonce":{},"ou":"{}","timestamp":{}}}'.format(
        tx["from"], tx["to_"], tx["amount"], tx["nonce"], tx["ou"], tx["timestamp"]
    )

    signature = sk.sign(blob.encode(), encoder=RawEncoder).signature
    signature_b64 = base64.b64encode(signature).decode()
    public_key_b64 = base64.b64encode(vk.encode()).decode()

    data = {
        "contract": contract,
        "method": method,
        "params": [],
        "caller": addr,
        "nonce": nonce + 1,
        "timestamp": timestamp,
        "signature": signature_b64,
        "public_key": public_key_b64
    }

    print("📡 Calling contract...")
    resp = api_call("POST", f"{RPC}/call-contract", data)
    tx_hash = resp.get("tx_hash")

    if tx_hash:
        print(f"✅ TX Sent: {tx_hash}")
    else:
        print(f"❌ Failed TX. Full response: {resp}")
