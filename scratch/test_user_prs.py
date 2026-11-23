import requests

r = requests.post('https://openreview-api.onrender.com/api/v1/auth/login', json={'email': 'architect@openreview.ai', 'password': 'OpenReview2026!'})
token = r.json().get('token', {}).get('access_token')

h = {'Authorization': f'Bearer {token}'}
r_prs = requests.get('https://openreview-api.onrender.com/api/v1/pull-requests', headers=h)
print('PR count:', len(r_prs.json()))
for p in r_prs.json():
    print(f"PR #{p.get('pr_number')}: {p.get('title')}")
