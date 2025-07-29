# Octra-2.0
---
## Octra 1.0 link - https://github.com/deepakdhaka-1/Octra-BOT
---
![Python](https://img.shields.io/badge/Built%20With-Python-3670A0?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

This Python tool allows you to **interact with Octra smart contracts**, claim tokens, and run methods on **multiple wallets** using private keys and addresses. It is based on the original Rust client but fully converted to Python with multi-wallet support.

---

## 📌 Features
- 🔁 Rust-compatible Ed25519 signing  
- ✅ Call any method from `exec_interface.json`  
- 💸 Multi-wallet batch execution (reads keys from files)  
- 📊 Automatic retry if transaction fails  
- 🕵️‍♂️ Supports both `view` and `call` contract methods  
- 🔐 Real-time transaction confirmation check  
- ⏱ Works with Octra public RPC or custom endpoints  

---

## 📂 Project Structure
```bash
.
├── README.md
├── main.py               # Support All mathematical and smart contact functions test
├── claim.py              # For execution of task claim token through contract
├── exec_interface.json   # Contract interface file
├── pvt.txt               # List of base64-encoded private keys
├── address.txt           # Corresponding wallet addresses
```

---

## 🔧 Installation
```
git clone https://github.com/deepakdhaka-1/Octra-2.0/
cd Octra-2.0
```

### 1️⃣ Install Python dependencies
```bash
pip install requests ed25519
```

#### `pvt.txt`
```bash
nano pvt.txt
```

#### `address.txt`
```bash
nano address.txt
```

---

## 🚀 Usage

### 🔹 All mathematical and smart contact functions test
```bash
python3 main.py
```
---

### 🔹 Contract Claim Mode
```bash
python3 claim.py
```
---

## 🔁 Automatic Retry
- If a transaction fails or returns `403 Forbidden`, the script will **retry until success**.
- You can adjust `TIMEOUT` or add `RETRY_DELAY` inside the script if needed.

---

## ⚠️ Notes
- Private keys must be **base64-encoded** Ed25519 keys (same format as Rust client).  
- The order of `pvt.txt` and `address.txt` must match line-by-line.  
- Ensure `exec_interface.json` matches the contract you are calling.  

---

## 📜 License
```bash
MIT – Use at your own risk.
```
