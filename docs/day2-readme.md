# Mini Watch Day2 — 클라우드 배포와 오류 수집

과제: https://classroom.codemit.kr/classes/5/problems/54/submit
작업일: 2026-10-13 / 작업 브랜치: `day2-deploy`
저장소: https://github.com/gkacksdnjs22-stack/codemit-mini-watch-day06

직접 완성한 Day06 프로젝트(main의 `325274e`)를 이어 사용했습니다.
지원 자료는 강사 저장소의 `day07-cloud-materials`에서 필요한 DB SSL 설정,
Sentry 초기화와 Next Route Handler를 비교해 적용했습니다. 기존 앱 전체를 덮어쓰지 않았습니다.

- `general/`: 회원 로그인, 가입, PostgreSQL 게시글 CRUD, 감시 서버에 요청 기록 전송.
- `monitor/backend/`: 운영자 로그인, 이벤트 토큰 검증·분류·DB 저장, 메모 CRUD.
- `monitor/next-frontend/`: 로그인 기록과 DB 메모 화면, 서버에서 감시 Flask로 요청 전달.

[배포 계획과 필수·선택 미션 설명](deployment-plan.md)에 Render 설정, Supabase DB 구분,
환경 변수, 계정 준비, 주소 연결, 오류 수정 커밋과 진단 방법을 정리했습니다.
세 앱의 실제 클라우드 상태는 **미배포**입니다. 코드와 로컬 Docker 실행을 확인했으며
실제 Supabase 연결·Render HTTPS 서비스·Sentry 대시보드 수신은 확인하지 않았습니다.

## 이번에 변경한 파일

| 파일 | 목적 |
|---|---|
| 두 Flask `Dockerfile`, `requirements.txt`, `app.py` | Waitress 실행, Sentry 초기화, 상태 확인, 실습 오류 수정 |
| 두 Flask `db.py`, `sql/deploy.sql` | Session pooler SSL 연결과 자료를 보존하는 SQL |
| 두 Flask `.env.example`, `auth_helpers.py`, `create_user.py` | 별도 세션 키·Secure 쿠키, 비밀값 없는 예시, 입력받은 비밀번호 해시 저장 |
| 일반 `request_logging.py`, 감시 `routes/events.py` | 서버 간 EVENT_TOKEN 전송·검증, 로그인 성공/실패 기록 유지 |
| 두 Flask `routes/auth.py` | 일반 가입의 운영자 중복 확인을 세션 키 대신 서버 간 토큰으로 인증 |
| 두 Flask `observability.py` | DSN·환경·버전 설정과 요청·사용자 정보 제외 |
| Next `app/api/[...path]/route.js`, `.env.example` | 서버 전용 MONITOR_API_URL, Cookie/CSRF/Set-Cookie/상태 전달 |
| Next `Dockerfile`, `next.config.mjs` | npm ci → build → npm run start; 외부 API 없이 빌드 |
| Next `components/Events.js`, `components/ApiNotes.js` | API 오류 안내와 연결 다시 확인, 목록 재조회 |
| 두 Compose, `gateways/monitor.conf` | 로컬 실행을 유지하면서 Next 프록시 경로와 별도 세션 키 적용 |
| `tests/` | SSL·쿠키·Sentry 정보 제외·실습 경로 조건·이벤트 토큰·프록시 전달 검증 |

## 로컬 Docker 실행

아래 명령은 이 README가 있는 프로젝트 루트에서 실행합니다. Compose의 비밀번호·키·토큰은
로컬 실습용 공개 예제 값입니다. 클라우드에서는 `.env.example` 항목을 본인 값으로 설정합니다.
이미 공유 망이 있으면 첫 명령을 생략합니다.

```cmd
docker network create m5d1-events
docker compose -f compose-monitor.yaml config --quiet
docker compose -f compose-general.yaml config --quiet
docker compose -f compose-monitor.yaml up -d --build
curl.exe -f http://localhost:8082/api/auth/me
docker compose -f compose-general.yaml up -d --build
docker compose -f compose-general.yaml exec -e PRACTICE_USERNAME=student -e PRACTICE_PASSWORD=Learn123! general-api python create_user.py
docker compose -f compose-monitor.yaml exec -e PRACTICE_USERNAME=operator -e PRACTICE_PASSWORD=Learn123! monitor-api python create_user.py
```

일반 화면: http://localhost:8081/ / 감시 기록: http://localhost:8082/ /
감시 메모: http://localhost:8082/notes . 일반과 감시는 각각 로그인합니다.
수업용 계정은 위 명령의 예제 값이며 실제 배포 계정은 별도로 준비합니다.
두 DB 망은 internal, API만 공유 망에 참여하고 DB 포트는 PC에 공개하지 않습니다.
소스 변경은 `up -d --build`, 종료는 각 Compose의 `down`을 사용합니다.
DB 보존을 위해 볼륨 삭제 옵션을 사용하지 않습니다.

## 확인 결과 (2026-10-13)

- 두 Compose 구문 검사, 세 Docker 이미지 빌드와 production 실행 통과.
- Next 빌드는 MONITOR_API_URL·DB 없이 통과하고 API Route Handler는 요청 시 처리합니다.
- Flask 6개씩 총 12개 검사와 Node 프록시 3개 검사 통과.
- 실제 로컬 DB로 로그인 실패 401/성공 200 전송과 감시 DB 조회, 새 세션 메모 재조회 통과.
- Next 프록시를 거쳐 메모 등록·수정·조회·공백 입력 400·삭제·없는 메모 404 확인.
- 일반 게시글 등록·수정·재조회·삭제와 실습 경로 기본 404 확인.
- 두 deploy.sql을 기존 로컬 DB에 재실행했고 기존 테이블을 유지한 채 성공했습니다.
- 실습 오류는 로그인 함수를 대체한 로컬 Flask 검사에서 재현했고 수정 후 JSON 200을 확인했습니다.
  실제 Sentry로 오류를 보내거나 클라우드 재배포를 완료한 것으로 해석하지 않습니다.

검사를 다시 실행하려면 각 Flask의 의존성을 설치한 가상환경과 Node가 필요합니다.
Windows CMD에서 프로젝트 루트 기준:

```cmd
set PYTHONPATH=general
python tests/test_cloud.py
set PYTHONPATH=monitor/backend
python tests/test_cloud.py
set PYTHONPATH=
node --test tests/proxy.test.mjs
python verify_docker.py prepare
python verify_docker.py persisted
```

Docker 검증 프로그램은 위 예제 계정을 사용하며 `prepare`에서 점검 메모를 남기고
`persisted`에서 저장된 ID를 다시 읽습니다. 기존 자료를 지우지 않습니다.
이전 Day06 작업 기록은 [별도 기록](docs/day06-history.md)에 보관했습니다.
해당 문서의 이전 설정 설명보다 현재 README·배포 계획·실제 코드가 우선합니다.
