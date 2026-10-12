-- 새 codemit_general_db에 실행. 기존 게시글/계정은 지우거나 덮어쓰지 않습니다.
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT;
UPDATE users SET display_name = username WHERE display_name IS NULL;
ALTER TABLE users ALTER COLUMN display_name SET NOT NULL;
-- 원래 수업 DB의 posts.id를 자동 번호로 연결합니다.
BEGIN;
LOCK TABLE posts IN ACCESS EXCLUSIVE MODE;
CREATE SEQUENCE IF NOT EXISTS posts_id_seq;
ALTER SEQUENCE posts_id_seq OWNED BY posts.id;
ALTER TABLE posts ALTER COLUMN id SET DEFAULT nextval('posts_id_seq');
SELECT setval(
    'posts_id_seq',
    GREATEST(COALESCE((SELECT MAX(id) FROM posts), 0) + 1,
             (SELECT last_value + CASE WHEN is_called THEN 1 ELSE 0 END FROM posts_id_seq)),
    false
);
COMMIT;
