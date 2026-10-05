# Beta Order --- Order-029 Scenario B Decision Enforcement Fix

## 문서 정보

-   Order ID: Order-029
-   Project: Beta
-   Status: APPROVED
-   Type: Narrow Targeted Fix + Revalidation
-   Architecture / Terminology: FROZEN
-   Source Review: Order-028
-   Target: MVP Test 4 --- Bottleneck / Scenario B Decision Enforcement
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

Order-028에서 유일하게 남은 Scenario B Decision Enforcement 문제만
수정한다.

Root Cause: `record_retry_decision`이 `ALLOW_NEW_RUN` 또는
`BLOCK_BLIND_RETRY`를 올바르게 계산하지만, Scenario B에서 그 Decision을
`run_task` 호출 조건으로 사용하지 않고 무조건 호출한다.

수정 목표: `ALLOW_NEW_RUN`일 때만 `run_task`를 호출한다. 그 외
Decision에서는 실행하지 않는다.

다른 Bottleneck 로직은 수정하지 않는다.

## 2. 근거

Order-028: - 판정 FAIL - Retry actual-count PASS - Run ID 집합 PASS -
Retry Limit 실행 PASS - Blind Retry 차단 PASS - ALLOW_NEW_RUN Check만
FAIL - Mutation E\~H PASS - Regression 37 PASS - Official Plan1.1
Evidence PASS - Preservation PASS - 유일한 잔존 문제: Scenario B 호출
제어

## 3. Precondition

-   Architecture/Terminology FROZEN
-   Phase1 CLOSED
-   Test1/2 OFFICIAL PASS
-   Order-028 FAIL
-   Test4 Plan1.0/1.1 존재
-   Retry Limit Blocker RESOLVED
-   Run/EVD Important RESOLVED
-   Test3/5/6/7 NOT VERIFIED
-   Phase2 없음 다르면 BLOCK.

## 4. Write Scope

수정 허용: - `03_Tests/fixtures/bottleneck_scenario_executor.py` -
`03_Tests/test_mvp_bottleneck.py` --- Decision Enforcement 회귀 Test에
필요한 최소 변경 - `03_Tests/fixtures/task_mvp_test_4_bottleneck.json` →
Plan 1.2 - 필요 시 Plan1.1 보존 Fixture - `Beta-Index.md` -
`01_Orders/Order-History.md` - Plan1.2 신규 Event/Evidence

`bottleneck_validator.py`는 현재 사후 탐지가 정상 동작하므로 기본적으로
수정하지 않는다. 정말 필요한 경우 이유를 보고한다.

Core, Retry Limit Fixture, Fingerprint 로직 수정 금지.

기존 Plan1.0/1.1 Evidence 수정·삭제 금지.

## 5. Fix Contract

Scenario B에서 Decision 계산 후:

``` text
decision_b = record_retry_decision(...)

IF decision_b.decision == ALLOW_NEW_RUN
    → run_task(path_b2, ...)
ELSE
    → run_task 호출 금지
```

허용 Decision 문자열은 기존 Canonical 값을 그대로 사용한다.

BLOCK인 경우: - RUN_STARTED 추가 없음 - Run directory 추가 없음 -
Runtime EVD 추가 없음 - Decision Event는 보존

## 6. ALLOW_NEW_RUN 조건

기존 계약을 변경하지 않는다.

다음 모두 필요: 1. 새 plan_version 2. 실제 Fix Signature 변경 3.
change_reason_ref 존재 4. Retry Limit 미초과

모두 충족: → ALLOW_NEW_RUN → run_task 호출

하나라도 없음: → BLOCK → run_task 미호출

## 7. Scenario B 정상 경로

공식 Scenario B: - baseline Validation FAIL - 동일 Fingerprint - plan
1.0 → 1.1 - 실제 Fix Signature 변경 -
`change_reason_ref=Order-025-Scenario-B-Fix` - Limit 미초과

기대: - ALLOW_NEW_RUN - run_task 정확히 1회 - 새 RUN_STARTED 정확히
1건 - 새 Run directory 정확히 1개 - 수정 Run PASS - Gate PROCEED - 과거
FAIL 보존

## 8. Decision Enforcement Negative

최소 세 변형을 실제 제어 흐름으로 검증한다.

### Mutation I --- Reason + Version, Fix 없음

-   새 version
-   reason 있음
-   Fix Signature 동일

기대: - BLOCK_BLIND_RETRY - run_task 호출 0 - 추가 RUN_STARTED 0 - 추가
Run directory 0 - 신규 Runtime EVD 0

### Mutation J --- Fix + Reason, Version 동일

기대: - BLOCK - 실행 0

### Mutation K --- Fix + Version, Reason 없음

기대: - BLOCK - 실행 0

가능하면 기존 Test에서 같은 의미가 이미 있으면 중복 Test 파일을 만들지
말고 실제 호출 부재 단언을 강화한다.

## 9. Existing Validator Role

Validator의 사후 검출은 계속 유지한다.

Defense in depth: 1. Executor 제어 흐름이 BLOCK에서 실행하지 않음 2.
Validator가 잘못된 추가 실행이 있으면 FAIL

Validator를 실행 제어의 대체물로 사용하지 않는다.

## 10. 기존 PASS 영역 변경 금지

다음은 그대로 유지: - Fingerprint - Failure Class - Normalization -
Retry actual-count - Run ID 집합 교차검증 - Retry Limit - BLOCK_LIMIT
Enforcement - Scenario A/C/D Blind Retry - Run/EVD 실제 상태 검증 -
Mutation A\~H - 과거 FAIL 보존 - canonical Test ID

## 11. Regression

기존 37개 Test 의미 유지.

신규 Test는 최소화한다. Decision Enforcement의 호출 부재를 기존 Test에
강화할 수 있으면 재사용한다.

보고: - 기존 Test - 신규 Test - 총 Test - PASS/FAIL/ERROR

기존 Test 삭제/약화 금지.

## 12. Test Plan 1.2

Scenario Executor Hash 변경으로 새 Plan 사용.

-   mvp_test_id: `MVP-TEST-4`
-   Name: `Bottleneck`
-   plan_version: `1.2`
-   change_reason_ref: `Order-029`
-   task_id/test_plan_id: 기존 규칙 유지

변경된 Executor SHA를 고정. Validator가 불변이면 기존 Validator SHA를
그대로 고정.

Plan1.0/1.1 소급 수정 금지.

## 13. New Official Run

전체 Regression PASS 후 Plan1.2 New Official Run.

기대: - New Run ID - Execution PASS - Validation PASS - Gate PROCEED -
New Evidence/SHA - Scenario A\~E 및 Retry Limit 연결 - Scenario B
ALLOW_NEW_RUN 실제 호출 조건 확인 - Plan1.0/1.1 보존

## 14. Preservation

작업 전/후: - Test4 Plan1.0 - Test4 Plan1.1 - Test1 - Test2 - Phase1 -
Core7 - Ownership/Reuse Harness - Architecture/Terminology - Reference
를 비교.

기존 Event/Index/Evidence rewrite 금지. Plan1.2만 append.

## 15. View

Order-029 PASS 후 Claude Recheck 전:
`Test 4 Bottleneck = PASS 후보 — Final Delta Recheck 대기`

Index: - Order-028 FAIL - Root Cause - Order-029 결과 - Test1/2 OFFICIAL
PASS - Test4 후보 - Now/Next

History: - Order-028 FAIL - Order-029 결과

## 16. 하지 말 것

-   Retry Limit 재설계
-   Fingerprint 재설계
-   Validator 대규모 변경
-   Test5 Prevention
-   Test6 User Gate
-   Test7 Resume
-   Test3 Safe Parallel
-   Architecture/Terminology
-   Core
-   DB/Agent/Plugin/Adapter
-   기존 Evidence rewrite
-   Phase2

## 17. Architecture Delta

기본 NONE. Architecture/Core 계약 변경 필요 시 임의 수정하지 말고
`ARCHITECTURE-DELTA` 보고 후 중단.

## 18. Validation Checklist

### Scenario B

-   [ ] Decision 계산
-   [ ] ALLOW_NEW_RUN일 때만 run_task
-   [ ] 정상 Fix에서 run_task 정확히 1회
-   [ ] PASS / PROCEED
-   [ ] 과거 FAIL 보존

### BLOCK Enforcement

-   [ ] Mutation I 실행 0
-   [ ] Mutation J 실행 0
-   [ ] Mutation K 실행 0
-   [ ] 추가 RUN_STARTED 없음
-   [ ] 추가 Run directory 없음
-   [ ] 신규 Runtime EVD 없음

### Defense in Depth

-   [ ] Validator의 사후 추가 실행 탐지 유지
-   [ ] Mutation H 유지

### Regression

-   [ ] 기존 37개 의미 유지
-   [ ] 신규/강화 Test PASS

### Official 1.2

-   [ ] MVP-TEST-4 / Bottleneck
-   [ ] Plan 1.2
-   [ ] change_reason_ref Order-029
-   [ ] New Run
-   [ ] PASS / PASS / PROCEED
-   [ ] Evidence + SHA
-   [ ] Scenario 연결

### Preservation / Scope

-   [ ] Plan1.0/1.1 불변
-   [ ] Test1/2/Phase1 불변
-   [ ] Core/Architecture/Reference 불변
-   [ ] Test3/5/6/7 미구현
-   [ ] Phase2 없음

하나라도 실패하면 PASS 금지. 검사 자체 실패는 ERROR.

## 19. 결과 보고

# Order-029 Scenario B Decision Enforcement Fix 결과

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### Root Cause Resolution

Decision → run_task 호출 조건 연결 결과.

### 변경 파일

목록.

### Scenario B 정상

Decision / 실제 호출 수 / Run / Validation / Gate.

### Mutation I/J/K

Decision, run_task 호출 수, RUN_STARTED, Run dir, EVD.

### 기존 Bottleneck 회귀

Fingerprint / Retry Limit / Run ID / BLOCK_LIMIT / A/C/D / Mutation
A\~H.

### Regression

기존/신규/총/PASS/FAIL/ERROR.

### Official Plan 1.2

ID/Name/Version/reason/Run/Plan·Executor·Validator
Hash/Validation/Gate/Evidence/SHA/Scenario.

### Preservation

Plan1.0/1.1/Test1/Test2/Phase1/Core/Architecture/Reference.

### MVP Test 상태

-   Test1 Reuse: OFFICIAL PASS
-   Test2 Ownership: OFFICIAL PASS
-   Test3 Safe Parallel: NOT VERIFIED
-   Test4 Bottleneck: PASS 후보 --- Final Delta Recheck 대기 / FAIL /
    ERROR
-   Test5 Prevention: NOT VERIFIED
-   Test6 User Gate: NOT VERIFIED
-   Test7 Resume: NOT VERIFIED

### Architecture Delta / Scope

상세.

### Done / Now / Next

PASS: → Claude Code READ-ONLY Scenario B Final Delta Recheck → PASS이면
Test4 OFFICIAL PASS → Test5 Prevention 구현 Order

FAIL/ERROR: → Root Cause → Blind Retry 금지 → 최소 Fix

### 사용자 승인 필요

NO

## 20. 종료 조건

Scenario B 호출 제어, Negative I/J/K, Regression, Plan1.2 New Run,
Preservation, View 갱신 후 종료.

PASS해도 Claude/Test5/다른 Test/Architecture/Phase2 자동 시작 금지.

=== ORDER END ===
