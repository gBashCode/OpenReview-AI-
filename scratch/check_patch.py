import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'

async def check():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        p = (await conn.execute(text("SELECT id, status, branch_name, pr_url, rejection_reason FROM patches WHERE id = '559ad12b-e5e2-4b2f-948e-bd040f10c843';"))).fetchone()
        print('PATCH RECORD:', p)

if __name__ == '__main__':
    asyncio.run(check())
