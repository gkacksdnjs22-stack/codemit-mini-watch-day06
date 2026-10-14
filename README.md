# Mini Watch Day3 — 실제 요청 로그와 근거 화면

[과제](https://classroom.codemit.kr/classes/5/problems/55/submit) · 2026-10-14

## 1. 구성·개념 설명

본인이 Day06/Day2에 완성한 일반 Flask·감시 Flask·Next.js 프로젝트를 같은 폴더에서
이어 구현했다. 강사의 m5d3-start를 다시 복제하거나 개정 전 m5d3-solution으로
덮어쓰지 않았다. 기존 계정·게시글·메모·SQL·두 Compose 이름·볼륨을 보존한다.
이전 과제 설명은 [Day2 기록](docs/day2-readme.md)과 [배포 계획](deployment-plan.md)에 있다.

### 변경 파일과 수업 파일 대응

| 파일·함수 | 연결과 역할 |
|---|---|
| general/routes/auth.py:home | 로그인한 일반 회원의 GET / 에 게시판 목록을 직접 200으로 응답. 기존 /board·CRUD·가입·로그인 유지 |
| general/app.py → register_request_logging | request_logging.py가 app.after_request(record_request)로 응답 뒤 기록 함수를 연결 |
| general/request_logging.py:record_request | 실제 방법·경로·응답 상태를 기록. print의 JSON 표준 출력과 requests.post의 감시 전송은 별개 |
| monitor/backend/routes/events.py:receive_event | X-Event-Token 검증 후 event_rules.py:make_event 호출 |
| event_rules.py:make_event | GET / 200은 post_list, 없는 경로 404는 request_error. 기존 로그인 분류 유지 |
| repositories/events.py:create_event | http_events에 INSERT. 원본 ID는 identity, occurred_at은 DB DEFAULT NOW()로 수신·저장 시 생성 |
| repositories/events.py:latest_event_id/read_observation | 최대 ID와 고정한 기준시각 최근 60초의 원본 조회 |
| learning/capture_case.py:capture | 기존 일반 회원 로그인 후 로컬 목록 요청과 /training-missing 요청을 실제로 보내고 이번 DB 행을 읽음 |
| learning/normalize.py:normalize_event | 원본 딕셔너리 복사, 숫자 ID→http-원본ID, source=http_live, kind=원본 event_type |
| learning/http_rules.py:select_views | GET·경로 /·상태 200·kind post_list 네 조건을 모두 적용해 행 목록 반환 |
| learning/http_rules.py:find_following_errors | 선택한 마지막 조회 수신시각 뒤 0 < gap <= 30인 404만 전체 정규화 행에서 선택. 조회 없으면 [] |
| learning/support.py, lesson2.py~lesson5.py | 같은 learning/data/observation.json의 읽기·정규화·선택·기준 비교·문맥 분석 |
| learning/report.py:build_report | 같은 조회 목록에서 횟수와 조회 ID 계산. count >= threshold 판정과 records·evidence를 HTTP 카드 하나로 반환 |
| routes/analysis.py, monitor/backend/app.py | 로그인·CSRF·ID·기준·시간대·미래시각 검증, 실제 DB 행을 보고서로 전달 |
| AnalysisClient.js, app/analysis/page.js | 새 관찰·기준 입력·결과 조회·ID/수신시각/방법/경로/상태/종류/역할 표 |
| Next api/notes.js, app/api/[...path]/route.js | 분석 API 요청, 쿠키·CSRF·응답 전달. 서버 환경변수는 브라우저에 노출하지 않음 |
| SiteNav.js, Events.js, globals.css | 요청 분석 메뉴·반응형 결과 카드·새 기록 종류 표시 |
| compose-monitor.yaml | 학습 폴더의 읽기 전용 마운트, 로컬 일반 서비스 주소와 실습 회원 환경변수 |

일반 MONITOR_URL=http://monitor-api:5000/api/events는 전송 주소이며 양쪽 EVENT_TOKEN은
일치해야 한다. Next MONITOR_API_URL은 서버 전용이고 브라우저는 같은 출처 /api를 쓴다.
두 API만 기존 m5d1-events 공유 망에 참여한다. DB 망은 internal이며 DB 포트를 공개하지 않는다.
터미널 출력만으로 DB 저장 성공을 판단하지 않고 전송 경고와 실제 DB 행을 확인한다.

정규화는 원본 방법·경로·상태·수신시각과 404를 보존하고 원본을 덮어쓰지 않는다.
없는 사용자·IP를 만들어 넣지 않는다. http-123의 123은 원본 DB ID이다.
occurred_at은 요청 발생시각이 아니라 감시 DB 수신·저장시각이다.

조회 횟수와 조회 ID는 같은 select_views 목록에서 구한다. 뒤따른 404는 문맥 근거에만
붙인다. 통제한 12회 사례의 관찰값은 12, 근거는 조회 12+404 1=13행이다.
모든 실제 상황에서 무조건 13행을 만드는 것이 아니다.

새 관찰은 현재 최대 ID를 after_id로 저장하며 기존 행을 삭제하지 않는다.
첫 결과 요청에서 reference_time을 정하고 SQL은 id > after_id와
reference_time-60초 <= occurred_at <= reference_time을 함께 적용한다.
시작 뒤 60초 자동 수집 타이머가 아니다. 기준만 10→20으로 바꾸면 화면이 기존
after_id·reference_time을 재사용한다. 새 관찰 성공 때 이전 결과와 기준시각을 초기화한다.

같은 서비스의 시간상 뒤따른 기록이라는 범위를 넘지 않는다. 같은 사용자·IP·인과관계·
침해를 확정할 수 없고 기준 미해당은 정상 입증이 아니다. PCAP·IOC 예제는 HTTP 근거에 섞지 않는다.

## 2. 실행 방법

다음은 두 Compose 파일이 있는 기존 프로젝트 루트의 Windows CMD 명령이다.
Docker Desktop Linux 엔진과 기존 계정·볼륨을 그대로 사용한다. 공유 망이 없을 때만
docker network create m5d1-events를 먼저 실행한다.

```cmd
docker compose -f compose-general.yaml config --quiet
docker compose -f compose-monitor.yaml config --quiet
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-general.yaml up -d --build
curl.exe -f http://localhost:8082/api/auth/me
curl.exe -f http://localhost:8081/health
```

계정이 없는 경우에만 다음 명령으로 입력받아 준비한다. 기존 계정은 덮어쓰지 않는다.
일반 회원은 일반 DB, 운영자는 감시 DB에 저장한다.

```cmd
docker compose -f compose-general.yaml exec general-api python create_user.py
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
```

Compose의 DB 비밀번호·키·토큰은 이전 수업의 로컬 전용 공개 예시다.
실제 운영에 안전한 값으로 간주하지 않으며 실제 운영 비밀값은 제출하지 않는다.
일반 게시판은 http://localhost:8081/, 감시 로그인은 http://localhost:8082/,
요청 분석은 http://localhost:8082/analysis, 기존 메모는 /notes이다.
화면은 운영자로 로그인하고 capture는 기존 일반 회원을 사용한다.

처음 Python 앱이나 Compose를 바꾸면 위 up -d --build를 실행한다.
그 뒤 learning 폴더는 읽기 전용 마운트로 읽으므로 학습 함수 변경은 재시작으로 적용한다.
routes 등의 변경은 API 재빌드가 필요하다. Next 변경은 web 재빌드가 필요하다.

```cmd
docker compose -f compose-monitor.yaml restart monitor-api
docker compose -f compose-monitor.yaml up -d --build monitor-web
docker compose -f compose-monitor.yaml restart monitor-gateway
```

화면을 새로고침한다. 캡처 계정을 PC 환경변수에 입력하고 exec에는 이름만 전달한다.
set /p는 입력을 화면에 표시하므로 로컬에서 사용하고 종료 후 CMD를 닫는다.
README에는 실제 비밀번호를 넣지 않았다.

```cmd
set /p TRAINING_USERNAME=기존 일반 회원 아이디:
set /p TRAINING_PASSWORD=기존 일반 회원 비밀번호:
if not exist monitor\backend\learning\data mkdir monitor\backend\learning\data
```

GENERAL_SERVICE_URL은 공유 망의 http://general-api:5000이며 capture는 로컬 HTTP만 허용한다.
capture가 로그인 후 기록한 최대 ID 이후의 행을 읽으므로 로그인 기록은 파일 사례에서 제외한다.
화면 분석도 로그인 행을 조회 횟수나 뒤따른 404 근거에 포함하지 않는다.

### 4회 사례와 같은 파일 실습

```cmd
docker compose -f compose-monitor.yaml exec -T -e TRAINING_USERNAME -e TRAINING_PASSWORD monitor-api python -m learning.capture_case 4 > monitor\backend\learning\data\observation-next.json && move /Y monitor\backend\learning\data\observation-next.json monitor\backend\learning\data\observation.json
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson2
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson3
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson4
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson5
```

각 명령의 성공을 확인하고 다음으로 진행한다. -T는 터미널 장식을 없애고 >는 PC의
임시 파일에 JSON을 저장한다. && move /Y는 캡처 성공 때만 observation.json을 교체한다.
컨테이너의 읽기 전용 폴더에 직접 쓰지 않는다. 실패한 캡처는 종료 코드 1과 stderr를
반환한다. 이전 파일이 남아 있어도 이번 원본으로 주장하지 않는다.

### 12회 사례와 10·20 비교

1. 다른 탭에서 일반 요청을 멈춘다. /analysis에서 기준 10으로 **새 관찰 시작**.
2. 아래 capture 12를 실행한다.
3. 성공했다면 요청을 만든 뒤 **1분 안에 결과 불러오기**, 근거 보기를 펼친다.
4. 새 관찰을 누르지 않고 기준만 **20**으로 바꿔 조회한다. 관찰값·시각·근거 ID는 같고
   판정만 바뀌어야 한다. 기준 **10**으로 복구해 다시 조회한다.
5. **새 관찰 시작** 후 일반 요청 없이 조회한다. 이전 DB 행은 남지만 새 ID 경계 때문에
   관찰값 0·해당 근거 없음이다.

```cmd
docker compose -f compose-monitor.yaml exec -T -e TRAINING_USERNAME -e TRAINING_PASSWORD monitor-api python -m learning.capture_case 12 > monitor\backend\learning\data\observation-next.json && move /Y monitor\backend\learning\data\observation-next.json monitor\backend\learning\data\observation.json
```

파일 실습은 observation.json, 화면은 감시 DB를 읽는다. 이 절차에서는 같은 실제 요청으로
만든 원본을 사용한다. capture 오류·다른 개수·60초 경과 때는 다음을 점검하고
**새 관찰 → 캡처 → 즉시 첫 결과**부터 다시 실행한다. 숫자 수정·직접 INSERT·DB 삭제로 맞추지 않는다.

```cmd
docker compose -f compose-general.yaml logs --tail 20 general-api
docker compose -f compose-monitor.yaml logs --tail 20 monitor-api
docker compose -f compose-monitor.yaml exec monitor-db psql -U monitor_user -d monitor_db -c "SELECT id, occurred_at, method, path, status_code, event_type FROM http_events ORDER BY id DESC LIMIT 20;"
```

SELECT로 근거 ID 원본과 이전 기록 보존을 확인한다. down -v·volume 삭제·DB 초기화는 하지 않는다.

## 3. 예상 결과와 실제 확인 상태

| 통제한 사례 | 예상 관찰값·판정 | 원본/근거 |
|---|---|---|
| 4회+404, 기준 10 | 4·기준 미해당(False) | 원본·정규화 5행, 선택 조회 4행 |
| 12회+404, 기준 10 | 12·검토 후보 | 조회 12+문맥 1=근거 13행 |
| 같은 구간, 기준 20 | 12·기준 미해당 | 같은 기준시각·원본 ID·13행 |
| 같은 구간, 10 복구 | 12·검토 후보 | 비교 조건만 바뀜 |
| 새 관찰 뒤 일반 요청 없음 | 0·기준 미해당 | 해당 근거 없음, 기존 DB 행 유지 |

### 실제 확인 (2026-10-14)

- 분석 테스트 5개 통과: 네 조회 조건·원본 보존·없는 사용자/IP 배제·0/30/30.001초
  경계·조회 0·>= 경계·같은 근거·로그인·CSRF·입력 검증.
- 기존 Next 프록시 테스트 3개 통과.
- Next production 빌드 및 두 Compose 문법 검사 통과.
- 기존 Flask 회귀 테스트 일반·감시 각 6개, 총 12개 통과.
- 기존 Docker 볼륨으로 세 이미지 재빌드·일반/감시 gateway 실행 통과.
- 실제 4회 캡처: 원본 5행·정규화 5행·조회 선택 4행 확인.
- 실제 12회 캡처: 원본 13행. 파일의 같은 자료 기준 10은 True, 20은 False,
  양쪽 관찰값 12·근거 13행 확인. lesson5에서 조회 12·뒤따른 404 1행 확인.
- 브라우저 운영자 로그인·새 관찰·결과 불러오기·근거 표 확인:
  기준 10에서 12회·검토 후보·13행, 기준 20에서 12회·기준 미해당·13행.
  두 결과의 기준시각·시작 ID·근거 표의 모든 셀이 같음을 비교했다. 10 복구도 통과.
- 새 관찰 뒤 일반 요청 없이 조회: 0회·기준 미해당·0행 확인. DB 직접 조회에서
  새 관찰 전 74행과 이전 근거 13행이 삭제되지 않고 남아 있음을 확인했다.
- 실제 10회 경계: 10회·검토 후보·11행 확인 후 새 관찰과 capture 12로 기본 사례 복구.
- 새 클라우드 배포는 하지 않았다.

### 선택: 기준 경계

새 관찰에서 capture 명령의 횟수를 **10**으로 바꿔 실행하고 즉시 기준 10으로 조회한다.
10 >= 10이라 검토 후보이고 근거는 조회 10+404 1=11행이다.
그 뒤 새 관찰에서 capture **12**를 실행해 기본 사례로 돌아간다.
단위 테스트의 확인과 실제 요청 실행 확인은 구분한다.

### 선택: AI 후보 코드 검토

실제 로그·비밀값을 외부 AI/API에 보내지 않고 규칙 요구만으로 다음 순수 함수 후보를 검토했다.

```python
# 거절한 후보
def candidate(events, threshold):
    chosen = [e for e in events if e["path"] == "/" or e["status_code"] == 404]
    return len(chosen) > threshold, [e["id"] for e in chosen]
```

이 후보는 GET·200·post_list 조건을 빠뜨리고 404를 횟수에 더하며, 마지막 조회 뒤
30초 범위를 적용하지 않고 >라 정확히 10회 경계도 틀린다. 따라서 거절했다.
채택한 http_rules.py/report.py 핵심은 다음과 같다.

```python
views = select_views(events)  # GET, /, 200, post_list
errors = find_following_errors(events, views)  # 조회 없으면 [], 0 < gap <= 30
count = len(views)
matched = count >= threshold
view_ids = [event["id"] for event in views]
records = views + errors
evidence = [event["id"] for event in records]
```

같은 목록으로 횟수·근거를 구하며 404는 문맥으로만 합친다. API/화면도 ID와 시각을 보존한다.
PCAP·IOC 선택 실습은 구현하지 않았다.

### 제출물

일반·감시 소스, Dockerfile·Compose·gateway 설정·requirements·package.json·
package-lock.json·기존 SQL·README를 저장소 기본 브랜치로 제출한다.
실제 .env·운영 비밀번호·키·토큰·원본 로그·DB·observation.json·node_modules·
.next·가상환경·캐시는 제외한다. 원본이나 스크린샷·새 검사 파일은 필수 제출물이 아니다.
