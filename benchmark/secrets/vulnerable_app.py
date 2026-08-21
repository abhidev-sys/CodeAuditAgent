"""Hardcoded secrets — for testing only."""

# VULNERABLE: Hardcoded credentials
DATABASE_PASSWORD = "super_secret_password_123"
API_KEY = "sk-abcdef123456789"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def connect_db():
    password = "admin123"  # VULNERABLE
    return f"postgresql://admin:{password}@localhost/db"