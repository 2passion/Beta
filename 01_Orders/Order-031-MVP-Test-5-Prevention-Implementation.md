# Beta Order --- Order-031 MVP Test 5 Prevention Implementation

## 문서 정보

-   Order ID: Order-031
-   Project: Beta
-   Status: APPROVED
-   Type: MVP Test Implementation
-   Architecture / Terminology: FROZEN
-   Baseline: Phase 1 CLOSED + Common Harness reusable
-   Target: MVP Test 5 --- Prevention
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Root: `C:\Obsidian\Beta`

## 1. Intent

MVP Test 4 Bottleneck의 OFFICIAL PASS와 실제 실패→Fix→재검증 Evidence를
재사용하여 MVP Test 5 Prevention을 최소 구현한다.

검증 질문:

> 과거에 검증된 해결 경험이 다음 유사 작업에서 실제로 검색·재사용되는가?

핵심 흐름:

``` text
과거 FAIL
→ Fingerprint
→ Root Cause
→ Fix
→ New Run
→ Revalidation PASS
→ Verified Fix
→ Prevention Candidate
→ 다음 유사 Task
→ Prevention Search
→ REUSE
→ 실행
→ Evidence
```

Prevention은 Rule과 다르다. 이번 Order에서는 Prevention을 Active Rule로
승격하지 않는다.

## 2. 근거

Order-030: - PASS - Scenario B Decision Enforcement RESOLVED - Retry
Limit Blocker RESOLVED - Run/EVD Important RESOLVED - 새로운 Blocker
NONE - Test 4 Bottleneck OFFICIAL PASS 가능 - Bottleneck Review/Fix Loop
종료 가능 - 다음 구현 순서: Test 5 Prevention

Test 4의 실제 실패/Fingerprint/Fix/New Run/PASS 기록을 Prevention의
Source Evidence로 재사용한다.

## 3. Precondition

실행 전 확인:

-   Architecture / Terminology FROZEN
-   Phase 1 CLOSED
-   Test 1 Reuse OFFICIAL PASS
-   Test 2 Ownership OFFICIAL PASS
-   Test 4 Bottleneck OFFICIAL PASS
-   Test 5 NOT VERIFIED
-   Test 3/6/7 NOT VERIFIED
-   Common Harness reusable
-   Test 4 Plan 1.2 Evidence 존재
-   Phase 2 없음
-   기존 Prevention/Rule/Asset 검색 완료

다르면 BLOCK.

## 4. View Sync

이번 Write Owner 작업 시작 시 최소 동기화한다.

Beta-Index: - Order-030 PASS - Test 4 Bottleneck OFFICIAL PASS -
Bottleneck Review/Fix Loop CLOSED - Test 5 Prevention IMPLEMENTING / NOT
VERIFIED - Test 1/2 OFFICIAL PASS - Test 3/6/7 NOT VERIFIED - Now / Next

Order-History: - Order-030 PASS - Test 4 OFFICIAL PASS - Order-031 실제
상태

과거 결과 변경 금지.

## 5. Reuse Before Create

새 Prevention 구조를 만들기 전에 검색한다.

재사용 우선: - Test 4 Fingerprint - Test 4 Failure Class - Test 4
Scenario B의 baseline FAIL - Actual Fix Signature - change_reason_ref -
New Run / Revalidation PASS - Common MVP Test Harness - EventStore /
Evidence / Gate - JSON / JSONL

새 DB, Vector DB, Agent, Rule Engine을 만들지 않는다.

## 6. Prevention 최소 정의

Prevention은:

> 과거 문제에서 실제 재검증을 통과한 해결 지식을 다음 유사 작업에서
> 재사용하기 위한 기록

이다.

Prevention은 Rule이 아니다.

상태 최소: - `candidate` - `verified`

이번 Test에서 `verified`는 Prevention 재사용 Scenario 자체가 검증됐다는
의미다.

`active_rule` 상태는 만들지 않는다.

## 7. Prevention 최소 데이터

MVP Fixture/Record의 최소 필드:

-   `prevention_id`
-   `status`
-   `failure_fingerprint`
-   `failure_class`
-   `problem_description`
-   `root_cause`
-   `fix_description`
-   `fix_signature`
-   `source_fail_run_id`
-   `source_pass_run_id`
-   `source_evidence_ids`
-   `applicable_scope`
-   `created_from`
-   `verification_status`

가능하면 JSON 1개 또는 기존 Event/Evidence에 연결된 작은 JSON 구조를
사용한다.

운영용 Prevention Registry 위치/DB는 이번 Order에서 확정하지 않는다.

## 8. Verified Fix 자격

Prevention Candidate 생성은 다음이 모두 있어야 한다.

1.  실제 과거 FAIL 또는 ERROR
2.  Failure Fingerprint
3.  Root Cause가 가설이 아니라 확인된 원인으로 표시
4.  실제 Fix
5.  New Run
6.  Revalidation PASS
7.  PASS Evidence
8.  FAIL Evidence와 PASS Evidence 연결

하나라도 없으면 Prevention Candidate 생성 금지.

단순: - 성공했다는 문자열 - change_reason_ref만 존재 - Root Cause
Hypothesis만 존재 - Unit Test만 PASS 로는 Verified Fix가 아니다.

## 9. Source Evidence

가능하면 Test 4 Scenario B의 실제 기록을 Source Evidence로 사용한다.

기대 연결: - baseline FAIL Run - Fingerprint - 확인된 Root Cause - Fix
Signature - changed plan_version - change_reason_ref - fixed New Run -
Validation PASS - Gate PROCEED - FAIL/PASS Evidence

Source Evidence가 Prevention Record에서 실제 ID/Hash로 추적 가능해야
한다.

Test 4 원본 Evidence 수정 금지.

## 10. Prevention Search

다음 유사 Task가 들어오면 실행 전에 Prevention을 검색한다.

최소 검색 기준: - failure_fingerprint exact match 또는 - 이번 MVP에서
승인한 결정적 matching key

AI/LLM 의미 검색은 사용하지 않는다.

검색 Event 최소: `PREVENTION_SEARCH`

payload: - requested_fingerprint - matched_prevention_ids -
selected_prevention_id 또는 null - decision: `REUSE_PREVENTION` /
`NO_MATCH` - reason

## 11. Prevention Apply

verified Prevention이 정확히 일치하면:

``` text
PREVENTION_SEARCH
→ REUSE_PREVENTION
→ 해당 Fix를 새 Task Plan에 적용
→ 실행
→ Validation
→ Gate
→ Evidence
```

적용 Evidence: - prevention_id - source fail/pass Evidence -
applied_fix_signature - target task/run - 결과

Prevention을 찾았다는 이유만으로 PASS하지 않는다. 적용 후 실제
Revalidation PASS가 필요하다.

## 12. Scenario A --- Verified Prevention 생성

Test 4의 실제 FAIL→Fix→PASS Chain을 읽는다.

기대: - 모든 Verified Fix 자격 충족 - Prevention Candidate 생성 - Source
FAIL/PASS Evidence 연결 - fingerprint/fix_signature 일치 - status
candidate 또는 검증 단계에 맞는 값 - 원본 Evidence 불변

## 13. Scenario B --- 다음 유사 Task에서 재사용

새 합성 Task: - 과거와 동일 failure fingerprint 조건 - 아직 Fix가
적용되지 않은 상태

실행 전: - PREVENTION_SEARCH - verified/candidate 중 이번 Test 계약상
재사용 가능한 검증 대상 선택 - selected prevention - Fix 적용

기대: - 같은 실패를 먼저 재현하는 Blind Retry 없이 Fix가 선적용 - New
Task Run - Validation PASS - Gate PROCEED - Prevention 적용 Evidence
연결

목표는: `과거 실패 경험 때문에 다음 작업이 같은 실패를 반복하지 않는가`
를 증명하는 것이다.

## 14. Scenario C --- 다른 Fingerprint

새 Task의 failure fingerprint가 다름.

기대: - PREVENTION_SEARCH - NO_MATCH - 기존 Prevention 자동 적용 금지 -
다른 문제에 잘못 재사용하지 않음

이번 Test에서 새 Fix를 자동 생성하지 않는다.

## 15. Scenario D --- 미검증 Fix

Prevention 후보처럼 보이지만 다음 중 하나가 빠진 Fixture: - PASS
Evidence 없음 - Root Cause 미확인 - New Run 없음 - Revalidation PASS
없음

기대: - REUSE_PREVENTION 금지 - 적용 금지 - Validator FAIL 또는
NO_MATCH/NOT_ELIGIBLE

## 16. Rule 경계

이번 Order에서 반드시 확인:

-   Prevention 생성 ≠ Rule 활성화
-   Prevention 재사용 성공 ≠ 자동 Active Rule
-   `active_rule` 생성 금지
-   전역/Core Rule 변경 금지
-   Rule 승격 Gate/User Gate 미실행

Rule Candidate/Active는 향후 별도 범위다.

## 17. Prevention Validator

별도 프로세스 Validator는 Scenario Executor 자기평가를 신뢰하지 않는다.

직접 확인: - Source FAIL Event/Evidence - Fingerprint - Root Cause 확인
상태 - Fix Signature - Source PASS Run/Evidence - Prevention Record -
PREVENTION_SEARCH - 적용 대상 Plan - 실제 적용된 Fix Signature - Target
Run/Event/Evidence - Validation/Gate - Rule 미생성

PASS 조건: A. Verified Fix 자격이 실제 Evidence로 충족 B. Prevention이
Source Evidence에 추적 가능 C. 동일 Fingerprint Task에서 검색/재사용 D.
재사용 후 실제 PASS E. 다른 Fingerprint에는 미적용 F. 미검증 Fix는
미적용 G. Rule 자동 승격 없음

## 18. Negative Test

최소:

### Mutation A --- PASS Evidence 없음

Prevention 생성/재사용 시도 → FAIL/BLOCK

### Mutation B --- 다른 Fingerprint에 강제 적용

→ FAIL/BLOCK

### Mutation C --- Root Cause Hypothesis만 있음

확인된 Root Cause 없이 재사용 → FAIL/BLOCK

### Mutation D --- Fix Signature 불일치

기록된 Fix와 실제 적용 Fix가 다름 → FAIL/BLOCK

### Mutation E --- Prevention을 Active Rule로 자동 승격

→ FAIL/BLOCK

## 19. Common Harness 재사용

흐름:

``` text
MVP Test Plan
→ Prevention Scenario Executor
→ Source Evidence 읽기
→ Prevention 생성/검색/적용
→ 내부 Run/Event/Evidence
→ 독립 Prevention Validator
→ 기존 Gate
→ 공식 MVP Test Evidence
```

Prevention 전용 새 Harness/DB/STATE SSOT 금지.

## 20. Core 변경 최소화

우선순위: 1. 기존 Test 4 Evidence/Fingerprint 재사용 2. Common Harness
재사용 3. Fixture/Scenario 수준 4. 정말 공통 Runtime 기능이 필요할 때만
작은 `prevention.py` 5. Core CLI 변경은 최소

논리 역할마다 프로그램 생성 금지.

## 21. Regression

기존 40개 Test 의미를 모두 보존한다.

신규: - Scenario A\~D - Negative A\~E - 필요한 최소 계약 Test

보고: - 기존 Test - 신규 Test - 총 Test - PASS / FAIL / ERROR

기존 Test 삭제/약화 금지.

## 22. 공식 MVP Test 5 Run

전체 Test PASS 후 공식 Run:

-   canonical mvp_test_id: `MVP-TEST-5`
-   Name: `Prevention`
-   Plan Version: `1.0`
-   change_reason_ref: `Order-031`

기대: - Execution PASS - Validation PASS - Gate PROCEED - 공식
Evidence + SHA-256 - Scenario A\~D 연결 - Source Test 4 FAIL/PASS
Evidence 연결 - Prevention Search/Apply Evidence - Rule 미생성 근거

## 23. Preservation

작업 전/후 확인: - Phase 1 - Test 1 - Test 2 - Test 4 Plan 1.0/1.1/1.2 -
Common Harness - Core - Architecture/Terminology - Reference

기존 Evidence/Run 불변. Test 5 기록만 추가.

## 24. 이번 Order에서 하지 말 것

-   Test 6 User Gate
-   Test 7 Resume
-   Test 3 Safe Parallel
-   Active Rule 생성
-   Rule Candidate 승격 Workflow
-   전역/Core Rule 변경
-   Agent/Skill/Hook
-   Plugin/Adapter
-   Vector DB/SQLite/복잡 DB
-   AI 의미 검색
-   Architecture/Terminology 변경
-   기존 Evidence rewrite
-   Phase 2

## 25. Architecture Delta

기본 예상: `NONE`

FROZEN Architecture 변경 필요 시 임의 수정하지 않고 `ARCHITECTURE-DELTA`
보고 후 해당 구현 중단.

## 26. View / History

완료 후 최소 갱신.

Beta-Index: - Order-030 PASS - Test 4 Bottleneck OFFICIAL PASS -
Bottleneck Review/Fix Loop CLOSED - Order-031 결과 - Test 5 상태 - Now /
Next

Order-History: - Order-030 PASS - Test 4 OFFICIAL PASS - Order-031 실제
결과

Independent Review 전:
`Test 5 Prevention = PASS 후보 — Independent Review 대기`

## 27. Validation Checklist

### Verified Fix

-   [ ] Source FAIL 존재
-   [ ] Fingerprint 존재
-   [ ] 확인된 Root Cause
-   [ ] 실제 Fix
-   [ ] New Run
-   [ ] Revalidation PASS
-   [ ] FAIL/PASS Evidence 연결

### Prevention Record

-   [ ] 최소 필드
-   [ ] Source Evidence ID/Hash 추적
-   [ ] Fingerprint/fix_signature 일치
-   [ ] 원본 Evidence 불변

### Search / Apply

-   [ ] PREVENTION_SEARCH 실행 전
-   [ ] 동일 Fingerprint match
-   [ ] Prevention 선택
-   [ ] Fix 선적용
-   [ ] 같은 실패 재현 없이 Target Run
-   [ ] Target Validation PASS
-   [ ] Gate PROCEED
-   [ ] 적용 Evidence

### Boundaries

-   [ ] 다른 Fingerprint 미적용
-   [ ] 미검증 Fix 미적용
-   [ ] Active Rule 없음
-   [ ] Rule 자동 승격 없음

### Negative

-   [ ] PASS Evidence 없음 → FAIL/BLOCK
-   [ ] 다른 Fingerprint 강제 적용 → FAIL/BLOCK
-   [ ] Root Cause Hypothesis만 → FAIL/BLOCK
-   [ ] Fix Signature 불일치 → FAIL/BLOCK
-   [ ] Active Rule 자동 승격 → FAIL/BLOCK

### Regression

-   [ ] 기존 40개 의미 유지
-   [ ] 신규 Test PASS

### Official

-   [ ] MVP-TEST-5 / Prevention / Plan1.0 / Order-031
-   [ ] PASS / PASS / PROCEED
-   [ ] Evidence + SHA
-   [ ] Scenario A\~D
-   [ ] Test4 Source Evidence 연결
-   [ ] Rule 미생성

### Preservation / Scope

-   [ ] Test1/2/4/Phase1 불변
-   [ ] Core/Architecture/Reference 불변
-   [ ] Test3/6/7 미구현
-   [ ] Rule 활성화 없음
-   [ ] 외부 DB/Agent 없음
-   [ ] Phase2 없음

필수 항목 하나라도 실패하면 Test 5 PASS 금지. 검사 자체 실패는 ERROR.

## 28. 결과 보고 형식

# Order-031 MVP Test 5 Prevention 결과

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### View Sync

Index / History.

### Prevention 구현

데이터 구조, Source Evidence, Search/Apply.

### 생성/수정 파일

목록.

### Verified Fix Source

FAIL Run / Fingerprint / Root Cause / Fix / PASS Run / Evidence.

### Scenario A\~D

각 결과.

### Negative A\~E

각 결과.

### Rule Boundary

Prevention과 Rule 분리 결과.

### Regression

기존 / 신규 / 총 / PASS / FAIL / ERROR.

### 공식 MVP Test 5

ID / Name / Version / reason / Run / Plan·Executor·Validator Hash /
Validation / Gate / Evidence / SHA / Scenario / Source Evidence.

### Preservation

Phase1 / Test1 / Test2 / Test4 / Core / Architecture / Reference.

### MVP Test 상태

-   Test 1 Reuse: OFFICIAL PASS
-   Test 2 Ownership: OFFICIAL PASS
-   Test 3 Safe Parallel: NOT VERIFIED
-   Test 4 Bottleneck: OFFICIAL PASS
-   Test 5 Prevention: PASS 후보 --- Independent Review 대기 / FAIL /
    ERROR
-   Test 6 User Gate: NOT VERIFIED
-   Test 7 Resume: NOT VERIFIED

### Architecture Delta / Scope

상세.

### Done / Now / Next

PASS: → Claude Code READ-ONLY MVP Test 5 Independent Review → PASS이면
Test 5 OFFICIAL PASS → Test 6 User Gate 구현 Order

FAIL/ERROR: → Root Cause → Blind Retry 금지 → 최소 Fix

### 사용자 승인 필요

NO

## 29. 종료 조건

View Sync, Prevention 구현, Source Evidence 연결, Scenario, Negative
Test, Regression, 공식 Run, Evidence, Preservation, Index/History 갱신
후 종료한다.

PASS해도 자동 시작 금지: - Claude Code 호출 - Test 6/다른 Test - Rule
승격 - Architecture 변경 - Phase 2

결과를 ChatGPT Project Beta에 전달한다.

=== ORDER END ===
