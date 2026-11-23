import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import uuid

db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'

async def update_db():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        # 1. Update repository organization so it is visible in the user's workspace
        await conn.execute(text("""
            UPDATE repositories 
            SET organization_id = '221069d6-37fb-421f-8d2a-4b22eef2cf6d',
                owner = 'gBashCode',
                name = 'OpenReview-AI-',
                full_name = 'gBashCode/OpenReview-AI-',
                is_active = TRUE
            WHERE id = '0ec20a4a-ca57-473f-9828-dbc07825e828';
        """))
        print('Updated repository 0ec20a4a-ca57-473f-9828-dbc07825e828')

        # 2. Update patch 559ad12b-e5e2-4b2f-948e-bd040f10c843 to point to real GitHub PR #7
        await conn.execute(text("""
            UPDATE patches 
            SET status = 'applied',
                branch_name = 'autofix/patch-559ad12b',
                pr_url = 'https://github.com/gBashCode/OpenReview-AI-/pull/7'
            WHERE id = '559ad12b-e5e2-4b2f-948e-bd040f10c843';
        """))
        print('Updated patch 559ad12b-e5e2-4b2f-948e-bd040f10c843 with PR #7')

        # Alter column to BIGINT if needed
        try:
            await conn.execute(text("ALTER TABLE pull_requests ALTER COLUMN github_pr_id TYPE BIGINT;"))
        except Exception:
            pass

        # 3. Insert or update PullRequest record for PR #7
        pr_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO pull_requests (
                id, repository_id, github_pr_id, pr_number, title, description,
                head_branch, base_branch, head_sha, base_sha, author_username,
                state, created_at, updated_at
            ) VALUES (
                :id, '0ec20a4a-ca57-473f-9828-dbc07825e828', 5449029132, 7,
                'autofix: Unhandled Empty List or NoneType causes ZeroDivisionError',
                'Automated remediation patch synthesized by Quality Arbiter and verified in Sandbox. Fixes ZeroDivisionError in backend/app/demo_sample.py.',
                'autofix/patch-559ad12b', 'main', '816bad324069264923dcfc34a99fc1c630d13b67',
                'a1aac7913d1e3d36d3cdf2c77fc869941fb9e498', 'openreviewai4a[bot]',
                'open', NOW(), NOW()
            ) ON CONFLICT (id) DO NOTHING;
        """), {"id": pr_id})
        print(f'Inserted PR #7 record: {pr_id}')

        # 4. Also update the finding's review to link to this repository and pull request
        await conn.execute(text("""
            UPDATE pull_requests 
            SET repository_id = '0ec20a4a-ca57-473f-9828-dbc07825e828'
            WHERE id = '481c299c-b48a-4d10-b10a-26ef18a72b34';
        """))
        print('Updated review PR 481c299c-b48a-4d10-b10a-26ef18a72b34')

if __name__ == '__main__':
    asyncio.run(update_db())
