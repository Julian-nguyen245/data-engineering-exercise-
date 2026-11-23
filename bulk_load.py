"""Nạp 2 file .tsv vào DB bằng COPY ... FROM STDIN.

Cần chạy schema.sql trước. Dùng: python bulk_load.py [--limit N]
"""
from common import finish, run, tables

READ_SIZE = 1 << 20


class CopyStream:
    """File-like đọc từ iterator các dòng, trả về text định dạng COPY (tab, \\N)."""

    def __init__(self, rows):
        self.rows = iter(rows)

    @staticmethod
    def line(row):
        return '\t'.join(r'\N' if v is None else str(v).replace('\\', '\\\\') for v in row) + '\n'

    def read(self, size=-1):
        parts, n = [], 0
        for row in self.rows:
            s = self.line(row)
            parts.append(s)
            n += len(s)
            if n >= size:
                break
        return ''.join(parts)


def load(conn, limit=None):
    total = 0
    with conn.cursor() as cur:
        for table, cols, rows in tables(limit):
            cur.copy_expert(f"COPY {table} ({', '.join(cols)}) FROM STDIN",
                            CopyStream(rows), size=READ_SIZE)
            total += cur.rowcount
            conn.commit()
        finish(cur)
    conn.commit()
    return total


if __name__ == '__main__':
    run(load)
