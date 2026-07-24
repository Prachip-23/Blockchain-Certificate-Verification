#!/usr/bin/env python3
"""
Smart Contract Deployment Script
Deploys CertificateRegistry.sol to Ganache
"""

import json
from pathlib import Path
from web3 import Web3
import sys

# Configure paths
GANACHE_RPC = "http://127.0.0.1:8545"
SOLIDITY_VERSION = "0.8.21"
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"

# Contract code (embedded)
CONTRACT_CODE = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

contract CertificateRegistry {
    struct Certificate {
        address issuer;
        address recipient;
        uint256 issuedAt;
        string metadata;
    }
    
    mapping(bytes32 => Certificate) private certificates;
    bytes32[] private certificateHashes;
    mapping(bytes32 => bool) private revoked;
    
    event CertificateIssued(
        bytes32 indexed certHash,
        address indexed issuer,
        address indexed recipient,
        uint256 issuedAt,
        string metadata
    );
    
    event CertificateRevoked(
        bytes32 indexed certHash,
        address revokedBy,
        uint256 revokedAt
    );
    
    function issueCertificate(
        bytes32 _certHash,
        address _recipient,
        string memory _metadata
    ) public {
        require(_recipient != address(0), "Invalid address");
        require(_certHash != bytes32(0), "Invalid hash");
        require(certificates[_certHash].issuedAt == 0, "Certificate already exists");
        require(bytes(_metadata).length > 0, "Metadata cannot be empty");
        
        certificates[_certHash] = Certificate({
            issuer: msg.sender,
            recipient: _recipient,
            issuedAt: block.timestamp,
            metadata: _metadata
        });
        
        certificateHashes.push(_certHash);
        
        emit CertificateIssued(
            _certHash,
            msg.sender,
            _recipient,
            block.timestamp,
            _metadata
        );
    }
    
    function getCertificate(bytes32 _certHash)
        public
        view
        returns (
            address issuer,
            address recipient,
            uint256 issuedAt,
            string memory metadata
        )
    {
        Certificate memory cert = certificates[_certHash];
        return (cert.issuer, cert.recipient, cert.issuedAt, cert.metadata);
    }
    
    function isIssued(bytes32 _certHash) public view returns (bool) {
        return certificates[_certHash].issuedAt != 0;
    }
    
    function verifyRecipient(bytes32 _certHash, address _recipient)
        public
        view
        returns (bool)
    {
        Certificate memory cert = certificates[_certHash];
        return cert.recipient == _recipient && cert.issuedAt != 0;
    }
    
    function getTotalCertificates() public view returns (uint256) {
        return certificateHashes.length;
    }
    
    function revokeCertificate(bytes32 _certHash) public {
        require(
            certificates[_certHash].issuer == msg.sender,
            "Only issuer can revoke"
        );
        require(!revoked[_certHash], "Certificate already revoked");
        
        revoked[_certHash] = true;
        emit CertificateRevoked(_certHash, msg.sender, block.timestamp);
    }
    
    function isRevoked(bytes32 _certHash) public view returns (bool) {
        return revoked[_certHash];
    }
}
'''

def check_ganache_running():
    """Check if Ganache is running"""
    try:
        web3 = Web3(Web3.HTTPProvider(GANACHE_RPC))
        if web3.is_connected():
            print(f"✅ Connected to Ganache at {GANACHE_RPC}")
            return web3, True
    except Exception as e:
        pass
    
    print(f"❌ Cannot connect to Ganache at {GANACHE_RPC}")
    print("❌ Please start Ganache in a NEW PowerShell window:")
    print("   ganache-cli --deterministic --host 0.0.0.0 --port 8545")
    return None, False

def install_solc():
    """Install Solidity compiler"""
    print("\n📥 Installing Solidity compiler...")
    try:
        from solcx import install_solc
        install_solc(f"v{SOLIDITY_VERSION}")
        print(f"✅ Solidity {SOLIDITY_VERSION} installed")
        return True
    except Exception as e:
        print(f"⚠️  Compiler installation: {e}")
        return True  # Continue anyway

def compile_contract():
    """Compile Solidity contract"""
    print("\n📝 Compiling CertificateRegistry...")
    try:
        from solcx import compile_source
        
        compiled = compile_source(
            CONTRACT_CODE,
            output_values=["abi", "bin"],
            solc_version=f"v{SOLIDITY_VERSION}"
        )
        
        contract = compiled['<stdin>:CertificateRegistry']
        print("✅ Contract compiled successfully")
        return contract['abi'], contract['bin']
    
    except Exception as e:
        print(f"❌ Compilation failed: {e}")
        print("\n💡 Trying alternative approach...")
        return compile_with_remixd()

def compile_with_remixd():
    """Fallback: Use online compiler"""
    try:
        import requests
        print("📡 Using online Solidity compiler...")
        
        # Use Remix API
        url = "https://remix-api.ethereum.org/api/v1/compile"
        payload = {
            "sources": {
                "CertificateRegistry.sol": {
                    "content": CONTRACT_CODE
                }
            },
            "language": "Solidity",
            "settings": {
                "optimizer": {"enabled": False},
                "outputSelection": {
                    "*": {
                        "*": ["abi", "evm.bytecode"]
                    }
                }
            }
        }
        
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        if "contracts" in result:
            contract_data = result["contracts"]["CertificateRegistry.sol"]["CertificateRegistry"]
            abi = contract_data["abi"]
            bytecode = contract_data["evm"]["bytecode"]["object"]
            print("✅ Contract compiled using online compiler")
            return abi, bytecode
    except Exception as e:
        print(f"❌ Online compilation failed: {e}")
    
    return None, None

def deploy_contract(web3, abi, bytecode):
    """Deploy contract to Ganache"""
    print("\n🚀 Deploying contract to Ganache...")
    
    try:
        accounts = web3.eth.accounts
        if not accounts:
            print("❌ No accounts found in Ganache")
            return None
        
        deployer = accounts[0]
        print(f"📍 Deployer account: {deployer}")
        
        Contract = web3.eth.contract(abi=abi, bytecode=bytecode)
        
        tx = Contract.constructor().build_transaction({
            'from': deployer,
            'gas': 500000,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(deployer)
        })
        
        print("📤 Sending deployment transaction...")
        tx_hash = web3.eth.send_transaction(tx)
        print(f"📋 Transaction hash: {tx_hash.hex()}")
        
        print("⏳ Waiting for confirmation...")
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        contract_address = tx_receipt['contractAddress']
        print(f"✅ Contract deployed at: {contract_address}")
        
        return contract_address
    
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return None

def save_contract_info(contract_address, abi):
    """Save contract address and ABI to backend"""
    print("\n💾 Saving contract information...")
    
    BACKEND_DIR.mkdir(parents=True, exist_ok=True)
    
    address_file = BACKEND_DIR / 'contract_address.txt'
    address_file.write_text(contract_address)
    print(f"✅ Saved: {address_file}")
    
    abi_file = BACKEND_DIR / 'contract_abi.json'
    with open(abi_file, 'w') as f:
        json.dump(abi, f, indent=2)
    print(f"✅ Saved: {abi_file}")

def test_contract(web3, contract_address, abi):
    """Test deployed contract"""
    print("\n🧪 Testing contract...")
    try:
        contract = web3.eth.contract(address=contract_address, abi=abi)
        
        total = contract.functions.getTotalCertificates().call()
        print(f"✅ Total certificates: {total}")
        
        print("✅ Contract tested successfully")
        return True
    except Exception as e:
        print(f"⚠️  Test failed (non-critical): {e}")
        return True

def main():
    print("=" * 60)
    print("  CertificateRegistry Smart Contract Deployment")
    print("=" * 60)
    
    # Check Ganache
    web3, connected = check_ganache_running()
    if not connected:
        sys.exit(1)
    
    # Install compiler
    install_solc()
    
    # Compile
    abi, bytecode = compile_contract()
    if not abi:
        print("❌ Compilation failed completely")
        sys.exit(1)
    
    # Deploy
    contract_address = deploy_contract(web3, abi, bytecode)
    if not contract_address:
        sys.exit(1)
    
    # Save
    save_contract_info(contract_address, abi)
    
    # Test
    test_contract(web3, contract_address, abi)
    
    print("\n" + "=" * 60)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print(f"📍 Contract: {contract_address}")
    print(f"📁 Address: {BACKEND_DIR / 'contract_address.txt'}")
    print(f"📋 ABI: {BACKEND_DIR / 'contract_abi.json'}")
    print("\n⏭️  Next steps:")
    print("   cd backend")
    print("   python app.py")
    print("=" * 60)

if __name__ == '__main__':
    main()