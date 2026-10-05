# Beta Order --- Order-015 Final Timeout Delta Recheck

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-015
-   Project: Beta
-   Status: APPROVED
-   Order Type: READ-ONLY Final Timeout Delta Recheck
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Status: FROZEN
-   Terminology: `Terminology.md`
-   Terminology Status: FROZEN
-   Implementation Under Review: Order-014
-   Reviewer: Claude Code
-   Write Owner of reviewed implementation: Codex
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Order-014에서 수정한 shared timeout Root Cause만 최종 재확인한다.

이번 Order는 Phase 1 전체 Cross Review가 아니다. 새로운 Mutation 탐색,
LATER 발굴, 기능 개선 제안을 하지 않는다.

확인 범위:

1.  Executor Timeout / Validator Timeout 실제 분리
2.  정상 Executor가 Validator Timeout의 영향을 받지 않음
3.  Timeout Test 반복 안정성
4.  plan 1.3 New Run / Evidence 정합성
5.  기존 plan 1.0 / 1.1 / 1.2 기록 보존
6.  Architecture / Scope 불변

모두 PASS하면 Phase 1 Review/Fix 수정 루프를 종료한다.

## 2. 권한

이번 Order는 READ-ONLY다.

Claude Code는 다음을 하지 않는다.

-   Core 수정
-   Test / Fixture 수정
-   Evidence 수정
-   Beta-Index / Order-History 수정
-   Architecture / Terminology 수정
-   새 파일 생성
-   파일 삭제 / 이동 / 이름 변경
-   Fix 수행
-   Mutation 후보 추가
-   LATER 후보 추가
-   Phase 2 시작
-   MVP Test 추가 구현
-   Git 작업

검증은 읽기, Hash 재계산, Beta 밖 격리 복사본에서의 비파괴 Test에
한정한다.

## 3. Precondition

실행 전 확인:

-   Order 마지막 `=== ORDER END ===`
-   Architecture v1.0 FROZEN
-   Terminology FROZEN
-   Order-010 PASS
-   Order-011 PASS WITH IMPORTANT FIX
-   Order-012 PASS
-   Order-013 FAIL
-   Order-014 PASS
-   Phase 2 미착수
-   plan 1.0 / 1.1 / 1.2 / 1.3 기록 존재

전제가 다르면 BLOCKED.

## 4. 반드시 읽을 대상

### 기준

-   `Beta-Index.md`
-   `00_Architecture\Harness-A-Architecture-v1.0.md`
-   `00_Architecture\Terminology.md`
-   `01_Orders\Order-014-Executor-Validator-Timeout-Separation-Fix.md`
-   `01_Orders\Order-History.md`

### 변경 코드 / Test

-   `02_Core\beta_core\cli.py`
-   Order-014에서 실제 수정된 다른 Core 파일이 있다면 해당 파일
-   `03_Tests\test_phase1.py`
-   `03_Tests\fixtures\task_phase1.json`
-   `03_Tests\fixtures\validator_timeout.py`

### Evidence

-   `04_Evidence\phase1\events.jsonl`
-   `04_Evidence\phase1\evidence_index.jsonl`
-   plan 1.0 / 1.1 / 1.2 / 1.3 EVD
-   네 Run 디렉터리의 실제 결과 파일

## 5. Check 1 --- Timeout 책임 분리

실제 코드에서 확인한다.

PASS 조건:

-   `executor_timeout_seconds` 존재
-   `validator_timeout_seconds` 존재
-   Executor subprocess는 Executor Timeout만 사용
-   Validator subprocess는 Validator Timeout만 사용
-   Validator의 짧은 Timeout 값이 Executor에 전달되지 않음
-   기존 Execution ERROR / Validation ERROR 의미 유지
-   CLI가 두 Timeout을 독립적으로 받을 수 있음

단순 변수명만 두 개이고 내부에서는 다시 하나로 합치는 구현이면 FAIL.

판정: PASS / FAIL

## 6. Check 2 --- Timeout Test 의미

Validator Timeout Test를 직접 읽는다.

PASS 조건:

-   Executor Timeout은 정상 Executor가 완료하기 충분한 값
-   Validator Timeout은 Fixture sleep보다 짧음
-   Executor가 먼저 정상 완료됨
-   `RUN_COMPLETED` 존재
-   `EXECUTION_ERROR` 없음
-   Validator가 Timeout
-   Validation ERROR
-   Gate BLOCK

현재 보고값: - Executor Timeout 10.0초 - Validator Timeout 0.1초 -
Validator Fixture sleep 1.0초

실제 코드/Test와 일치하는지 확인한다.

판정: PASS / FAIL

## 7. Check 3 --- 반복 안정성

Beta 원본을 변경하지 않는 격리 복사본에서 검증한다.

최소:

1.  Validator Timeout Test 단독 20회
2.  Executor Error + Validator Timeout 묶음 10회
3.  전체 Test Suite 10회

가능하면 Order-013과 유사한 합리적 CPU 부하 상황에서 Validator Timeout
Test를 추가 확인한다.

PASS 조건:

-   정상 Executor Timeout = 0
-   Validator Timeout Test가 매번 Validation ERROR / Gate BLOCK
-   flaky FAIL = 0
-   전체 Suite의 Timeout 관련 실패 = 0

외부 Stress Tool 설치 금지.

판정: PASS / FAIL

## 8. Check 4 --- 기존 17 Test 회귀

전체 Test Suite가 Order-014 수정 후에도 기존 의미를 유지하는지 확인한다.

PASS 조건:

-   총 Test 수 최소 17
-   17개 기존 의미 모두 존재
-   1회 전체 실행 PASS
-   Timeout API 분리 때문에 다른 Test가 약화되지 않음

새 Test를 요구하지 않는다.

판정: PASS / FAIL

## 9. Check 5 --- plan 1.3 New Run

실제 Event / Evidence를 직접 검산한다.

기대:

-   Task ID: `TASK-PHASE1-SYNTHETIC-001`
-   plan_version: `1.3`
-   Run ID: `RUN-be4dc547-28fd-4a33-a2b3-db4e9907fa2e`
-   change_reason_ref: `Order-014`
-   Execution PASS
-   Validation PASS
-   Gate PROCEED

독립 재계산:

-   task_plan_sha256
-   executor_sha256
-   validator_sha256
-   Evidence SHA-256

Evidence index / Event payload / 실제 파일과 서로 일치해야 한다.

판정: PASS / FAIL

## 10. Check 6 --- Preservation

Order-014 이전 기록을 독립 검산한다.

### Event prefix

기존 20줄 / 9,695바이트가 현재 `events.jsonl`의 byte-prefix로 동일한지
확인.

기대 SHA-256:
`639CC529B6AA6D5A9689ACCE9424FD116F8C3C9B7BECC3349999D5CB1D572077`

### Evidence Index prefix

기존 3줄 / 1,798바이트가 현재 index의 byte-prefix로 동일한지 확인.

기대 SHA-256:
`2A4A790FB449F32DBB0EA30BD49018CED3946138536F0D76207F2E10D88CEC0B`

### EVD

plan 1.0 / 1.1 / 1.2 기존 EVD Hash 불변 확인.

### Run

기존 Run 디렉터리 3개 보존 확인.

### Append

-   신규 Event 7개만 추가
-   신규 Evidence Index 1행만 추가
-   최종 Event 27개
-   최종 Evidence 4개
-   Event ID 중복 없음

판정: PASS / FAIL

## 11. Check 7 --- Architecture / Scope

확인:

-   Architecture / Terminology FROZEN 불변
-   Reference 불변
-   F1/F2 수정 없음
-   다른 LATER 수정 없음
-   Phase 2 없음
-   다른 MVP Test 구현 없음
-   외부 패키지 없음
-   네트워크/API/Agent 없음
-   SQLite 없음
-   Order-013 FAIL 기록 보존
-   Order-014 PASS 기록

`runpy` 비치명 경고는 이번 Scope 밖이며 판정에 포함하지 않는다.

판정: PASS / FAIL

## 12. 새로운 Blocker 검사

Order-014 변경으로 직접 발생한 다음 문제만 확인한다.

-   두 Timeout이 실제로 분리되지 않음
-   정상 Executor가 Validator Timeout 때문에 실패
-   Validator Timeout이 PASS/PROCEED로 샘
-   plan 1.3 Evidence 불일치
-   과거 Event/Evidence 변경
-   Architecture/Scope 위반

없으면: `NONE`

새로운 개선사항을 발굴하지 않는다.

## 13. 최종 판정

이번 Recheck는 다음만 사용한다.

### PASS

-   Check 1\~7 모두 PASS
-   새로운 Blocker NONE
-   shared timeout Root Cause 해결 확인
-   Phase 1 수정 루프 종료 가능

### FAIL

-   Check 1\~7 중 하나 이상 실질 FAIL
-   shared timeout Root Cause 미해결
-   Order-014 변경으로 직접 문제 발생

### BLOCKED

-   필수 파일 접근 실패
-   Order 불완전
-   독립 검증 불가

`PASS WITH MINOR/IMPORTANT`는 사용하지 않는다.

## 14. 결과 보고 형식

# Order-015 Final Timeout Delta Recheck 결과

### 현재 판정

PASS / FAIL / BLOCKED

### Check Matrix

  Check                    판정   핵심 근거
  ------------------------ ------ -----------
  1 Timeout 책임 분리             
  2 Timeout Test 의미             
  3 반복 안정성                   
  4 기존 17 Test 회귀             
  5 plan 1.3 New Run              
  6 Preservation                  
  7 Architecture / Scope          

### Root Cause

shared timeout: RESOLVED / NOT_RESOLVED

### 새로운 Blocker

NONE 또는 상세.

### 반복 검증

-   Timeout 단독 20회
-   관련 묶음 10회
-   전체 Suite 10회
-   부하 검증 결과
-   정상 Executor Timeout 횟수
-   flaky FAIL 수

### plan 1.3 Evidence 독립 검산

-   Plan Hash
-   Executor Hash
-   Validator Hash
-   Evidence Hash
-   Event / Index 연결

### Preservation

-   Event prefix
-   Index prefix
-   plan 1.0 / 1.1 / 1.2 EVD
-   기존 Run
-   최종 Event / Evidence 수

### 파일 변경 확인

모든 Beta 파일: NO 새 파일: NO

### Done

Order-014 Timeout Fix 독립 재확인.

### Now

PASS이면 Local Core MVP Phase 1 Review/Fix 수정 루프 종료.

### Next

PASS: → ChatGPT Project Beta 검토 → MVP Test 1\~7 구현 순서 확정 → 다음
구현 Order

FAIL: → Root Cause 재분석 → 새로운 Fix 근거 → Blind Retry 금지

### 사용자 승인 필요

NO

## 15. 종료 조건

Check 1\~7과 결과 보고 후 종료한다.

어떤 Beta 파일도 수정하지 않는다.

PASS해도 자동으로: - Phase 2 - 다음 MVP Test - Architecture 변경 - Fix
를 시작하지 않는다.

결과를 ChatGPT Project Beta에 전달한다.

=== ORDER END ===
