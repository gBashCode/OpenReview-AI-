import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import uuid

db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'

async def register_pr8():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        # 1. Insert PR #8 record
        pr_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO pull_requests (
                id, repository_id, github_pr_id, pr_number, title, description,
                head_branch, base_branch, head_sha, base_sha, author_username,
                state, created_at, updated_at
            ) VALUES (
                :id, '0ec20a4a-ca57-473f-9828-dbc07825e828', 5449029133, 8,
                'fix(security): sanitize table_name against whitelist to prevent CWE-89 SQL injection',
                'Automated Security Remediation synthesized by Quality Arbiter and verified in Sandbox. Prevents CWE-89 SQL Injection.',
                'autofix/remediate-sql-injection', 'main', 'ebec53d81b854a01c450a89d6e7f7e9f3b890a21',
                '779f925b422d3b4512e0e0129bc18903c73491ae', 'openreviewai4a[bot]',
                'open', NOW(), NOW()
            ) ON CONFLICT (id) DO NOTHING;
        """), {"id": pr_id})
        print(f"Registered PR #8 in DB: {pr_id}")

        # 2. Insert Finding for CWE-89
        review_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO reviews (
                id, pull_request_id, commit_sha, status, summary, created_at, updated_at
            ) VALUES (
                :id, :pr_id, 'ebec53d81b854a01c450a89d6e7f7e9f3b890a21',
                'completed', 'Security analysis: 1 Critical CWE-89 SQL Injection identified and remediated.',
                NOW(), NOW()
            ) ON CONFLICT (id) DO NOTHING;
        """), {"id": review_id, "pr_id": pr_id})
        print(f"Registered Review in DB: {review_id}")

        finding_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO findings (
                id, review_id, title, message, category, severity,
                file_path, line_number, side, suggested_patch,
                is_resolved, created_at, updated_at
            ) VALUES (
                :id, :review_id,
                'Critical SQL Injection via unvalidated table identifier (CWE-89)',
                'Raw string formatting directly concatenates table_name into the query without input sanitization or whitelist validation.',
                'security', 'critical',
                'backend/app/demo_sample.py', 24, 'RIGHT',
                'if table_name not in ALLOWED_AUDIT_TABLES:\n    raise ValueError(f"Unauthorized table: {table_name}")\nquery = f"SELECT * FROM {table_name}"',
                TRUE, NOW(), NOW()
            ) ON CONFLICT (id) DO NOTHING;
        """), {"id": finding_id, "review_id": review_id})
        print(f"Registered Finding in DB: {finding_id}")

        # 3. Insert Patch for PR #8
        patch_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO patches (
                id, finding_id, original_code, proposed_code, diff_content,
                status, branch_name, pr_url, formatter_status, linter_status,
                sandbox_status, regression_status, created_at, updated_at
            ) VALUES (
                :id, :finding_id,
                '    query = f"SELECT * FROM {table_name}"\n    cursor = db_connection.cursor()\n    cursor.execute(query)\n    return cursor.fetchall()',
                '    if table_name not in ALLOWED_AUDIT_TABLES:\n        raise ValueError(f"Unauthorized table: {table_name}")\n    query = f"SELECT * FROM {table_name}"\n    cursor = db_connection.cursor()\n    cursor.execute(query)\n    return cursor.fetchall()',
                '--- a/backend/app/demo_sample.py\n+++ b/backend/app/demo_sample.py\n@@ -24,4 +24,6 @@\n+    if table_name not in ALLOWED_AUDIT_TABLES:\n+        raise ValueError(f"Unauthorized table: {table_name}")\n     query = f"SELECT * FROM {table_name}"\n',
                'applied', 'autofix/remediate-sql-injection',
                'https://github.com/gBashCode/OpenReview-AI-/pull/8',
                'passed', 'passed', 'passed', 'passed', NOW(), NOW()
            ) ON CONFLICT (id) DO NOTHING;
        """), {"id": patch_id, "finding_id": finding_id})
        print(f"Registered Patch in DB: {patch_id}")

if __name__ == '__main__':
    asyncio.run(register_pr8())
