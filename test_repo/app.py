from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.route('/user')
def get_user():
    user_id = request.args.get('id')
    conn = sqlite3.connect('users.db')
    query = "SELECT * FROM users WHERE id=" + user_id
    result = conn.execute(query)
    return str(result.fetchall())

if __name__ == '__main__':
    app.run(debug=True)