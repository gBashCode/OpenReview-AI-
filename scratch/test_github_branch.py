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
print('Got installation token')

h2 = {'Authorization': f'Bearer {inst_token}', 'Accept': 'application/vnd.github+json'}

# Check default branch SHA of gBashCode/OpenReview-AI-
r_main = requests.get('https://api.github.com/repos/gBashCode/OpenReview-AI-/git/ref/heads/main', headers=h2)
print('Main branch status:', r_main.status_code, r_main.json().get('object', {}).get('sha'))

main_sha = r_main.json().get('object', {}).get('sha')
if main_sha:
    # Try creating branch autofix/test-branch
    branch_payload = {'ref': 'refs/heads/autofix/test-branch', 'sha': main_sha}
    r_branch = requests.post('https://api.github.com/repos/gBashCode/OpenReview-AI-/git/refs', headers=h2, json=branch_payload)
    print('Create branch status:', r_branch.status_code, r_branch.text)
