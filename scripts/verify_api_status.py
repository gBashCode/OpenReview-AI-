import httpx

client = httpx.Client()
r = client.post('http://127.0.0.1:8000/api/v1/auth/login', json={'email': 'architect@openreview.ai', 'password': 'OpenReview2026!'})
print('Login status:', r.status_code)
token = r.json()['token']['access_token']
headers = {'Authorization': f'Bearer {token}'}

review_id = '49ae3e84-a938-47f8-95ad-77ae602074b0'
rev = client.get(f'http://127.0.0.1:8000/api/v1/reviews/{review_id}', headers=headers)
print('Review status:', rev.status_code)
if rev.status_code == 200:
    data = rev.json()
    print('Review Quality Score:', data.get('quality_score'))
    print('Review Status:', data.get('status'))
    findings = data.get('findings', [])
    print(f'Findings count: {len(findings)}')

conf = client.get(f'http://127.0.0.1:8000/api/v1/reviews/{review_id}/conference', headers=headers)
print('Conference status:', conf.status_code)
if conf.status_code == 200:
    conf_data = conf.json()
    print('Conference keys:', list(conf_data.keys()))
    print('discussion_threads in conf_data:', len(conf_data.get('discussion_threads', [])))
    print('general_discussions in conf_data:', len(conf_data.get('general_discussions', [])))
    print('summary_metrics:', conf_data.get('summary_metrics'))

prs = client.get('http://127.0.0.1:8000/api/v1/pull-requests', headers=headers)
print('PRs count:', len(prs.json()) if prs.status_code == 200 else prs.status_code)

patches = client.get('http://127.0.0.1:8000/api/v1/autofix', headers=headers)
print('Patches status:', patches.status_code)
if patches.status_code == 200:
    patch_list = patches.json()
    print('Patches count:', len(patch_list))
    if patch_list:
        print('Sample patch status:', patch_list[0].get('status'), 'sandbox_status:', patch_list[0].get('sandbox_status'))
        print('Patch diff:', patch_list[0].get('diff_content')[:120])
