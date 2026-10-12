-- 기존 http_events와 게시판 자료를 보존하며 대시보드 테이블만 추가합니다.
CREATE TABLE IF NOT EXISTS http_events (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    event_type TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- 기존 메모는 내용과 시각을 보존하고 '확인 전' 상태로 시작합니다.
ALTER TABLE notes ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending';
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'notes'::regclass AND conname = 'notes_status_valid') THEN
        ALTER TABLE notes ADD CONSTRAINT notes_status_valid CHECK (status IN ('pending', 'in_progress', 'completed'));
    END IF;
END $$;
