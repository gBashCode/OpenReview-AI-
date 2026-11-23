import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def register_demo_repo():
    db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        # Check organizations
        res = await conn.execute(text("SELECT id, slug FROM organizations WHERE slug IN ('demo-sandbox-org', 'akshadit-workspace-2005e1');"))
        orgs = res.fetchall()
        print('Found orgs:', orgs)
        
        for org_id, slug in orgs:
            # Check if gBashCode/demo exists for this org
            chk = await conn.execute(text(f"SELECT id FROM repositories WHERE owner = 'gBashCode' AND name = 'demo' AND organization_id = '{org_id}';"))
            existing = chk.scalar()
            if existing:
                print(f"Repo gBashCode/demo already registered for org {slug} (ID: {existing})")
            else:
                new_id = str(uuid.uuid4())
                await conn.execute(text("""
                    INSERT INTO repositories (
                        id, organization_id, github_repo_id, owner, name, full_name,
                        default_branch, description, clone_url, is_active, created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :gh_id, 'gBashCode', 'demo', 'gBashCode/demo',
                        'main', 'Autonomous AutoFix Studio Demo Repository',
                        'https://github.com/gBashCode/demo.git', TRUE, NOW(), NOW()
                    );
                """), {
                    "id": new_id,
                    "org_id": org_id,
                    "gh_id": 999123456 if slug == 'demo-sandbox-org' else 999123457
                })
                print(f"Registered gBashCode/demo for org {slug} (ID: {new_id})")

if __name__ == '__main__':
    asyncio.run(register_demo_repo())
