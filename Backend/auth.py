"""
Authentication Module - MetaMask Signature Verification
"""

from eth_account.messages import encode_defunct
from eth_account import Account

def verify_signature(address: str, signature: str, nonce: str) -> bool:
    """
    Verify that the signature was signed by the address with the given nonce
    
    Args:
        address: Ethereum address (0x...)
        signature: Signed message (hex string)
        nonce: Original message that was signed
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Prepare message
        message = encode_defunct(text=nonce)
        
        # Recover address from signature
        recovered_address = Account.recover_message(message, signature=signature)
        
        # Compare with provided address (case-insensitive)
        return recovered_address.lower() == address.lower()
    
    except Exception as e:
        print(f"❌ Signature verification failed: {e}")
        return False

def get_message_to_sign(nonce: str) -> str:
    """Format the message for signing"""
    return f"Sign this message to login: {nonce}"