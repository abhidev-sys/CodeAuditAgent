"""Intentionally vulnerable database module for testing."""
import sqlite3
import pickle
import requests
from flask import request


def get_user_by_id(user_id):
    """VULNERABLE: SQL Injection"""
    conn = sqlite3.connect('users.db')
    # CWE-89: Direct string concatenation
    query = "SELECT * FROM users WHERE id=" + str(user_id)
    return conn.execute(query).fetchall()


def get_user_by_name(username):
    """VULNERABLE: SQL Injection via format string"""
    conn = sqlite3.connect('users.db')
    query = "SELECT * FROM users WHERE username='%s'" % username
    return conn.execute(query).fetchall()


def load_user_data(raw_bytes):
    """VULNERABLE: Insecure Deserialization"""
    # CWE-502: pickle.loads with untrusted data
    return pickle.loads(raw_bytes)


def fetch_external_resource(url_param):
    """VULNERABLE: SSRF"""
    # CWE-918: User controlled URL
    user_url = request.args.get('url')
    response = requests.get(user_url)
    return response.text


# VULNERABLE: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
SECRET_API_KEY = "sk-abcdef123456789secret"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"