# acl.py
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# --------------------------------------------------------------------
# Load environment variables
# --------------------------------------------------------------------
load_dotenv()

DB_PATH = 'acl.db'
DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY")

if not DB_ENCRYPTION_KEY:
    raise ValueError("DB_ENCRYPTION_KEY not set in environment (.env file)")

# Fernet requires a 32-byte base64 key.
# If user gives plain text, we derive one automatically.
def _prepare_key(key_str: str) -> bytes:
    try:
        # If already base64 urlsafe encoded (like Fernet.generate_key()), just use it
        return key_str.encode()
    except Exception:
        raise ValueError("Invalid DB_ENCRYPTION_KEY format. Use Fernet.generate_key().")

fernet = Fernet(_prepare_key(DB_ENCRYPTION_KEY))


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def _ensure_db_dir() -> None:
    """Create parent directory for DB if DB_PATH includes a directory."""
    dirpath = os.path.dirname(DB_PATH)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)


def encrypt_payload(payload: str) -> str:
    """Encrypt a string payload before writing to DB."""
    return fernet.encrypt(payload.encode()).decode()


def decrypt_payload(encrypted: str) -> str:
    """Decrypt a string payload after reading from DB."""
    return fernet.decrypt(encrypted.encode()).decode()


# --------------------------------------------------------------------
# Database Functions
# --------------------------------------------------------------------
def init_db() -> None:
    """Create the audit table if it doesn't exist."""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def log_event(event_type: str, payload: Dict[str, Any]) -> int:
    """
    Insert an event into the audit ledger (payload is encrypted).
    Returns the inserted row ID.
    """
    _ensure_db_dir()
    try:
        payload_json = json.dumps(payload, default=str, ensure_ascii=False)
    except Exception:
        payload_json = json.dumps({"__repr__": repr(payload)})

    encrypted_payload = encrypt_payload(payload_json)

    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO audit (timestamp, event_type, payload) VALUES (?, ?, ?)",
            (datetime.utcnow().isoformat() + "Z", event_type, encrypted_payload),
        )
        conn.commit()
        return c.lastrowid
    finally:
        conn.close()


def get_event(event_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single event by ID. Decrypts payload.
    Returns None if not found.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT id, timestamp, event_type, payload FROM audit WHERE id = ?", (event_id,))
        row = c.fetchone()
        if not row:
            return None

        decrypted = None
        if row[3]:
            try:
                decrypted = decrypt_payload(row[3])
                payload = json.loads(decrypted)
            except Exception:
                payload = {"raw": row[3]}
        else:
            payload = None

        return {"id": row[0], "timestamp": row[1], "event_type": row[2], "payload": payload}
    finally:
        conn.close()


def get_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Return the most recent `limit` events (ordered by id desc).
    Decrypts payloads.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT id, timestamp, event_type, payload FROM audit ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        out = []
        for r in rows:
            try:
                decrypted = decrypt_payload(r[3]) if r[3] else None
                payload = json.loads(decrypted) if decrypted else None
            except Exception:
                payload = {"raw": r[3]}
            out.append({"id": r[0], "timestamp": r[1], "event_type": r[2], "payload": payload})
        return out
    finally:
        conn.close()


# --------------------------------------------------------------------
# CLI Debug Mode
# --------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("Initialized ACL DB at", DB_PATH)
    print("Recent 10 events:")
    for ev in get_recent_events(10):
        print(ev)
