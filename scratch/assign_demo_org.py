import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def assign_org():
    db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT id FROM organizations WHERE slug = 'demo-sandbox-org';"))
        org_id = res.scalar()
        print('Demo Org ID:', org_id)
        if org_id:
            await conn.execute(text(f"UPDATE repositories SET organization_id = '{org_id}' WHERE organization_id IS NULL;"))
            print('Updated unassigned repositories to demo organization!')

if __name__ == '__main__':
    asyncio.run(assign_org())
