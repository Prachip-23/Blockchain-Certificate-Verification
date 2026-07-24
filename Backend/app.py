from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, session, redirect
from flask_cors import CORS
from utils import (
    init_db, save_certificate_data, get_certificate_by_hash, 
    get_certificates_by_owner, store_nonce, get_nonce, 
    create_session, get_session, delete_old_nonces
)
from auth import verify_signature
from contract_manager import ContractManager
from datetime import datetime, timedelta, timezone
import secrets
import os
import qrcode
import uuid
from pathlib import Path
import json
from io import BytesIO
import traceback


# Configuration
BASE = Path(__file__).resolve().parent
STATIC = BASE / 'static'
UPLOAD_DIR = STATIC / 'uploads'
QR_DIR = STATIC / 'qrcodes'
CONTRACT_FILE = BASE / 'contract_address.txt'
CONTRACT_ABI_FILE = BASE / 'contract_abi.json'


# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

app.secret_key = 'f3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9'

app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_NAME'] = 'certauth_session'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = BASE / '.flask_session'
app.config['SESSION_FILE_DIR'].mkdir(exist_ok=True)


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
QR_DIR.mkdir(parents=True, exist_ok=True)

init_db()

contract_manager = None
blockchain_available = False
try:
    contract_manager = ContractManager(
        rpc_url="http://127.0.0.1:8545",
        contract_address_file=str(CONTRACT_FILE),
        contract_abi_file=str(CONTRACT_ABI_FILE)
    )
    blockchain_available = True
    print("✅ Contract manager initialized successfully")
except Exception as e:
    print(f"⚠️  Warning: Blockchain not available: {e}")
    blockchain_available = False


# ==================== UTILITIES ====================

def load_contract_address():
    if CONTRACT_FILE.exists():
        return CONTRACT_FILE.read_text().strip()
    return ''


def get_utc_now():
    return datetime.now(timezone.utc).isoformat()


# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    return redirect('/landing')


@app.route('/landing')
def landing():
    return render_template('landing_page.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'wallet_address' not in session:
        return redirect('/login')
    
    contract_addr = load_contract_address()
    return render_template('dashboard.html', 
                         contract_address=contract_addr,
                         wallet_address=session.get('wallet_address'))


@app.route('/issue')
def issue_certificate():
    if 'wallet_address' not in session:
        return redirect('/login')
    
    contract_addr = load_contract_address()
    return render_template('issue-cert.html', 
                         contract_address=contract_addr,
                         wallet_address=session.get('wallet_address'))


@app.route('/verify')
def verify_certificate():
    contract_addr = load_contract_address()
    return render_template('verify-cert.html', 
                         contract_address=contract_addr,
                         wallet_address=session.get('wallet_address'))


@app.route('/admin')
def admin_panel():
    if 'wallet_address' not in session:
        return redirect('/login')
    
    contract_addr = load_contract_address()
    return render_template('admin-panel.html', 
                         contract_address=contract_addr,
                         wallet_address=session.get('wallet_address'))


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/auth/nonce/<address>', methods=['GET'])
def get_nonce_route(address):
    delete_old_nonces()
    nonce = f"Sign this message to login: {secrets.token_hex(16)}"
    store_nonce(address.lower(), nonce)
    return jsonify({'nonce': nonce, 'timestamp': get_utc_now()})


@app.route('/api/auth/verify', methods=['POST'])
def verify_signature_route():
    data = request.get_json() or {}
    address = data.get('address', '').lower()
    signature = data.get('signature', '')
    
    if not address or not signature:
        return jsonify({'error': 'address and signature required'}), 400
    
    nonce = get_nonce(address)
    if not nonce:
        return jsonify({'error': 'nonce not found or expired'}), 400
    
    if not verify_signature(address, signature, nonce):
        return jsonify({'error': 'invalid signature'}), 401
    
    session['wallet_address'] = address
    session['login_time'] = datetime.now().isoformat()
    session.permanent = True
    
    return jsonify({
        'authenticated': True,
        'address': address
    })


@app.route('/api/auth/connect', methods=['POST'])
def simple_connect():
    try:
        data = request.get_json() or {}
        address = (data.get('address') or '').strip()
        if not address:
            return jsonify({'error': 'address required'}), 400
        
        session['wallet_address'] = address
        session['login_time'] = datetime.now().isoformat()
        session.permanent = True
        
        return jsonify({'success': True, 'address': address}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/status')
def auth_status():
    return jsonify({
        'authenticated': 'wallet_address' in session,
        'address': session.get('wallet_address', None)
    })


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect('/landing')


# ==================== CERTIFICATE ROUTES ====================

@app.route('/api/cert/issue', methods=['POST'])
def issue_certificate_to_blockchain():
    """Issue certificate - Works with or without blockchain"""
    try:
        if 'wallet_address' not in session:
            return jsonify({'error': 'not authenticated'}), 401
        
        issuer_address = session.get('wallet_address')
        data = request.get_json() or {}
        
        # Get and validate data
        cert_hash = data.get('hash', '').strip()
        student_name = data.get('studentName', '').strip()
        student_roll = data.get('studentRoll', '').strip()
        course = data.get('course', '').strip()
        issue_date = data.get('issueDate', '').strip()
        recipient_address = (data.get('recipientAddress', '') or '').strip().lower()
        
        if not all([cert_hash, student_name, course, recipient_address]):
            return jsonify({'error': 'missing required fields'}), 400
        
        if not recipient_address.startswith('0x') or len(recipient_address) != 42:
            return jsonify({'error': 'invalid recipient address format'}), 400
        
        if len(cert_hash) != 64:
            return jsonify({'error': 'invalid hash format'}), 400
        
        # Prepare metadata
        metadata = {
            'studentName': student_name,
            'studentRoll': student_roll,
            'course': course,
            'issueDate': issue_date,
            'issuedAt': get_utc_now(),
            'issuer': issuer_address,
            'nonce': secrets.token_hex(8)
        }
        metadata_str = json.dumps(metadata)
        
        print(f"\n🚀 ISSUING CERTIFICATE")
        print(f"   Hash: {cert_hash[:20]}...")
        print(f"   Recipient: {recipient_address}")
        print(f"   Issuer: {issuer_address}")
        
        # Try blockchain first
        tx_hash = None
        blockchain_status = "Not Available"
        
        if blockchain_available and contract_manager:
            try:
                print(f"   📡 Attempting blockchain integration...")
                tx_hash = contract_manager.issue_certificate(
                    cert_hash=cert_hash,
                    recipient_address=recipient_address,
                    metadata=metadata_str
                )
                
                if tx_hash:
                    print(f"   ✅ Blockchain: SUCCESS - TX: {tx_hash[:20]}...")
                    blockchain_status = "Stored on Blockchain"
                else:
                    raise Exception("Transaction hash is None")
                    
            except Exception as e:
                print(f"   ⚠️  Blockchain failed: {type(e).__name__}")
                print(f"      {str(e)[:100]}")
                tx_hash = None
                blockchain_status = "Failed"
        else:
            blockchain_status = "Unavailable"
            print(f"   ℹ️  Blockchain: Not available")
        
        # Use mock if blockchain failed
        if not tx_hash:
            tx_hash = f"0x{uuid.uuid4().hex[:64]}"
            print(f"   💾 Using Mock TX: {tx_hash[:20]}...")
            blockchain_status = "Database Only"
        
        # Save to database - FIXED PARAMETERS
        try:
            cert_id = save_certificate_data(
                filename=None,  # No file upload
                cert_hash=cert_hash,
                owner_address=recipient_address,
                issuer_address=issuer_address,
                metadata=metadata_str
            )
            print(f"   ✅ Database: SAVED (ID: {cert_id})")
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            traceback.print_exc()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        
        print(f"   ✅ CERTIFICATE ISSUED\n")
        
        return jsonify({
            'success': True,
            'message': 'Certificate issued successfully',
            'tx_hash': tx_hash,
            'cert_hash': cert_hash,
            'metadata': metadata,
            'issuer': issuer_address,
            'recipient': recipient_address,
            'blockchain_status': blockchain_status,
            'db_id': cert_id
        }), 200
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': f"Error: {str(e)}"}), 500


@app.route('/api/cert/verify', methods=['POST'])
def verify_certificate_on_blockchain():
    try:
        data = request.get_json() or {}
        cert_hash = data.get('hash', '').strip()
        
        if not cert_hash:
            return jsonify({'error': 'hash required'}), 400
        
        if len(cert_hash) != 64:
            return jsonify({'error': 'invalid hash format (must be 64 chars)'}), 400
        
        # Try database first
        cert_data = get_certificate_by_hash(cert_hash)
        if cert_data:
            return jsonify({
                'verified': True,
                'certificate': cert_data,
                'message': 'Certificate found in database',
                'source': 'database'
            }), 200
        
        # Try blockchain
        if blockchain_available and contract_manager:
            try:
                cert_data = contract_manager.get_certificate(cert_hash)
                if cert_data and cert_data.get('issuer') != '0x0000000000000000000000000000000000000000':
                    return jsonify({
                        'verified': True,
                        'certificate': cert_data,
                        'message': 'Certificate verified on blockchain',
                        'source': 'blockchain'
                    }), 200
            except Exception as e:
                print(f"Blockchain verification error: {e}")
        
        return jsonify({
            'verified': False,
            'message': 'Certificate not found'
        }), 200
        
    except Exception as e:
        print(f"Verification error: {e}")
        return jsonify({'verified': False, 'error': str(e)}), 500


@app.route('/api/cert/list', methods=['GET'])
def list_user_certificates():
    if 'wallet_address' not in session:
        return jsonify({'error': 'not authenticated'}), 401
    
    address = session.get('wallet_address')
    certificates = get_certificates_by_owner(address)
    return jsonify({'certificates': certificates})


@app.route('/api/cert/<int:cert_id>/download', methods=['GET'])
def download_certificate(cert_id):
    for file in UPLOAD_DIR.iterdir():
        if file.name.startswith(f'cert_{cert_id}.'):
            return send_from_directory(str(UPLOAD_DIR), file.name, as_attachment=True)
    return jsonify({'error': 'certificate not found'}), 404


# ==================== QR CODE ROUTES ====================

@app.route('/api/qr/<cert_hash>', methods=['GET'])
def generate_qr_code(cert_hash):
    try:
        QR_DIR.mkdir(parents=True, exist_ok=True)
        verify_url = f"{request.host_url}verify?hash={cert_hash}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_path = QR_DIR / f"{cert_hash}.png"
        img.save(str(img_path))
        
        return send_file(str(img_path), mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== STATUS ROUTES ====================

@app.route('/api/status', methods=['GET'])
def system_status():
    contract_addr = load_contract_address()
    return jsonify({
        'status': 'running',
        'contract_connected': blockchain_available and contract_addr != '',
        'contract_address': contract_addr,
        'blockchain_available': blockchain_available,
        'network': 'Ganache (localhost:8545)' if blockchain_available else 'Database Only'
    })


@app.route('/api/contract-address', methods=['GET'])
def get_contract_address():
    return jsonify({'contract_address': load_contract_address()})


# ==================== STATIC FILES ====================

@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(STATIC / 'js', filename)

@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(STATIC / 'css', filename)

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(STATIC / 'images', filename)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'internal server error'}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 CERTIFICATE VERIFICATION SYSTEM")
    print("=" * 70)
    if blockchain_available:
        print("✅ Blockchain: CONNECTED")
    else:
        print("⚠️  Blockchain: NOT AVAILABLE (Using Database Only)")
    print("💾 Database: READY")
    print("🔗 Backend: http://localhost:5000")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=True)
