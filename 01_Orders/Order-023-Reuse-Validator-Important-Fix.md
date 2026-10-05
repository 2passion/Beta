# Beta Order --- Order-023 Reuse Validator Important Fix

## 문서 정보

-   Order ID: Order-023
-   Project: Beta
-   Status: APPROVED
-   Type: Targeted Important Fix + Revalidation
-   Architecture / Terminology: FROZEN
-   Source Review: Order-022
-   Target: MVP Test 1 Reuse Validator
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

Order-022의 IMPORTANT 2건만 수정한다. 1. REUSE 시 selected Asset path와
실제 Executor path 동일성 강제. 2. CREATE 시 REUSE_SEARCH/reason이 신규
Executor 파일 생성보다 먼저임을 강제.

기존 Test 1 Plan 1.0 Evidence는 보존하고 Plan 1.1 + New Run + Evidence로
재검증. 다른 MVP Test 금지.

## 2. 근거

Order-022 = PASS WITH IMPORTANT FIX, Blocker NONE, Plan 1.0 Evidence
유효. Important-001: 같은 Hash의 다른 경로 복사본 실행을 못 잡음.
Important-002: CREATE 파일을 REUSE_SEARCH보다 먼저 만들어도 못 잡음.
Architecture Delta NONE / 사용자 승인 NO.

## 3. Precondition

Architecture/Terminology FROZEN, Phase 1 CLOSED, Test 2 OFFICIAL PASS,
Order-022 결과, Test 1 Plan 1.0 존재, Test 3\~7 NOT VERIFIED, Phase 2
없음. 다르면 BLOCK.

## 4. Write Scope

허용: - 03_Tests/fixtures/reuse_validator.py -
03_Tests/test_mvp_reuse.py - 필요 시 reuse_scenario_executor.py 최소
수정 - task_mvp_test_1_reuse.json → Plan 1.1 - 필요 시 Plan 1.0 보존
Fixture - Beta-Index.md / 01_Orders/Order-History.md - Plan 1.1 신규
Event/Evidence 기존 Test 1 Plan 1.0/Scenario, Test 2, Phase 1 Evidence
수정·삭제 금지.

## 5. Important-001 --- 실제 Path

Scenario A Validator가 연결: Asset JSON(asset_id/path/sha) →
REUSE_SEARCH(selected id/path/sha) → scenario_task_plan(executor
path/sha) → RUN_STARTED(plan sha/executor sha) → 실제 Executor 파일.

PASS: - Asset path = selected_path = Plan executor.path - 모든 SHA =
실제 파일 SHA - Plan 실제 SHA = RUN_STARTED task_plan_sha256 -
subprocess가 Plan Executor path 사용 - approved Asset 존재 시
byte-identical copy/중복 파일 실행 금지 경로는 정규화하되 서로 다른 실제
파일을 같게 취급 금지.

## 6. Mutation D

격리 복사본에서 approved 원본 유지 + byte-identical copy 생성 + Plan은
copy 실행 + REUSE_SEARCH는 원본 선택 유지. 기대: Validator FAIL / Gate
BLOCK. 실패 이유 path mismatch/duplicate execution. Hash 동일만으로 PASS
금지.

## 7. Important-002 --- CREATE 선행성

Scenario B/C에서: REUSE_SEARCH time \< created executor file creation
time \< RUN_STARTED time 을 강제.

Event time과 파일 creation time을 동일 기준으로 비교. 파일시스템 시간
해상도 고려. 불확실하면 임의 PASS 금지. 가능하면 기존 생성시각 사용, 새
Event Type은 추가하지 않는다. 신뢰 가능한 생성시각을 얻을 수 없으면
우회하지 말고 보고.

## 8. Mutation E

격리 Test에서 신규 Executor 파일을 먼저 생성 → REUSE_SEARCH → Run. 기대:
Validator FAIL / Gate BLOCK / CREATE-before-search 이유.

## 9. 기존 규칙 보존

exact search, approved/reference, approved 있으면 REUSE, 없을 때 CREATE,
Reference 실행 금지, Asset 목록 불변, REUSE_SEARCH가 RUN_STARTED보다 앞,
Executor 자기평가 불신, Event/Run/Evidence 직접 검증, Common Harness
재사용.

## 10. Later 제외

reference_executed 상수 개선, Scenario 링크 확대는 보류.

## 11. Regression

기존 24개 의미 보존. 신규 Mutation D/E 최소 추가.
기존/신규/총/PASS/FAIL/ERROR 보고. 삭제/약화 금지.

## 12. Test Plan 1.1

-   MVP-TEST-1 / Reuse
-   plan_version 1.1
-   change_reason_ref Order-023 변경 Validator SHA 고정. Executor 변경
    시 SHA도 고정. Plan 1.0 소급 수정 금지.

## 13. New Official Run

전체 Test PASS 후 Plan 1.1 New Run. 새 Run ID, Execution PASS,
Validation PASS, Gate PROCEED, 새 Evidence/SHA, A/B/C 새 Evidence, 기존
Plan 1.0 보존.

## 14. Preservation

작업 전 Test 1 Plan 1.0 공식/Scenario/Event/Index/Run, Test 2, Phase 1,
Architecture/Terminology/Reference 기록. 작업 후 기존 모두 불변, Plan
1.1만 추가, Ownership Harness 불변.

## 15. View

Claude Recheck 전 Test 1 공식 PASS 금지. Order-023 PASS 후
`Test 1 Reuse = PASS 후보 — Delta Recheck 대기`. Index: Order-022 PASS
WITH IMPORTANT FIX, Order-023 결과, Test 1 후보, Test 2 PASS, Now/Next.
History: Order-022/023 결과.

## 16. 하지 말 것

Test 4/3/5/6/7, Fingerprint/Retry, Prevention/Rule, USER-GATE,
Scheduler/WAIT, Registry 확장, DB/SQLite, Agent/Plugin/Adapter,
Architecture/Terminology, Phase 1 Core, 기존 Evidence rewrite, Phase 2
금지.

## 17. Architecture Delta

기본 NONE. 필요 시 ARCHITECTURE-DELTA 보고 후 중단.

## 18. Validation

### Important-001

-   [ ] Asset path
-   [ ] REUSE_SEARCH path
-   [ ] Plan Executor path
-   [ ] 실제 Executor path
-   [ ] SHA 연결
-   [ ] Plan SHA ↔ RUN_STARTED
-   [ ] Mutation D FAIL/BLOCK

### Important-002

-   [ ] REUSE_SEARCH time
-   [ ] created file time
-   [ ] RUN_STARTED time
-   [ ] 정상 B/C search \< create \< run
-   [ ] Mutation E FAIL/BLOCK

### Regression

-   [ ] 기존 24 의미 유지
-   [ ] 신규 PASS
-   [ ] Harness 독립성 유지

### Official 1.1

-   [ ] MVP-TEST-1 / Reuse / 1.1 / Order-023
-   [ ] New Run
-   [ ] Execution PASS
-   [ ] Validation PASS
-   [ ] Gate PROCEED
-   [ ] Evidence + SHA
-   [ ] Scenario 연결

### Preservation/Scope

-   [ ] Plan 1.0/Test2/Phase1 불변
-   [ ] Architecture/Terminology/Reference 불변
-   [ ] 다른 Test 없음
-   [ ] 외부 패키지/DB/Agent/Phase2 없음

하나라도 실패하면 PASS 금지. 검사 자체 실패는 ERROR.

## 19. 결과 보고

# Order-023 Reuse Validator Important Fix 결과

-   현재 상태
-   Important-001/002
-   변경 파일
-   Mutation D/E
-   Path: Asset → REUSE_SEARCH → Plan → 실제 Executor
-   CREATE 순서: Search → file creation → RUN_STARTED
-   Regression
-   Official Plan 1.1: ID/Version/reason/Run/Plan/Executor/Validator
    Hash/Validation/Gate/Evidence/SHA/Scenario
-   Preservation
-   Test 1 PASS 후보-Recheck 대기 / Test 2 PASS / Test 3\~7 NOT VERIFIED
-   Architecture Delta / Scope
-   Done/Now/Next

PASS Next: Claude READ-ONLY Reuse Validator Delta Recheck → PASS이면
Test 1 OFFICIAL PASS → Test 4 Bottleneck. 사용자 승인 필요 NO.

## 20. 종료 조건

Important 2건, Negative Test, Regression, Plan 1.1 New Run,
Preservation, View 갱신 후 종료. PASS해도 Claude/Test4/다른
Test/Architecture/Phase2 자동 시작 금지.

=== ORDER END ===
