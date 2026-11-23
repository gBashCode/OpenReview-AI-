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

# Test PUT /repos/{owner}/{repo}/contents/{path}
test_content = "print('test')"
import base64
b64 = base64.b64encode(test_content.encode()).decode()

put_payload = {
    'message': 'test commit',
    'content': b64,
    'branch': 'autofix/test-branch-2'
}
r_put = requests.put('https://api.github.com/repos/gBashCode/OpenReview-AI-/contents/test_file.py', headers=h2, json=put_payload)
print('PUT contents status:', r_put.status_code, r_put.text)
