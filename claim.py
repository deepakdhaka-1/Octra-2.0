import base64
import json
import time
import requests
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder

# Load wallet.json
with open("pvt.txt") as f:
    wallet = json.load(f)

priv_key_b64 = wallet["priv"]
addr = wallet["addr"]
rpc = wallet["rpc"]

sk_bytes = base64.b64decode(priv_key_b64)
sk = SigningKey(sk_bytes)
vk = sk.verify_key

with open("exec_interface.json") as f:
    interface = json.load(f)

contract = interface["contract"]
method = interface["methods"][0]["name"]

print(f"Using contract: {contract}, method: {method}")

def api_call(method_type, url, data=None):
    headers = {"Content-Type": "application/json"}  # explicit like Rust
    if method_type == "GET":
        r = requests.get(url, headers=headers, timeout=30)
    else:
        r = requests.post(url, headers=headers, json=data, timeout=30)
    r.raise_for_status()
    return r.json()

# Balance
bal_resp = api_call("GET", f"{rpc}/balance/{addr}")
nonce = bal_resp["nonce"]
print(f"Nonce: {nonce}")

# Match Rust numeric values
timestamp = round(time.time(), 6)  # same precision as serde_json
tx = {
    "from": addr,
    "to_": contract,
    "amount": "0",
    "nonce": nonce + 1,  # numeric, not string
    "ou": "1",           # keep as string because Rust does
    "timestamp": timestamp
}

# EXACT order & formatting for signing
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

print("Calling contract...")
resp = api_call("POST", f"{rpc}/call-contract", data)
print("TX:", resp.get("tx_hash"))
