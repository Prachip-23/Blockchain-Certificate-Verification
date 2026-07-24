/**
 * UI Controller - Certificate Management System
 * Handles all UI interactions and displays
 */

class UIController {
    constructor() {
        this.alerts = [];
        this.isLoading = false;
    }

    /**
     * Show alert message
     */
    showAlert(message, type = 'info', duration = 5000) {
        const alertId = Math.random().toString(36).substr(2, 9);
        const alert = {
            id: alertId,
            message,
            type,
            created: new Date()
        };
        
        this.alerts.push(alert);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeAlert(alertId);
            }, duration);
        }
        
        return alertId;
    }

    /**
     * Remove alert
     */
    removeAlert(alertId) {
        this.alerts = this.alerts.filter(a => a.id !== alertId);
    }

    /**
     * Clear all alerts
     */
    clearAlerts() {
        this.alerts = [];
    }

    /**
     * Format Ethereum address
     */
    formatAddress(address) {
        if (!address) return 'Unknown';
        if (address.length < 10) return address;
        return address.substring(0, 6) + '...' + address.substring(address.length - 4);
    }

    /**
     * Format certificate hash
     */
    formatHash(hash) {
        if (!hash) return 'Unknown';
        if (hash.length < 20) return hash;
        return hash.substring(0, 10) + '...' + hash.substring(hash.length - 10);
    }

    /**
     * Format date to readable format
     */
    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        
        try {
            let date;
            
            // If it's a timestamp (number)
            if (typeof dateString === 'number') {
                date = new Date(dateString * 1000);
            } else if (typeof dateString === 'string') {
                // Try to parse ISO string or timestamp
                date = new Date(dateString);
            } else {
                date = new Date(dateString);
            }
            
            if (isNaN(date.getTime())) return 'Invalid Date';
            
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } catch (e) {
            return 'Invalid Date';
        }
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * Disable button
     */
    disableButton(buttonId) {
        const btn = document.getElementById(buttonId);
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.6';
            btn.style.cursor = 'not-allowed';
        }
    }

    /**
     * Enable button
     */
    enableButton(buttonId) {
        const btn = document.getElementById(buttonId);
        if (btn) {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    }

    /**
     * Show loading state
     */
    showLoading(elementId, message = 'Loading...') {
        const el = document.getElementById(elementId);
        if (el) {
            el.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div style="font-size: 32px; margin-bottom: 15px; animation: spin 1s linear infinite;">⏳</div>
                    <div style="font-size: 16px; font-weight: 500;">${message}</div>
                </div>
            `;
        }
        this.isLoading = true;
    }

    /**
     * Hide loading state
     */
    hideLoading(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.innerHTML = '';
        }
        this.isLoading = false;
    }

    /**
     * Show error in UI
     */
    showError(elementId, error) {
        const el = document.getElementById(elementId);
        if (el) {
            el.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #ef4444;">
                    <div style="font-size: 48px; margin-bottom: 15px;">❌</div>
                    <div style="font-weight: 500;">${error}</div>
                </div>
            `;
        }
    }

    /**
     * Show success message
     */
    showSuccess(elementId, message) {
        const el = document.getElementById(elementId);
        if (el) {
            el.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #10b981;">
                    <div style="font-size: 48px; margin-bottom: 15px;">✅</div>
                    <div style="font-weight: 500;">${message}</div>
                </div>
            `;
        }
    }

    /**
     * Display table of certificates
     */
    displayCertificateTable(elementId, certificates) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (!certificates || certificates.length === 0) {
            el.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div style="font-size: 48px; margin-bottom: 10px;">📭</div>
                    <div style="font-size: 16px; color: var(--text-secondary);">No certificates found</div>
                </div>
            `;
            return;
        }

        const table = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Student Name</th>
                        <th>Course</th>
                        <th>Issue Date</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${certificates.map(cert => `
                        <tr>
                            <td><strong>${cert.studentName || 'N/A'}</strong></td>
                            <td>${cert.course || 'N/A'}</td>
                            <td>${this.formatDate(cert.uploadedAt)}</td>
                            <td><span class="badge badge-success">✅ Verified</span></td>
                            <td>
                                <button class="btn btn-sm btn-outline" onclick="verifyCertificate('${cert.hash}')">
                                    Verify
                                </button>
                                <a href="/verify?hash=${cert.hash}" class="btn btn-sm btn-outline" target="_blank">
                                    View
                                </a>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        el.innerHTML = table;
    }

    /**
     * Display verification result
     */
    displayVerificationResult(elementId, result) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (result.verified) {
            try {
                const meta = JSON.parse(result.certificate.metadata);
                
                el.innerHTML = `
                    <div class="alert alert-success">
                        ✅ <strong>Certificate Verified!</strong>
                        <p style="margin-top: 10px; font-size: 14px;">
                            This certificate is authentic and stored on the blockchain
                        </p>
                    </div>

                    <div style="margin-top: 20px; background: var(--secondary-bg); padding: 16px; border-radius: 8px;">
                        <strong>📋 Certificate Details:</strong>
                        <div style="margin-top: 12px; font-size: 14px; line-height: 1.8;">
                            <div><strong>Student:</strong> ${meta.studentName || 'N/A'}</div>
                            <div><strong>Course:</strong> ${meta.course || 'N/A'}</div>
                            <div><strong>Issued:</strong> ${meta.issuedAt || 'N/A'}</div>
                        </div>
                    </div>

                    <div style="margin-top: 16px; background: var(--secondary-bg); padding: 16px; border-radius: 8px;">
                        <strong>⛓️ Blockchain Details:</strong>
                        <div style="margin-top: 12px; font-size: 13px; font-family: monospace; line-height: 1.6; word-break: break-all;">
                            <div><strong>Issuer:</strong><br>${result.certificate.issuer}</div>
                            <div style="margin-top: 8px;"><strong>Recipient:</strong><br>${result.certificate.recipient}</div>
                        </div>
                    </div>
                `;
            } catch (e) {
                el.innerHTML = `
                    <div class="alert alert-success">
                        ✅ <strong>Certificate Verified!</strong>
                        <p style="margin-top: 10px;">Certificate is authentic on blockchain</p>
                    </div>
                `;
            }
        } else {
            el.innerHTML = `
                <div class="alert alert-error">
                    ❌ <strong>Certificate Not Found</strong>
                    <p style="margin-top: 10px;">
                        ${result.message || 'This certificate is not registered on the blockchain'}
                    </p>
                </div>
            `;
        }
    }

    /**
     * Copy to clipboard
     */
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showAlert('✅ Copied to clipboard!', 'success', 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    }

    /**
     * Validate Ethereum address
     */
    isValidAddress(address) {
        return /^0x[a-fA-F0-9]{40}$/.test(address);
    }

    /**
     * Validate certificate hash
     */
    isValidHash(hash) {
        return /^[a-fA-F0-9]{64}$/.test(hash);
    }

    /**
     * Get query parameter from URL
     */
    getQueryParam(param) {
        const params = new URLSearchParams(window.location.search);
        return params.get(param);
    }

    /**
     * Redirect after delay
     */
    redirectAfterDelay(url, delay = 3000) {
        setTimeout(() => {
            window.location.href = url;
        }, delay);
    }
}

// Initialize global UI controller
const ui = new UIController();

// Add animation for loading
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);