# Beta Order --- Order-017 MVP Test 2 Ownership + Common Test Harness Implementation

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-017
-   Project: Beta
-   Status: APPROVED
-   Order Type: MVP Test Implementation
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Status: FROZEN
-   Terminology: `Terminology.md`
-   Terminology Status: FROZEN
-   Baseline: Local Core MVP Phase 1 CLOSED
-   Target: MVP Test 2 --- Ownership
-   Write Owner: Codex
-   Reviewer: Claude Code
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Phase 1의 기존 Local Core를 재사용하여 첫 공식 MVP Test 판정 구조를
만들고, MVP Test 2 --- Ownership을 실제 Runtime Evidence로 검증한다.

이번 Order의 두 목표:

1.  이후 MVP Test 1\~7이 재사용할 수 있는 최소 Common Test Harness 검증
2.  MVP Test 2 Ownership 공식 판정 Run 생성

이번 Order는 Ownership 이외의 MVP Test를 구현하지 않는다.

## 2. 근거

Order-015: - PASS - shared timeout RESOLVED - Phase 1 Review/Fix Loop
종료 가능

Order-016: - READY - 다음 구현 권장: Common Test Harness + MVP Test 2
Ownership - Core 변경 없이 기존 Phase 1 기능 대부분 재사용 가능 - 사용자
승인 불필요 - Architecture Delta NONE

## 3. Precondition

실행 전 확인:

-   Architecture v1.0 FROZEN
-   Terminology FROZEN
-   Order-015 PASS
-   Phase 1 CLOSED
-   Order-016 READY
-   Phase 2 미착수
-   기존 Phase 1 Core/Test/Evidence 보존
-   Reuse Before Create 검색 수행

전제가 다르면 BLOCK한다.

## 4. 상태 View Drift 선행 동기화

Order-016에서 확인된 View Drift를 이번 Write Owner 작업에서 먼저 최소
수정한다.

### Beta-Index

반영: - Order-015 = PASS - shared timeout = RESOLVED - Local Core MVP
Phase 1 Review/Fix Loop = CLOSED - Order-016 = READY - Now = MVP Test 2
Ownership + Common Test Harness 구현 - Next = Order-017 결과 검토

### Order-History

반영: - Order-015 PASS - Order-016 READY - Phase 1 CLOSED

과거 Order 결과를 변경하지 않는다.

이 동기화는 Runtime Evidence나 Architecture를 변경하지 않는다.

## 5. Reuse Before Create

새 코드를 만들기 전에 기존 Phase 1을 재사용한다.

반드시 재사용 검토: - `run_task` - `validate_contract` - append-only
Event Store - 별도 Validator subprocess - Gate - Evidence + SHA-256
index - plan version / hash 불변성 - write_owner 검사

Common Test Harness를 새로운 거대한 Framework로 만들지 않는다.

가능하면 Test Fixture + Validator + 기존 `run_task` 조합으로 구현한다.

## 6. Common Test Harness 최소 계약

목적: MVP Test 자체도 하나의 검증 가능한 Task로 실행하여 공식 판정
Evidence를 남긴다.

최소 흐름:

``` text
MVP Test Plan
   ↓
Scenario Executor
   ↓
내부 합성 Task / Run 실행
   ↓
Scenario Result
   └─ 내부 events.jsonl 경로 등
   ↓
독립 MVP Test Validator
   ↓
PASS / FAIL / ERROR
   ↓
기존 Gate
   ↓
MVP Test Evidence
```

중요: - MVP Test Validator는 Scenario Executor와 별도 프로세스 -
Scenario Executor의 "PASS 주장"을 신뢰하지 않음 - Validator가 내부
Event/Run 폴더를 직접 읽어 판정 - Phase 1의 Gate/Evidence를 재사용 - 새
Test 판정 DB 금지 - 새 Dashboard/STATE SSOT 금지

## 7. MVP Test 판정 추적 계약

공식 MVP Test 판정에는 최소 다음이 연결되어야 한다.

-   `mvp_test_id`
-   `mvp_test_name`
-   Test Plan ID
-   Test Plan Version
-   판정 Run ID
-   Validator ID
-   Validation Status
-   Gate Decision
-   Evidence 위치
-   Evidence SHA-256
-   Scenario 내부 Run / Event 위치

가능하면 기존 Event payload / Evidence 본문에 넣고 새 Entity를 만들지
않는다.

## 8. MVP Test 2 --- Ownership 목적

FROZEN Architecture의 질문:

> 하나의 Task에 하나의 Write Owner가 유지되는가?

공식 PASS는 단순 Unit Test가 아니라 실제 합성 Scenario와 독립 Validator
Evidence로 증명한다.

Scope 밖 쓰기 검사는 이번 Test에 포함하지 않는다. 이는 MVP Test 3 Safe
Parallel에서 다룬다.

## 9. Ownership Scenario

최소 세 Scenario를 포함한다.

### Scenario A --- 정상 단일 Owner

계획: - write_owner = `Codex` - 정상 실행

기대: - Run 생성 - `RUN_STARTED`에 Owner 1명 - Execution/Validation
정상 - Evidence 존재

### Scenario B --- 다중 Owner 위반

계획: - 두 Owner를 표현하는 금지 값 - 예: `Codex, Claude Code`

기대: - 실행 전 BLOCK - `BLOCKED` Event - `RUN_STARTED` 없음 - Run
디렉터리 없음 - Executor 실행 흔적 없음

### Scenario C --- Owner 변경

기준 계획: - plan_version A - owner = `Codex`

변경 시도 1: - 같은 plan_version - owner = `Claude-Code`

기대: - 같은 `(task_id, plan_version)` Plan Hash 불변성 때문에 BLOCK -
기존 Run의 Owner 불변

변경 시도 2: - 새 plan_version - owner = `Claude-Code` -
change_reason_ref 기록

기대: - New Run 허용 - 새 Run의 Owner = Claude-Code - 이전 Codex Run
보존

## 10. Scenario 저장 위치

조건 A 유지:

-   Scenario 입력: `03_Tests\fixtures\...`
-   Scenario의 격리 Runtime 결과: `04_Evidence` 아래 MVP Test 2 전용
    위치 또는 실행 시 생성되는 명확한 하위 경로
-   공식 판정 Evidence: `04_Evidence` 아래

실제 운영 Task 저장 위치를 결정하지 않는다.

Scenario 내부 Runtime과 공식 판정 Run을 경로/ID로 명확히 구별한다.

## 11. Ownership Validator

별도 프로세스 Validator는 Scenario Executor가 만든 요약 문자열을 그대로
신뢰하지 않는다.

직접 확인:

-   내부 `events.jsonl`
-   내부 Run 디렉터리
-   Plan Version
-   Owner
-   BLOCKED Event
-   RUN_STARTED 존재/부재
-   과거 Run 보존
-   새 Version의 새 Run

PASS 조건:

1.  정상 계획은 Owner 1명으로 실행됨
2.  다중 Owner 계획은 Run 전에 BLOCK
3.  위반 계획에 Run 폴더가 없음
4.  같은 Version에서 Owner 변경은 BLOCK
5.  새 Version에서 Owner 변경은 New Run으로 허용
6.  이전 Run의 Owner 기록은 불변
7.  Scenario Evidence가 공식 판정 Evidence에 연결됨

하나라도 실패하면 MVP Test 2 PASS 금지.

## 12. 기존 Unit Test 회귀

기존 Phase 1 17개 Test는 계속 PASS해야 한다.

새 Harness/Ownership Test를 추가할 수 있다.

보고: - 기존 Test 수 - 신규 Test 수 - 총 Test 수 - PASS / FAIL / ERROR

기존 Test를 삭제하거나 의미를 약화하지 않는다.

## 13. 공식 MVP Test 2 판정 Run

Unit Test 전체 PASS 후 실제 공식 판정 Run을 수행한다.

공식 Test: - ID: `MVP-TEST-2` - Name: `Ownership`

판정: - Validation PASS - Gate PROCEED 이어야 공식 PASS 후보.

공식 Evidence에는 내부 Scenario Evidence 경로와 해시를 연결한다.

## 14. MVP Test 상태

이번 Order에서 다음 상태를 구별한다.

-   NOT_RUN
-   RUNNING
-   PASS
-   FAIL
-   ERROR

MVP Test 2만 판정한다.

MVP Test 1, 3, 4, 5, 6, 7은 계속 NOT_RUN / NOT_VERIFIED 상태다.

## 15. 실패 처리

Scenario 또는 공식 Validator가 실패하면:

-   MVP Test 2를 PASS로 기록하지 않는다.
-   FAIL / ERROR를 구별한다.
-   실패 Evidence 보존
-   Blind Retry 금지
-   Root Cause를 보고
-   자동 Fix 금지

## 16. Security / Scope

유지: - Python 표준 라이브러리만 - JSON/JSONL - shell=True 금지 -
네트워크/API/Agent 없음 - SQLite 없음 - Reference 쓰기 없음 - 실제 운영
데이터 없음

Scenario subprocess는 승인된 Fixture/Core 범위만 사용한다.

## 17. 이번 Order에서 하지 말 것

-   MVP Test 1 Reuse 구현
-   MVP Test 3 Safe Parallel 구현
-   MVP Test 4 Bottleneck 구현
-   MVP Test 5 Prevention 구현
-   MVP Test 6 User Gate 구현
-   MVP Test 7 Resume 구현
-   Asset Registry 생성
-   Fingerprint 구현
-   USER-GATE 구현
-   WAIT 구현
-   Scheduler 구현
-   Agent/Skill/Hook
-   Plugin/Adapter
-   Architecture/Terminology 수정
-   Phase 1 과거 Evidence 수정
-   실제 운영 Task 위치 결정
-   EXE/PWA

## 18. Architecture Delta

구현 중 FROZEN Architecture 변경 필요성이 발견되면 임의 수정하지 않는다.

`ARCHITECTURE-DELTA`로 보고하고 해당 부분 구현을 중단한다.

기본 예상: `NONE`

## 19. Index / History

구현 + Test + 공식 MVP Test 2 판정이 완료된 뒤에만 최소 갱신한다.

Beta-Index: - Order-015 PASS - Phase 1 CLOSED - Order-016 READY -
Order-017 실제 결과 - MVP Test 2 상태 - Now / Next

Order-History: - Order-015 PASS - Order-016 READY - Order-017 실제 결과

MVP Test 1,3,4,5,6,7을 PASS로 표시하지 않는다.

## 20. Validation Checklist

### View Sync

-   [ ] Order-015 PASS 반영
-   [ ] Phase 1 CLOSED 반영
-   [ ] Order-016 READY 반영

### Harness

-   [ ] Scenario Executor와 MVP Test Validator 분리
-   [ ] Validator가 내부 Event를 직접 읽음
-   [ ] 기존 Gate/Evidence 재사용
-   [ ] 공식 Test 판정 추적 필드 연결
-   [ ] 새 DB/SSOT 없음

### Ownership

-   [ ] 정상 단일 Owner Run
-   [ ] 다중 Owner 실행 전 BLOCK
-   [ ] 위반 계획 RUN_STARTED 없음
-   [ ] 위반 계획 Run 폴더 없음
-   [ ] 같은 Version Owner 변경 BLOCK
-   [ ] 새 Version Owner 변경 New Run
-   [ ] 이전 Owner Run 보존

### Regression

-   [ ] 기존 Phase 1 17 Test PASS
-   [ ] 신규 Test PASS
-   [ ] FAIL/ERROR 구별

### Official Evidence

-   [ ] MVP-TEST-2
-   [ ] Ownership
-   [ ] 공식 판정 Run ID
-   [ ] Validation PASS
-   [ ] Gate PROCEED
-   [ ] Evidence + SHA-256
-   [ ] 내부 Scenario Evidence 연결

### Scope

-   [ ] Architecture/Terminology 불변
-   [ ] Reference 불변
-   [ ] 다른 MVP Test 미구현
-   [ ] Phase 1 과거 Evidence 불변
-   [ ] 외부 패키지/네트워크/Agent 없음

필수 항목 하나라도 실패하면 MVP Test 2 PASS 금지. 검사 자체 실패는
ERROR.

## 21. 결과 보고 형식

# Order-017 MVP Test 2 Ownership 결과

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### View Sync

Index / History 상태.

### Common Test Harness

구현 구조와 재사용 항목.

### 생성/수정 파일

목록.

### Unit / Regression Test

-   기존 Test
-   신규 Test
-   총 Test
-   PASS / FAIL / ERROR

### Ownership Scenario

-   A 정상 Owner
-   B 다중 Owner
-   C 같은 Version Owner 변경
-   C 새 Version Owner 변경

각각 Run/Event/Folder 결과.

### 공식 MVP Test 2 판정

-   Test ID
-   Test Name
-   Test Plan Version
-   판정 Run ID
-   Validation
-   Gate
-   Evidence
-   SHA-256
-   Scenario Evidence 연결

### MVP Test 상태

-   Test 1 Reuse: NOT VERIFIED
-   Test 2 Ownership: PASS / FAIL / ERROR
-   Test 3 Safe Parallel: NOT VERIFIED
-   Test 4 Bottleneck: NOT VERIFIED
-   Test 5 Prevention: NOT VERIFIED
-   Test 6 User Gate: NOT VERIFIED
-   Test 7 Resume: NOT VERIFIED

### Architecture Delta

NONE 또는 상세.

### Scope

위반 여부.

### Done

Common Test Harness + MVP Test 2 공식 판정.

### Now

결과에 따른 현재 상태.

### Next

PASS: → Claude Code READ-ONLY MVP Test 2 Independent Review → PASS이면
MVP Test 1 Reuse 구현 Order

FAIL/ERROR: → Root Cause → Fix 근거 → New Run / Revalidation

### 사용자 승인 필요

NO

## 22. 종료 조건

View Sync, Harness, Ownership Scenario, 전체 Test, 공식 MVP Test 2 판정,
Evidence, Index/History 갱신 후 종료한다.

PASS해도 자동 시작 금지: - Claude Code 호출 - MVP Test 1 - 다른 MVP
Test - Architecture 변경 - Phase 2 - 제품화

결과를 ChatGPT Project Beta에 전달한다.

=== ORDER END ===
