import os
import sqlite3
import pymysql
from pymysql.cursors import DictCursor
from config import Config

# Track active database mode
ACTIVE_DB_TYPE = None

def get_connection():
    """
    Attempts to connect to MySQL first.
    If MySQL is unavailable or connection is refused, falls back to SQLite.
    """
    global ACTIVE_DB_TYPE
    
    # Try MySQL first
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            cursorclass=DictCursor,
            autocommit=True,
            connect_timeout=2
        )
        ACTIVE_DB_TYPE = "MySQL"
        return conn, "mysql"
    except Exception as e:
        # Fallback to SQLite
        ACTIVE_DB_TYPE = "SQLite"
        conn = sqlite3.connect(Config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def get_db_type():
    global ACTIVE_DB_TYPE
    if ACTIVE_DB_TYPE is None:
        _, db_type = get_connection()
        return "MySQL" if db_type == "mysql" else "SQLite (Auto-fallback)"
    return "MySQL" if ACTIVE_DB_TYPE == "MySQL" else "SQLite (Auto-fallback)"

def query_db(query, args=(), one=False):
    """Execute a SELECT query and return dict or list of dicts."""
    conn, db_type = get_connection()
    try:
        cursor = conn.cursor()
        # Adapt placeholders if needed (%s for MySQL, ? for SQLite)
        if db_type == "sqlite":
            query = query.replace("%s", "?")
            cursor.execute(query, args)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        else:
            cursor.execute(query, args)
            result = cursor.fetchall()
            
        cursor.close()
        conn.close()
        return (result[0] if result else None) if one else result
    except Exception as err:
        conn.close()
        raise err

def execute_db(query, args=()):
    """Execute an INSERT, UPDATE, or DELETE query and return the last inserted ID."""
    conn, db_type = get_connection()
    try:
        cursor = conn.cursor()
        if db_type == "sqlite":
            query = query.replace("%s", "?")
            cursor.execute(query, args)
            last_id = cursor.lastrowid
            conn.commit()
        else:
            cursor.execute(query, args)
            last_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return last_id
    except Exception as err:
        conn.close()
        raise err

def init_db():
    """Initializes the database schema and default seeds."""
    conn, db_type = get_connection()
    cursor = conn.cursor()

    if db_type == "mysql":
        # Check if incidents table exists
        cursor.execute("SHOW TABLES LIKE 'incidents';")
        if not cursor.fetchone():
            # Run database.sql
            sql_file_path = os.path.join(os.path.dirname(__file__), 'database.sql')
            if os.path.exists(sql_file_path):
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_commands = f.read().split(';')
                    for cmd in sql_commands:
                        cmd = cmd.strip()
                        if cmd and not cmd.lower().startswith('create database') and not cmd.lower().startswith('use '):
                            cursor.execute(cmd)
    else:
        # SQLite schema initialization
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_code TEXT NOT NULL UNIQUE,
            emergency_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            location_address TEXT NOT NULL,
            landmark TEXT DEFAULT '',
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            urgency_level TEXT NOT NULL DEFAULT 'MEDIUM',
            urgency_score INTEGER NOT NULL DEFAULT 50,
            urgency_reasons TEXT,
            people_affected INTEGER DEFAULT 0,
            trapped_count INTEGER DEFAULT 0,
            injured_count INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Reported',
            is_sos INTEGER NOT NULL DEFAULT 0,
            is_duplicate INTEGER NOT NULL DEFAULT 0,
            parent_incident_id INTEGER DEFAULT NULL,
            reporter_name TEXT DEFAULT 'Anonymous Citizen',
            reporter_email TEXT DEFAULT NULL,
            reporter_contact TEXT DEFAULT 'Simulated Contact',
            source TEXT DEFAULT 'Citizen Mobile Form',
            confidence_score REAL DEFAULT 0.90,
            photo_url TEXT DEFAULT NULL,
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            recommendation_text TEXT NOT NULL,
            priority_level TEXT DEFAULT 'Normal',
            suggested_actions TEXT,
            evidence_refs TEXT,
            confidence REAL DEFAULT 0.85,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS simulated_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            agency_type TEXT NOT NULL,
            agency_name TEXT NOT NULL,
            alert_channel TEXT NOT NULL,
            alert_title TEXT NOT NULL,
            alert_message TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING_APPROVAL',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            acknowledged_at TIMESTAMP DEFAULT NULL,
            officer_approved_by TEXT DEFAULT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agency_id TEXT NOT NULL,
            resource_name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            total_capacity INTEGER NOT NULL DEFAULT 1,
            available_capacity INTEGER NOT NULL DEFAULT 1,
            base_location TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT DEFAULT 'Available',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER DEFAULT NULL,
            actor_name TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action_type TEXT NOT NULL,
            details TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            old_status TEXT DEFAULT NULL,
            new_status TEXT DEFAULT NULL,
            status TEXT NOT NULL,
            error_message TEXT DEFAULT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dedup_key TEXT UNIQUE,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS agent_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            response_json TEXT DEFAULT NULL,
            execution_time_ms INTEGER DEFAULT 0,
            error_message TEXT DEFAULT NULL,
            analysis_mode TEXT DEFAULT 'rule_based',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP DEFAULT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS agent_system_state (
            agent_id TEXT PRIMARY KEY,
            agent_name TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'IDLE',
            current_task TEXT DEFAULT 'Initialized and standby',
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tasks_processed INTEGER DEFAULT 0,
            errors_count INTEGER DEFAULT 0,
            health_score REAL DEFAULT 1.0,
            metadata_json TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS agent_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_agent TEXT NOT NULL,
            receiver_agent TEXT NOT NULL,
            message_type TEXT NOT NULL,
            incident_id INTEGER DEFAULT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'DELIVERED',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ai_operator_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            summary TEXT NOT NULL,
            details_json TEXT DEFAULT '{}',
            severity TEXT DEFAULT 'INFO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

        # Seed initial resources if table is empty
        cursor.execute("SELECT COUNT(*) as cnt FROM resources;")
        row = cursor.fetchone()
        count = row['cnt'] if isinstance(row, sqlite3.Row) else row[0]
        if count == 0:
            cursor.executescript("""
            INSERT INTO resources (agency_id, resource_name, resource_type, total_capacity, available_capacity, base_location, latitude, longitude, status) VALUES
            ('police', 'Rapid Response Patrol Unit Alpha', 'Police Vehicle', 4, 3, 'Central Police Station', 15.9054, 80.4682, 'Available'),
            ('police', 'Traffic & Perimeter Control Unit 3', 'Police Squad', 6, 5, 'North Bypass Checkpost', 15.9180, 80.4590, 'Available'),
            ('fire', 'Heavy Water Tender & Foam Truck #1', 'Fire Engine', 2, 2, 'Main Fire Station HQ', 15.9010, 80.4720, 'Available'),
            ('fire', 'Rescue Boat & Hydraulic Cutter Unit #1', 'Flood & Rescue Boat', 3, 2, 'Riverbank Emergency Depot', 15.8920, 80.4850, 'Available'),
            ('fire', 'Hydraulic Aerial Ladder Truck (50m)', 'Fire Equipment', 1, 1, 'Main Fire Station HQ', 15.9010, 80.4720, 'Available'),
            ('medical', 'Advanced Life Support (ALS) Ambulance #1', 'Ambulance', 3, 2, 'General District Hospital', 15.9120, 80.4620, 'Available'),
            ('medical', 'Basic Life Support (BLS) Ambulance #2', 'Ambulance', 2, 1, 'Community Health Center', 15.9220, 80.4480, 'Available'),
            ('medical', 'Emergency Trauma & ICU Ward Beds', 'Hospital ICU Beds', 20, 14, 'General District Hospital', 15.9120, 80.4620, 'Available'),
            ('rescue', 'NDRF Urban Search & Rescue Battalion (USAR-1)', 'Rescue Team', 15, 12, 'State Disaster Response Base', 15.8850, 80.4750, 'Available'),
            ('rescue', 'Inflatable Motorized Rescue Boats Fleet', 'Rescue Craft', 6, 4, 'Coastal Relief Outpost', 15.8790, 80.4910, 'Available');

            INSERT INTO audit_logs (incident_id, actor_name, actor_role, action_type, details) VALUES
            (NULL, 'System Init', 'System Administrator', 'SYSTEM_INITIALIZED', 'DisasterSync AI database initialized with sample agencies and resource stocks.');
            """)
            conn.commit()

    # Auto-migrate photo_url column if not present in existing table
    try:
        cursor.execute("SELECT photo_url FROM incidents LIMIT 1")
    except Exception:
        try:
            cursor.execute("ALTER TABLE incidents ADD COLUMN photo_url TEXT DEFAULT NULL")
            if db_type == "sqlite":
                conn.commit()
        except Exception:
            pass

    # Auto-migrate reporter_email column if not present
    try:
        cursor.execute("SELECT reporter_email FROM incidents LIMIT 1")
    except Exception:
        try:
            cursor.execute("ALTER TABLE incidents ADD COLUMN reporter_email TEXT DEFAULT NULL")
            if db_type == "sqlite":
                conn.commit()
        except Exception:
            pass

    # Auto-migrate email_notifications table if not present
    try:
        cursor.execute("SELECT id FROM email_notifications LIMIT 1")
    except Exception:
        try:
            if db_type == "sqlite":
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id INTEGER NOT NULL,
                    recipient_email TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    old_status TEXT DEFAULT NULL,
                    new_status TEXT DEFAULT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT DEFAULT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    dedup_key TEXT UNIQUE,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
                );
                """)
                conn.commit()
            else:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `email_notifications` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `incident_id` INT NOT NULL,
                    `recipient_email` VARCHAR(255) NOT NULL,
                    `subject` VARCHAR(255) NOT NULL,
                    `notification_type` VARCHAR(50) NOT NULL,
                    `old_status` VARCHAR(50) DEFAULT NULL,
                    `new_status` VARCHAR(50) DEFAULT NULL,
                    `status` VARCHAR(50) NOT NULL,
                    `error_message` TEXT DEFAULT NULL,
                    `sent_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `dedup_key` VARCHAR(255) UNIQUE,
                    FOREIGN KEY (`incident_id`) REFERENCES `incidents`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        except Exception as e:
            print("Email table migration notice:", e)

    # Auto-migrate agent_executions table if not present
    try:
        cursor.execute("SELECT id FROM agent_executions LIMIT 1")
    except Exception:
        try:
            if db_type == "sqlite":
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    response_json TEXT DEFAULT NULL,
                    execution_time_ms INTEGER DEFAULT 0,
                    error_message TEXT DEFAULT NULL,
                    analysis_mode TEXT DEFAULT 'rule_based',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP DEFAULT NULL,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
                );
                """)
                conn.commit()
            else:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `agent_executions` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `incident_id` INT NOT NULL,
                    `agent_id` VARCHAR(50) NOT NULL,
                    `agent_name` VARCHAR(100) NOT NULL,
                    `status` VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                    `response_json` LONGTEXT DEFAULT NULL,
                    `execution_time_ms` INT DEFAULT 0,
                    `error_message` TEXT DEFAULT NULL,
                    `analysis_mode` VARCHAR(50) DEFAULT 'rule_based',
                    `started_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `completed_at` DATETIME DEFAULT NULL,
                    FOREIGN KEY (`incident_id`) REFERENCES `incidents`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        except Exception as e:
            print("Agent executions table migration notice:", e)

    # Auto-migrate agent_system_state table
    try:
        cursor.execute("SELECT agent_id FROM agent_system_state LIMIT 1")
    except Exception:
        try:
            if db_type == "sqlite":
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_system_state (
                    agent_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'IDLE',
                    current_task TEXT DEFAULT 'Initialized and standby',
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tasks_processed INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    health_score REAL DEFAULT 1.0,
                    metadata_json TEXT DEFAULT '{}'
                );
                """)
                conn.commit()
            else:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `agent_system_state` (
                    `agent_id` VARCHAR(50) PRIMARY KEY,
                    `agent_name` VARCHAR(100) NOT NULL,
                    `category` VARCHAR(50) NOT NULL,
                    `status` VARCHAR(50) NOT NULL DEFAULT 'IDLE',
                    `current_task` TEXT DEFAULT NULL,
                    `last_activity` DATETIME DEFAULT CURRENT_TIMESTAMP,
                    `tasks_processed` INT DEFAULT 0,
                    `errors_count` INT DEFAULT 0,
                    `health_score` DOUBLE DEFAULT 1.0,
                    `metadata_json` LONGTEXT DEFAULT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        except Exception as e:
            print("Agent system state migration notice:", e)

    # Auto-migrate agent_messages table
    try:
        cursor.execute("SELECT id FROM agent_messages LIMIT 1")
    except Exception:
        try:
            if db_type == "sqlite":
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_agent TEXT NOT NULL,
                    receiver_agent TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    incident_id INTEGER DEFAULT NULL,
                    content TEXT NOT NULL,
                    status TEXT DEFAULT 'DELIVERED',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                conn.commit()
            else:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `agent_messages` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `sender_agent` VARCHAR(100) NOT NULL,
                    `receiver_agent` VARCHAR(100) NOT NULL,
                    `message_type` VARCHAR(100) NOT NULL,
                    `incident_id` INT DEFAULT NULL,
                    `content` TEXT NOT NULL,
                    `status` VARCHAR(50) DEFAULT 'DELIVERED',
                    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        except Exception as e:
            print("Agent messages migration notice:", e)

    # Auto-migrate ai_operator_logs table
    try:
        cursor.execute("SELECT id FROM ai_operator_logs LIMIT 1")
    except Exception:
        try:
            if db_type == "sqlite":
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_operator_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    details_json TEXT DEFAULT '{}',
                    severity TEXT DEFAULT 'INFO',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                conn.commit()
            else:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS `ai_operator_logs` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `action_type` VARCHAR(100) NOT NULL,
                    `summary` TEXT NOT NULL,
                    `details_json` LONGTEXT DEFAULT NULL,
                    `severity` VARCHAR(20) DEFAULT 'INFO',
                    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        except Exception as e:
            print("AI operator logs migration notice:", e)

    cursor.close()
    conn.close()

