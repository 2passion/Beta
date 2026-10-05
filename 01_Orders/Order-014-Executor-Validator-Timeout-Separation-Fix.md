# Beta Order --- Order-014 Executor / Validator Timeout Separation Fix

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-014
-   Project: Beta
-   Status: APPROVED
-   Order Type: Targeted Root Cause Fix + Revalidation
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Status: FROZEN
-   Terminology: `Terminology.md`
-   Terminology Status: FROZEN
-   Source Review: Order-013 Important Fix Recheck
-   Write Owner: Codex
-   Reviewer: Claude Code
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Order-013에서 확인된 단일 Root Cause만 수정한다.

Root Cause: `run_task(timeout_seconds)` 하나의 제한값을 Executor와
Validator가 공유하여, Validator Timeout Test에서 정상 Executor까지
동일한 짧은 Timeout의 영향을 받는다.

목표: - Executor Timeout과 Validator Timeout을 분리한다. - 정상
Executor는 충분한 시간 안에서 실행한다. - Validator Timeout Fixture만
의도적으로 Timeout시킨다. - Validation ERROR / Gate BLOCK 경로를
안정적으로 재현한다. - 기존 plan 1.0 / 1.1 / 1.2 Run과 Evidence를
보존한다. - 새 plan 1.3 Run으로 변경 후 Runtime Revalidation을 수행한다.

이번 Order에서는 다른 IMPORTANT, LATER, Mutation 개선 후보를 수정하지
않는다.

## 2. 근거

Order-013: - 최종 판정: FAIL - Blocker: NONE - Important-001: RESOLVED -
Important-002: NOT_RESOLVED --- Timeout Fixture 안정성만 남음 -
Important-003: RESOLVED - Root Cause: Executor와 Validator가 하나의
timeout 값을 공유

따라서 Blind Retry하지 않고 Root Cause를 수정한다.

## 3. Precondition

실행 전 확인: - Architecture v1.0 FROZEN - Terminology FROZEN -
Order-010 PASS - Order-011 PASS WITH IMPORTANT FIX - Order-012 PASS -
Order-013 FAIL - 기존 plan 1.0 / 1.1 / 1.2 Run, Event, Evidence 존재 -
Phase 2 미착수

다르면 BLOCK.

## 4. Write Scope

수정 허용: - `02_Core\beta_core\cli.py` - Timeout 분리를 위해 실제로
필요한 기존 Core 파일 최소 수정 - `03_Tests\test_phase1.py` -
`03_Tests\fixtures\validator_timeout.py` - Timeout 관련 합성 Fixture
최소 수정 - `03_Tests\fixtures\task_phase1.json` --- plan 1.3
Revalidation에 필요한 최소 변경 - `Beta-Index.md` -
`01_Orders\Order-History.md`

Evidence: - 기존 파일 수정 금지 - plan 1.3 New Run의 새 Event / Evidence
append만 허용

그 외 수정 금지.

## 5. Fix --- Timeout 책임 분리

현재 단일: `timeout_seconds`

를 최소 다음 두 책임으로 분리한다.

-   `executor_timeout_seconds`
-   `validator_timeout_seconds`

원칙: - Executor Timeout은 Executor 실행 한도 - Validator Timeout은
Validator 실행 한도 - 서로의 값을 암묵적으로 공유하지 않는다. -
Execution ERROR와 Validation ERROR의 기존 의미를 유지한다.

CLI 또는 함수 호출의 기본값은 정상 Phase 1 실행에 충분한 기존 안전
기본값을 유지한다.

Test에서만 Validator Timeout을 짧게 설정할 수 있어야 한다.

## 6. Timeout Test 계약

Validator Timeout Test는 다음을 반드시 증명한다.

1.  Executor는 정상 완료
2.  `RUN_COMPLETED` 존재
3.  Validator가 의도적으로 Timeout
4.  Validation Status = ERROR
5.  Gate = BLOCK
6.  Executor Timeout이 원인이 아님

Fixture: - Validator는 충분히 긴 sleep으로 의도적 Timeout - Validator
Timeout은 그보다 짧게 설정 - Executor Timeout은 정상 Executor 최대 관측
시간보다 충분히 큰 값

단순히 모든 Timeout을 늘려 Test를 우연히 통과시키지 않는다.

## 7. Stress Revalidation

격리 환경에서 Timeout 관련 Test를 반복 실행한다.

최소: - Validator Timeout Test 단독 20회 - 관련 Executor Error +
Validator Timeout Test 묶음 10회 - 전체 Test Suite 10회

가능하면 시스템 부하 상황도 합리적 범위에서 확인한다.

PASS 조건: - 정상 Executor가 Timeout 때문에 실패한 횟수 0 - Validator
Timeout Test 결과가 매번 Validation ERROR / Gate BLOCK - 전체 Suite
반복에서 Timeout 관련 flaky FAIL 0

과도한 CPU Stress Tool이나 외부 도구를 새로 설치하지 않는다.

## 8. 기존 Test 회귀

Order-012의 17개 Test 의미를 유지한다.

Timeout API 변경으로 기존 Test 호출부가 깨지면 최소 수정한다.

다음을 다시 확인: - Plan Version 불변성 - Write Owner - Executor ERROR -
Validator Timeout/ERROR - Evidence 실패 - Event append - Hash 독립
검산 - 기존 회귀 Test

## 9. plan 1.3 New Run

Fix와 전체 Test가 PASS한 뒤 실제 합성 CLI Run을 새 plan_version으로
실행한다.

권장: `plan_version = 1.3`

`change_reason_ref = Order-014`

새 Run에서 최소 추적: - task_plan_sha256 - executor_sha256 -
validator_sha256 - change_reason_ref - Execution - Validation - Gate -
Evidence

정상 Runtime Run은: - Execution PASS - Validation PASS - Gate PROCEED

이어야 한다.

Timeout Test의 ERROR/BLOCK은 합성 Test이며 정상 Runtime Evidence와
구별한다.

## 10. Preservation

작업 전 기록: - 기존 Event 전체 또는 prefix - Evidence Index - plan 1.0
/ 1.1 / 1.2 EVD Hash - 기존 Run 디렉터리

작업 후: - 기존 Event가 byte-prefix로 보존 - 기존 Index가 prefix로
보존 - 기존 EVD Hash 불변 - 기존 Run 디렉터리 보존 - plan 1.3
Event/Evidence만 append

과거 기록 rewrite 금지.

## 11. Order-013 Mutation F1/F2

이번 Scope에서 수정하지 않는다.

-   F1: RUN_STARTED의 Executor/Validator Hash 필드 누락 Mutation을 단위
    Test가 직접 탐지하지 못함
-   F2: Evidence의 change_reason_ref 누락 Mutation을 단위 Test가 직접
    탐지하지 못함

실제 기록은 정상이고 Order-013도 새 Important로 승격하지 않았다.

향후 Test Quality 후보로만 보존한다.

## 12. Architecture / Decision

이번 Fix는 기존 FROZEN Architecture의: - Execution ERROR - Validator
ERROR 분리를 구현 수준에서 명확히 하는 작업이다.

Architecture Delta 없음이 기본 예상이다.

Architecture 변경 필요성이 발견되면 임의 수정하지 않고
`ARCHITECTURE-DELTA`로 보고하고 중단한다.

## 13. Security / Scope

유지: - Python 표준 라이브러리만 - shell=True 금지 - 네트워크/API/Agent
없음 - SQLite 없음 - 실제 운영 데이터 없음 - Downloads/Reference 쓰기
없음 - Phase 2 없음

## 14. Index / History

Fix, Test, Stress Revalidation, plan 1.3 New Run이 모두 PASS한 뒤에만
최소 갱신한다.

Beta-Index: - Order-013 = FAIL 기록 - Root Cause = shared timeout -
Order-014 결과 - Now: Timeout Separation Fix Revalidation 결과 - Next:
Claude Code READ-ONLY Timeout Delta Recheck

Order-History: - Order-013 FAIL - Order-014 실제 결과

Order-010/011/012 과거 결과를 변경하지 않는다.

## 15. Validation Checklist

### Root Cause Fix

-   [ ] Executor / Validator Timeout 분리
-   [ ] Executor는 Validator Timeout 값의 영향을 받지 않음
-   [ ] Validator Timeout → Validation ERROR
-   [ ] Gate BLOCK
-   [ ] Execution ERROR와 Validation ERROR 구별 유지

### Test

-   [ ] 기존 17개 의미 유지
-   [ ] 전체 Test PASS
-   [ ] Validator Timeout 단독 20회 PASS
-   [ ] 관련 Test 묶음 10회 PASS
-   [ ] 전체 Suite 10회 flaky FAIL 0
-   [ ] 정상 Executor Timeout 0회

### New Run

-   [ ] plan 1.3
-   [ ] 새 Run ID
-   [ ] change_reason_ref = Order-014
-   [ ] Execution PASS
-   [ ] Validation PASS
-   [ ] Gate PROCEED
-   [ ] 새 Evidence / Hash

### Preservation

-   [ ] 기존 plan 1.0 EVD 불변
-   [ ] 기존 plan 1.1 EVD 불변
-   [ ] 기존 plan 1.2 EVD 불변
-   [ ] 기존 Event prefix 보존
-   [ ] 기존 Index prefix 보존
-   [ ] 기존 Run 보존

### Scope

-   [ ] Architecture/Terminology 불변
-   [ ] Reference 불변
-   [ ] Phase 2 없음
-   [ ] F1/F2 Scope 확대 없음
-   [ ] 외부 패키지/네트워크/Agent 없음

필수 항목 하나라도 실패하면 PASS 금지. 검사 자체 실패는 ERROR.

## 16. 결과 보고 형식

# Order-014 Timeout Separation Fix 결과

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### Root Cause

shared timeout 해결 여부.

### 변경 파일

목록.

### Timeout 계약

-   executor timeout
-   validator timeout
-   기본값
-   Test 값

### Test

-   총 Test 수
-   PASS / FAIL / ERROR
-   Timeout 단독 20회
-   관련 묶음 10회
-   전체 Suite 10회
-   정상 Executor timeout 횟수

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
-   Evidence SHA-256

### Preservation

기존 Event/Index/EVD/Run 보존 결과.

### Architecture Delta

NONE 또는 상세.

### Scope

위반 여부.

### Done

Timeout Root Cause Fix + Revalidation.

### Now

결과에 따른 Phase 1 상태.

### Next

PASS: → Claude Code READ-ONLY Timeout Delta Recheck → PASS이면 Phase 1
수정 루프 종료 → MVP Test 구현 순서 확정

FAIL/ERROR: → Root Cause 재분석 → Blind Retry 금지

### 사용자 승인 필요

NO

## 17. 종료 조건

Timeout 분리, 전체 Test, Stress Revalidation, plan 1.3 New Run,
Preservation, Index/History 최소 갱신 후 종료한다.

PASS해도 자동 시작 금지: - Claude Code 호출 - Phase 2 - 다음 MVP Test -
Architecture 변경 - 제품화 작업

결과를 ChatGPT Project Beta에 전달한다.

=== ORDER END ===
