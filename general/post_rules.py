def validate_post(title, body):
    title = title.strip()
    body = body.strip()
    error = None
    if not title or not body:
        error = "제목과 내용을 모두 입력해 주세요."
    return title, body, error
