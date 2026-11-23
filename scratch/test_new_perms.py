import jwt, time, requests
from pathlib import Path

pem = Path('certs/github-app.private-key.pem').read_text()
app_id = '5833689'
now = int(time.time())
payload = {'iat': now - 60, 'exp': now + (10 * 60), 'iss': app_id}
token = jwt.encode(payload, pem, algorithm='RS256')

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
inst_id = 183719282
r = requests.get(f'https://api.github.com/app/installations/{inst_id}', headers=headers)
print('Installation status:', r.status_code)
print('Permissions:', r.json().get('permissions'))

# Get installation access token
r_tok = requests.post(f'https://api.github.com/app/installations/{inst_id}/access_tokens', headers=headers)
inst_token = r_tok.json().get('token')
print('Token permissions:', r_tok.json().get('permissions'))

h2 = {'Authorization': f'Bearer {inst_token}', 'Accept': 'application/vnd.github+json'}

# Test creating a branch ref
r_main = requests.get('https://api.github.com/repos/gBashCode/OpenReview-AI-/git/ref/heads/main', headers=h2)
main_sha = r_main.json().get('object', {}).get('sha')
print('Main SHA:', main_sha)

test_branch = f'autofix/test-perm-{int(time.time())}'
r_ref = requests.post('https://api.github.com/repos/gBashCode/OpenReview-AI-/git/refs', headers=h2, json={
    'ref': f'refs/heads/{test_branch}',
    'sha': main_sha
})
print('Create ref status:', r_ref.status_code, r_ref.json().get('ref') or r_ref.text)
