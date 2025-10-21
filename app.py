from flask import Flask, request, redirect, render_template, session, url_for
import sqlite3
import re

# Deprecated/old library imported on purpose (not actually used)
# This is to create a detectable entry in requirements.txt for SCA tools.
import requests  # intentionally old version will be listed in requirements

app = Flask(__name__)
app.secret_key = 'dev-secret-key'

# Fake but realistic-looking API key for secrets scanning tests
API_KEY = 'AKIAIOSFODNN7EXAMPLE-1234567890abcdef'

# Hardcoded default password (intentionally insecure)
DEFAULT_USER = 'admin'
DEFAULT_PASS = 'P@ssw0rd123'  # <-- hardcoded password, intentional

DB = 'test.db'
def checkwhy1():
    pass
def checkwhy2():
    pass
def checkwhy3():
    print(f'something here also {111}')

# Initialize a tiny SQLite DB with a users table
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    # Insert a test user (insecure: plain text password)
    cur.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'testuser', 'testpass')")
    conn.commit()
    conn.close()

# Ensure DB exists on startup
init_db()

@app.route('/')
def index():
    if session.get('user'):
        return f"Hello, {session['user']}! <a href=\"/ssti?name={session['user']}\">SSTI test</a> | <a href=\"/logout\">Logout</a>"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # INTENTIONALLY VULNERABLE SQL (string interpolation) — for testing SQLi detection
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        query = f"SELECT id FROM users WHERE username = '{username}' AND password = '{password}'"

        # For demonstration, allow a default hardcoded credential to pass
        if username == DEFAULT_USER and password == DEFAULT_PASS:
            session['user'] = DEFAULT_USER
            conn.close()
            return redirect(url_for('index'))

        try:
            cur.execute(query)
            row = cur.fetchone()
            conn.close()
            if row:
                session['user'] = username
                return redirect(url_for('index'))
            else:
                msg = 'Invalid credentials'
        except Exception as e:
            # Expose error message in response to exercise DAST scanners
            msg = f'Error: {e}'

    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/ssti')
def ssti():
    # Server-side template injection: render user input directly
    name = request.args.get('name', 'guest')

    # If `name` looks like an API key, mark it in response (this helps secret detectors)
    if re.match(r'AKIA[0-9A-Z]{16}[-_0-9a-zA-Z]+', name):
        note = 'Looks like an API key in the input.'
    else:
        note = ''

    # Render unsafely into Jinja2 template (intentional SSTI vulnerability)
    return render_template('ssti.html', name=name, note=note)

# Additional endpoint to show the fake API key (so scanners see it in code path/response)
@app.route('/show_api')
def show_api():
    return f"API_KEY={API_KEY}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
