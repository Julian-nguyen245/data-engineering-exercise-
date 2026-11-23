"""Phần dùng chung cho chunk_insert.py, bulk_load.py và benchmark.py.

Kết nối DB lấy từ biến môi trường (mặc định: localhost:5432, user/db = postgres):
PGHOST, PGPORT, PGUSER, PGDATABASE, PGPASSWORD.
"""
import argparse, csv, os, time
from itertools import islice
from pathlib import Path

import psycopg2

csv.field_size_limit(10**9)

DIR = Path(__file__).parent
BASICS = DIR / 'title.basics.tsv'
AKAS = DIR / 'title.akas.tsv'

AKAS_COLS = ('title_id', 'ordering', 'title', 'region', 'language',
             'types', 'attributes', 'is_original_title')
BASICS_COLS = ('tconst', 'title_type', 'primary_title', 'original_title',
               'is_adult', 'start_year', 'end_year', 'runtime_minutes')


def connect():
    return psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        port=os.getenv('PGPORT', '5432'),
        user=os.getenv('PGUSER', 'postgres'),
        dbname=os.getenv('PGDATABASE', 'postgres'),
    )  # PGPASSWORD / PGOPTIONS được libpq tự đọc


def read_tsv(path, limit=None):
    """Đọc file TSV (bỏ dòng header), đổi \\N thành None, dừng sau `limit` dòng."""
    with open(path, encoding='utf-8', newline='') as f:
        r = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
        next(r)
        for row in islice(r, limit):
            yield [None if x == r'\N' else x for x in row]


def genre_ids(limit=None):
    names = {g for row in read_tsv(BASICS, limit) if row[8] for g in row[8].split(',')}
    return {g: i for i, g in enumerate(sorted(names), 1)}


def tables(limit=None):
    """Sinh (tên_bảng, các_cột, iterator_các_dòng) theo đúng schema.sql."""
    ids = genre_ids(limit)
    yield 'genres', ('genre_id', 'genre_name'), ((i, g) for g, i in ids.items())
    yield 'title_basics', BASICS_COLS, (r[:8] for r in read_tsv(BASICS, limit))
    yield ('title_genres', ('tconst', 'genre_id'),
           ((r[0], ids[g]) for r in read_tsv(BASICS, limit) if r[8] for g in r[8].split(',')))
    yield 'title_akas', AKAS_COLS, read_tsv(AKAS, limit)


def finish(cur):
    """genres được chèn với id tường minh nên phải đẩy sequence lên cho khớp."""
    cur.execute("SELECT setval(pg_get_serial_sequence('genres', 'genre_id'), "
                "(SELECT max(genre_id) FROM genres))")


def run(load):
    """Chạy một hàm load(conn, limit) từ command line và in thời gian."""
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, help='chỉ nạp N dòng đầu của mỗi file TSV')
    args = ap.parse_args()
    conn = connect()
    try:
        t0 = time.perf_counter()
        n = load(conn, args.limit)
        dt = time.perf_counter() - t0
        print(f'{n:,} dòng trong {dt:.1f}s ({n / dt:,.0f} dòng/s)')
    finally:
        conn.close()
