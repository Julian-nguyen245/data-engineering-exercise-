"""Nạp 2 file .tsv vào DB bằng INSERT theo từng chunk (execute_values).

Cần chạy schema.sql trước. Dùng: python chunk_insert.py [--limit N]
"""
from itertools import islice

from psycopg2.extras import execute_values

from common import finish, run, tables

CHUNK_SIZE = 10_000


def load(conn, limit=None):
    total = 0
    with conn.cursor() as cur:
        for table, cols, rows in tables(limit):
            sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s"
            while batch := list(islice(rows, CHUNK_SIZE)):
                execute_values(cur, sql, batch, page_size=CHUNK_SIZE)
                total += len(batch)
            conn.commit()
        finish(cur)
    conn.commit()
    return total


if __name__ == '__main__':
    run(load)
