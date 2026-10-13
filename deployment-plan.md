# Day2 배포 계획 · 필수와 선택 미션

작성일 2026-10-13. 저장소는 https://github.com/gkacksdnjs22-stack/codemit-mini-watch-day06,
배포 대상 브랜치는 `day2-deploy`입니다. Render Hobby/Free, Supabase Free,
Sentry Developer의 수업 무료 범위를 기준으로 준비했습니다. 결제나 유료 전환은 진행하지 않았습니다.

## 세 앱의 Render 설정과 진행 상태

| 앱 | 상태 | Root Directory | Dockerfile Path | Build Context | Health Check |
|---|---|---|---|---|---|
| 일반 Flask | 미배포 | general | ./Dockerfile | . | /health |
| 감시 Flask | 미배포 | monitor/backend | ./Dockerfile | . | /health |
| 감시 Next | 미배포 | monitor/next-frontend | ./Dockerfile | . | / |

세 앱 모두 Docker Web Service, 배포 브랜치 `day2-deploy`, Docker Command 빈칸,
Auto-Deploy On Commit, 인스턴스 Free를 사용합니다. 아직 본인 배포 주소가 없습니다.
`YOUR-...onrender.com`은 설명용 자리표시자이며 완료된 주소가 아닙니다.
Flask Dockerfile은 Waitress가 `app:app`을 0.0.0.0과 환경의 PORT에서 실행합니다.
`python app.py` 개발 실행도 같은 앱을 읽습니다. Next는 잠금 파일로 npm ci를 실행하고
npm run build 후 npm run start로 production 서버를 PORT와 0.0.0.0에서 실행합니다.

현재 로컬 이미지 빌드와 앱 실행은 완료했습니다. Supabase 두 프로젝트 연결값,
Render 서비스와 Sentry DSN은 아직 등록하지 않았습니다. 실제 배포, 외부 DB 저장,
Sentry 화면 수신은 미확인입니다. `/health` 200은 앱 응답 확인이며 DB 접속이나
테이블 SQL·계정 인증 성공까지 보장하지 않습니다. Next의 `/`도 페이지 제공 확인입니다.

두 Compose와 gateway는 로컬 7개 컨테이너 실행용으로 유지합니다. Render에는 Compose,
Nginx, 로컬 PostgreSQL을 배포하지 않고 각 앱 Dockerfile과 외부 Supabase DB를 사용합니다.
로컬에서도 감시 gateway는 Next로 요청을 전달하여 동일한 `/api` Route Handler를 검증합니다.

## 일반·감시 Supabase DB 대응

| 앱 | Supabase 프로젝트 | Session pooler 연결 | SQL | 저장 자료 |
|---|---|---|---|---|
| 일반 | 수업 샘플 프로젝트를 일반용으로 재사용할 예정 | 본인 GENERAL Host, postgres.GENERAL_PROJECT_REF | general/sql/deploy.sql | users, posts |
| 감시 | 일반과 다른 프로젝트를 별도로 준비할 예정 | 본인 MONITOR Host, postgres.MONITOR_PROJECT_REF | monitor/backend/sql/deploy.sql | users, http_events, notes |

두 프로젝트의 Connect 화면에서 **Session pooler** Host와 User를 복사합니다.
포트는 5432, DB_NAME은 postgres, DB_SSLMODE는 require입니다. 같은 지역의 Host나
같은 DB 이름만 보고 같은 DB라고 판단하지 않고 프로젝트 ref와 사용자 값을 구분합니다.
두 Flask의 db.py가 DB_HOST·DB_PORT·DB_NAME·DB_USER·DB_PASSWORD·DB_SSLMODE를 읽고
psycopg에 전달합니다. 사용자 입력은 기존 repositories의 `%s` 매개변수 바인딩을 유지합니다.

각 프로젝트의 SQL Editor에서 해당 deploy.sql만 실행합니다. users의 id/username/
display_name/password_hash, posts의 id/title/body, http_events의 id/occurred_at/method/
path/status_code/event_type, notes의 id/title/body/status/created_at/updated_at가 앱과 대응합니다.
CREATE TABLE IF NOT EXISTS·ADD COLUMN IF NOT EXISTS를 사용하며 DROP/TRUNCATE나
기존 행 삭제를 요구하지 않습니다. 일반 게시글 시퀀스도 기존 최대 ID 이상으로 유지합니다.
두 SQL은 기존 로컬 DB에 적용을 확인했으나 실제 Supabase에서는 아직 실행하지 않았습니다.

수업 구성대로 Supabase Data API를 끄고 Flask가 PostgreSQL에 직접 연결합니다.
새 프로젝트를 만들 때 Data API 비활성화를 선택하거나 해당 프로젝트 API 설정에서 확인합니다.
이 과제에서는 별도 RLS 정책을 추가하지 않습니다. DB 비밀번호는 프로젝트별로 관리하며
Git, README, 브라우저에 넣지 않습니다. 앱 재배포는 코드를 바꾸고 기존 외부 DB 자료는 유지합니다.

## 환경 변수와 계정 준비

각 Flask 폴더의 .env.example을 .env로 복사하고 로컬에서 본인 값을 채웁니다.
Render에서는 해당 서비스 Environment에 같은 이름을 설정합니다. 실제 .env는 제출하지 않습니다.

| 변수 | 설정할 앱 | 역할 |
|---|---|---|
| DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSLMODE | 두 Flask | 각자의 Supabase Session pooler 연결 |
| SECRET_KEY | 두 Flask | 앱마다 다른 무작위 32자 이상 세션 서명 키 |
| SESSION_COOKIE_SECURE | 두 Flask | 로컬 HTTP false, Render HTTPS true |
| PORT | 세 앱 | Render가 제공하는 수신 포트; 로컬 Flask 5000 / Next 3000 |
| MONITOR_URL | 일반 Flask | 감시 Flask HTTPS 주소 + /api/events |
| MONITOR_API_URL | 일반 Flask | 감시 Flask 기준 주소; 기존 운영자 로그인/아이디 중복 확인 |
| DASHBOARD_URL | 일반 Flask | 감시 Next HTTPS 주소, 운영자 화면 이동 |
| EVENT_TOKEN | 두 Flask | 동일한 무작위 서버 간 토큰; 이벤트 전송과 계정 중복 확인 인증 |
| MONITOR_API_URL | Next 서버 | 감시 Flask HTTPS 기준 주소; /api 접미사를 붙이지 않음 |
| SENTRY_DSN | 두 Flask | Sentry 프로젝트 DSN, 제출 예시는 빈값 |
| SENTRY_ENVIRONMENT | 두 Flask | 일반 mini-general / 감시 mini-monitor |
| APP_VERSION | 두 Flask | 실제 배포하는 Git 커밋 식별자를 권장 |
| ENABLE_SENTRY_TEST | 일반 Flask | 최종 false, 실습 경로 잠시 활성화 |

DB 비밀번호·세션 키·EVENT_TOKEN·DSN은 서버 설정에서만 읽습니다.
Next에는 감시 API 기준 주소만 필요하며 NEXT_PUBLIC_*에 비밀값을 넣지 않습니다.
SESSION_COOKIE_HTTPONLY와 SameSite=Lax, 일반/감시의 서로 다른 쿠키 이름을 유지합니다.
서로 다른 세션 키를 사용하므로 일반 화면과 감시 화면에 각각 로그인합니다.
일반의 운영자 중복 확인은 X-Internal-Auth의 EVENT_TOKEN으로 검증하여 세션 키 분리를 지원합니다.

계정은 각 Flask 폴더의 **로컬 가상환경**에서 따로 준비합니다. 아래는 Windows CMD 명령입니다.
프로젝트 루트에서 일반 계정을 준비하고, 감시는 monitor/backend로 이동해 같은 절차를 반복합니다.
이미 가상환경이 있으면 생성 단계를 생략합니다.

```cmd
cd general
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
rem .env에 해당 프로젝트 연결값과 별도 SECRET_KEY 등을 입력
.venv\Scripts\python.exe create_user.py
.venv\Scripts\python.exe app.py
```

create_user.py는 아이디와 getpass로 비밀번호를 입력받아 Werkzeug 해시만 해당 users에 저장합니다.
기존 username은 ON CONFLICT DO NOTHING으로 보존합니다. 비밀번호 평문을 출력하지 않습니다.
감시 계정도 같은 명령으로 감시 DB에서 준비합니다. 로컬 HTTP 개발 실행 때 Secure=false를 설정합니다.
일반과 감시를 동시에 개발 실행하려면 일반 PORT=5100, 감시 PORT=5200으로 구분하고
MONITOR_URL/MONITOR_API_URL을 감시의 http://127.0.0.1:5200으로 바꿉니다.
Next 개발 실행은 npm ci → npm run dev이고 서버 환경 MONITOR_API_URL에 감시 주소를 설정합니다.

## 로그인·기록·메모 요청 흐름

브라우저 → 감시 Next의 같은 사이트 /api/... → 서버 Route Handler →
MONITOR_API_URL의 감시 Flask /api/... → 감시 DB입니다.
Route Handler는 허용된 auth/me·login·logout, events GET, notes CRUD만 프록시하고,
요청 Cookie·X-CSRF-Token·Content-Type·본문·쿼리를 전달합니다.
응답 Set-Cookie(여러 개도 유지)·Content-Type·HTTP 상태를 전달하므로 로그인 쿠키와 CSRF가
다음 메모 요청에도 사용됩니다. auth/account-exists와 events POST는 브라우저 프록시에서 허용하지 않습니다.

일반 Flask → MONITOR_URL의 감시 Flask /api/events → EVENT_TOKEN 확인 →
rules.make_event 분류 → repositories.events의 DB 저장 → 감시 events GET → 화면 표시입니다.
X-Event-Token이 없거나 다르면 403이고 저장하지 않습니다. 일반 `/login` 폼 성공 303은
request_logging에서 의미상 성공 200으로 기록하고, JSON 로그인도 200입니다.
틀린 비밀번호는 401이며 감시에서 login_failure/401과 login_success/200으로 나눕니다.
게시글과 메모 CRUD는 기존 DB repositories를 유지하고, 새 세션/새로고침 후 DB에서 다시 읽습니다.

## 오류 재현·수정과 커밋

| 단계 | 커밋 식별자 | 변경 |
|---|---|---|
| 배포 설정 및 지원 자료 오류 재현 | 43381ce | Flask/Next 배포·SSL·세션·토큰·Sentry, gated sentry_test의 1 / 0 |
| 실습 오류 수정 | 64b19b4eecf63000ebb33822fff192249b8156ae | general/app.py의 sentry_test에서 1 / 0을 1 / 1로 변경 |

오류 파일은 general/app.py, 함수는 sentry_test입니다. 분모 0으로 ZeroDivisionError가
발생하여 정상 응답을 만들 수 없었습니다. 분모를 1로 바꿔 JSON `{"result":1.0}`과
HTTP 200을 반환하게 했습니다. ENABLE_SENTRY_TEST가 true일 때만 활성화하고 로그인
확인은 그대로 유지했습니다. 최종 예시 파일은 false입니다. 일반 로그인·게시글·기록 코드는
이 수정 커밋에서 바꾸지 않았고 통합 확인에서도 동작했습니다.

선택 항목의 수정 전후 diff는 [sentry-fix.diff](docs/sentry-fix.diff)이며
`git diff 43381ce 64b19b4 -- general/app.py`로 같은 내용을 확인할 수 있습니다.
재현 커밋은 비교용 이력이며 최종 배포는 수정 이후 브랜치 HEAD를 사용합니다.
로컬 Flask 검사에서 오류 재현과 수정 후 200, 비로그인 401, 비활성 404를 확인했습니다.
실제 Sentry 수신을 완료했다고 주장하지 않습니다.

실제 배포 실습 때는 감시 /health 확인 → 일반·Next 주소와 환경 변수 연결 →
각 화면 로그인 → 일반 실패/성공 생성 → 감시 기록 조회 → 게시글/메모 등록·수정·재조회 및
각 DB 행 확인 순서로 진행합니다. 오류 재현이 필요하면 별도 로컬 checkout에서 재현 커밋을
사용하고 ENABLE_SENTRY_TEST=true로 잠시 확인합니다. 외부 수신 확인은 본인 DSN을 설정한
환경에서만 수행합니다. 최종 배포에 재현 커밋을 사용하지 않습니다.

수정 파일 확인 → git add/commit → git push origin day2-deploy → Render 배포 상세에서
커밋 식별자 확인 → 동일 계정·동일 경로 정상 JSON 확인 → ENABLE_SENTRY_TEST=false로
변경·재시작/재배포 → /api/sentry-test 404 → 기존 게시글·메모 다시 조회 순서입니다.
APP_VERSION도 배포 코드 식별자와 맞춥니다. **Sentry Resolve는 이슈 상태 표시**이며
코드 수정·push·재배포를 대신하지 않습니다.

## 선택 1: 설정 오류 진단

| 증상·처리 경로 | 먼저 확인할 설정·로그 | 다음 확인 |
|---|---|---|
| Next 프록시 503 | Next의 MONITOR_API_URL 누락, Next 서비스 설정 | 감시 Flask 기준 HTTPS 주소를 넣고 재시작 |
| Next 프록시 502 | Next 로그, MONITOR_API_URL 오타/프로토콜·감시 서비스 상태 | 감시 /health 확인 후 DB 기능 별도 확인 |
| 일반 기록 전달 경고 | 일반 로그의 전달 실패, MONITOR_URL, 감시 주소 | 두 EVENT_TOKEN 일치와 감시 403 여부, 감시 DB |
| 감시 DB 처리 503 | monitor/backend/app.py DB error handler 로그의 예외 종류 | DB_HOST/PORT/NAME/USER/PASSWORD/SSLMODE와 deploy.sql·users 해시 |
| 일반 로그인/게시글 503 | 일반 routes/auth.py·routes/posts.py의 DB/연결 처리 경로 | 일반 DB 설정·SQL, 운영자 경로일 때 감시 주소/상태 |
| 빈 입력 400 | notes.validate_note, general.post_rules 또는 로그인 입력 | 입력 제목·본문·아이디를 수정, 인프라 오류와 구분 |
| 인증 401/CSRF 403 | 로그인 상태·X-CSRF-Token·Cookie 전달 | 같은 사이트 세션을 다시 읽고 로그인 |
| 이벤트 403 | monitor routes/events의 토큰 검사 | 서버 간 EVENT_TOKEN 일치; 브라우저에 토큰 노출하지 않음 |

/health가 성공해도 두 Flask는 그 경로에서 DB에 연결하지 않습니다. 실제 로그인/메모/게시글
작업으로 DNS·DB 인증·테이블·저장을 단계별로 확인합니다. 일반 기록 전송은 실패해도
원래 응답을 유지하고 경고를 남기며 자동 재전송하지 않으므로 복구 후 새 로그인 요청을 만듭니다.

## 선택 2: 요청 실패 안내와 재시도

Next route.js는 서버 주소 누락을 503, 연결/타임아웃 실패를 502 JSON으로 응답합니다.
감시 Flask 자체의 400/401/403/404/503도 변경하지 않고 전달합니다.
api/notes.js의 request는 HTTP 실패 JSON의 error를 ApiError로 만들고 ApiNotes.report가
상태 코드와 메시지를 role=alert로 표시합니다. 수정 state는 성공 응답 뒤에 반영됩니다.
로그인 이전 연결 실패는 **연결 다시 확인**, 로그인 뒤 목록 실패는 **DB 목록 새로고침**으로
재시도합니다. Events도 같은 프록시 오류를 role=alert로 표시하며 연결 다시 확인 또는
기록 불러오기를 다시 누를 수 있습니다. 로그인은 먼저 getSession을 호출해 최신 CSRF를 얻습니다.
Node 테스트에서 누락 503·연결 실패 502·상태 전달·Cookie/CSRF/Set-Cookie 전달을 검증했습니다.

## 선택 3: Sentry 자료의 정보 제외

두 observability.py가 앱 import/생성 시 configure_errors를 실행하므로 개발·Waitress에
모두 적용됩니다. 빈 DSN이면 외부 수집을 시작하지 않습니다. FlaskIntegration을 연결하고
SENTRY_ENVIRONMENT·APP_VERSION을 읽으며 service 태그를 mini-general/mini-monitor로 구분합니다.

- send_default_pii=false: 기본 사용자 개인정보 수집을 비활성화합니다.
- include_local_variables=false: 예외 스택 지역 변수의 비밀번호·DB 값 노출을 줄입니다.
- max_request_body_size=never: 로그인·메모 요청 본문 수집을 비활성화합니다.
- before_send=remove_request_secrets: request의 data·cookies·headers·query_string과 최상위 user를 제거합니다.
- traces_sample_rate=0.0: 이 실습은 오류 수집 중심으로 두고 트랜잭션 추적은 수집하지 않습니다.

본인 DSN은 서버 환경에만 설정하며 예시 DSN은 비워 두었습니다. 정보 제외 함수와 초기화
옵션을 두 앱의 테스트에서 직접 확인했습니다. Sentry 수신 화면 자체는 미확인입니다.

## 선택 4: 오류 수정 변경 비교

위 재현/수정 커밋과 docs/sentry-fix.diff를 함께 제출합니다. 변경은 sentry_test의 계산과
주석뿐이며 로그인 확인·ENABLE_SENTRY_TEST·Sentry 초기화·일반 게시판 라우트는 유지합니다.
이로써 같은 인증·활성화 조건의 요청이 ZeroDivisionError 대신 JSON 200으로 바뀝니다.

공식 참고: [Render Docker](https://render.com/docs/docker),
[Supabase DB 연결](https://supabase.com/docs/guides/database/connecting-to-postgres),
[Sentry Python 설정](https://docs.sentry.io/platforms/python/configuration/options/).
