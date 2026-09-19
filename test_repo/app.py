"""Intentionally vulnerable Flask app for testing."""
from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.route('/user')
def get_user():
    """SQL Injection vulnerability."""
    user_id = request.args.get('id')
    conn = sqlite3.connect('users.db')
    query = "SELECT * FROM users WHERE id=" + user_id
    result = conn.execute(query)
    return str(result.fetchall())

@app.route('/search')
def search():
    """Another SQL Injection."""
    name = request.args.get('name')
    conn = sqlite3.connect('users.db')
    query = "SELECT * FROM users WHERE name='%s'" % name
    result = conn.execute(query)
    return str(result.fetchall())

if __name__ == '__main__':
    app.run(debug=True)