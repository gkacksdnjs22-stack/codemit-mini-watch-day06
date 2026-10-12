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
