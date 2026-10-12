# Mini Watch Day06 — 두 Compose로 실행하기

과제: https://classroom.codemit.kr/classes/5/problems/51/submit

2026-10-12, 기존에 직접 구현한 `mini-watch` 일반 Flask 게시판/감시 Flask API와
Day05 Next.js DB 메모 컴포넌트를 이어 사용했습니다. 강사 완성본을 복사하지 않았습니다.
일반 앱은 `general/`, 감시 API는 `monitor/backend/`, 감시 Next.js는
`monitor/next-frontend/`이며 수업의 서비스 이름과 포트는 그대로 사용합니다.

## 직접 완성한 내용

- 두 Compose의 7개 서비스, DB healthcheck/대기, 독립된 DB 볼륨, 내부 망과 외부 공유 망.
- 두 Flask Dockerfile과 Next.js 다단계 production/standalone Dockerfile, 각 `.dockerignore`.
- 두 Nginx gateway와 앱의 DB 코드에 맞춘 `sql/docker-init.sql`.
- Flask의 `0.0.0.0:5000` 바인딩, 컨테이너 간 기록 전달 주소, 실습 계정 준비 스크립트.
- Next.js 로그인 기록 화면과 기존 DB 메모 CRUD 화면 연결. 브라우저 API 요청은 상대 주소
  `/api/...`를 사용하고 Nginx가 `monitor-api:5000`으로 전달합니다.
- 실제 일반 앱 로그인 경로(`/login`, `/api/auth/login`)를 감시 분류에 반영했습니다.
  일반 HTML 폼 성공은 브라우저에 303으로 게시판 이동을 안내하되, 감시 이벤트에는 로그인
  성공 결과인 200을 기록합니다. 실패는 401입니다. JSON 로그인 성공도 200입니다.
- localhost의 포트는 쿠키 저장 범위를 나누지 않으므로 일반/감시 쿠키 이름을 구분했습니다.
  운영자는 감시 화면에서 별도로 로그인합니다. 기존 일반 서비스의 운영자 계정 확인은
  공유 망의 `MONITOR_API_URL`을 사용합니다.

## 설치와 첫 실행 (PowerShell 또는 CMD)

Docker Desktop의 Linux 컨테이너 엔진이 필요합니다. 아래 명령은 이 README와 두 YAML이
있는 `mini-watch-day06` 폴더에서 실행합니다. Node/Python/DB를 PC에 따로 실행하지 않습니다.
Compose에 적힌 비밀번호와 SECRET_KEY는 이 로컬 실습만을 위한 공개 예제 값입니다.
기존 실제 `.env`와 계정 정보를 복사하지 않았습니다.

```powershell
docker network create m5d1-events
docker compose -f compose-general.yaml config --quiet
docker compose -f compose-monitor.yaml config --quiet
docker compose -f compose-monitor.yaml up -d --build
curl.exe -f http://localhost:8082/api/auth/me
```

공유 망이 이미 있다면 생성 명령을 반복하지 않습니다. `auth/me`가 HTTP 200과
`user`, `csrf_token` JSON을 반환할 때까지 기다립니다. 실패하면 아래 로그를 확인합니다.
감시 API가 준비된 후에 일반 서비스를 실행합니다. 기록 전송은 재전송 큐가 없으므로
감시 서비스가 준비되기 전의 로그인 실험은 이후에 다시 수행해야 합니다.

```powershell
docker compose -f compose-general.yaml up -d --build
docker compose -f compose-general.yaml exec general-api python create_user.py
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
```

실습 계정은 일반 `student / Learn123!`, 감시 `operator / Learn123!`입니다.
스크립트는 이미 있는 계정을 덮어쓰지 않습니다. 비밀번호는 해시로 DB에 저장됩니다.
계정을 바꾸려면 실행 전에 `exec -e PRACTICE_USERNAME=... -e PRACTICE_PASSWORD=...`를 지정합니다.

- 일반 게시판: http://localhost:8081/ (로그인 → `/posts`)
- 감시 로그인 기록: http://localhost:8082/
- 감시 DB 메모: http://localhost:8082/notes

## 동작 확인과 자료 보존

1. 일반 화면에서 student의 틀린 비밀번호로 로그인하여 401을 확인합니다.
2. 올바른 비밀번호로 로그인하여 게시판을 엽니다.
3. 감시 화면에서 operator로 로그인하고 `기록 불러오기`를 누릅니다.
   `/login`의 `login_failure / 401`, `login_success / 200`을 각각 확인합니다.
4. 감시 메모 화면에서 제목 `Docker 점검`, 내용 `로그인 실패와 성공을 확인했다`를
   등록합니다. 새로고침한 뒤 다시 불러왔을 때 같은 메모가 보여야 합니다.
5. 아래 종료 명령으로 각각 종료합니다. 볼륨 삭제 옵션을 붙이지 않습니다.

```powershell
docker compose -f compose-general.yaml down
docker compose -f compose-monitor.yaml down
docker compose -f compose-monitor.yaml up -d
curl.exe -f http://localhost:8082/api/auth/me
docker compose -f compose-general.yaml up -d
```

다시 로그인해 저장한 기록과 메모를 확인합니다. PostgreSQL 16의 실제 저장 경로
`/var/lib/postgresql/data`에 각각 `m5d1-general_general-data`,
`m5d1-monitor_monitor-data` named volume이 연결되어 컨테이너 재생성에도 보존됩니다.
초기 SQL은 빈 볼륨의 첫 시작에서만 실행됩니다. DB 자료 폴더는 제출하지 않습니다.

## 서비스와 네트워크

| 서비스 | 참여 망 | PC 공개 포트 |
|---|---|---|
| general-gateway | general-web-net | 127.0.0.1:8081 → 80 |
| general-api | general-web-net, general-db-net, events | 없음 (내부 5000) |
| general-db | general-db-net | 없음 (내부 5432) |
| monitor-gateway | monitor-web-net | 127.0.0.1:8082 → 80 |
| monitor-web | monitor-web-net | 없음 (내부 3000) |
| monitor-api | monitor-web-net, monitor-db-net, events | 없음 (내부 5000) |
| monitor-db | monitor-db-net | 없음 (내부 5432) |

두 DB 망에는 `internal: true`를 지정했습니다. DB는 공유 망에 참여하지 않습니다.
`events`라는 YAML 이름만 같으면 Compose가 프로젝트 이름을 붙여 서로 다른 망을
만듭니다. 두 파일 모두 `external: true`, `name: m5d1-events`를 지정해야 이미 만든
같은 실제 망에 참여합니다. 공유 망에는 두 API만 참여합니다.
일반 API의 `MONITOR_URL`은 `http://monitor-api:5000/api/events`이며 DB_HOST는 각자
`general-db`, `monitor-db`입니다. 컨테이너 내부 localhost는 그 컨테이너 자신입니다.
다른 프로젝트를 depends_on으로 참조하지 않고 감시 준비를 확인한 후 일반을 시작합니다.

## 점검 명령과 확인 범위

```powershell
docker compose -f compose-general.yaml config --quiet
docker compose -f compose-monitor.yaml config --quiet
docker compose -f compose-general.yaml ps
docker compose -f compose-monitor.yaml ps
docker compose -f compose-general.yaml logs --tail 50 general-api
docker compose -f compose-monitor.yaml logs --tail 50 monitor-api monitor-web
docker network inspect m5d1-events
docker compose -f compose-general.yaml exec general-api getent hosts monitor-api
docker compose -f compose-general.yaml exec general-api python -c "import requests; r=requests.get('http://monitor-api:5000/api/auth/me'); print(r.status_code); r.raise_for_status()"
```

`config`는 구성 문법/참조, `ps`는 실행 상태와 DB healthy, `logs`는 초기화/요청 오류를
확인합니다. `inspect`에서는 두 API만 공유 망에 있는지 확인합니다. `getent`는 DNS
이름 조회만 확인하며 HTTP 수신·DB 저장을 보장하지 않습니다. 실제 HTTP 200은 앱이
응답하는지 확인하고, 일반 로그인 후 감시 기록 조회와 메모 저장/재조회는 DB까지
연결되는지 확인합니다. 자동 점검은 `verify_docker.py`로 제공합니다.

## 심화: 공유 망 분리와 복구

아래 PowerShell 명령은 실험을 원할 때만 실행합니다. 최종 제출 설정은 두 API의
공유 망 참여를 유지합니다.

```powershell
$generalApiId = docker compose -f compose-general.yaml ps -q general-api
docker network disconnect m5d1-events $generalApiId
docker compose -f compose-general.yaml exec general-api getent hosts monitor-api
docker network connect --alias general-api m5d1-events $generalApiId
docker compose -f compose-general.yaml exec general-api getent hosts monitor-api
```

분리 중에는 두 API 사이의 유일한 공통 망이 없어 감시 이름 조회/기록 전송이 실패합니다.
자기 DB/게시판 망은 유지되므로 일반 게시판은 실행될 수 있습니다. 복구 후 이름 조회를
확인하고 새 로그인 실패·성공을 만들어 기록 전달을 확인합니다. 누락된 과거 요청은
자동 재전송하지 않습니다.

## 심화: restart와 rebuild

두 Flask Dockerfile은 `COPY . .`로 소스를 이미지에 넣고 Compose는 앱 소스를 bind mount하지
않습니다. 따라서 호스트의 Python 파일 수정 후 `restart`만 하면 이전 이미지 코드가
다시 실행됩니다. 변경 반영은 다음 명령을 사용합니다. DB named volume은 유지됩니다.

```powershell
docker compose -f compose-general.yaml up -d --build general-api
docker compose -f compose-monitor.yaml up -d --build monitor-api monitor-web
```

Next.js도 Docker 빌드 중 `npm ci`와 `npm run build`를 실행하고 standalone `server.js`와
정적 파일을 최종 이미지에 복사하므로 소스 변경 후 재빌드해야 합니다.
gateway 설정은 읽기 전용 bind mount이므로 설정 변경 후 gateway를 재시작합니다.

## 심화: DB 망 분리

```powershell
docker compose -f compose-general.yaml exec general-api getent hosts general-db
docker compose -f compose-general.yaml exec general-api getent hosts monitor-db
```

자기 DB는 공통 general-db-net을 통해 조회됩니다. monitor-db는 monitor-db-net에만 참여해
일반 API에서는 조회되지 않습니다. DNS 성공은 주소를 찾은 단계이며 DB 접속 인증은
계정·비밀번호·DB 이름이 맞는 단계, SQL 실행은 테이블·열·권한까지 맞는 별도 단계입니다.
공유 망에 DB를 넣거나 공개 포트를 추가하여 우회하지 않습니다.

공식 참고: [Compose 네트워크](https://docs.docker.com/compose/how-tos/networking/),
[DB 준비 대기](https://docs.docker.com/compose/how-tos/startup-order/).

## Git 작업

Docker 적용 커밋 식별자와 검증 결과는 작업을 마친 뒤 아래에 기록합니다.
앱 소스/SQL/의존성 잠금 파일/Compose/Dockerfile/gateway/이 README를 함께 제출합니다.
실제 `.env`, node_modules, .next, 가상환경, 캐시, DB 자료는 Git과 Docker 빌드에서 제외합니다.
