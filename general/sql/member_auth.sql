-- 과제 전용 codemit_general_db에만 적용. 수업 DB는 수정하지 않습니다.
ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT;
UPDATE users SET display_name = username WHERE display_name IS NULL;
ALTER TABLE users ALTER COLUMN display_name SET NOT NULL;
