import urllib.request
import json
import sys
import time

BASE_URL = "https://openreview-ai-kappa.vercel.app"

def request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "OpenReview-E2E-Tester/1.0"
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    else:
        body = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            content_type = resp.headers.get("content-type", "")
            raw = resp.read().decode("utf-8", errors="replace")
            if "application/json" in content_type:
                try:
                    payload = json.loads(raw)
                except Exception:
                    payload = raw
            else:
                payload = raw
            return status, payload
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw
        return e.code, payload
    except Exception as e:
        return 0, str(e)


def run_e2e_tests():
    results = []
    def log(step, name, passed, detail=""):
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] Step {step}: {name} - {detail}")
        results.append((step, name, passed, detail))

    step = 1

    # 1. UI Routes
    print("\n--- Phase 1: Frontend SPA Routes ---")
    routes = [
        "/login", "/dashboard", "/repositories", "/pull-requests",
        "/agents", "/security", "/performance", "/autofix",
        "/history", "/team", "/settings", "/models", "/analytics", "/landing"
    ]
    all_routes_ok = True
    for r in routes:
        code, body = request(r)
        if code != 200 or "<!doctype html>" not in body.lower():
            all_routes_ok = False
            log(step, f"UI Route {r}", False, f"HTTP {code}")
            break
    if all_routes_ok:
        log(step, "All 14 Frontend SPA Routes", True, "200 OK via SPA fallback")
    step += 1

    # 2. System Health
    print("\n--- Phase 2: Production Health Check ---")
    code, body = request("/api/v1/health")
    db_ok = isinstance(body, dict) and body.get("components", {}).get("database", {}).get("status") == "healthy"
    redis_ok = isinstance(body, dict) and body.get("components", {}).get("redis", {}).get("status") == "healthy"
    log(step, "Health Check (Neon PostgreSQL & Upstash Redis)", code == 200 and db_ok and redis_ok, 
        f"DB: {body.get('components', {}).get('database', {}).get('latency_ms')}ms, Redis: {body.get('components', {}).get('redis', {}).get('latency_ms')}ms")
    step += 1

    # 3. Authentication
    print("\n--- Phase 3: Authentication & Session Initialization ---")
    code, body = request("/api/v1/auth/demo", method="POST")
    token = None
    user_id = None
    if code == 200 and isinstance(body, dict) and "token" in body:
        token = body["token"].get("access_token")
        user_id = body["user"].get("id")
        log(step, "Demo Authentication (JWT Generation)", True, f"User: {body['user']['email']}, ID: {user_id}")
    else:
        log(step, "Demo Authentication (JWT Generation)", False, f"Code: {code}, Body: {body}")
        print("Cannot proceed with authenticated tests without token.")
        return results
    step += 1

    # 4. Authenticated Profile
    print("\n--- Phase 4: User Profile Verification ---")
    code, body = request("/api/v1/auth/me", token=token)
    log(step, "User Profile /auth/me", code == 200 and body.get("id") == user_id, f"Role: {body.get('role', 'standard')}, Demo: {body.get('is_demo')}")
    step += 1

    # 5. Organizations & Multi-Tenancy
    print("\n--- Phase 5: Multi-Tenant Organizations ---")
    code, body = request("/api/v1/organizations", token=token)
    org_id = None
    if code == 200 and isinstance(body, list) and len(body) > 0:
        org_id = body[0].get("id")
        log(step, "Organization Discovery", True, f"Org: {body[0].get('name')}, Plan: {body[0].get('plan')}")
    else:
        log(step, "Organization Discovery", code == 200, f"Count: {len(body) if isinstance(body, list) else 0}")
    step += 1

    # 6. AI Review Council Registry
    print("\n--- Phase 6: AI Council Registry ---")
    code, body = request("/api/v1/reviews/council/registry", token=token)
    agents = body.get("agents", []) if isinstance(body, dict) else []
    log(step, "Council Registry Discovery", code == 200 and len(agents) >= 4, f"Active Agents: {[a.get('role') for a in agents]}")
    step += 1

    # 7. Repository Management
    print("\n--- Phase 7: Repository Management ---")
    code, body = request("/api/v1/repositories", token=token)
    repo_id = None
    if code == 200 and isinstance(body, list) and len(body) > 0:
        repo_id = body[0].get("id")
        log(step, "Repository Listing", True, f"Found existing repo: {body[0].get('full_name')}")
    else:
        unique_suffix = int(time.time()) % 100000
        new_repo = {
            "name": f"test-codebase-{unique_suffix}",
            "owner": "openreview-demo",
            "full_name": f"openreview-demo/test-codebase-{unique_suffix}",
            "default_branch": "main",
            "description": "Production E2E Automated Test Codebase",
            "clone_url": "https://github.com/openreview-demo/test-codebase.git",
            "is_active": True
        }
        create_code, create_body = request("/api/v1/repositories", method="POST", data=new_repo, token=token)
        if create_code in (200, 201) and isinstance(create_body, dict):
            repo_id = create_body.get("id")
            log(step, "Repository Provisioning", True, f"Created repository {create_body.get('full_name')} (ID: {repo_id})")
        else:
            log(step, "Repository Provisioning", False, f"Code: {create_code}, Details: {create_body}")
    step += 1

    if repo_id:
        # 8. Repository Architecture Graph
        print("\n--- Phase 8: Repository Architecture Analysis ---")
        code, body = request(f"/api/v1/repositories/{repo_id}/architecture", token=token)
        log(step, "Repository Architecture Graph", code == 200 and isinstance(body, dict), f"Graph response received, status: {code}")
        step += 1

        # 9. Pull Requests
        print("\n--- Phase 9: Pull Request Management ---")
        code, body = request(f"/api/v1/pull-requests?repository_id={repo_id}", token=token)
        pr_id = None
        if code == 200 and isinstance(body, list) and len(body) > 0:
            pr_id = body[0].get("id")
            log(step, "Pull Request Discovery", True, f"Found PR #{body[0].get('pr_number')}: {body[0].get('title')}")
        else:
            new_pr = {
                "repository_id": repo_id,
                "github_pr_id": int(time.time()) % 1000000,
                "pr_number": 42,
                "title": "feat: harden authentication and connection security",
                "description": "Multi-agent review candidate PR",
                "head_branch": "feature/security-hardening",
                "base_branch": "main",
                "head_sha": "a1b2c3d4e5f678901234567890abcdef12345678",
                "base_sha": "f1e2d3c4b5a678901234567890abcdef12345678",
                "author_username": "demo_architect",
                "status": "open"
            }
            create_pr_code, create_pr_body = request("/api/v1/pull-requests", method="POST", data=new_pr, token=token)
            if create_pr_code in (200, 201) and isinstance(create_pr_body, dict):
                pr_id = create_pr_body.get("id")
                log(step, "Pull Request Creation", True, f"Created PR #{create_pr_body.get('pr_number')} (ID: {pr_id})")
            else:
                log(step, "Pull Request Creation", False, f"Code: {create_pr_code}, Details: {create_pr_body}")
        step += 1

        # 10. Review Lifecycle
        if pr_id:
            print("\n--- Phase 10: Multi-Agent Review Lifecycle ---")
            code, body = request(f"/api/v1/reviews?pull_request_id={pr_id}", token=token)
            review_id = None
            if code == 200 and isinstance(body, list) and len(body) > 0:
                review_id = body[0].get("id")
                log(step, "Review Discovery", True, f"Found Review ID: {review_id}, Status: {body[0].get('status')}")
            else:
                new_review = {
                    "pull_request_id": pr_id,
                    "commit_sha": "a1b2c3d4e5f678901234567890abcdef12345678"
                }
                cr_code, cr_body = request("/api/v1/reviews", method="POST", data=new_review, token=token)
                if cr_code in (200, 201) and isinstance(cr_body, dict):
                    review_id = cr_body.get("id")
                    log(step, "Review Provisioning", True, f"Created Review ID: {review_id}, Status: {cr_body.get('status')}")
                else:
                    log(step, "Review Provisioning", False, f"Code: {cr_code}, Details: {cr_body}")
            step += 1

            if review_id:
                # 11. Review Detail & Verdict
                print("\n--- Phase 11: Review Inspection & Council Verdict ---")
                code, body = request(f"/api/v1/reviews/{review_id}", token=token)
                log(step, "Review Detail & Verdict", code == 200, f"Status: {body.get('status') if isinstance(body, dict) else 'N/A'}")
                step += 1

    # 12. AutoFix Engine
    print("\n--- Phase 12: AutoFix Engine ---")
    code, body = request("/api/v1/autofix", token=token)
    log(step, "AutoFix Patch Listing", code == 200, f"Patches Count: {len(body) if isinstance(body, list) else 0}")
    step += 1

    # 13. Analytics & Benchmarks
    print("\n--- Phase 13: Analytics & Audit Logs ---")
    code, stats = request("/api/v1/analytics/stats", token=token)
    log(step, "Analytics & Telemetry Stats", code == 200, 
        f"Deliberation Latency: {stats.get('avg_deliberation_latency_ms', 0)}ms, Consensus Rate: {stats.get('consensus_rate', 0)}%")
    step += 1

    code, logs = request("/api/v1/analytics/audit-logs", token=token)
    log(step, "Enterprise Audit Logs", code == 200, f"Logged Audit Events: {len(logs) if isinstance(logs, list) else 0}")
    step += 1

    # Summary
    passed_count = sum(1 for r in results if r[2])
    total_count = len(results)
    print(f"\n==========================================")
    print(f"E2E TEST RUN COMPLETED: {passed_count}/{total_count} PASSED")
    print(f"==========================================")
    return results

if __name__ == "__main__":
    run_e2e_tests()
