import jwt, time, requests
from pathlib import Path

pem = Path('certs/github-app.private-key.pem').read_text()
app_id = 5833689
now = int(time.time())
payload = {'iat': now - 60, 'exp': now + (10 * 60), 'iss': str(app_id)}
token = jwt.encode(payload, pem, algorithm='RS256')

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
inst_id = 183719282
r = requests.post(f'https://api.github.com/app/installations/{inst_id}/access_tokens', headers=headers)
inst_token = r.json().get('token')

h2 = {'Authorization': f'Bearer {inst_token}', 'Accept': 'application/vnd.github+json'}

# Create PR
pr_payload = {
    'title': 'autofix: Unhandled Empty List or NoneType causes ZeroDivisionError',
    'head': 'autofix/patch-559ad12b',
    'base': 'main',
    'body': 'Automated remediation patch synthesized by Quality Arbiter and verified in Sandbox.\n\nFixes ZeroDivisionError in `backend/app/demo_sample.py`.'
}
r_pr = requests.post('https://api.github.com/repos/gBashCode/OpenReview-AI-/pulls', headers=h2, json=pr_payload)
print('Create PR status:', r_pr.status_code)
print(r_pr.json())
