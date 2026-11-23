"""So sánh tổng thời gian (đọc TSV + ghi DB): INSERT theo chunk vs COPY.

Chạy trong schema tạm `bench` (tạo lại bằng schema.sql rồi xóa khi xong),
không đụng tới các bảng thật. Dùng: python benchmark.py [--limit N]
"""
import argparse, os, time

import bulk_load, chunk_insert, common


def reset_schema(conn):
    with conn.cursor() as cur:
        cur.execute('DROP SCHEMA IF EXISTS bench CASCADE; CREATE SCHEMA bench')
        cur.execute((common.DIR / 'schema.sql').read_text(encoding='utf-8'))
    conn.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=500_000,
                    help='số dòng đầu của mỗi file TSV (mặc định 500000)')
    limit = ap.parse_args().limit

    os.environ['PGOPTIONS'] = '-c search_path=bench'  # mọi bảng nằm trong schema bench
    conn = common.connect()
    results = []
    try:
        for name, mod in (('chunk_insert (execute_values)', chunk_insert),
                          ('bulk_load (COPY)', bulk_load)):
            reset_schema(conn)
            t0 = time.perf_counter()
            rows = mod.load(conn, limit)
            results.append((name, rows, time.perf_counter() - t0))
    finally:
        with conn.cursor() as cur:
            cur.execute('DROP SCHEMA IF EXISTS bench CASCADE')
        conn.commit()
        conn.close()

    print(f'\nlimit={limit:,} dòng mỗi file')
    print(f'{"phương pháp":<32}{"dòng":>12}{"thời gian (s)":>15}{"dòng/s":>12}')
    for name, rows, dt in results:
        print(f'{name:<32}{rows:>12,}{dt:>15.1f}{rows / dt:>12,.0f}')
    print(f'\nCOPY nhanh hơn ~{results[0][2] / results[1][2]:.1f}x')


if __name__ == '__main__':
    main()
