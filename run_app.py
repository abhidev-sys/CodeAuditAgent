from flask import Flask, send_file
import subprocess, threading

app = Flask(__name__)

@app.route('/')
def login():
    return send_file('dashboard/login.html')

def start_streamlit():
    subprocess.run(['streamlit', 'run', 'dashboard/app.py', '--server.port=8501'])

if __name__ == '__main__':
    t = threading.Thread(target=start_streamlit, daemon=True)
    t.start()
    app.run(port=5000)