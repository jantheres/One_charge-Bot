
import mysql.connector
import json
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_customer_profile(customer_id: str):
    """
    Optional integration with the host app database.
    If a `customers` table exists, fetch name/phone/vehicle_model for context.
    Returns None if not available.
    """
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, phone, vehicle_model FROM customers WHERE id = %s LIMIT 1",
            (customer_id,),
        )
        row = cursor.fetchone()
        return row
    except Exception:
        # Table may not exist in some environments; treat as optional.
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=settings.DB_PORT
        )
    except mysql.connector.Error as err:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        print("\n" + "="*80)
        print("🚨 DATABASE ERROR: Cannot connect to MySQL.")
        print("Please ensure your local MySQL/XAMPP server is running on port 3306.")
        print(f"Details: {err}")
        print("-" * 80)
        print(f"Environment Check (Loaded from .env):")
        print(f" - DB_HOST: {settings.DB_HOST}")
        print(f" - DB_USER: {settings.DB_USER}")
        print(f" - DB_NAME: {settings.DB_NAME}")
        print(f" - DB_PORT: {settings.DB_PORT}")
        print("="*80 + "\n")
        
        logger.error(f"Database connection error: {err}")
        return None

def _parse_json_column(data):
    if isinstance(data, (bytes, bytearray)):
        data = data.decode('utf-8')
    if isinstance(data, str):
        try:
            return json.loads(data)
        except:
            return {}
    return data if isinstance(data, dict) else {}

def setup_db():
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    
    # Create chat_sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        session_id VARCHAR(255) PRIMARY KEY,
        customer_id VARCHAR(255),
        status ENUM('ACTIVE', 'ESCALATED', 'RESOLVED') DEFAULT 'ACTIVE',
        current_flow_step VARCHAR(255),
        extracted_data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_customer (customer_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # Create messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        message_id INT AUTO_INCREMENT PRIMARY KEY,
        session_id VARCHAR(255),
        role ENUM('user', 'assistant', 'system'),
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # Create tickets table (agent handoff + lifecycle)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id VARCHAR(255) NOT NULL,
        user_id VARCHAR(255) NOT NULL,
        source ENUM('ESCALATION', 'SERVICE') DEFAULT 'ESCALATION',
        reason VARCHAR(100) NOT NULL,
        priority ENUM('normal', 'high', 'emergency') DEFAULT 'normal',
        status ENUM('OPEN', 'IN_PROGRESS', 'DISPATCHED', 'ON_SITE', 'RESOLVED', 'CLOSED') DEFAULT 'OPEN',
        customer_name VARCHAR(255) NULL,
        phone VARCHAR(50) NULL,
        vehicle_model VARCHAR(255) NULL,
        collected_data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_ticket_session (session_id),
        INDEX idx_ticket_status (status),
        INDEX idx_ticket_user (user_id),
        FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Database setup complete.")

def get_active_session(customer_id: str):
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM chat_sessions WHERE customer_id = %s AND status IN ('ACTIVE','ESCALATED') ORDER BY updated_at DESC LIMIT 1",
        (customer_id,)
    )
    session = cursor.fetchone()
    if session:
        session['extracted_data'] = _parse_json_column(session.get('extracted_data'))
    cursor.close()
    conn.close()
    return session


def get_session_by_id(session_id: str):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chat_sessions WHERE session_id = %s LIMIT 1", (session_id,))
    session = cursor.fetchone()
    if session:
        session["extracted_data"] = _parse_json_column(session.get("extracted_data"))
    cursor.close()
    conn.close()
    return session

def create_session(
    session_id: str,
    customer_id: str,
    system_prompt: str,
    initial_data: dict = None,
    initial_flow_step: str = "SAFETY",
):
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_sessions (session_id, customer_id, extracted_data, current_flow_step) VALUES (%s, %s, %s, %s)",
        (session_id, customer_id, json.dumps(initial_data or {}), initial_flow_step)
    )
    cursor.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
        (session_id, 'system', system_prompt)
    )
    conn.commit()
    cursor.close()
    conn.close()

def save_message(session_id: str, role: str, content: str):
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
        (session_id, role, content)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_chat_history(session_id: str, limit: int = 10):
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT role, content FROM (SELECT * FROM messages WHERE session_id = %s ORDER BY created_at DESC LIMIT %s) sub ORDER BY created_at ASC",
        (session_id, limit)
    )
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    return history

def update_session(session_id: str, flow_step: str, extracted_data: dict, status: str = 'ACTIVE'):
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE chat_sessions SET current_flow_step = %s, extracted_data = %s, status = %s WHERE session_id = %s",
        (flow_step, json.dumps(extracted_data), status, session_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

# --- Agent Dashboard Functions ---

def get_escalated_sessions():
    """Fetch all rows from chat_sessions where status = 'ESCALATED'."""
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT session_id, customer_id, current_flow_step, extracted_data, updated_at FROM chat_sessions WHERE status = 'ESCALATED' ORDER BY updated_at DESC"
        )
        sessions_data = cursor.fetchall()
        for s in sessions_data:
            s['extracted_data'] = _parse_json_column(s.get('extracted_data'))
        return sessions_data
    finally:
        if conn: conn.close()


# --- Ticketing (Production Agent Handoff) ---

def get_open_ticket_for_session(session_id: str):
    """Return the most recent non-closed ticket for a session, if any."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM tickets
            WHERE session_id = %s AND status NOT IN ('RESOLVED','CLOSED')
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        if row:
            row["collected_data"] = _parse_json_column(row.get("collected_data"))
        return row
    finally:
        if conn:
            conn.close()


def create_ticket(
    session_id: str,
    user_id: str,
    reason: str,
    priority: str = "normal",
    source: str = "ESCALATION",
    collected_data: dict | None = None,
    customer_name: str | None = None,
    phone: str | None = None,
    vehicle_model: str | None = None,
):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tickets
                (session_id, user_id, source, reason, priority, status, customer_name, phone, vehicle_model, collected_data)
            VALUES
                (%s, %s, %s, %s, %s, 'OPEN', %s, %s, %s, %s)
            """,
            (
                session_id,
                str(user_id),
                source,
                reason,
                priority,
                customer_name,
                phone,
                vehicle_model,
                json.dumps(collected_data or {}),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        if conn:
            conn.close()


def list_open_tickets():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM tickets
            WHERE status IN ('OPEN','IN_PROGRESS','DISPATCHED','ON_SITE')
            ORDER BY updated_at DESC
            """
        )
        rows = cursor.fetchall()
        for r in rows:
            r["collected_data"] = _parse_json_column(r.get("collected_data"))
        return rows
    finally:
        if conn:
            conn.close()


def update_ticket_status(ticket_id: int, status: str):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, session_id FROM tickets WHERE id = %s LIMIT 1", (ticket_id,))
        row = cursor.fetchone()
        if not row:
            return False

        cursor.execute("UPDATE tickets SET status = %s WHERE id = %s", (status, ticket_id))

        # When ticket is resolved/closed, also close the associated chat session so
        # a new conversation can start cleanly without exposing session_id to clients.
        if status in ("RESOLVED", "CLOSED"):
            cursor.execute(
                "UPDATE chat_sessions SET status = 'RESOLVED' WHERE session_id = %s",
                (row["session_id"],),
            )
        conn.commit()
        return True
    finally:
        if conn:
            conn.close()

def get_session_transcript(session_id: str):
    """Fetches extracted_data and chronological chat history for a session."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        # 1. Fetch extracted data and flow metadata
        cursor.execute(
            "SELECT session_id, customer_id, current_flow_step, extracted_data FROM chat_sessions WHERE session_id = %s",
            (session_id,)
        )
        metadata = cursor.fetchone()
        if not metadata:
            return None
        
        metadata['extracted_data'] = _parse_json_column(metadata.get('extracted_data'))
            
        # 2. Fetch full chronological message history
        cursor.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,)
        )
        metadata['messages'] = cursor.fetchall()
        return metadata
    finally:
        if conn: conn.close()

def mark_session_resolved(session_id: str):
    """Update status to 'RESOLVED' for the given session ID."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chat_sessions SET status = 'RESOLVED' WHERE session_id = %s",
            (session_id,)
        )
        conn.commit()
        success = cursor.rowcount > 0
        return success
    finally:
        if conn: conn.close()
