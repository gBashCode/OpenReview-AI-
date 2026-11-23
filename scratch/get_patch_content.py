import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'

async def query():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        f = (await conn.execute(text("SELECT id, title, suggested_patch, file_path FROM findings WHERE id = '4db37ea4-6a41-43fb-a408-4ade80023e61';"))).fetchone()
        print('SUGGESTED PATCH:\n', f[2])
        p = (await conn.execute(text("SELECT id, proposed_code, original_code, diff_content FROM patches WHERE id = '559ad12b-e5e2-4b2f-948e-bd040f10c843';"))).fetchone()
        print('PROPOSED CODE:\n', p[1])

if __name__ == '__main__':
    asyncio.run(query())
