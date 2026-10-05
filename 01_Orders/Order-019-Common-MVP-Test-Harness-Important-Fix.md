# Beta Order --- Order-019 Common MVP Test Harness Important Fix

## 문서 정보

-   Order ID: Order-019
-   Project: Beta
-   Status: APPROVED
-   Type: Targeted Important Fix + Revalidation
-   Architecture: Harness-A-Architecture-v1.0.md / FROZEN
-   Terminology: Terminology.md / FROZEN
-   Source Review: Order-018
-   Target: Common MVP Test Harness + MVP Test 2 Ownership
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

Order-018의 IMPORTANT 2건만 수정한다. 1. Ownership Validator가 BLOCK
여부뿐 아니라 정확한 BLOCK 사유까지 검증. 2. Scenario Executor의
PYTHONPATH/경로 숨은 의존 제거.

기존 Test Plan 1.0과 Evidence는 보존하고 새 Plan 1.1 + New Official
Run + Evidence로 재검증한다. 다른 MVP Test는 시작하지 않는다.

## 2. 근거

Order-018 = PASS WITH IMPORTANT FIX, Blocker NONE, 공식 Test 2 Evidence
유효, Architecture Delta NONE, 사용자 승인 NO.

## 3. Precondition

Architecture/Terminology FROZEN, Phase 1 CLOSED, Order-017 PASS 후보,
Order-018 결과, Test 1/3/4/5/6/7 NOT VERIFIED, 기존 Test 2 Plan 1.0
Run/Evidence 존재를 확인. 다르면 BLOCK.

## 4. Write Scope

수정 허용: - 03_Tests`\fixtures`{=tex}`\ownership`{=tex}\_validator.py -
03_Tests`\fixtures`{=tex}`\ownership`{=tex}\_scenario_executor.py -
03_Tests`\test`{=tex}\_mvp_ownership.py - 필요한 Ownership Fixture 최소
수정 -
03_Tests`\fixtures`{=tex}`\task`{=tex}\_mvp_test_2_ownership.json: New
Run은 plan_version 1.1, change_reason_ref=Order-019 - Beta-Index.md -
01_Orders`\Order`{=tex}-History.md - Plan 1.1 신규 Event/Evidence

기존 Plan 1.0/Scenario/Phase 1 Evidence 수정·삭제 금지. 그 외 수정 금지.

## 5. Important-001 --- BLOCK Reason

Scenario B Validator: - BLOCKED reason이 write_owner 단일 식별자 계약
위반임을 확인 - missing field/hash mismatch 등 다른 BLOCK을 Ownership
PASS로 인정 금지 - RUN_STARTED/Run 폴더/성공 Evidence 없음 확인

Scenario C same version: - BLOCKED reason이 Task Plan Hash 불일치 -
first_task_plan_sha256 존재 및 기준 Codex Run 최초 Plan Hash와 일치 -
attempted Plan Hash가 변경 Fixture 실제 Hash와 일치 - 새 정상 Run 없음 -
기존 Codex Run/Evidence 불변

문구 전체 문자열에 과도하게 결합하지 말고 안정적인 reason 구조/키워드의
최소 조건을 사용한다.

## 6. Negative Test

Mutation B: - Owner 정상 - 필수 steps 삭제 - 내부 Task BLOCK 가능 - 공식
Ownership Validator는 FAIL, Gate PROCEED 금지

Mutation C: - same-version Fixture를 Owner 형식 오류로 먼저 BLOCK되게
변경 - 내부 Task BLOCK 가능 - 공식 Ownership Validator는 FAIL, Gate
PROCEED 금지

Beta 실제 Evidence를 훼손하지 않는 격리 Test에서 수행.

## 7. Important-002 --- 실행 환경 의존 제거

ownership_scenario_executor.py: - **file** 기준으로 Beta Root/02_Core
경로 계산 - subprocess 내부에서 beta_core import 가능 - 전역 PYTHONPATH
설정 불필요 - 외부 설치 불필요 - C:`\Obsidian`{=tex}`\Beta `{=tex}절대
경로 하드코딩 금지 - 경로 계산 실패 시 명확한 ERROR

## 8. Windows 경로

Production 경로 시스템을 만들지 않는다. Test Harness에서: - 격리 임시
Root를 짧게 유지 - 불필요한 중첩 경로 금지 - 실제 Beta와 다른 짧은
경로에서도 재현 Windows Registry/OS 설정 변경 금지.

## 9. Environment Reproduction

Beta 밖 격리 복사본: A. PYTHONPATH 미설정 + 짧은 임시 경로 → 전체 PASS
B. PYTHONPATH 미설정 + 일반 다른 프로젝트 경로 → 전체 PASS C. Beta 실제
경로와 동등 구조 → 전체 PASS

과도한 장경로 OS 한계 자체는 PASS 조건 아님.

## 10. Harness 독립성 보존

-   Executor/Validator 별도 프로세스
-   Validator는 scenario_runs 자기평가 미사용
-   Event/Run/Evidence 직접 검증
-   Scenario 허용 Root 확인
-   기존 Gate/Evidence 재사용
-   새 DB/STATE SSOT 없음

## 11. Regression

기존 Phase 1 17 + Ownership 1 = 18개 의미 유지. Important Fix용 Negative
Test 추가 가능. 기존 Test 삭제/약화 금지. 보고: 기존/신규/총 Test,
PASS/FAIL/ERROR.

## 12. Test Plan 1.1

-   Test ID MVP-TEST-2
-   Name Ownership
-   plan_version 1.1
-   change_reason_ref Order-019
-   변경된 Scenario Executor SHA-256 고정
-   변경된 Validator SHA-256 고정 기존 Plan 1.0 Event/Evidence 소급 수정
    금지.

## 13. New Official Run

전체 Test PASS 후 Plan 1.1 New Run. 기대: - 새 Run ID - Execution PASS -
Validation PASS - Gate PROCEED - 새 Evidence/SHA-256 - 새 Scenario A/B/C
Evidence - 기존 Plan 1.0 Evidence 보존 강화된 BLOCK reason 검사를 실제
통과해야 한다.

## 14. Preservation

작업 전 Plan 1.0 공식/Scenario Evidence Hash, Event/Index, Run 목록
기록. 작업 후 기존 Plan 1.0/Scenario/Run/Phase 1 Evidence 불변, Plan
1.1만 추가. rewrite 금지.

## 15. View 정정

Claude Recheck 전 Test 2를 공식 PASS로 확정 금지. - 작업 중/실패: PASS
후보 / IMPORTANT FIX - Order-019 PASS 후: PASS 후보 --- Recheck 대기

Beta-Index: - Order-018 PASS WITH IMPORTANT FIX - Test 2 PASS
후보/Recheck 대기 - Order-019 결과 - Now/Next

Order-History: - Order-018 결과 - Order-019 결과

## 16. 하지 말 것

Test 1/3/4/5/6/7, Asset Registry, Fingerprint, Prevention, USER-GATE,
Resume, Scheduler/WAIT, F1/F2, Architecture/Terminology, Phase 1 Core,
기존 Evidence, 외부 패키지, OS 설정, Phase 2 수정 금지.

## 17. Architecture Delta

기본 NONE. 필요 시 ARCHITECTURE-DELTA 보고 후 중단.

## 18. Validation

### Important-001

-   [ ] B reason=Owner 계약 위반
-   [ ] 다른 reason PASS 금지
-   [ ] C reason=Plan Hash mismatch
-   [ ] first_task_plan_sha256 기준과 일치
-   [ ] attempted hash Fixture와 일치
-   [ ] Mutation B Validator FAIL
-   [ ] Mutation C Validator FAIL

### Important-002

-   [ ] PYTHONPATH 없이 import 성공
-   [ ] 절대 Beta 경로 없음
-   [ ] **file** 기반
-   [ ] 짧은 격리 경로 PASS
-   [ ] 일반 다른 경로 PASS
-   [ ] 불필요한 깊은 경로 없음

### Regression

-   [ ] 기존 18개 의미 유지
-   [ ] 신규 Negative Test PASS
-   [ ] Harness 독립성 유지

### Official Run

-   [ ] MVP-TEST-2 / Plan 1.1
-   [ ] change_reason_ref Order-019
-   [ ] New Run
-   [ ] Execution PASS
-   [ ] Validation PASS
-   [ ] Gate PROCEED
-   [ ] Evidence + SHA-256
-   [ ] Scenario 연결

### Preservation / Scope

-   [ ] Plan 1.0/Scenario/Phase 1 불변
-   [ ] Architecture/Terminology 불변
-   [ ] Phase 1 Core 불변
-   [ ] 다른 MVP Test 없음
-   [ ] 외부 패키지/Phase 2 없음

하나라도 실패하면 PASS 금지. 검사 자체 실패는 ERROR.

## 19. 결과 보고

# Order-019 Common Harness Important Fix 결과

-   현재 상태: PASS / FAIL / ERROR / BLOCKED
-   Important-001/002
-   변경 파일
-   Mutation B/C 결과
-   Environment A/B/C
-   PYTHONPATH 필요 여부 / 경로 문제
-   Regression: 기존/신규/총 Test, PASS/FAIL/ERROR
-   Official Plan 1.1: ID/Name/Version/reason/Run/Executor
    Hash/Validator Hash/Validation/Gate/Evidence/SHA/Scenario 연결
-   Preservation
-   MVP Test 1\~7 상태(Test 2는 PASS 후보 --- Recheck 대기)
-   Architecture Delta
-   Scope
-   Done/Now/Next
-   사용자 승인 필요: NO

PASS Next: Claude Code READ-ONLY Common Harness Delta Recheck → PASS이면
Test 2 공식 PASS 확정 → Test 1 Reuse 구현 Order.

## 20. 종료 조건

Important 2건, Regression, 환경 재현, Plan 1.1 New Run, Preservation,
View 갱신 후 종료. PASS해도 Claude 호출, Test 1/다른 Test, Architecture
변경, Phase 2 자동 시작 금지.

=== ORDER END ===
