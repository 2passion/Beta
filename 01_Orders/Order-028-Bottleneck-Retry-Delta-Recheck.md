# Beta Order --- Order-028 Bottleneck Retry Delta Recheck

## 문서 정보

-   Order ID: Order-028
-   Project: Beta
-   Status: APPROVED
-   Type: READ-ONLY Delta Recheck
-   Architecture / Terminology: FROZEN
-   Source Fix: Order-027
-   Target: MVP Test 4 --- Bottleneck Plan 1.1
-   Reviewer: Claude Code
-   Write Owner of reviewed implementation: Codex
-   Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

Order-027에서 수정한 Retry Enforcement 범위만 최종 READ-ONLY 재확인한다.

Bottleneck 전체 Independent Review를 반복하지 않는다. 새
Mutation/LATER/기능 개선을 적극 발굴하지 않는다.

확인 범위: 1. Retry Limit이 실제 Event/Run/Evidence 기록을 직접 세는가
2. Event와 Run directory가 숫자뿐 아니라 동일한 Run ID 집합으로
교차검증되는가 3. BLOCK_LIMIT 뒤 run_task/New Run이 실제로 없는가 4.
BLOCK_BLIND_RETRY 뒤 run_task/New Run이 실제로 없는가 5. Fake Count /
Fake Run / Missing Run / BLOCK 후 실행을 Validator가 잡는가 6. Plan 1.1
공식 Evidence와 Scenario 연결이 정상인가 7. Plan
1.0/Test1/Test2/Phase1이 불변인가

모두 PASS하면 Order-026 Blocker/Important를 RESOLVED하고 Test 4
Bottleneck을 OFFICIAL PASS로 확정할 수 있다.

## 2. 권한

READ-ONLY.

금지: - Core/Harness/Test/Fixture/Evidence 수정 -
Beta-Index/Order-History 수정 - Architecture/Terminology 수정 - 새 파일
생성 - Fix 수행 - Test 5 Prevention 구현 - 다른 MVP Test 구현 - Phase
2 - Git

읽기, Hash 재계산, Beta 밖 격리 복사본의 비파괴 Test만 허용.

## 3. Precondition

-   Order 마지막 `=== ORDER END ===`
-   Architecture/Terminology FROZEN
-   Phase1 CLOSED
-   Test1 Reuse OFFICIAL PASS
-   Test2 Ownership OFFICIAL PASS
-   Order-026 REVISION REQUIRED
-   Order-027 PASS 보고
-   Test4 = PASS 후보 / Delta Recheck 대기
-   Test3/5/6/7 NOT VERIFIED
-   Phase2 없음
-   Test4 Plan1.0/1.1 존재

다르면 BLOCKED.

## 4. 읽을 대상

기준: - Beta-Index.md - Architecture - Terminology - Order-027 -
Order-History

변경: - bottleneck_scenario_executor.py - bottleneck_validator.py -
bottleneck_retry_limits.json - test_mvp_bottleneck.py -
task_mvp_test_4_bottleneck.json - Plan1.0 보존 Fixture

Evidence: - 04_Evidence/mvp_test_4 Plan1.0/1.1 공식 Evidence - Plan1.1
Scenario A\~E - Retry Limit Scenario - Event/Index/Run directory 전체
실제 디렉터리 목록에서 확인한다.

## 5. Check 1 --- Retry Count 실제 기록 기반

Validator 코드를 직접 읽고 확인한다.

Validator ERROR: - 실제 관련 failure Event - RUN_STARTED - Run
directory - Runtime EVD 를 직접 count.

Execution ERROR: - 실제 EXECUTION_ERROR - RUN_STARTED - Run directory 를
직접 count. Runtime EVD=0이 계약과 일치.

Plan Version New Run: - 동일 Task + 동일 plan_version의 실제
RUN_STARTED와 Run directory를 직접 count.

Executor의 `attempts` 자기보고를 판정 근거로 사용하지 않아야 한다.

판정 PASS/FAIL.

## 6. Check 2 --- Run ID 집합 교차검증

단순히: Event count = 2 Run directory count = 2 만 확인해서는 안 된다.

각 허용 시도에 대해: - RUN_STARTED의 run_id 집합 - 실제 Run directory
이름/metadata의 run_id 집합 - 해당 failure Event의 run_id 집합 -
Evidence가 존재해야 하는 class는 Evidence의 run_id 집합

을 비교한다.

기대: - 계약상 존재해야 하는 집합이 동일 - Execution ERROR처럼
Evidence가 없어야 하는 class는 그 부재가 정확히 확인됨 - 다른 Run ID를
넣어 숫자만 맞추는 변형은 FAIL

독립 Mutation 가능: Event의 Run ID 하나를 다른 값으로 바꾸고 count는
동일하게 유지 → Validator FAIL / Gate BLOCK.

판정 PASS/FAIL.

## 7. Check 3 --- Retry Limit 실제 실행

공식 Plan1.1 Scenario에서 직접 확인.

### Validator ERROR

-   limit 2
-   허용 Run 실제 2개
-   3번째 요청 BLOCK_LIMIT
-   3번째 RUN_STARTED 없음
-   3번째 Run directory 없음
-   신규 Runtime EVD 없음

### Execution ERROR

동일하게 2개 허용, 3번째 BLOCK, 초과 Run 없음.

### Plan Version New Run

-   limit 3
-   실제 Run 3개
-   4번째 요청 BLOCK_LIMIT
-   4번째 Run 없음

판정 PASS/FAIL.

## 8. Check 4 --- Blind Retry 실제 차단

Scenario A/C/D에서: - RETRY_DECISION = BLOCK_BLIND_RETRY - 그 이후
run_task 호출 없음 - 추가 RUN_STARTED 없음 - 추가 Run directory 없음 -
신규 Runtime EVD 없음

코드 제어 흐름도 읽어 Decision이 실제 호출 조건으로 사용되는지 확인.

판정 PASS/FAIL.

## 9. Check 5 --- ALLOW_NEW_RUN

Scenario B: - 새 plan_version - 실제 Fix Signature 변경 -
change_reason_ref - Retry Limit 미초과 모두 확인된 경우에만 run_task
호출.

Reason-only / version-only / fix-only 우회가 여전히 차단되는지 확인.

판정 PASS/FAIL.

## 10. Check 6 --- Mutation E\~H 독립 재현

E Fake Count: 실제 Event/Run 0 + 자기보고 초과 → FAIL/BLOCK.

F Fake Run: BLOCK된 retry에 가짜 Run directory → FAIL/BLOCK.

G Missing Run: 허용 Run directory 삭제 → FAIL/BLOCK.

H BLOCK 후 run_task: 추가 Run 실행 → FAIL/BLOCK.

각각 다른 우연한 오류가 아닌 의도한 위반으로 실패해야 한다.

추가 Run-ID mismatch 변형을 수행했다면 결과도 보고한다.

판정 PASS/FAIL.

## 11. Check 7 --- 기존 PASS 영역 회귀

다음을 변경하지 않았는지 확인: - Fingerprint 결정성 - failure_class
분리 - normalization - Actual Fix Signature - reason-only 차단 -
Negative A\~D - 과거 FAIL 보존 - canonical Test ID

필요 최소한만 재검증.

판정 PASS/FAIL.

## 12. Check 8 --- Regression

Beta 밖 격리 복사본 전체 Suite.

기대: - 기존 32 의미 유지 - 신규 5 - 총 37 - 37 PASS - 0 FAIL - 0
ERROR - PYTHONPATH 불필요 - 임시 잔여물 없음

판정 PASS/FAIL.

## 13. Check 9 --- Official Plan 1.1

실제 파일에서 재계산:

-   mvp_test_id = MVP-TEST-4
-   Name Bottleneck
-   Version 1.1
-   change_reason_ref Order-027
-   Run `RUN-dc6413d1-9815-4763-9767-33dd60f79100`
-   Plan SHA
    `B037AAAFE5E4220E4EEC762BADC6DAF8209F355582D7288B00FA48B1D1E295B5`
-   Executor SHA
    `4D7AB0E1FB7EAE2107BA3980DA39C50912BA432BB7FB62FBF9D2A41D97C468E5`
-   Validator SHA
    `DF2E151ADD96D7F28A3E61AEAA652F8DF0546FF9907DCFBEDC9F1DCCF6C88D82`
-   Execution PASS
-   Validation PASS
-   Gate PROCEED
-   Evidence `EVD-fead1b4e-2126-4a2a-b410-c961bb237ae1`
-   Evidence SHA
    `9B83FB6773F36926FA4A4317EF202DFFFA38898E85B22978ACB22619BF4292E4`
-   Scenario `SCN-a4cbe8c2-b2ab-41cf-9807-5ce82aff0139`
-   Scenario 연결 47개

Plan/Executor/Validator/Evidence/47개 링크 Hash 직접 재계산.

판정 PASS/FAIL.

## 14. Check 10 --- Preservation

확인: - Test4 Plan1.0 Plan/Evidence/Scenario/Event/Index/Run 불변 -
Test1 불변 - Test2 불변 - Phase1 불변 - Core7 불변 - Ownership/Reuse
Harness 불변 - Architecture/Terminology FROZEN 불변 - Reference 불변 -
Test3/5/6/7 미구현 - Phase2 없음 - 임시 잔여물 없음

판정 PASS/FAIL.

## 15. 새로운 Blocker

Order-027 직접 변경 범위에서만 확인: - Retry count 자기보고 의존 잔존 -
Event/Run ID 집합 불일치 미탐지 - BLOCK_LIMIT 후 실제 Run -
BLOCK_BLIND_RETRY 후 실제 Run - Fake/Missing Run 미탐지 - Plan1.1
Evidence 불일치 - 과거 기록 변경 - Scope 침범

없으면 NONE. 새 기능 아이디어 발굴 금지.

## 16. 최종 판정

이번 Delta Recheck는 다음만 사용한다.

### PASS

-   Check 1\~10 모두 PASS
-   Blocker NONE
-   Order-026 Blocker RESOLVED
-   관련 Important RESOLVED
-   Test4 OFFICIAL PASS 확정 가능

### FAIL

-   실질 Check FAIL
-   Blocker/Important 미해결
-   Order-027 직접 문제

### BLOCKED

-   독립 검증 불가

PASS WITH IMPORTANT FIX는 사용하지 않는다.

## 17. 결과 보고

# Order-028 Bottleneck Retry Delta Recheck 결과

### 현재 판정

PASS / FAIL / BLOCKED

### Check Matrix

1 Retry actual-count 2 Run ID 집합 3 Retry Limit 실행 4 Blind Retry 차단
5 ALLOW_NEW_RUN 6 Mutation E\~H 7 기존 PASS 영역 8 Regression 9 Official
Plan1.1 10 Preservation

### Resolution

-   Order-026 Blocker: RESOLVED / NOT_RESOLVED
-   Run/EVD Important: RESOLVED / NOT_RESOLVED
-   Decision Enforcement Important: RESOLVED / NOT_RESOLVED

### Retry Count

각 유형 limit / Event IDs / Run IDs / Evidence IDs / 초과 Run 여부.

### Enforcement

BLOCK_LIMIT / BLOCK_BLIND_RETRY / ALLOW_NEW_RUN 실제 호출 제어.

### Mutation

E\~H + Run-ID mismatch가 있으면 결과.

### Official Evidence

Plan/Executor/Validator/Evidence/Scenario 47개 Hash.

### Regression

기존/신규/총/PASS/FAIL/ERROR.

### Preservation

Plan1.0/Test1/Test2/Phase1/Core/Architecture/Reference.

### 새로운 Blocker

NONE 또는 상세.

### MVP Test 상태

1\~7.

### 파일 변경

모든 Beta 파일 NO / 새 파일 NO.

### Done / Now / Next

PASS: → ChatGPT Beta 검토 → Test4 Bottleneck OFFICIAL PASS → Test5
Prevention 구현 Order

FAIL: → Root Cause → 최소 Fix → New Run/Revalidation

### 사용자 승인 필요

NO

## 18. 종료 조건

Check 1\~10 및 보고 후 종료. Beta 수정 금지. PASS해도 Test5/다른
Test/Architecture/Phase2/Fix 자동 시작 금지.

=== ORDER END ===
