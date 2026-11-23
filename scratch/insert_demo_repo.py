import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def insert_demo_repo():
    db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        # Insert gBashCode/demo
        await conn.execute(text("""
            INSERT INTO repositories (
                id, organization_id, github_repo_id, owner, name, full_name,
                default_branch, description, clone_url, is_active, created_at, updated_at
            ) VALUES (
                'd3m00000-0000-0000-0000-000000000001',
                '221069d6-37fb-421f-8d2a-4b22eef2cf6d',
                999123456,
                'gBashCode',
                'demo',
                'gBashCode/demo',
                'main',
                'Autonomous AutoFix Studio Demo Repository',
                'https://github.com/gBashCode/demo.git',
                TRUE,
                NOW(),
                NOW()
            ) ON CONFLICT (full_name) DO UPDATE SET organization_id = '221069d6-37fb-421f-8d2a-4b22eef2cf6d';
        """))
        
        # Link PR to gBashCode/demo
        await conn.execute(text("""
            UPDATE pull_requests 
            SET repository_id = 'd3m00000-0000-0000-0000-000000000001'
            WHERE id = '481c299c-b48a-4d10-b10a-26ef18a72b34';
        """))
        
        # Reset patch to pending and ready for action
        await conn.execute(text("""
            UPDATE patches 
            SET status = 'pending', branch_name = NULL, pr_url = NULL 
            WHERE id = '559ad12b-e5e2-4b2f-948e-bd040f10c843';
        """))
        
        print("Successfully created and linked gBashCode/demo in database!")

if __name__ == '__main__':
    asyncio.run(insert_demo_repo())
