import jwt, time, requests
from pathlib import Path

pem = Path('certs/github-app.private-key.pem').read_text()
app_id = '5833689'
now = int(time.time())
payload = {'iat': now - 60, 'exp': now + (10 * 60), 'iss': app_id}
token = jwt.encode(payload, pem, algorithm='RS256')

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
r = requests.get('https://api.github.com/app', headers=headers)
print('App permissions:', r.json().get('permissions'))
