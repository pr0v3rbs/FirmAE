import sqlite3
import time

DB_PATH = "firmae.db"

# =========================
# DB CONNECTION
# =========================

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Requests table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        request_id TEXT PRIMARY KEY,
        firmware TEXT,
        status TEXT,
        created_at REAL,
        updated_at REAL,
        result TEXT,
        error TEXT
    )
    """)

    # Logs table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT,
        timestamp REAL,
        message TEXT,
        FOREIGN KEY(request_id) REFERENCES requests(request_id)
    )
    """)

    conn.commit()
    conn.close()

# =========================
# REQUEST OPERATIONS
# =========================

def insert_request(request_id, firmware_path):
    conn = get_conn()
    cur = conn.cursor()
    now = time.time()

    cur.execute("""
        INSERT INTO requests
        (request_id, firmware, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (request_id, firmware_path, "queued", now, now))

    conn.commit()
    conn.close()


def update_request(request_id, status=None, result=None, error=None):
    conn = get_conn()
    cur = conn.cursor()

    fields = []
    values = []

    if status is not None:
        fields.append("status = ?")
        values.append(status)

    if result is not None:
        fields.append("result = ?")
        values.append(result)

    if error is not None:
        fields.append("error = ?")
        values.append(error)

    fields.append("updated_at = ?")
    values.append(time.time())

    values.append(request_id)

    cur.execute(
        f"UPDATE requests SET {', '.join(fields)} WHERE request_id = ?",
        values
    )

    conn.commit()
    conn.close()


def fetch_request(request_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT request_id, status, created_at, updated_at, result, error, firmware
        FROM requests
        WHERE request_id = ?
    """, (request_id,))

    row = cur.fetchone()
    conn.close()
    return row


def fetch_all_requests():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT request_id, status, created_at, updated_at
        FROM requests
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_firmware_path(request_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT firmware
        FROM requests
        WHERE request_id = ?
    """, (request_id,))

    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

# =========================
# LOG OPERATIONS
# =========================

def add_log(request_id, message):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO logs (request_id, timestamp, message)
        VALUES (?, ?, ?)
    """, (request_id, time.time(), message))

    conn.commit()
    conn.close()


def fetch_logs(request_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT timestamp, message
        FROM logs
        WHERE request_id = ?
        ORDER BY timestamp
    """, (request_id,))

    rows = cur.fetchall()
    conn.close()
    return rows
