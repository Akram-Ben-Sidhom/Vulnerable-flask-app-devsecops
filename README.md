# Vulnerable Flask App (for DevSecOps testing)

This small Flask app includes multiple intentional vulnerabilities to validate your DevSecOps pipeline:
- SQL injection in /login
- Hardcoded default password
- SSTI via /ssti?name=<payload>
- Fake API_KEY variable present in code
- Deprecated/old packages in requirements.txt


Run locally (in an isolated environment):


1. python3 -m venv venv
2. source venv/bin/activate
3. pip install -r requirements.txt
4. python app.py
5. Open http://localhost:5000/login

Or Using docker:
1. docker build -t vuln-flask-app:latest .
2. docker run --rm -p 5000:5000 --name vuln-flask-app vuln-flask-app:latest





Test hints:
- SQLi: try `username: ' OR '1'='1` and any password
- SSTI: pass payloads in `?name={{7*7}}` or other Jinja expressions (only for testing)
- Check `/show_api` to see the fake API_KEY in responses


**Do not expose this app to the public internet.**
