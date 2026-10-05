# Beta Order --- Order-027 Bottleneck Retry Enforcement Fix

## 문서 정보

-   Order ID: Order-027
-   Project: Beta
-   Status: APPROVED
-   Type: Targeted Blocker / Important Fix + Revalidation
-   Architecture / Terminology: FROZEN
-   Source Review: Order-026
-   Target: MVP Test 4 --- Bottleneck
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

Order-026의 Blocker 1건과 관련 Important 2건만 수정한다.

1.  Retry Limit을 자기보고 attempts가 아니라 실제 Event/Run 기록을 직접
    세어 판정
2.  BLOCK_BLIND_RETRY / BLOCK_LIMIT이면 run_task 호출 자체 금지
3.  Validator가 Event뿐 아니라 실제 Run 폴더/Evidence 파일 존재·부재도
    검증

이미 PASS한 Fingerprint, Failure Class, Actual Fix Signature, reason
검증, Negative A\~D, 실패 보존, Test ID는 불필요하게 변경하지 않는다.

수정 후 Test 4 Plan 1.1 + New Official Run. Test 5는 시작하지 않는다.

## 2. 근거

Order-026 = REVISION REQUIRED. Blocker: retry_limits Evidence에
RUN_STARTED가 0인데 Executor가 attempts=limit+1을 기록하고 Validator가
Fixture 숫자와만 비교해 PASS. Important: - Run 폴더/EVD 실제 상태 직접
검증 부족 - Retry Decision이 실제 실행 제어와 직접 연결되지 않음 그 외
Check는 PASS.

## 3. Precondition

Architecture/Terminology FROZEN, Phase1 CLOSED, Test1/2 OFFICIAL PASS,
Order-026 REVISION REQUIRED, Test4 Plan1.0 존재, Test3/5/6/7 NOT
VERIFIED, Phase2 없음. 다르면 BLOCK.

## 4. Write Scope

허용: - bottleneck_scenario_executor.py - bottleneck_validator.py -
bottleneck_retry_limits.json 필요 시 최소 수정 -
test_mvp_bottleneck.py - task_mvp_test_4_bottleneck.json → Plan 1.1 -
필요 시 Plan1.0 보존 Fixture - Beta-Index.md / Order-History.md -
Plan1.1 신규 Event/Evidence Core 변경 기본 금지. 필요 시 임의 수정하지
말고 보고. 기존 Plan1.0/Test1/Test2/Phase1 Evidence 수정·삭제 금지.

## 5. Retry Limit 실제 계수

Executor의 하드코딩 attempts 판정 제거.

Validator ERROR: - 실제 Validator ERROR Event/Run 직접 count - limit=2 -
실제 2회 기록 - 3번째 요청은 기존 count=2 근거로 BLOCK_LIMIT - 3번째 Run
생성 금지

Execution ERROR: - 실제 Execution ERROR Run/Event 직접 count - limit=2 -
3번째 요청 BLOCK_LIMIT - 3번째 Run 금지

Plan Version별 New Run: - 같은 Task + 같은 plan_version 실제 RUN_STARTED
직접 count - limit=3 - 실제 Run 3개 - 4번째 요청 BLOCK_LIMIT - 4번째 Run
금지

Executor 계산 count와 Validator 독립 계산 count가 일치해야 한다.

## 6. Count Source

기존 원본 우선: - events.jsonl - Run directories - Evidence index 파생
summary를 SSOT로 만들지 않는다. Validator는 Event count와 실제 Run
directory count를 교차 확인. Execution ERROR처럼 EVD가 없는 정상 상태는
failure class 계약에 맞게 처리.

## 7. Retry Decision → 실행 제어

BLOCK_BLIND_RETRY: - run_task 미호출 - RUN_STARTED 없음 - Run directory
없음 - 신규 Runtime EVD 없음 - RETRY_DECISION Evidence만 남김

BLOCK_LIMIT도 동일.

ALLOW_NEW_RUN은 다음 모두 필요: - 새 plan_version - 실제 Fix Signature
변경 - change_reason_ref - Retry Limit 미초과 그때만 run_task 호출.

## 8. Validator 실제 파일 상태

Blind Retry BLOCK: - 차단 Run directory 없음 - EVD 없음 - RUN_STARTED
없음

Execution ERROR 허용 Run: - Run directory 존재 - RUN_STARTED - Execution
ERROR Event - Validator 실행 없음 - EVD 부재가 계약과 일치

Validation FAIL/ERROR 허용 Run: - Run directory 존재 - 관련 Event -
계약에 따른 EVD 존재/부재

가짜 Run directory/EVD 추가, 실제 Run directory 삭제를 탐지.

## 9. Mutation E\~H

기존 Negative A\~D 유지.

E Fake Count: Event/Run 0인데 attempts=limit+1 자기보고 → FAIL/BLOCK.

F Fake Run Directory: BLOCK된 retry에 가짜 Run directory 추가 →
FAIL/BLOCK.

G Missing Run Directory: 허용 Run의 Run directory 삭제 → FAIL/BLOCK.

H Decision BLOCK but run_task executed: BLOCK 뒤 실제 Run 생성 →
FAIL/BLOCK.

각각 의도한 위반 때문에 실패해야 한다.

## 10. 기존 PASS 영역

변경 최소화: Fingerprint 결정성, failure class, normalization, Actual
Fix Signature, reason-only 차단, Scenario A\~E 의미, Negative A\~D, 과거
FAIL 보존, canonical ID.

## 11. Retry Limit Fixture

값 유지: - Validator ERROR 2 - Execution ERROR 2 - Plan Version New Run
3 MVP Fixture일 뿐 전역 Rule 아님. 초과 → BLOCK_LIMIT.
user_gate_required_reason 기록 가능. USER-GATE Workflow 구현 금지.

## 12. Regression

기존 32개 의미 유지. Mutation E\~H + actual-count limit Test 추가. 기존
삭제/약화 금지. 기존/신규/총/PASS/FAIL/ERROR 보고.

## 13. Test Plan 1.1

-   mvp_test_id MVP-TEST-4
-   Name Bottleneck
-   plan_version 1.1
-   change_reason_ref Order-027
-   task_id/test_plan_id 기존 규칙 유지 변경 Executor/Validator SHA
    고정. Plan1.0 소급 수정 금지.

## 14. New Official Run

전체 PASS 후 Plan1.1 New Run: 새 Run ID, PASS/PASS/PROCEED,
Evidence/SHA, Scenario A\~E, 실제 Retry Limit Scenario. 기존 Plan1.0
보존.

## 15. Preservation

Test4 Plan1.0 공식/Scenario/Event/Index/Run, Test1/2, Phase1,
Ownership/Reuse Harness, Core7, Architecture/Terminology/Reference 전후
확인. 기존 rewrite 금지. Plan1.1만 추가.

## 16. View

Order-027 PASS 후 Claude Recheck 전:
`Test 4 Bottleneck = PASS 후보 — Delta Recheck 대기`. Index/History에
Order-026 REVISION REQUIRED, 원인, Order-027 결과, Test1/2 PASS, Test4
후보, Now/Next 최소 반영.

## 17. 하지 말 것

Test5 Prevention, Test6 User Gate Workflow, Test7 Resume, Test3 Safe
Parallel, Prevention/Rule, Agent/Plugin/Adapter, SQLite/DB,
Architecture/Terminology, 기존 Evidence rewrite, Phase2 금지.

## 18. Architecture Delta

기본 NONE. Core/Architecture 계약 변경 필요 시 ARCHITECTURE-DELTA 보고
후 중단.

## 19. Validation

### Retry Count

-   [ ] Validator ERROR 실제 count
-   [ ] Execution ERROR 실제 count
-   [ ] plan_version 실제 Run count
-   [ ] Event/Run directory 교차검증
-   [ ] 자기보고 attempts 미신뢰
-   [ ] limit 직전/초과 정확

### Enforcement

-   [ ] BLOCK_BLIND_RETRY → run_task 미호출
-   [ ] BLOCK_LIMIT → run_task 미호출
-   [ ] RUN_STARTED 없음
-   [ ] Run directory 없음
-   [ ] 신규 Runtime EVD 없음
-   [ ] ALLOW_NEW_RUN 조건 모두 필요

### File State

-   [ ] 허용 Run directory 존재
-   [ ] 차단 Run directory 부재
-   [ ] EVD 존재/부재 계약 일치
-   [ ] Fake Run/EVD 탐지
-   [ ] Missing Run 탐지

### Mutation

-   [ ] E Fake Count FAIL/BLOCK
-   [ ] F Fake Run Directory FAIL/BLOCK
-   [ ] G Missing Run Directory FAIL/BLOCK
-   [ ] H BLOCK 후 실행 FAIL/BLOCK
-   [ ] 기존 A\~D 유지

### Regression

-   [ ] 기존 32 의미 유지
-   [ ] 신규 PASS

### Official 1.1

-   [ ] MVP-TEST-4 / Bottleneck / 1.1 / Order-027
-   [ ] New Run
-   [ ] PASS / PASS / PROCEED
-   [ ] Evidence + SHA
-   [ ] Scenario 연결

### Preservation/Scope

-   [ ] Plan1.0/Test1/Test2/Phase1 불변
-   [ ] Core/Architecture/Reference 불변
-   [ ] Test3/5/6/7 미구현
-   [ ] USER-GATE Workflow 없음
-   [ ] Phase2 없음

하나라도 실패하면 PASS 금지. 검사 자체 실패는 ERROR.

## 20. 결과 보고

# Order-027 Bottleneck Retry Enforcement Fix 결과

-   현재 상태
-   Blocker Resolution: actual-count 기반 여부
-   Important Resolution: Run/EVD 직접 검증, BLOCK 실제 실행 차단
-   변경 파일
-   Retry Limit: limit/실제 Event count/실제 Run count/직전/초과
    Decision/초과 Run 여부
-   Enforcement: BLOCK_BLIND_RETRY/BLOCK_LIMIT/ALLOW_NEW_RUN 호출 여부
-   Mutation E\~H
-   Regression
-   Official Plan1.1 ID/Name/Version/reason/Run/Plan·Executor·Validator
    Hash/Validation/Gate/Evidence/SHA/Scenario
-   Preservation
-   상태: Test1 PASS, Test2 PASS, Test3 NOT VERIFIED, Test4 PASS
    후보-Recheck 대기, Test5\~7 NOT VERIFIED
-   Architecture Delta/Scope
-   Done/Now/Next

PASS Next: Claude READ-ONLY Bottleneck Retry Delta Recheck → PASS이면
Test4 OFFICIAL PASS → Test5 Prevention. 사용자 승인 필요 NO.

## 21. 종료 조건

Blocker/Important 수정, actual-count Scenario, Mutation E\~H,
Regression, Plan1.1 New Run, Preservation, View 갱신 후 종료. PASS해도
Claude/Test5/다른 Test/Architecture/Phase2 자동 시작 금지.

=== ORDER END ===
