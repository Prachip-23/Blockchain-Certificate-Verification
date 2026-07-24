# 🔐 Blockchain-Based Certificate Verification System

A secure and decentralized certificate verification system built using **Blockchain Technology**, **Solidity**, **Web3.py**, and **Flask**. The system allows educational institutions to issue tamper-proof digital certificates that can be verified instantly without relying on a centralized authority.

---

## 📌 Features

- 🎓 Issue blockchain-based certificates
- ✅ Verify certificate authenticity
- 🔒 Prevent certificate forgery and duplication
- 📄 Store certificate metadata securely
- 📱 Generate QR code for certificate verification
- 🌐 Web-based interface using Flask
- ⛓️ Smart contract deployed on Ethereum (Ganache Local Blockchain)

---

## 🛠️ Tech Stack

### Frontend
- HTML
- CSS
- JavaScript
- Bootstrap

### Backend
- Python
- Flask
- Flask-CORS
- Flask-Session

### Blockchain
- Solidity
- Web3.py
- Ganache
- MetaMask

### Database
- Blockchain Storage (Smart Contract)

### Other Libraries
- py-solc-x
- qrcode
- Pillow
- python-dotenv
- eth-account

---

# 📂 Project Structure

```
Blockchain-Technology-main
│
├── Backend
│   ├── app.py
│   ├── requirements.txt
│   ├── templates
│   ├── static
│   └── utils.py
│
├── smartcontracts
│   ├── contracts
│   │   └── CertificateRegistry.sol
│   └── scripts
│       └── deploy.py
│
├── venv
└── README.md
```

---

# ⚙️ Prerequisites

Install the following software before running the project:

- Python 3.11
- Node.js
- Ganache
- MetaMask
- Visual Studio Code

---

# 🚀 Installation

## Clone Repository

```bash
git clone <repository-url>
cd Blockchain-Technology-main
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Activate Environment

Windows

```bash
.\venv\Scripts\activate
```

---

## Install Python Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

If any package is missing:

```bash
pip install Flask
pip install Flask-Cors
pip install Flask-Session
pip install web3
pip install qrcode
pip install pillow
pip install py-solc-x
```

---

# ▶️ Running the Project

## Terminal 1 – Start Ganache

```bash
cd Blockchain-Technology-main
ganache --port 8545
```

Keep this terminal running.

---

## Terminal 2 – Deploy Smart Contract

```bash
cd Blockchain-Technology-main

.\venv\Scripts\activate

cd smartcontracts
cd scripts

python deploy.py
```

---

## Terminal 3 – Start Backend

```bash
cd Blockchain-Technology-main

.\venv\Scripts\activate

cd Backend

python app.py
```

---

## Open Browser

```
http://127.0.0.1:5000
```

---

# 📝 Workflow

1. Institution uploads certificate.
2. Certificate details are converted into metadata.
3. SHA-256 hash is generated.
4. Smart contract stores the certificate hash on blockchain.
5. QR Code is generated.
6. Anyone can verify the certificate using the certificate hash.
7. Blockchain confirms whether the certificate is genuine.

---

# 🔐 Smart Contract

The smart contract provides:

- Issue Certificate
- Verify Certificate
- Get Certificate Details
- Get Total Certificates
- Verify Recipient
- Revoke Certificate
- Check Revoked Status

---

## 📸 Application Screenshots

<p align="center">
  <img src="screenshoots/LoginPage.jpg" alt="Login Page" width="800"/>
</p>

<p align="center">
  <b>Login Page</b><br>
  Secure entry point for administrators to access the certificate management system.
</p>

---

### 🏠 Dashboard

<p align="center">
  <img src="screenshoots/DashboardPage.jpg" alt="Dashboard" width="800"/>
</p>

<p align="center">
  Central dashboard providing quick access to certificate issuance and verification.
</p>

---

### 📜 Issue Certificate

<p align="center">
  <img src="screenshoots/IssueCertiPage.jpg" alt="Issue Certificate" width="800"/>
</p>

<p align="center">
  Fill in student and certificate details to issue a new blockchain-backed certificate.
</p>

---

### ✅ Certificate Issued Successfully

<p align="center">
  <img src="screenshoots/CertiIssued.jpg" alt="Certificate Issued" width="800"/>
</p>

<p align="center">
  Displays the generated certificate hash and confirms successful blockchain registration.
</p>

---

### 🔍 Verify Certificate

<p align="center">
  <img src="screenshoots/VerifyCertiPage.jpg" alt="Verify Certificate" width="800"/>
</p>

<p align="center">
  Verify certificate authenticity using the certificate hash stored on the blockchain.
</p>

---

### 🎓 Certificate Details

<p align="center">
  <img src="screenshoots/CertiVerified.jpg" alt="Certificate Verified" width="800"/>
</p>

<p align="center">
  Shows complete certificate information retrieved securely from the blockchain.
</p>

---

### 👨‍💼 Admin Panel

<p align="center">
  <img src="screenshots/AdminPage.jpg" alt="Admin Panel" width="800"/>
</p>

<p align="center">
  Administrative interface for managing certificates, viewing reports, and monitoring system statistics.
</p>
---

# Future Enhancements

- IPFS Integration
- QR Code Scanner
- Multi-Institution Support
- Admin Dashboard
- Email Notification
- Cloud Deployment
- Ethereum Testnet Deployment

---

# Advantages

- Tamper Proof Certificates
- Instant Verification
- Decentralized Architecture
- Secure Record Management
- Reduced Fraud
- Transparent Verification

---

# Limitations

- Uses Local Blockchain (Ganache)
- Requires MetaMask
- No IPFS Storage
- Suitable for Educational Demonstration

---

# Authors

Patel Prachi Rakeshkumar

Aditi Parmar 

Institute of Advanced Research (IAR)

B.Tech Computer Engineering (Artificial Intelligence)

---

# License

This project is developed for educational purposes.
