import os
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
UPLOAD_DIR = BASE / 'static' / 'uploads'
DB_PATH = BASE / 'db.sqlite3'

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Certificates table - Updated schema
    c.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_hash TEXT UNIQUE NOT NULL,
            filename TEXT,
            stored_path TEXT,
            owner_address TEXT NOT NULL,
            issuer_address TEXT NOT NULL,
            metadata TEXT,
            issued_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Nonces table
    c.execute('''
        CREATE TABLE IF NOT EXISTS nonces (
            address TEXT PRIMARY KEY,
            nonce TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sessions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            address TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")


def save_certificate_data(filename, cert_hash, owner_address, issuer_address, metadata):
    """
    Save certificate data to database
    
    Parameters:
    - filename: Certificate file name (optional, can be None)
    - cert_hash: SHA-256 hash of certificate (REQUIRED)
    - owner_address: Wallet address of certificate owner (REQUIRED)
    - issuer_address: Wallet address of certificate issuer (REQUIRED)
    - metadata: JSON metadata string (REQUIRED)
    
    Returns:
    - cert_id: Database ID of saved certificate
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Store file if provided
        stored_path = None
        if filename:
            stored_path = str(UPLOAD_DIR / filename)
        
        issued_at = datetime.utcnow().isoformat()
        
        # Insert certificate
        c.execute('''
            INSERT INTO certificates 
            (cert_hash, filename, stored_path, owner_address, issuer_address, metadata, issued_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            cert_hash,
            filename,
            stored_path,
            owner_address.lower(),
            issuer_address.lower(),
            metadata,
            issued_at
        ))
        
        cert_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Certificate saved to DB with ID: {cert_id}")
        return cert_id
        
    except Exception as e:
        print(f"❌ Database save error: {e}")
        raise


def get_certificate_by_hash(cert_hash):
    """Get certificate from database by hash"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, cert_hash, owner_address, issuer_address, metadata, issued_at
            FROM certificates
            WHERE cert_hash = ?
        ''', (cert_hash,))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'hash': row[1],
                'owner': row[2],
                'issuer': row[3],
                'metadata': row[4],
                'issued_at': row[5]
            }
        return None
        
    except Exception as e:
        print(f"❌ Database query error: {e}")
        return None


def get_certificates_by_owner(owner_address):
    """Get all certificates owned by an address"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, cert_hash, owner_address, issuer_address, metadata, issued_at
            FROM certificates
            WHERE owner_address = ?
            ORDER BY id DESC
        ''', (owner_address.lower(),))
        
        rows = c.fetchall()
        conn.close()
        
        certificates = []
        for row in rows:
            certificates.append({
                'id': row[0],
                'hash': row[1],
                'owner': row[2],
                'issuer': row[3],
                'metadata': row[4],
                'issued_at': row[5]
            })
        
        return certificates
        
    except Exception as e:
        print(f"❌ Database query error: {e}")
        return []


def store_nonce(address, nonce):
    """Store nonce for authentication"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        created_at = datetime.utcnow().isoformat()
        
        c.execute('''
            REPLACE INTO nonces (address, nonce, created_at)
            VALUES (?, ?, ?)
        ''', (address.lower(), nonce, created_at))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Nonce store error: {e}")


def get_nonce(address):
    """Get and validate nonce"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT nonce FROM nonces WHERE address = ?
        ''', (address.lower(),))
        
        row = c.fetchone()
        conn.close()
        
        return row[0] if row else None
        
    except Exception as e:
        print(f"❌ Nonce get error: {e}")
        return None


def delete_old_nonces(hours=1):
    """Delete nonces older than specified hours"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Calculate cutoff time
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        c.execute('''
            DELETE FROM nonces WHERE created_at < ?
        ''', (cutoff_str,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Nonce cleanup error: {e}")


def create_session(token, address):
    """Create a new session"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        created_at = datetime.utcnow().isoformat()
        
        c.execute('''
            INSERT OR REPLACE INTO sessions (token, address, created_at)
            VALUES (?, ?, ?)
        ''', (token, address.lower(), created_at))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Session create error: {e}")


def get_session(token):
    """Get session address by token"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT address FROM sessions WHERE token = ?
        ''', (token,))
        
        row = c.fetchone()
        conn.close()
        
        return row[0] if row else None
        
    except Exception as e:
        print(f"❌ Session get error: {e}")
        return None


print("✅ Utils module loaded")