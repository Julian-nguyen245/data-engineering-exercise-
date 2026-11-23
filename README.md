
# Homework: nạp dữ liệu IMDb vào PostgreSQL bằng 2 cách và so sánh tốc độ

## Họ và tên: Nguyễn Trung Hiếu - MSV: 23001606


## Dữ liệu

Dataset [IMDb Non-Commercial Datasets](https://datasets.imdbws.com/) (định dạng TSV, giải nén từ `.tsv.gz`).
File TSV không được đưa lên Git (xem `.gitignore`), cần tải về đặt cạnh các script.

| File | Số dòng (gồm header) | Dung lượng |
|---|---|---|
| `title.basics.tsv` | 12.992.889 | 1,1 GB |
| `title.akas.tsv` | 60.599.445 | 3,1 GB |

Kiểm tra số dòng: `wc -l title.basics.tsv title.akas.tsv`

## Các file trong thư mục

| File | Vai trò |
|---|---|
| `schema.sql` | **DDL, chạy trước khi nạp.** Xóa (nếu có) rồi tạo 4 bảng, chỉ có khóa chính để nạp nhanh. |
| `constraints.sql` | **Chạy sau khi nạp xong.** Xóa dòng mồ côi, thêm khóa ngoại và index, rồi `ANALYZE`. Thêm ràng buộc sau khi nạp nhanh hơn nhiều so với kiểm tra từng dòng lúc nạp. |
| `common.py` | Phần dùng chung: kết nối DB, đọc TSV (đổi `\N` thành NULL), tách cột `genres`. Cả hai cách ghi dùng chung nên so sánh công bằng. |
| `chunk_insert.py` | **Cách 1:** `INSERT` theo chunk 10.000 dòng bằng `psycopg2.extras.execute_values`. |
| `bulk_load.py` | **Cách 2:** `COPY ... FROM STDIN` (bulk load), dữ liệu đẩy thẳng dạng stream. |
| `benchmark.py` | Chạy cả hai cách trong schema tạm `bench` (không đụng bảng thật), đo tổng thời gian bằng `time.perf_counter()` và in bảng so sánh. |
| `.gitignore` | Bỏ qua file `.tsv` và `__pycache__/`. |

## Schema

```
title_basics (tconst PK, title_type, primary_title, original_title,
              is_adult, start_year, end_year, runtime_minutes)
genres       (genre_id PK, genre_name UNIQUE)          -- tách từ cột genres
title_genres (tconst, genre_id)  PK(tconst, genre_id)   -- quan hệ nhiều-nhiều
title_akas   (title_id, ordering, title, region, language,
              types, attributes, is_original_title)  PK(title_id, ordering)
```

`title.basics.tsv` được dùng cho 3 bảng (`title_basics`, `genres`, `title_genres`),
`title.akas.tsv` cho bảng `title_akas`.

## Hướng dẫn chạy

1. **Chạy PostgreSQL bằng Docker** (lần đầu):
   ```bash
   docker run --name pg -e POSTGRES_PASSWORD=<mật khẩu> -p 5432:5432 -d postgres:16
   ```
   Các lần sau: `docker start pg`.

2. **Cài thư viện:**
   ```bash
   pip install psycopg2-binary
   ```

3. **Cấu hình kết nối** bằng biến môi trường (mặc định `localhost:5432`, user và db đều là `postgres`):
   ```bash
   export PGPASSWORD=<mật khẩu>
   # tùy chọn: PGHOST, PGPORT, PGUSER, PGDATABASE
   ```

4. **Tạo bảng:**
   ```bash
   docker exec -i pg psql -U postgres < schema.sql
   ```

5. **Nạp dữ liệu** (chọn một cách; muốn nạp lại thì chạy lại bước 4):
   ```bash
   python bulk_load.py                    # COPY
   python chunk_insert.py                 # INSERT theo chunk
   python bulk_load.py --limit 2700000    # chỉ nạp N dòng đầu của mỗi file
   ```

6. **Thêm khóa ngoại và index** (sau khi nạp xong):
   ```bash
   docker exec -i pg psql -U postgres < constraints.sql
   ```

7. **So sánh tốc độ:**
   ```bash
   python benchmark.py --limit 2700000
   ```
   Benchmark tự tạo và tự xóa schema `bench`. `--limit` tính theo số dòng của mỗi file TSV
   (2.700.000 dòng mỗi file cho khoảng 9,7 triệu dòng tổng cộng). Nạp full cần khoảng 12 GB đĩa trống
   và `chunk_insert` có thể chạy hơn 30 phút.

## Kết quả so sánh

`benchmark.py --limit 2700000`, ghi 9.708.913 dòng vào 4 bảng (tổng thời gian đọc TSV và ghi DB):

| Cách | Thời gian | Tốc độ |
|---|---|---|
| `chunk_insert` (`execute_values`) | 104,2 s | ~93.000 dòng/s |
| `bulk_load` (`COPY`) | 24,2 s | ~402.000 dòng/s |

`COPY` nhanh hơn khoảng **4,3 lần**. Thời gian tính cả bước đọc và parse TSV bằng Python
(giống nhau ở cả hai cách), nên chênh lệch riêng phần ghi DB còn lớn hơn.

## Ưu và nhược điểm

### Cách 1: `INSERT` theo chunk (`chunk_insert.py`)

| Ưu điểm | Nhược điểm |
|---|---|
| Linh hoạt: dùng được toàn bộ cú pháp `INSERT`, ví dụ `ON CONFLICT DO NOTHING/UPDATE` để bỏ qua hoặc cập nhật dòng trùng khóa, `RETURNING`. | Chậm hơn khoảng 4,3 lần (~93.000 dòng/s so với ~402.000 dòng/s). |
| Dễ kiểm soát theo chunk: có thể in tiến độ, thử lại hoặc commit sau mỗi chunk. | Mỗi chunk là một câu SQL rất dài, psycopg2 phải chuyển từng giá trị thành chuỗi SQL và server phải parse lại. |
| Không phải tự lo định dạng escape: psycopg2 xử lý dấu nháy và ký tự đặc biệt. | Phải giữ cả chunk (10.000 tuple) trong RAM trước khi gửi. |

### Cách 2: `COPY` (`bulk_load.py`)

| Ưu điểm | Nhược điểm |
|---|---|
| Nhanh nhất: dữ liệu được stream thẳng vào bảng, không phải parse từng câu `INSERT` (nhanh hơn khoảng 4,3 lần). | Không có `ON CONFLICT`: gặp dòng trùng khóa chính là cả lệnh `COPY` lỗi. |
| Ít tốn RAM: dòng nào đọc xong được gửi đi ngay theo luồng. | Tất cả hoặc không: một dòng lỗi làm hủy cả lệnh `COPY` của bảng đó, nên khó biết và xử lý riêng dòng hỏng. |
| Một lệnh cho cả bảng, code ngắn. | Phải tự escape đúng định dạng text của `COPY` (dấu `\`, tab, xuống dòng, `\N` cho NULL). |

### Kết luận

- **Nạp lượng dữ liệu lớn lần đầu vào bảng trống** (như bài này): dùng `COPY`.
- **Cần xử lý dòng trùng, cập nhật dữ liệu có sẵn, lấy lại giá trị vừa chèn, hoặc dữ liệu ít**: dùng `INSERT`.
- Dù chọn cách nào, nên nạp trước rồi mới thêm khóa ngoại và index (`constraints.sql`) để nạp nhanh hơn.
