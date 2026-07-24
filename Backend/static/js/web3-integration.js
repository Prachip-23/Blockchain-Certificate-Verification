/**
 * Web3 & MetaMask Integration
 * Handles wallet connection and authentication
 */

// ==================== METAMASK DETECTION ====================

async function isMetaMaskInstalled() {
    return typeof window.ethereum !== 'undefined';
}

async function checkMetaMaskNetwork() {
    try {
        const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        // 0x539 = Ganache default chainId (1337)
        return chainId === '0x539' || chainId === '0x1337';
    } catch (error) {
        console.error('❌ Network check failed:', error);
        return false;
    }
}

// ==================== WALLET CONNECTION ====================

async function connectWallet() {
    if (!window.ethereum) {
        throw new Error('❌ MetaMask not installed. Please install MetaMask extension.');
    }
    
    try {
        const accounts = await window.ethereum.request({
            method: 'eth_requestAccounts'
        });
        
        if (accounts.length === 0) {
            throw new Error('❌ No accounts found in MetaMask');
        }
        
        return accounts[0];
    } catch (error) {
        console.error('❌ Connection failed:', error);
        throw error;
    }
}

async function switchToGanache() {
    try {
        await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: '0x539' }]
        });
    } catch (error) {
        if (error.code === 4902) {
            // Chain not added, try to add it
            try {
                await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [{
                        chainId: '0x539',
                        chainName: 'Ganache',
                        rpcUrls: ['http://127.0.0.1:8545'],
                        nativeCurrency: {
                            name: 'Ether',
                            symbol: 'ETH',
                            decimals: 18
                        }
                    }]
                });
            } catch (addError) {
                console.error('❌ Failed to add Ganache network:', addError);
                throw addError;
            }
        } else {
            throw error;
        }
    }
}

// ==================== AUTHENTICATION ====================

async function requestNonce(address) {
    const response = await fetch(`/api/auth/nonce/${address}`);
    if (!response.ok) throw new Error('Failed to get nonce');
    const data = await response.json();
    return data.nonce;
}

async function signNonce(nonce, address) {
    try {
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [nonce, address]
        });
        return signature;
    } catch (error) {
        console.error('❌ User rejected signature:', error);
        throw error;
    }
}

async function verifySignature(address, signature) {
    const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            address: address,
            signature: signature
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Verification failed');
    }
    
    return response.json();
}

async function loginWithMetaMask() {
    try {
        // Check if MetaMask is installed
        if (!await isMetaMaskInstalled()) {
            throw new Error('MetaMask not installed');
        }
        
        // Switch to Ganache
        await switchToGanache();
        
        // Connect wallet
        const address = await connectWallet();
        console.log('✅ Connected:', address);
        
        // Get nonce
        const nonce = await requestNonce(address);
        console.log('✅ Nonce received');
        
        // Sign nonce
        const signature = await signNonce(nonce, address);
        console.log('✅ Message signed');
        
        // Verify signature
        const result = await verifySignature(address, signature);
        
        if (result.session_token) {
            // Store session
            localStorage.setItem('session_token', result.session_token);
            localStorage.setItem('wallet_address', result.address);
            
            console.log('✅ Logged in:', result.address);
            return result;
        }
        
        throw new Error('Login failed');
    } catch (error) {
        console.error('❌ Login error:', error.message);
        throw error;
    }
}

function logoutUser() {
    localStorage.removeItem('session_token');
    localStorage.removeItem('wallet_address');
    console.log('✅ Logged out');
}

function isAuthenticated() {
    return localStorage.getItem('session_token') !== null;
}

function getSessionToken() {
    return localStorage.getItem('session_token');
}

function getWalletAddress() {
    return localStorage.getItem('wallet_address');
}

// ==================== REQUEST HEADERS ====================

function getAuthHeaders() {
    const token = getSessionToken();
    return token ? {
        'X-Session-Token': token,
        'Content-Type': 'application/json'
    } : {
        'Content-Type': 'application/json'
    };
}

// ==================== ACCOUNT INFO ====================

async function getAccountBalance(address) {
    try {
        const balanceWei = await window.ethereum.request({
            method: 'eth_getBalance',
            params: [address, 'latest']
        });
        
        const balanceEth = parseInt(balanceWei, 16) / 1e18;
        return balanceEth.toFixed(4);
    } catch (error) {
        console.error('❌ Failed to get balance:', error);
        return '0';
    }
}

// ==================== EVENT LISTENERS ====================

window.ethereum?.on('accountsChanged', (accounts) => {
    if (accounts.length === 0) {
        console.log('⚠️  MetaMask disconnected');
        logoutUser();
        window.location.reload();
    } else if (accounts[0] !== getWalletAddress()) {
        console.log('⚠️  Account changed');
        logoutUser();
        window.location.reload();
    }
});

window.ethereum?.on('chainChanged', () => {
    console.log('⚠️  Network changed');
    window.location.reload();
});