-- =========================================================
-- schema.sql : Tạo bảng cho IMDb (title.basics + title.akas)
-- Chạy TRƯỚC khi nạp data.
-- Có thể chạy lại nhiều lần (DROP ... IF EXISTS).
-- =========================================================

DROP TABLE IF EXISTS title_akas   CASCADE;
DROP TABLE IF EXISTS title_genres CASCADE;
DROP TABLE IF EXISTS genres       CASCADE;
DROP TABLE IF EXISTS title_basics CASCADE;

-- 1. Bảng phim (từ title.basics)
CREATE TABLE title_basics (
    tconst          VARCHAR(12) PRIMARY KEY,   -- vd: tt0111161
    title_type      VARCHAR(20) NOT NULL,      -- movie, short, tvSeries...
    primary_title   TEXT        NOT NULL,
    original_title  TEXT,
    is_adult        BOOLEAN     NOT NULL DEFAULT FALSE,
    start_year      SMALLINT,                  -- \N -> NULL
    end_year        SMALLINT,
    runtime_minutes INT
);

-- 2. Danh mục thể loại (tách từ cột genres của title.basics)
CREATE TABLE genres (
    genre_id   SERIAL      PRIMARY KEY,
    genre_name VARCHAR(30) UNIQUE NOT NULL
);

-- 3. Bảng nối phim - thể loại (quan hệ nhiều-nhiều)
CREATE TABLE title_genres (
    tconst   VARCHAR(12) NOT NULL,
    genre_id INT         NOT NULL,
    PRIMARY KEY (tconst, genre_id)
);

-- 4. Tên phim theo quốc gia/ngôn ngữ (từ title.akas)
CREATE TABLE title_akas (
    title_id          VARCHAR(12) NOT NULL,
    ordering          INT         NOT NULL,
    title             TEXT        NOT NULL,
    region            VARCHAR(10),            -- US, VN, XWW...
    language          VARCHAR(10),            -- en, vi, ja...
    types             TEXT,
    attributes        TEXT,
    is_original_title BOOLEAN,
    PRIMARY KEY (title_id, ordering)
);