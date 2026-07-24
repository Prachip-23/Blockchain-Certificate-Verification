"""
Smart Contract Manager - Web3 Integration with Ganache
Handles all blockchain interactions
"""

from web3 import Web3
from pathlib import Path
import json
from datetime import datetime

class ContractManager:
    """Manager for blockchain certificate operations"""
    
    def __init__(self, rpc_url, contract_address_file, contract_abi_file):
        """
        Initialize contract manager
        
        Args:
            rpc_url: Ganache RPC endpoint (http://127.0.0.1:8545)
            contract_address_file: Path to file containing contract address
            contract_abi_file: Path to contract ABI JSON
        """
        self.rpc_url = rpc_url
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address_file = Path(contract_address_file)
        self.contract_abi_file = Path(contract_abi_file)
        
        # Verify connection
        if not self.web3.is_connected():
            raise Exception(f"❌ Cannot connect to {rpc_url}. Is Ganache running?")
        
        print(f"✅ Connected to Ganache at {rpc_url}")
        
        self.contract = self._load_contract()
    
    def _load_contract(self):
        """Load contract ABI and initialize contract instance"""
        # Load ABI
        if not self.contract_abi_file.exists():
            raise Exception(f"❌ Contract ABI file not found: {self.contract_abi_file}")
        
        with open(self.contract_abi_file, 'r') as f:
            contract_abi = json.load(f)
        
        # Load address
        if not self.contract_address_file.exists():
            raise Exception(f"❌ Contract address file not found: {self.contract_address_file}")
        
        contract_address = self.contract_address_file.read_text().strip()
        
        if not Web3.is_address(contract_address):
            raise Exception(f"❌ Invalid contract address: {contract_address}")
        
        contract_address = Web3.to_checksum_address(contract_address)
        print(f"✅ Contract loaded at {contract_address}")
        
        return self.web3.eth.contract(address=contract_address, abi=contract_abi)
    
    def get_accounts(self):
        """Get available Ganache accounts"""
        return self.web3.eth.accounts
    
    def issue_certificate(self, cert_hash, recipient_address, metadata):
        """
        Issue certificate to blockchain
        
        Args:
            cert_hash: SHA256 hash of certificate (64-char hex string)
            recipient_address: Ethereum address of recipient
            metadata: JSON string of certificate metadata
        
        Returns:
            Transaction hash
        """
        try:
            # Validate inputs
            if not Web3.is_address(recipient_address):
                raise ValueError(f"Invalid recipient address: {recipient_address}")
            
            recipient_address = Web3.to_checksum_address(recipient_address)
            
            # Convert hash to bytes32
            if len(cert_hash) != 64:
                raise ValueError(f"Invalid cert hash length: {len(cert_hash)} (expected 64)")
            
            cert_hash_bytes = bytes.fromhex(cert_hash)
            
            # Get sender account
            accounts = self.web3.eth.accounts
            if not accounts:
                raise Exception("❌ No Ganache accounts available")
            
            sender = accounts[0]
            
            # Build transaction
            tx = self.contract.functions.issueCertificate(
                cert_hash_bytes,
                recipient_address,
                metadata
            ).build_transaction({
                'from': sender,
                'gas': 300000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(sender)
            })
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=None)
            # Note: In Ganache, transactions are signed automatically
            
            tx_hash = self.web3.eth.send_transaction(tx)
            
            # Wait for receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            print(f"✅ Certificate issued. TX: {tx_hash.hex()}")
            return tx_hash.hex()
        
        except Exception as e:
            print(f"❌ Error issuing certificate: {e}")
            raise
    
    def get_certificate(self, cert_hash):
        """
        Retrieve certificate from blockchain
        
        Args:
            cert_hash: SHA256 hash of certificate (64-char hex string)
        
        Returns:
            Certificate data dict or None
        """
        try:
            # Convert hash to bytes32
            if len(cert_hash) != 64:
                raise ValueError(f"Invalid cert hash length: {len(cert_hash)}")
            
            cert_hash_bytes = bytes.fromhex(cert_hash)
            
            # Call contract
            cert_data = self.contract.functions.getCertificate(cert_hash_bytes).call()
            
            if cert_data and cert_data[0] != '0x0000000000000000000000000000000000000000':
                return {
                    'issuer': cert_data[0],
                    'recipient': cert_data[1],
                    'issuedAt': cert_data[2],
                    'metadata': cert_data[3],
                    'verified': True
                }
            
            return None
        
        except Exception as e:
            print(f"❌ Error retrieving certificate: {e}")
            return None
    
    def is_certificate_issued(self, cert_hash):
        """Check if certificate exists on blockchain"""
        try:
            cert_hash_bytes = bytes.fromhex(cert_hash)
            return self.contract.functions.isIssued(cert_hash_bytes).call()
        except Exception as e:
            print(f"❌ Error checking certificate: {e}")
            return False
    
    def get_transaction_status(self, tx_hash):
        """Get transaction status"""
        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return {
                    'blockNumber': receipt['blockNumber'],
                    'status': receipt['status'],  # 1 = success, 0 = failed
                    'gasUsed': receipt['gasUsed']
                }
            return None
        except Exception as e:
            print(f"❌ Error getting transaction status: {e}")
            return None

# ==================== CONTRACT DEPLOYMENT ====================

def deploy_contract(web3, contract_abi, contract_bytecode, account):
    """
    Deploy CertificateRegistry contract
    
    Args:
        web3: Web3 instance
        contract_abi: Contract ABI
        contract_bytecode: Contract bytecode
        account: Deployer account address
    
    Returns:
        Contract address
    """
    try:
        Contract = web3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
        
        # Build transaction
        tx = Contract.constructor().build_transaction({
            'from': account,
            'gas': 500000,
            'gasPrice': web3.eth.gas_price,
            'nonce': web3.eth.get_transaction_count(account)
        })
        
        # Send transaction
        tx_hash = web3.eth.send_transaction(tx)
        
        # Wait for receipt
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        contract_address = tx_receipt['contractAddress']
        print(f"✅ Contract deployed at {contract_address}")
        
        return contract_address
    
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        raise