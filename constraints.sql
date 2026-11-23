-- =========================================================
-- constraints.sql : Thêm khóa ngoại + index
-- Chạy SAU KHI đã nạp xong data (load nhanh hơn nhiều).
-- =========================================================

-- Xóa các dòng "mồ côi" (id không có trong title_basics) để FK không báo lỗi
DELETE FROM title_akas a
WHERE NOT EXISTS (SELECT 1 FROM title_basics b WHERE b.tconst = a.title_id);

DELETE FROM title_genres g
WHERE NOT EXISTS (SELECT 1 FROM title_basics b WHERE b.tconst = g.tconst);

-- Khóa ngoại
ALTER TABLE title_genres
    ADD CONSTRAINT fk_tg_title FOREIGN KEY (tconst)   REFERENCES title_basics(tconst);
ALTER TABLE title_genres
    ADD CONSTRAINT fk_tg_genre FOREIGN KEY (genre_id) REFERENCES genres(genre_id);
ALTER TABLE title_akas
    ADD CONSTRAINT fk_akas_title FOREIGN KEY (title_id) REFERENCES title_basics(tconst);

-- Index phục vụ truy vấn
CREATE INDEX idx_akas_region      ON title_akas(region);
CREATE INDEX idx_basics_type_year ON title_basics(title_type, start_year);
CREATE INDEX idx_tg_genre         ON title_genres(genre_id);

-- Cập nhật thống kê cho query planner
ANALYZE;