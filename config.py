import os

# Automatic .env file loader (No external dependencies required)
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_file):
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'disastersync-ai-hackathon-2026-secret-key')
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'disastersync_db')
    
    # Fallback SQLite DB Path if MySQL is not reachable
    SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'disastersync.db')
    
    # Project & Hackathon Metadata
    PROJECT_NAME = "DisasterSync AI"
    PROJECT_TITLE = "AI-Powered Multi-Agent Disaster Response and Emergency Coordination System"
    PROJECT_CODE = "AG-AI-01"
    TEAM_NAME = "DISASTERSYNC AI"
    TEAM_MEMBERS = ["K. Mrudhula Reddy", "G. Kavya", "T. Sneha Latha"]
    COLLEGE = "Bapatla Women's Engineering College"
    MENTOR = "Narayana swamy sir"
    EVENT_DATE = "07/11/2026"
    
    # Emergency Agency Channels
    AGENCIES = [
        {"id": "police", "name": "Police Department", "code": "PD", "color": "#3B82F6", "icon": "fa-shield-halved"},
        {"id": "fire", "name": "Fire & Rescue Department", "code": "FRD", "color": "#EF4444", "icon": "fa-fire-extinguisher"},
        {"id": "medical", "name": "Hospital & Emergency Medical", "code": "EMS", "color": "#10B981", "icon": "fa-truck-medical"},
        {"id": "rescue", "name": "NDRF / Disaster Rescue Teams", "code": "NDRF", "color": "#F59E0B", "icon": "fa-life-ring"}
    ]
    
    # Gmail SMTP Configuration (Req 9, 10, 11: Securely configured via environment variables / .env)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() in ['true', '1', 'yes']
    GMAIL_USER = (os.environ.get('GMAIL_USER') or os.environ.get('SMTP_USER')
                  or os.environ.get('EMAIL_ADDRESS', ''))
    GMAIL_APP_PASSWORD = (os.environ.get('GMAIL_APP_PASSWORD') or os.environ.get('SMTP_PASSWORD')
                          or os.environ.get('EMAIL_PASSWORD', ''))
    SMTP_USER = GMAIL_USER
    SMTP_PASSWORD = GMAIL_APP_PASSWORD  # Never hardcode email passwords or API keys in source code
    OFFICER_EMAILS = os.environ.get('OFFICER_EMAILS', 'officer.emergency@disastersync.ai,command.center@disastersync.ai')
    EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('EMAIL_NOTIFICATIONS_ENABLED', 'true').lower() in ['true', '1', 'yes']
    
    # Gemini LLM API Configuration (Optional: for enhanced AI agent responses)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

    # Public Base URL / HTTPS Deployment Setting (fixes the tracking link issue for public deployment)
    APP_BASE_URL = os.environ.get('APP_BASE_URL') or os.environ.get('BASE_URL', 'http://127.0.0.1:5000').rstrip('/')

