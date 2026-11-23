import jwt, time, requests
from pathlib import Path

pem = Path('certs/github-app.private-key.pem').read_text()
app_id = '5833689'
now = int(time.time())
payload = {'iat': now - 60, 'exp': now + (10 * 60), 'iss': app_id}
token = jwt.encode(payload, pem, algorithm='RS256')

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
inst_id = 183719282
r = requests.post(f'https://api.github.com/app/installations/{inst_id}/access_tokens', headers=headers)
inst_token = r.json().get('token')

h2 = {'Authorization': f'Bearer {inst_token}', 'Accept': 'application/vnd.github+json'}

# Create PR
pr_payload = {
    'title': 'fix(security): sanitize table_name against whitelist to prevent CWE-89 SQL injection',
    'head': 'autofix/remediate-sql-injection',
    'base': 'main',
    'body': '### Automated Security Remediation\n\n- **Defect Identified**: CWE-89 SQL Injection via unvalidated table identifier.\n- **Remediation**: Implemented strict whitelist validation against `ALLOWED_AUDIT_TABLES`.\n- **Verifier**: Ephemeral Container Sandbox unit tests passed.\n\nSynthesized by **Quality Arbiter** via **OpenReview AI**.'
}
r_pr = requests.post('https://api.github.com/repos/gBashCode/OpenReview-AI-/pulls', headers=h2, json=pr_payload)
print('Create PR status:', r_pr.status_code)
pr_res = r_pr.json()
print('PR Number:', pr_res.get('number'))
print('PR HTML URL:', pr_res.get('html_url'))
print('User:', pr_res.get('user', {}).get('login'))
