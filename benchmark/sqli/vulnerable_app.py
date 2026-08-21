"""
Intentionally vulnerable Flask app for testing.
DO NOT use in production.
"""
from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.route('/user')
def get_user():
    # VULNERABLE: SQL Injection
    user_id = request.args.get('id')
    conn = sqlite3.connect('users.db')
    query = "SELECT * FROM users WHERE id=" + user_id
    result = conn.execute(query)
    return str(result.fetchall())

@app.route('/login', methods=['POST'])
def login():
    # VULNERABLE: SQL Injection with format string
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect('users.db')
    query = "SELECT * FROM users WHERE username='%s' AND password='%s'" % (username, password)
    result = conn.execute(query)
    return str(result.fetchone())