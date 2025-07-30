import base64
import json
import os
import time
from typing import List, Dict, Tuple, Optional
import requests
from ed25519 import SigningKey, VerifyingKey

# Configuration
CONTRACT_INTERFACE_FILE = "exec_interface.json"
PVT_FILE = "pvt.txt"
ADDRESS_FILE = "address.txt"
RPC_ENDPOINT = "https://octra.network"
TIMEOUT = 100  # seconds for tx confirmation

class Wallet:
    def __init__(self, private_key: str, address: str):
        self.private_key = private_key
        self.address = address
        self.signing_key = SigningKey(base64.b64decode(private_key))

class ContractMethod:
    def __init__(self, name: str, label: str, params: List[Dict], method_type: str):
        self.name = name
        self.label = label
        self.params = params
        self.type = method_type

class ContractInterface:
    def __init__(self, contract_address: str, methods: List[ContractMethod]):
        self.contract = contract_address
        self.methods = methods

def load_wallets() -> List[Wallet]:
    with open(PVT_FILE, 'r') as f:
        private_keys = [line.strip() for line in f if line.strip()]
    
    with open(ADDRESS_FILE, 'r') as f:
        addresses = [line.strip() for line in f if line.strip()]
    
    if len(private_keys) != len(addresses):
        raise ValueError("Mismatch between number of private keys and addresses")
    
    return [Wallet(pvt, addr) for pvt, addr in zip(private_keys, addresses)]

def load_contract_interface() -> ContractInterface:
    with open(CONTRACT_INTERFACE_FILE, 'r') as f:
        data = json.load(f)
    
    methods = []
    for method_data in data['methods']:
        methods.append(ContractMethod(
            name=method_data['name'],
            label=method_data['label'],
            params=method_data['params'],
            method_type=method_data['type']
        ))
    
    return ContractInterface(data['contract'], methods)

def api_call(method: str, url: str, data: Optional[Dict] = None) -> Dict:
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            raise ValueError("Unsupported HTTP method")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Error: {e}")
        raise

def sign_tx(signing_key: SigningKey, tx_data: Dict) -> str:
    blob = json.dumps(tx_data, separators=(',', ':'))
    signature = signing_key.sign(blob.encode(), encoding='base64')
    return signature.decode('utf-8')

def get_balance(wallet: Wallet) -> Tuple[float, int]:
    try:
        data = api_call("GET", f"{RPC_ENDPOINT}/balance/{wallet.address}")
        return float(data['balance_raw']) / 1_000_000.0, int(data['nonce'])
    except:
        return 0.0, 0

def view_call(contract: str, method: str, params: List[str], caller: str) -> Optional[str]:
    try:
        data = {
            "contract": contract,
            "method": method,
            "params": params,
            "caller": caller
        }
        response = api_call("POST", f"{RPC_ENDPOINT}/contract/call-view", data)
        return response.get('result') if response.get('status') == "success" else None
    except:
        return None

def call_contract(wallet: Wallet, contract: str, method: str, params: List[str]) -> Optional[str]:
    try:
        _, nonce = get_balance(wallet)
        timestamp = time.time()
        
        tx_data = {
            "from": wallet.address,
            "to_": contract,
            "amount": "0",
            "nonce": nonce + 1,
            "ou": "1",
            "timestamp": timestamp
        }
        
        signature = sign_tx(wallet.signing_key, tx_data)
        public_key = base64.b64encode(wallet.signing_key.get_verifying_key().to_bytes()).decode()
        
        call_data = {
            "contract": contract,
            "method": method,
            "params": params,
            "caller": wallet.address,
            "nonce": nonce + 1,
            "timestamp": timestamp,
            "signature": signature,
            "public_key": public_key
        }
        
        response = api_call("POST", f"{RPC_ENDPOINT}/call-contract", call_data)
        return response.get('tx_hash')
    except Exception as e:
        print(f"Error calling contract: {e}")
        return None

def wait_tx(tx_hash: str) -> bool:
    start_time = time.time()
    
    while time.time() - start_time < TIMEOUT:
        try:
            response = api_call("GET", f"{RPC_ENDPOINT}/tx/{tx_hash}")
            if response.get('status') == "confirmed":
                return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(5)
    
    return False

def get_user_input(prompt: str) -> str:
    return input(prompt).strip()

def parse_params(params: List[Dict]) -> List[str]:
    result = []
    for param in params:
        prompt = param['name']
        if 'example' in param:
            prompt += f" (e.g. {param['example']})"
        if 'max' in param:
            prompt += f" (max: {param['max']})"
        prompt += ": "
        result.append(get_user_input(prompt))
    return result

def execute_on_all_wallets(wallets: List[Wallet], contract: ContractInterface, method_idx: int):
    method = contract.methods[method_idx]
    print(f"\nExecuting: {method.label} ({method.name})")
    
    params = parse_params(method.params) if method.params else []
    
    for i, wallet in enumerate(wallets):
        print(f"\nProcessing wallet {i+1}/{len(wallets)}: {wallet.address[:8]}...{wallet.address[-6:]}")
        
        if method.type == "view":
            result = view_call(contract.contract, method.name, params, wallet.address)
            print(f"Result: {result}")
        elif method.type == "call":
            tx_hash = call_contract(wallet, contract.contract, method.name, params)
            if tx_hash:
                print(f"Transaction Hash: {tx_hash}")
                if get_user_input("Wait for confirmation? (y/n): ").lower() == "y":
                    print("Waiting", end="", flush=True)
                    if wait_tx(tx_hash):
                        print("\nTransaction confirmed!")
                    else:
                        print("\nTimeout waiting for confirmation")
        else:
            print(f"Unknown method type: {method.type}")

def main():
    try:
        wallets = load_wallets()
        contract = load_contract_interface()
        
        print(f"\nLoaded {len(wallets)} wallets")
        print(f"Contract: {contract.contract}")
        
        while True:
            print("\n--- OctaSpace Multi-Wallet Client ---")
            for i, method in enumerate(contract.methods):
                print(f"{i+1}. {method.label}")
            print("0. Exit")
            
            choice = get_user_input("\nSelect method: ")
            if choice == "0":
                break
            
            try:
                method_idx = int(choice) - 1
                if 0 <= method_idx < len(contract.methods):
                    execute_on_all_wallets(wallets, contract, method_idx)
                else:
                    print("Invalid method selection")
            except ValueError:
                print("Please enter a valid number")
            
            get_user_input("\nPress Enter to continue...")
    
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\nExiting...")

if __name__ == "__main__":
    main()
