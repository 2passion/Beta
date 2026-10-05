# Beta Order --- Order-033 Prevention Enforcement Fix

## 문서 정보

-   Order ID: Order-033
-   Project: Beta
-   Status: APPROVED
-   Type: Targeted Blocker / Important Fix + Revalidation
-   Architecture / Terminology: FROZEN
-   Source Review: Order-032
-   Target: MVP Test 5 --- Prevention
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Root: `C:\Obsidian\Beta`

## 1. Intent

Order-032에서 확인된 Prevention Blocker 1건과 관련 Important 3건만 최소
수정한다.

1.  Target Plan의 실제 내용에서 Fix Signature를 계산하여 Source
    Prevention Fix와 대조
2.  Candidate 적격성을 라벨이 아니라 실제 Source Evidence / Run / Hash로
    검증
3.  `MATCH + ELIGIBLE`일 때만 Fix 적용 및 `run_task` 호출
4.  Root Cause `CONFIRMED`가 실제 Source Evidence 근거를 갖도록 연결

정상 Prevention Workflow, Rule Boundary, Fingerprint, 기존 Test 4
Evidence는 재설계하지 않는다.

수정 후 Test 5 Plan 1.1 + New Official Run + Evidence로 재검증한다.

Test 6 User Gate는 시작하지 않는다.

## 2. 근거

Order-032 = REVISION REQUIRED.

### Blocker

Target Plan의 `prevention_application.fix_signature` 선언값만 Prevention
Record와 비교한다. Target Plan의 실제 executor / validator / criteria를
실패 버전으로 되돌려도 선언값을 유지하면 Validator가 PASS했다.

### Important

I1. Candidate eligibility가 `root_cause_status`, `verification_status`,
Evidence ID 개수 등 라벨 중심이다. I2. `NO_MATCH`인데도 Target
`run_task`가 실행될 수 있고 Validator가 사후 FAIL시키는 구조다. I3.
`root_cause_status = CONFIRMED`가 Executor 상수이며 Source Evidence에서
직접 추적되지 않는다.

### 이미 PASS

-   Test 4 Source Verified Fix Chain
-   PREVENTION_SEARCH 선행성
-   공식 정상 Scenario의 Fix 선적용
-   Target 첫 Run PASS
-   다른 Fingerprint NO_MATCH
-   미검증 Scenario 차단
-   Rule Boundary
-   Negative A\~E
-   공식 Evidence Hash
-   Regression 46/46
-   Preservation

## 3. Precondition

-   Architecture / Terminology FROZEN
-   Phase 1 CLOSED
-   Test 1 Reuse OFFICIAL PASS
-   Test 2 Ownership OFFICIAL PASS
-   Test 4 Bottleneck OFFICIAL PASS
-   Order-032 REVISION REQUIRED
-   Test 5 Plan 1.0 Evidence 존재
-   Test 3/6/7 NOT VERIFIED
-   Phase 2 없음

다르면 BLOCK.

## 4. Write Scope

수정 허용:

-   `03_Tests\fixtures\prevention_scenario_executor.py`
-   `03_Tests\fixtures\prevention_validator.py`
-   `03_Tests\test_mvp_prevention.py`
-   `03_Tests\fixtures\task_mvp_test_5_prevention.json` → Plan 1.1
-   필요 시 Plan 1.0 보존 Fixture
-   Test 5 Source/Prevention Fixture의 최소 필드 보강
-   `Beta-Index.md`
-   `01_Orders\Order-History.md`
-   Test 5 Plan 1.1 신규 Event/Evidence

기본 금지: - Core 변경 - Test 4 Evidence 변경 - Rule 파일 생성 -
DB/Agent 추가

기존 Test 5 Plan 1.0 Evidence 수정·삭제 금지.

## 5. Fix 1 --- Actual Fix Signature

Fix Signature는 선언 필드 자체를 Hash하지 않는다.

Target Plan의 실제 Fix 관련 내용에서 결정적으로 계산한다.

최소 입력: - executor identity / path / sha256 중 현재 Test 계약상 실제
Fix를 나타내는 값 - validator identity / path / sha256 - criteria -
Fix와 직접 관련된 plan fields

제외: - run_id - timestamp - Event ID - prevention_application의 선언된
`fix_signature` - 무관한 metadata

동일 Source Fix와 동일 Target Fix는 같은 Signature가 나와야 한다.

실패 버전의 실제 Plan은 다른 Signature가 나와야 한다.

## 6. Source Fix Signature

Test 4 Source의 실제 fixed Plan 1.1에서 같은 함수/규칙으로 Fix
Signature를 재계산한다.

기대: - 재계산 Source Signature - Prevention Record `fix_signature` 가
일치.

기존 보고값:
`84EB231C7F640BA0554C1BB3D95B0D458B0A9FE06E243B06CD32E914342C56D6`

값이 현재 실제 Source에서 재계산한 결과와 다르면 임의로 맞추지 말고 Root
Cause를 보고한다.

## 7. Target Fix Signature

Target Plan 실제 executor / validator / criteria에서 같은 방식으로
Signature를 계산한다.

PASS: - Target 실제 Signature = Source 실제 Signature = Prevention
Record Signature

또한: - Target Plan 실제 SHA-256 - Target `RUN_STARTED.task_plan_sha256`
가 일치해야 한다.

즉 Validator가 실제 Run이 검증된 Target Plan을 사용했음을 확인한다.

## 8. Mutation F --- Declared Signature 정상 / 실제 Plan 실패 버전

격리 복사본:

-   `prevention_application.fix_signature`는 정상값 유지
-   실제 Target Plan executor / validator / criteria를 실패 버전으로
    변경
-   Link Hash는 일관되게 갱신

기대: - Target 실제 Fix Signature 불일치 - Validator FAIL - Gate BLOCK

선언값만 같아서 PASS하면 실패.

## 9. Fix 2 --- Candidate Eligibility 실제 Source 검증

`eligible()` 또는 동등 함수는 라벨만 보지 않는다.

재사용 가능 Candidate 판정 시 최소 실제 확인:

-   Source FAIL Run 존재
-   Source PASS Run 존재
-   FAIL Evidence 존재
-   PASS Evidence 존재
-   Evidence SHA가 Record와 일치
-   Evidence가 해당 Run ID에 연결
-   Source failure fingerprint 일치
-   Source 실제 Fix Signature 일치
-   Root Cause Confirmation Evidence 존재
-   verification_status 계약 충족

Source 파일을 실제로 읽을 수 없는 Candidate는 `NOT_ELIGIBLE`.

## 10. Mutation G --- Fake Source

라벨은 정상: - status CANDIDATE - root_cause_status CONFIRMED -
verification_status SOURCE_CHAIN_VERIFIED

하지만: - 존재하지 않는 Evidence ID - 가짜 PASS Run ID - 가짜
fix_signature

기대: - eligible = false - PREVENTION_SEARCH에서 선택 금지 - run_task
0 - Validator FAIL 또는 NOT_ELIGIBLE

## 11. Fix 3 --- Search Decision → 실행 제어

Target Scenario B 실행은 다음 조건에 묶는다.

``` text
search_result = prevention_search(...)

IF search_result.decision == MATCH
AND selected prevention is ELIGIBLE
AND actual Source/Target Fix contract is valid
    → Fix 선적용
    → run_task
ELSE
    → run_task 호출 금지
```

`NO_MATCH`, `NOT_ELIGIBLE`, invalid source에서는 실행하지 않는다.

Validator의 사후 검출은 2차 방어선으로 유지한다.

## 12. Mutation H --- NO_MATCH 실행 시도

Target fingerprint를 다른 값으로 변경.

기대: - PREVENTION_SEARCH = NO_MATCH - run_task 호출 0 - RUN_STARTED 0 -
Run directory 0 - Runtime Evidence 0

강제로 실행시키는 별도 변형에서는 Validator FAIL / Gate BLOCK.

## 13. Fix 4 --- Root Cause Confirmation Evidence

`root_cause_status = CONFIRMED`를 상수 선언만으로 인정하지 않는다.

이번 MVP에서는 복잡한 Root Cause 시스템을 만들지 않는다.

최소 Source 근거:

-   FAIL Plan / Event의 실패 조건
-   Fix 전 실제 validator / criteria 상태
-   Fix 후 변경된 validator / criteria
-   동일 문제의 New Run PASS
-   Fix Signature 변경
-   관련 `change_reason_ref`
-   이 연결을 가리키는 Source Evidence reference

Prevention Record에 최소: - `root_cause_status = CONFIRMED` -
`root_cause_evidence_refs` 또는 동등한 명확한 Source 참조

를 둔다.

Validator는 참조 대상이 실제 존재하고 Source chain과 일치하는지
확인한다.

## 14. Mutation I --- Root Cause 근거 없음

Record 라벨: `root_cause_status = CONFIRMED`

하지만: - root_cause_evidence_refs 없음 또는 - 참조가 존재하지 않음 /
Source와 불일치

기대: - NOT_ELIGIBLE - 재사용 금지 - run_task 0

## 15. 기존 정상 Scenario B

수정 후에도 정상 흐름은 유지한다.

``` text
PREVENTION_SEARCH
→ MATCH
→ 실제 Source Eligibility PASS
→ Source Fix Signature 검증
→ Target Fix 선적용
→ Target 실제 Signature 일치
→ Target Plan SHA 고정
→ run_task
→ 첫 Target Run PASS
→ Gate PROCEED
```

같은 Source Fingerprint FAIL이 Target에서 먼저 발생하면 FAIL.

## 16. Defense in Depth

두 방어선 유지:

1.  Executor:
    -   NO_MATCH / NOT_ELIGIBLE / invalid Fix → 실행하지 않음
2.  Validator:
    -   실제 Plan 내용 불일치
    -   Source Evidence 위조
    -   BLOCK 후 실행
    -   Rule 자동 승격 등을 사후 검출

## 17. 기존 PASS 영역 보존

불필요하게 변경하지 않는다.

-   Test 4 Source chain
-   PREVENTION_SEARCH 선행
-   Target 첫 Run PASS 원칙
-   다른 Fingerprint NO_MATCH
-   Rule Boundary
-   Negative A\~E
-   Common Harness
-   canonical Test ID

## 18. Rule Boundary

계속 유지:

-   Prevention 상태 = CANDIDATE
-   Active Rule 없음
-   Rule 자동 승격 없음
-   Rule Registry 없음
-   Rule 승격 Workflow 없음
-   User Gate 없음

이번 Fix 성공을 Rule 승격 근거로 자동 사용하지 않는다.

## 19. Regression

기존 46개 Test 의미 유지.

신규 최소: - Mutation F - Mutation G - Mutation H - Mutation I - Target
Plan SHA ↔ RUN_STARTED 연결 Test - 필요한 최소 eligibility Test

기존 Test 삭제/약화 금지.

보고: - 기존 - 신규 - 총 - PASS / FAIL / ERROR

## 20. Test Plan 1.1

Executor / Validator 변경으로 새 Plan 사용.

-   canonical mvp_test_id: `MVP-TEST-5`
-   Name: `Prevention`
-   plan_version: `1.1`
-   change_reason_ref: `Order-033`

변경 Executor / Validator SHA 고정.

Plan 1.0 소급 수정 금지.

## 21. New Official Run

전체 Regression PASS 후 Plan 1.1 New Official Run.

기대: - New Run ID - Execution PASS - Validation PASS - Gate PROCEED -
New Evidence + SHA - Scenario A\~D - Source Test 4 Evidence 연결 -
Actual Source/Target Fix Signature Evidence - Target Plan SHA ↔
RUN_STARTED - Candidate Eligibility Evidence - Rule 미생성

## 22. Preservation

작업 전/후:

-   Test 5 Plan 1.0
-   Test 4 Plan 1.0/1.1/1.2
-   Test 1
-   Test 2
-   Phase 1
-   Core 7개
-   Common Harness
-   Architecture/Terminology
-   Reference

비교.

기존 Evidence rewrite 금지. Plan 1.1만 append.

## 23. View

Order-033 PASS 후 Claude Delta Recheck 전:

`Test 5 Prevention = PASS 후보 — Delta Recheck 대기`

Beta-Index: - Order-032 REVISION REQUIRED - Blocker / Important 요약 -
Order-033 결과 - Test 1/2/4 OFFICIAL PASS - Test 5 후보 - Now / Next

Order-History: - Order-032 결과 - Order-033 결과

## 24. 하지 말 것

-   Test 6 User Gate
-   Test 7 Resume
-   Test 3 Safe Parallel
-   Active Rule
-   Rule 승격 Workflow
-   Agent/Plugin/Adapter
-   Vector DB/SQLite
-   AI 의미 검색
-   Core 변경
-   Architecture/Terminology 변경
-   기존 Evidence rewrite
-   Phase 2

## 25. Architecture Delta

기본 `NONE`.

Core/Architecture 계약 변경 필요 시 임의 수정하지 말고
`ARCHITECTURE-DELTA` 보고 후 해당 구현 중단.

## 26. Validation Checklist

### Actual Fix

-   [ ] Source 실제 Fix Signature 계산
-   [ ] Record Signature와 일치
-   [ ] Target 실제 Fix Signature 계산
-   [ ] Source = Record = Target
-   [ ] Target Plan SHA = RUN_STARTED task_plan_sha256
-   [ ] Mutation F FAIL/BLOCK

### Eligibility

-   [ ] Source FAIL Run 실존
-   [ ] Source PASS Run 실존
-   [ ] FAIL/PASS EVD 실존
-   [ ] EVD SHA 일치
-   [ ] Run ↔ EVD 연결
-   [ ] Fingerprint 일치
-   [ ] 실제 Fix Signature 일치
-   [ ] Root Cause Evidence 실존
-   [ ] Mutation G NOT_ELIGIBLE

### Search Enforcement

-   [ ] MATCH + ELIGIBLE일 때만 run_task
-   [ ] NO_MATCH → 실행 0
-   [ ] NOT_ELIGIBLE → 실행 0
-   [ ] Mutation H 실행 0
-   [ ] 강제 실행 시 Validator FAIL

### Root Cause

-   [ ] CONFIRMED Source 근거
-   [ ] root_cause_evidence_refs 또는 동등 연결
-   [ ] Mutation I NOT_ELIGIBLE

### Prevention

-   [ ] Target 첫 Run PASS
-   [ ] Source fingerprint FAIL 선행 없음
-   [ ] Rule 미생성
-   [ ] Candidate 유지

### Regression

-   [ ] 기존 46 의미 유지
-   [ ] 신규 Test PASS

### Official 1.1

-   [ ] MVP-TEST-5 / Prevention
-   [ ] Plan1.1 / Order-033
-   [ ] New Run
-   [ ] PASS / PASS / PROCEED
-   [ ] Evidence + SHA
-   [ ] Source/Target Fix 실제 검증
-   [ ] Scenario 연결

### Preservation / Scope

-   [ ] Plan1.0 불변
-   [ ] Test1/2/4/Phase1 불변
-   [ ] Core/Architecture/Reference 불변
-   [ ] Test3/6/7 미구현
-   [ ] Active Rule 없음
-   [ ] Phase2 없음

필수 항목 하나라도 실패하면 PASS 금지. 검사 자체 실패는 ERROR.

## 27. 결과 보고 형식

# Order-033 Prevention Enforcement Fix 결과

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### Blocker Resolution

Actual Fix Verification 결과.

### Important Resolution

-   Candidate Eligibility
-   Search → Execution Control
-   Root Cause Confirmation Evidence

### 변경 파일

목록.

### Actual Fix

Source 실제 Signature / Record / Target 실제 Signature / Target Plan SHA
/ RUN_STARTED SHA.

### Eligibility

Source Run/Evidence/Hash/Root Cause 근거.

### Search Enforcement

MATCH / NO_MATCH / NOT_ELIGIBLE 각각 run_task 호출 수.

### Mutation F\~I

결과와 실패 이유.

### Regression

기존 / 신규 / 총 / PASS / FAIL / ERROR.

### Official Plan 1.1

ID / Name / Version / reason / Run / Plan·Executor·Validator Hash /
Validation / Gate / Evidence / SHA / Scenario.

### Preservation

Plan1.0/Test1/Test2/Test4/Phase1/Core/Architecture/Reference.

### MVP Test 상태

-   Test 1 Reuse: OFFICIAL PASS
-   Test 2 Ownership: OFFICIAL PASS
-   Test 3 Safe Parallel: NOT VERIFIED
-   Test 4 Bottleneck: OFFICIAL PASS
-   Test 5 Prevention: PASS 후보 --- Delta Recheck 대기 / FAIL / ERROR
-   Test 6 User Gate: NOT VERIFIED
-   Test 7 Resume: NOT VERIFIED

### Architecture Delta / Scope

상세.

### Done / Now / Next

PASS: → Claude Code READ-ONLY Prevention Enforcement Delta Recheck →
PASS이면 Test 5 OFFICIAL PASS → Test 6 User Gate 구현 Order

FAIL/ERROR: → Root Cause → Blind Retry 금지 → 최소 Fix

### 사용자 승인 필요

NO

## 28. 종료 조건

Blocker/Important 수정, Mutation F\~I, Regression, Plan1.1 New Run,
Preservation, View 갱신 후 종료.

PASS해도 자동 시작 금지: - Claude Code 호출 - Test 6/다른 Test - Rule
승격 - Architecture 변경 - Phase 2

결과를 ChatGPT Project Beta에 전달한다.

=== ORDER END ===
