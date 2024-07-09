#api/database.py
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def connect_to_postgres():
    return await asyncpg.connect(
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME')
    )

async def close_connection(conn):
    await conn.close()