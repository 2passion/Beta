# Beta Order --- Order-010 Local Core MVP Phase 1 Bootstrap

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-010
-   Project: Beta
-   Status: APPROVED
-   Order Type: MVP Implementation --- Phase 1 Bootstrap
-   Architecture: Harness-A-Architecture-v1.0.md / FROZEN
-   Terminology: Terminology.md / FROZEN
-   Write Owner: Codex
-   Reviewer: Claude Code
-   File Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

사용자가 D-MVP-001\~005와 조건 A/B를 승인했다. FROZEN Architecture를
변경하지 않고 첫 Vertical Slice인
`Task 계획 → 실행 → 독립 Validator → Gate → Evidence`의 최소 기반을
구현하고 자동 Test와 실제 합성 Run Evidence로 검증한다. Harness 전체
구현은 하지 않는다.

## 2. 승인된 Implementation Decision

### D-MVP-001

Python 3 표준 라이브러리 + JSON/JSONL + CLI. 외부 패키지와 SQLite 금지.
03_Tests는 합성 Test Fixture 전용이며 실제 운영 Task 위치는 미결정.

### D-MVP-002

Validator는 Executor와 별도 프로세스. 실제 결과와 고정 기준만 검사.
종료코드 0=PASS, 1=FAIL, 그 외/Timeout/예외=ERROR. Validator SHA-256을
계획 버전에 고정. 로직 변경은 새 계획 버전 + New Run.

### D-MVP-003

동일 Fingerprint + 새로운 변경 근거 없음이면 Blind Retry 차단. 숫자는
전역 Rule이 아닌 MVP Test Fixture 값. Test 4 초기값: 제품 New Run 계획
버전당 최대 3회, Validator ERROR 2회, Execution ERROR 2회. Evidence 후
조정 가능.

### D-MVP-004

USER-GATE 최소 사유: Write Scope 확대, 권한 확대, 필수 Validator/완료
기준 약화, 재시도 한도 초과, 전역/Core Rule 활성화. 그 외 범위 안 일상
작업은 질문하지 않는다. Approval은 Task ID/계획 버전/행위/범위에
연결하며 계획 버전 변경 시 자동 재사용 금지.

### D-MVP-005

단계 단위 Checkpoint Event + 단계 ID + 상태 Hash. Resume은 New Run.
Checkpoint만 믿지 않고 실제 Side Effect를 재검증한다.

### 조건 A

03_Tests = 합성 시험 입력. 04_Evidence = 실행/검증 Evidence. 실제 운영
Task 위치는 미결정.

### 조건 B

RUN / VALIDATION / APPROVAL / CHECKPOINT는 논리적으로 구별한다. MVP 물리
저장은 append-only Event JSONL의 type으로 통합 가능하나 논리 개념을
합치지 않는다.

## 3. Precondition

Architecture v1.0 FROZEN, Terminology FROZEN, Order-008 PASS, Order-009
READY WITH DECISIONS, 위 Decision User Approval,
02_Core/03_Tests/04_Evidence 현재 상태, 기존 Asset 검색을 확인한다.
다르면 BLOCK.

## 4. Reuse Before Create

Beta 내부 Asset/Script/Validator/Tool을 먼저 검색한다. B는 개념 참고만
가능하며 코드 복사, 구조 복제, 명칭 강제, 자동 Asset 승격 금지. B 코드
재사용 필요 시 중단하고 별도 라이선스 검토 후보로 보고한다.

## 5. Phase 1 Scope

구현: 1. Task Plan JSON 읽기/계약 검사 2. Task/Run/Event ID 3.
append-only Event JSONL 4. 결정적 Executor subprocess 5. 별도 프로세스
Validator 6. PASS/FAIL/ERROR 구별 7. Gate Decision 8. Evidence 파일 +
SHA-256 색인 9. 필수 Validator 불변식 10. One Task One Write Owner
불변식 11. CLI 합성 Task 1건 12. unittest 13. 실제 Evidence

미구현: Safe Parallel 실제 병렬, Fingerprint Recovery 전체, Prevention
재사용, USER-GATE 승인 Workflow, Resume 전체,
Agent/Generator/Skill/Hook, Plugin/Adapter, EXE/PWA, SQLite, 실제 운영
Task.

## 6. 최소 파일 구조

02_Core/beta_core/: **init**.py, model.py, event_store.py, executor.py,
validator_runner.py, gate.py, cli.py 03_Tests/fixtures/:
task_phase1.json, executor_success.py, validator_success.py,
validator_fail.py 03_Tests/test_phase1.py 04_Evidence/phase1/: 실행 시
Evidence

별도 Router/Scheduler/Caller/Gate 프로그램을 만들지 않고 필요한 책임은
함수/모듈 수준으로 유지한다.

## 7. 최소 Task Plan

필드: task_id, plan_version, order_id, write_owner, write_scope\[\],
shared_resources\[\], depends_on\[\], steps\[\], executor(path,sha256),
required_validators[](validator_id,path,sha256,criteria),
completion_criteria, permissions. required_validators가 비면 실행 전
BLOCK. Write Owner가 정확히 1명이 아니면 실행 전 BLOCK.

## 8. Event JSONL

append-only. 공통 필드:
event_id,type,task_id,run_id,plan_version,actor_role,time,payload. 최소
type: RUN_STARTED, RUN_COMPLETED, EXECUTION_ERROR, VALIDATION_STARTED,
VALIDATION_RESULT, GATE_DECISION, EVIDENCE_RECORDED, BLOCKED. 기존 Event
수정/삭제 금지.

## 9. Evidence

최소: Evidence ID/파일명, Run ID, Task ID, plan_version, 경로, SHA-256,
생성시각, Validation 결과. Evidence 본체와 색인 구별.

## 10. Gate

Phase 1 판정: PROCEED / BLOCK. PROCEED = Execution 정상 +
required_validators 전부 PASS + Evidence 기록 성공. Validator FAIL =
BLOCK. Validator ERROR = BLOCK이며 제품 FAIL과 구별. USER-GATE 실제
처리는 이번 Phase에서 미구현.

## 11. 자동 Test

unittest 최소 10개: 1. 정상 Task → Validator PASS → PROCEED 2.
required_validators 빈 목록 → Run 전 BLOCK 3. Validator FAIL → BLOCK 4.
Validator ERROR → ERROR + BLOCK 5. Validator Hash 불일치 → 실행 전 BLOCK
6. Executor Hash 불일치 → 실행 전 BLOCK 7. Write Owner 위반 → 실행 전
BLOCK 8. Event JSONL append-only 순서/필수 필드 9. Evidence SHA-256 일치
10. 실패 Run을 PASS로 덮어쓰지 않음

Test 실행 자체 실패는 ERROR.

## 12. 실제 Validation Run

자동 Test PASS 후 task_phase1.json을 CLI로 실제 1회 실행한다. 새 Run ID,
Executor, 별도 Validator, Gate, Evidence를 생성한다. mock만으로 대체
금지.

## 13. Validation 상태

NOT_RUN / RUNNING / PASS / FAIL / ERROR. FAIL과 ERROR를 합치지 않는다.

## 14. Security / Scope

승인된 Fixture 경로만 subprocess 실행. 네트워크/API/Agent 호출 금지.
shell=True 금지. 사용자 홈/Downloads/Reference 수정 금지.

## 15. Architecture Delta

FROZEN Architecture 변경 필요 시 구현 편의로 수정하지 않고
ARCHITECTURE-DELTA로 보고하며 해당 구현을 중단한다.

## 16. Index / History

구현과 Validation 모두 PASS 후에만 최소 갱신. Beta-Index: Order-009
완료, D-MVP-001\~005+A/B 승인, Order-010 결과, Now/Next. Order-History:
Order-009 READY WITH DECISIONS, User Approval APPROVED, Order-010 실제
결과. Architecture/Terminology 불변.

## 17. 하지 말 것

Architecture/Terminology 수정, FROZEN 해제, SQLite, 외부 패키지,
Agent/Skill/Hook, Safe Parallel 완성, Prevention/Rule 자동 활성화,
USER-GATE/Resume 전체 구현, EXE/PWA, Plugin/Adapter, B 코드 복사, 실제
운영 데이터, 실제 운영 Task 위치 결정, Git 초기화.

## 18. Validation Checklist

### Precondition

-   [ ] FROZEN Architecture/Terminology
-   [ ] Order-009 확인
-   [ ] User Approval
-   [ ] Reuse Search

### Code

-   [ ] Python 표준 라이브러리만
-   [ ] 최소 구조
-   [ ] 논리 데이터 구분 유지
-   [ ] append-only Event JSONL
-   [ ] 별도 Validator
-   [ ] Validator/Executor Hash 고정
-   [ ] 빈 Validator 차단
-   [ ] One Task One Write Owner

### Test

-   [ ] unittest 전체 PASS
-   [ ] 최소 10개 시나리오
-   [ ] FAIL/ERROR 구별
-   [ ] FAIL Run 보존

### Runtime Evidence

-   [ ] 실제 CLI Run
-   [ ] Run ID / plan_version
-   [ ] Validation
-   [ ] Gate
-   [ ] Evidence + SHA-256
-   [ ] Event Log

### Scope

-   [ ] Architecture/Terminology/Reference 불변
-   [ ] 외부 패키지/네트워크/Agent 없음
-   [ ] 실제 운영 데이터 없음
-   [ ] Scope 밖 변경 없음

하나라도 실패하면 PASS 금지. 검사 자체 실패는 ERROR.

## 19. 결과 보고

# Order-010 Local Core MVP Phase 1 결과

-   현재 상태: PASS / FAIL / ERROR / BLOCKED
-   승인 Decision 적용 확인
-   Reuse Search
-   생성/수정 파일
-   자동 Test 수와 결과
-   실제 Run: Task ID, plan_version, Run ID, Execution, Validation,
    Gate, Evidence, SHA-256
-   Architecture Delta
-   Scope 위반
-   Evidence 경로/Hash
-   Done / Now / Next
-   사용자 승인 필요 여부

PASS Next: Claude Code READ-ONLY Phase 1 Review → 이후 MVP Test 구현
Order. FAIL/ERROR Next: Root Cause 분석 → Blind Retry 금지 → 수정 Order
후보.

## 20. 종료 조건

구현, unittest, 실제 합성 Run, Evidence, Index/History 최소 갱신 후
종료. PASS해도 Claude 호출, Phase 2, 전체 MVP Test, EXE/PWA,
Plugin/Adapter를 자동 시작하지 않는다.

=== ORDER END ===
