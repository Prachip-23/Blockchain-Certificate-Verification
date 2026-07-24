/**
 * Certificate Service - Certificate Operations
 * Handles certificate issuance, verification, and management
 */

// ==================== CERTIFICATE HASHING & UPLOAD ====================

async function uploadCertificate(file) {
    if (!isAuthenticated()) {
        throw new Error('❌ Not authenticated');
    }
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/cert/compute-hash', {
            method: 'POST',
            headers: {
                'X-Session-Token': getSessionToken()
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }
        
        const data = await response.json();
        console.log('✅ Certificate uploaded:', data.hash);
        return data;
    } catch (error) {
        console.error('❌ Upload failed:', error);
        throw error;
    }
}

// ==================== CERTIFICATE ISSUANCE ====================

async function issueCertificate(certData) {
    if (!isAuthenticated()) {
        throw new Error('❌ Not authenticated');
    }
    
    try {
        const response = await fetch('/api/cert/issue', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(certData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Issuance failed');
        }
        
        const result = await response.json();
        console.log('✅ Certificate issued:', result.tx_hash);
        return result;
    } catch (error) {
        console.error('❌ Issuance failed:', error);
        throw error;
    }
}

// ==================== CERTIFICATE VERIFICATION ====================

async function verifyCertificate(certHash) {
    try {
        const response = await fetch('/api/cert/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hash: certHash
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Verification failed');
        }
        
        const result = await response.json();
        console.log('✅ Verification complete:', result.verified);
        return result;
    } catch (error) {
        console.error('❌ Verification failed:', error);
        throw error;
    }
}

// ==================== CERTIFICATE LISTING ====================

async function listUserCertificates() {
    if (!isAuthenticated()) {
        throw new Error('❌ Not authenticated');
    }
    
    try {
        const response = await fetch('/api/cert/list', {
            method: 'GET',
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Listing failed');
        }
        
        const data = await response.json();
        return data.certificates;
    } catch (error) {
        console.error('❌ Listing failed:', error);
        throw error;
    }
}

// ==================== QR CODE GENERATION ====================

function generateQRCodeURL(certHash) {
    return `/api/qr/${certHash}`;
}

async function downloadCertificate(certId) {
    try {
        window.location.href = `/api/cert/${certId}/download`;
    } catch (error) {
        console.error('❌ Download failed:', error);
        throw error;
    }
}

// ==================== UTILITY FUNCTIONS ====================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        console.log('✅ Copied to clipboard');
    }).catch(err => {
        console.error('❌ Copy failed:', err);
    });
}

function formatHash(hash) {
    return hash ? hash.substring(0, 10) + '...' + hash.substring(hash.length - 10) : '';
}

function formatAddress(address) {
    return address ? address.substring(0, 6) + '...' + address.substring(address.length - 4) : '';
}

function formatDate(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString();
}

// ==================== FILE HANDLING ====================

function getFileHash(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            // For demo, we'll hash on backend
            // In production, you might compute SHA256 client-side
            resolve(null);
        };
        reader.onerror = reject;
        reader.readAsArrayBuffer(file);
    });
}

// ==================== VALIDATION ====================

function validateCertificateData(data) {
    const required = ['hash', 'studentName', 'course', 'recipientAddress'];
    for (const field of required) {
        if (!data[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }
    
    if (!data.recipientAddress.startsWith('0x') || data.recipientAddress.length !== 42) {
        throw new Error('Invalid recipient address');
    }
    
    return true;
}