import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'

async def trace():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        f = (await conn.execute(text("SELECT id, review_id, title, file_path, line_number FROM findings WHERE id = '4db37ea4-6a41-43fb-a408-4ade80023e61';"))).fetchone()
        print('FINDING:', f)
        if f:
            r = (await conn.execute(text(f"SELECT id, pull_request_id FROM reviews WHERE id = '{f[1]}';"))).fetchone()
            print('REVIEW:', r)
            if r:
                pr = (await conn.execute(text(f"SELECT id, repository_id, pr_number, title FROM pull_requests WHERE id = '{r[1]}';"))).fetchone()
                print('PR:', pr)
                if pr:
                    repo = (await conn.execute(text(f"SELECT id, owner, name, full_name, organization_id FROM repositories WHERE id = '{pr[1]}';"))).fetchone()
                    print('REPO:', repo)

if __name__ == '__main__':
    asyncio.run(trace())
