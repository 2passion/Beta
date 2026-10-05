# Beta Order --- Order-012 Local Core MVP Phase 1 Important Fix

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-012
-   Project: Beta
-   Status: APPROVED
-   Order Type: MVP Phase 1 Important Fix + Revalidation
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Status: FROZEN
-   Terminology: `Terminology.md`
-   Terminology Status: FROZEN
-   Source Review: Order-011 Phase 1 Independent Review
-   Write Owner: Codex
-   Reviewer: Claude Code
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Order-011 Independent Review에서 확인된 IMPORTANT 3건만 최소 수정한다.

Order-010 PASS는 과거 사실로 보존한다. Order-011
`PASS WITH IMPORTANT FIX`도 그대로 보존한다.

수정 후 기존 Evidence를 덮어쓰지 않고 새로운 Test와 New Run으로
재검증한다.

이번 Order의 수정 범위:

1.  Task Plan Version 불변성 및 변경 근거 추적
2.  Fail-open 경로 Test 보강
3.  Write Owner 단일 식별자 검사 강화

Architecture 변경, Phase 2, 새로운 MVP 기능 추가는 하지 않는다.

## 2. 근거

Order-011 판정: `PASS WITH IMPORTANT FIX`

Blocker: `NONE`

IMPORTANT: - Review-Important-001 --- 계획 버전 불변성과 변경 근거
부족 - Review-Important-002 --- Fail-open 경로 Test 부족 -
Review-Important-003 --- Write Owner 정확히 1명 검사 약함

따라서 Order-010 PASS를 취소하지 않고, 다음 단계 전에 위 세 건만
보완한다.

## 3. Precondition

실행 전 확인:

-   Architecture v1.0 FROZEN
-   Terminology FROZEN
-   Order-010 = PASS
-   Order-011 = PASS WITH IMPORTANT FIX
-   Phase 2 미착수
-   기존 `04_Evidence\phase1` 보존
-   기존 plan 1.0 / 1.1 Event와 Evidence 보존
-   기존 Core/Test 파일 상태 기록

전제가 다르면 BLOCK한다.

## 4. Reuse Before Create

기존 Order-010 Core/Test 구조를 재사용한다.

새 프레임워크, 새 데이터베이스, 새 패키지를 만들지 않는다.

B Reference를 다시 구현 근거로 확장하지 않는다.

## 5. Write Scope

수정 허용:

### Core

-   `02_Core\beta_core\model.py`
-   `02_Core\beta_core\event_store.py`
-   `02_Core\beta_core\cli.py`
-   실제 필요가 증명되는 경우에만 Order-010 Core의 다른 기존 파일 최소
    수정

### Test / Fixture

-   `03_Tests\test_phase1.py`
-   `03_Tests\fixtures\task_phase1.json`
-   필요한 합성 Fixture 최소 추가/수정

### 상태 View

-   `Beta-Index.md`
-   `01_Orders\Order-History.md`

### Evidence

-   기존 Evidence 수정 금지
-   New Run의 새 Evidence 추가만 허용

금지: - Architecture / Terminology 수정 - Reference 수정 - 기존
Event/Evidence 삭제·수정 - 기존 Run 디렉터리 변경 - Phase 2 코드 - 외부
패키지

## 6. Fix 1 --- Plan Version 불변성

### 6.1 Plan Hash

Task 실행 전에 Task Plan 파일 전체의 SHA-256을 계산한다.

`RUN_STARTED` 또는 실행 전 계약 Event에서 최소 다음을 추적한다.

-   task_id
-   plan_version
-   task_plan_sha256
-   executor_sha256
-   validator_sha256 목록
-   change_reason_ref

기존 Event 필드는 유지한다.

### 6.2 동일 Version 불변식

한 번 사용된:

`(task_id, plan_version)`

조합은 최초 `task_plan_sha256`과 연결된다.

같은 `(task_id, plan_version)`으로 다른 Plan Hash가 들어오면:

-   Executor 실행 금지
-   New Run 정상 실행 금지
-   BLOCK Event 기록
-   사용자에게 성공으로 보고 금지

### 6.3 Plan Version 변경

Plan 내용, Executor Hash, Validator Hash 또는 Validation 기준이 의미
있게 바뀌면 새 `plan_version`을 사용한다.

새 Version에는 `change_reason_ref`가 필요하다.

이번 Fix의 변경 근거는 최소:

`Order-011 / Review-Important-001`

을 참조한다.

### 6.4 과거 기록

기존 plan 1.0 / 1.1 Event와 Evidence를 소급 수정하지 않는다.

과거 Event에 새 필드를 추가하기 위해 rewrite하지 않는다.

새 계약은 Order-012 이후 New Run부터 적용한다.

## 7. Fix 2 --- Fail-open Test 보강

기존 10개 Test를 보존하고 최소 다음 Test를 추가한다.

### Test A --- Executor 비정상 종료

Executor가 비정상 종료하면:

-   Execution ERROR
-   `EXECUTION_ERROR` Event
-   Gate BLOCK
-   Validation PASS로 변환되지 않음

### Test B --- Validator Timeout / 예외

Validator Timeout 또는 비정상 예외:

-   Validation ERROR
-   Gate BLOCK
-   PASS로 변환되지 않음

Timeout Test는 짧은 합성 Fixture를 사용하고 전체 Test 시간을 과도하게
늘리지 않는다.

### Test C --- Evidence 기록 실패

Evidence 파일 또는 index 기록 실패를 안전하게 합성한다.

결과: - Gate PROCEED 금지 - BLOCK 또는 ERROR 경로 - 성공 Evidence가
존재한다고 기록 금지

운영 폴더 권한을 실제로 망가뜨리지 않고 임시 Test 위치에서 합성한다.

### Test D --- Event Log 보존

동일 Test 저장소에서 두 번째 Run을 실행한 뒤:

-   첫 Run Event가 그대로 존재
-   기존 Event ID 유지
-   새 Event가 뒤에 append
-   truncate / rewrite 없음

### Hash 독립 검산

Test의 Evidence/파일 Hash 검증은 Core의 `sha256_file()`만 재사용하지
않는다.

Test 코드에서 Python 표준 `hashlib`로 직접 계산한 값과 Core 결과를
비교한다.

### Mutation Regression

Order-011에서 빠져나간 의미 있는 네 변형에 대응하는 Test가 실제로
존재해야 한다.

이번 Order에서 대규모 Mutation Framework를 구현하지 않는다.

## 8. Fix 3 --- Write Owner 단일 식별자

MVP의 `write_owner`는 단일 식별자 문자열만 허용한다.

최소 패턴:

`^[A-Za-z0-9][A-Za-z0-9_-]*$`

허용 예: - `Codex` - `Claude-Code` - `USR-001`

차단 예: - `Codex, Claude Code` - `Codex / Claude` - `Codex;Claude` - 빈
문자열 - 리스트

표시명/사용자 Registry/한글 이름 정책은 이번 MVP 범위 밖이다.

위 패턴은 MVP 계약 검사 형식이며 영구 사용자 ID Architecture Rule로
승격하지 않는다.

## 9. Test Plan Version Fixture

기존 `task_phase1.json`의 과거 1.1 실행 사실을 소급 변경하지 않는다.

Order-012 New Run용 새 Plan Version을 사용한다.

권장: `plan_version = 1.2`

변경 이유: - Plan Hash 불변성 계약 - Write Owner 검사 강화 - Order-012
Revalidation

`change_reason_ref`: `Order-012`

실제 구현에 따라 별도 Fixture 파일을 생성할 수 있으나 과거 1.0/1.1이
존재했던 것처럼 소급 재구성하지 않는다.

## 10. New Run / Revalidation

Fix와 Test가 PASS한 뒤 실제 합성 CLI New Run을 수행한다.

조건: - 새 plan_version - 새 Run ID - 기존 Run 보존 -
`task_plan_sha256` - `executor_sha256` - `validator_sha256` -
`change_reason_ref` 추적

실제 Run에서: - Execution 정상 - Validation PASS - Gate PROCEED - 새
Evidence - 새 Evidence index 행 - 기존 Evidence 불변

을 확인한다.

## 11. Negative Revalidation

최소 다음을 실제 Test 또는 격리 실행으로 확인한다.

1.  같은 `(task_id, plan_version)` + 다른 plan hash → BLOCK
2.  `"Codex, Claude Code"` → Run 전 BLOCK
3.  Executor ERROR → BLOCK
4.  Validator Timeout/ERROR → BLOCK
5.  Evidence 기록 실패 → PROCEED 불가
6.  두 번째 Run 후 첫 Event 보존

## 12. Later 유지

Order-011의 LATER는 이번 Scope에서 수정하지 않는다.

-   Evidence 내부 `gate` 예측값 문제
-   Validator 여러 개일 때 집계 Label 우선순위
-   Execution PASS와 Validation PASS 용어 중복

Architecture/Runtime Evidence가 더 필요하므로 보류한다.

## 13. Architecture / Decision 경계

이번 Fix는 승인된 D-MVP-001\~005 + 조건 A/B 범위 안이다.

Architecture Change Proposal은 만들지 않는다.

Architecture Delta가 새로 발견되면: - 해당 구현 중단 -
`ARCHITECTURE-DELTA` 보고 - 임의 수정 금지

## 14. 자동 Test

기존 10개 Test + 신규 Test를 모두 실행한다.

최소 기대: - 기존 10개 회귀 PASS - 신규 Fail-open / Plan 불변성 / Owner
Test PASS

정확한 총 Test 수는 구현에 따라 증가 가능하다.

보고 시: - 총 Test 수 - 기존 Test 수 - 신규 Test 수 - PASS / FAIL /
ERROR 를 구별한다.

## 15. Evidence 보존 검증

작업 전: - `events.jsonl` Hash - `evidence_index.jsonl` Hash - 기존 EVD
파일 목록 + Hash - 기존 Run 디렉터리 목록

작업 후: - 기존 EVD 파일 Hash 불변 - 기존 Run 디렉터리 보존 - 기존 Event
줄이 동일 순서로 prefix 보존 - 새 Event만 append - 새 Evidence만 추가

append 때문에 전체 JSONL Hash가 바뀌는 것은 정상이다. 기존 prefix가
변하면 FAIL.

## 16. Security / Scope

계속 유지: - Python 표준 라이브러리 - shell=True 금지 -
네트워크/API/Agent 금지 - SQLite 금지 - Downloads/Reference 쓰기 금지 -
실제 운영 데이터 금지

## 17. Index / History

Fix + Test + New Run + Validation이 모두 PASS한 뒤에만 최소 갱신한다.

Beta-Index: - Order-011 = PASS WITH IMPORTANT FIX - Order-012 Important
Fix 완료 - Now: Phase 1 Important Fix 재검증 완료 - Next: Claude Code
변경 부분 READ-ONLY Recheck

Order-History: - Order-011 결과 - Order-012 실제 결과

과거 Order-010 PASS를 FAIL로 변경하지 않는다.

## 18. Validation Checklist

### Important-001

-   [ ] Plan SHA-256 기록
-   [ ] Executor SHA-256 기록
-   [ ] Validator SHA-256 기록
-   [ ] 동일 task/version 다른 Plan Hash BLOCK
-   [ ] change_reason_ref
-   [ ] 과거 1.0/1.1 rewrite 없음

### Important-002

-   [ ] Executor ERROR Test
-   [ ] Validator Timeout/ERROR Test
-   [ ] Evidence 실패 Test
-   [ ] Event append 보존 Test
-   [ ] hashlib 독립 검산
-   [ ] 기존 10개 Test 회귀 PASS

### Important-003

-   [ ] Owner 단일 식별자 패턴
-   [ ] 다중 Owner 문자열 BLOCK
-   [ ] 리스트 BLOCK
-   [ ] 정상 단일 Owner PASS

### New Run

-   [ ] 새 plan_version
-   [ ] 새 Run ID
-   [ ] Validation PASS
-   [ ] Gate PROCEED
-   [ ] 새 Evidence
-   [ ] 새 Hash/Reason 추적
-   [ ] 기존 Evidence/Run 보존

### Scope

-   [ ] Architecture/Terminology 불변
-   [ ] Reference 불변
-   [ ] Phase 2 없음
-   [ ] 외부 패키지 없음
-   [ ] 네트워크/Agent 없음
-   [ ] 기존 기록 덮어쓰기 없음

하나라도 실패하면 PASS 금지. 검사 자체 실패는 ERROR.

## 19. 결과 보고 형식

# Order-012 Phase 1 Important Fix 결과

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### Important Fix

-   Important-001: PASS / FAIL
-   Important-002: PASS / FAIL
-   Important-003: PASS / FAIL

### 변경 파일

목록.

### 자동 Test

-   총 Test
-   기존 / 신규
-   PASS / FAIL / ERROR

### New Run

-   Task ID
-   plan_version
-   Run ID
-   task_plan_sha256
-   executor_sha256
-   validator_sha256
-   change_reason_ref
-   Execution
-   Validation
-   Gate
-   Evidence

### Negative Revalidation

6개 항목 결과.

### Preservation

-   기존 Event prefix
-   기존 EVD Hash
-   기존 Run
-   새 Event / Evidence

### Architecture Delta

NONE 또는 상세.

### Scope

위반 여부.

### Done

IMPORTANT 3건 수정 + New Run + Revalidation.

### Now

결과에 따른 Phase 1 상태.

### Next

PASS: → Claude Code READ-ONLY 변경 부분 Recheck → PASS이면 MVP Test 구현
순서 확정

FAIL/ERROR: → Root Cause → 새 Fix 근거 → New Run

### 사용자 승인 필요

NO --- 기존 승인 범위 안의 Fix.

## 20. 종료 조건

IMPORTANT 3건 수정, 전체 Test, New Run, 보존 검증, Evidence,
Index/History 최소 갱신 후 종료한다.

PASS해도 자동 시작 금지: - Claude Code 호출 - Phase 2 - MVP Test 추가
구현 - Architecture 변경 - EXE/PWA - Plugin/Adapter

결과를 ChatGPT Project Beta에 전달한다.

=== ORDER END ===
