# Beta Order --- Order-013 Local Core MVP Phase 1 Important Fix Recheck

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-013
-   Project: Beta
-   Status: APPROVED
-   Order Type: READ-ONLY Important Fix Recheck
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Status: FROZEN
-   Terminology: `Terminology.md`
-   Terminology Status: FROZEN
-   Implementation Under Review: Order-012
-   Reviewer: Claude Code
-   Write Owner of reviewed implementation: Codex
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Order-012에서 수정한 IMPORTANT 3건만 READ-ONLY로 재확인한다.

이번 Order는 Phase 1 전체 Cross Review를 반복하지 않는다. 새로운 기능
제안이나 LATER 후보를 적극 발굴하지 않는다.

확인 범위:

1.  Plan Version 불변성 및 변경 근거
2.  Fail-open 신규 Test
3.  Write Owner 단일 식별자
4.  기존 plan 1.0 / 1.1 Event·Evidence 보존
5.  Validator Timeout Fixture가 의도대로 동작하는지

위 범위가 모두 정상이고 새로운 Blocker가 없으면 Phase 1 수정 루프를
종료한다.

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
-   Phase 2 시작
-   MVP Test 추가 구현
-   Git 작업

검증은 읽기, Hash 계산, 격리 복사본에서의 비파괴 Test 실행으로 제한한다.

## 3. Precondition

-   Order 마지막 `=== ORDER END ===` 확인
-   Architecture v1.0 FROZEN
-   Terminology FROZEN
-   Order-010 PASS
-   Order-011 PASS WITH IMPORTANT FIX
-   Order-012 PASS
-   Phase 2 미착수
-   기존 plan 1.0 / 1.1 / 1.2 기록 존재

전제가 다르면 BLOCKED.

## 4. 반드시 읽을 대상

### 기준

-   `Beta-Index.md`
-   `00_Architecture\Harness-A-Architecture-v1.0.md`
-   `00_Architecture\Terminology.md`
-   `01_Orders\Order-012-Local-Core-MVP-Phase1-Important-Fix.md`
-   `01_Orders\Order-History.md`

### 변경 코드

-   `02_Core\beta_core\model.py`
-   `02_Core\beta_core\event_store.py`
-   `02_Core\beta_core\cli.py`
-   Order-012에서 실제 수정된 다른 Core 파일이 있다면 해당 파일

### Test / Fixture

-   `03_Tests\test_phase1.py`
-   `03_Tests\fixtures\task_phase1.json`
-   `03_Tests\fixtures\executor_error.py`
-   `03_Tests\fixtures\validator_timeout.py`
-   관련 기존 Fixture

### Evidence

-   `04_Evidence\phase1\events.jsonl`
-   `04_Evidence\phase1\evidence_index.jsonl`
-   plan 1.0 / 1.1 / 1.2의 모든 EVD 파일
-   세 Run 디렉터리의 실제 결과 파일

## 5. Check 1 --- Plan Version 불변성

실제 코드와 Test를 확인한다.

PASS 조건:

-   Task Plan SHA-256을 실행 전에 계산
-   `RUN_STARTED` 또는 동등한 실행 기록에 `task_plan_sha256` 추적
-   `executor_sha256` 추적
-   Validator SHA-256 추적
-   `change_reason_ref` 추적
-   한 번 사용된 `(task_id, plan_version)`과 Plan Hash의 연결을 검사
-   같은 `(task_id, plan_version)` + 다른 Plan Hash → Executor 전에
    BLOCK
-   기존 1.0 / 1.1 Event를 rewrite하지 않음
-   새 계약은 Order-012 이후 기록에 적용

추가 독립 시험:

격리 복사본에서 같은 task/version 라벨에 Plan 내용 또는
Validator/Executor 관련 계획 내용을 바꿔 실행을 시도하고 실제
BLOCK되는지 확인한다.

판정: PASS / FAIL

## 6. Check 2 --- 변경 근거

plan 1.2 New Run에서 다음을 확인한다.

-   plan_version = 1.2
-   새 Run ID
-   task_plan_sha256
-   executor_sha256
-   validator_sha256
-   change_reason_ref = Order-012 또는 동등한 명확한 참조
-   기존 Run과 별도 기록

중요:

과거 plan 1.0 / 1.1에 존재하지 않았던 change_reason_ref를 소급 추가하지
않았는지 확인한다.

판정: PASS / FAIL

## 7. Check 3 --- Fail-open Test

Order-011에서 빠져나갔던 네 경로를 각각 독립 확인한다.

### A. Executor 비정상 종료

기대: - EXECUTION_ERROR - Gate BLOCK - Validation PASS로 변환되지 않음

### B. Validator Timeout / 예외

기대: - Validation ERROR - Gate BLOCK - PASS로 변환되지 않음

### C. Evidence 기록 실패

기대: - 성공 Evidence 기록 없음 - Gate PROCEED 금지

### D. Event Log 보존

기대: - 두 번째 Run 뒤에도 첫 Event byte-prefix 보존 - 기존 Event ID
유지 - 새 Event만 append

각 항목에 실제 Test 이름과 검증 코드를 연결한다.

판정: PASS / FAIL

## 8. Check 4 --- Hash Test 독립성

Test가 Core의 Hash 함수를 그대로 사용해 자기 자신을 검증하지 않는지
확인한다.

PASS 조건:

-   Test에서 Python 표준 `hashlib` 직접 계산
-   Core 계산값 또는 Evidence/index 값과 비교
-   최소 Evidence Hash와 Plan/파일 Hash 중 Order-012에서 요구한 독립
    검산이 실제 존재

판정: PASS / FAIL

## 9. Check 5 --- Write Owner

실제 `model.py`와 Test를 확인한다.

MVP 허용 패턴:

`^[A-Za-z0-9][A-Za-z0-9_-]*$`

독립 확인:

허용: - Codex - Claude-Code - USR-001

BLOCK: - `Codex, Claude Code` - `Codex / Claude` - `Codex;Claude` - 빈
문자열 - 리스트

이 패턴을 영구 Architecture 사용자 ID 규칙으로 승격했다고 해석하지
않는다.

판정: PASS / FAIL

## 10. Check 6 --- Timeout Fixture 안정성

Order-012 중간 Test에서 Timeout 설정 때문에 정상 Executor까지 중단된
이력이 있었다.

최종 Fixture가 다음을 만족하는지 확인한다.

-   정상 Executor는 timeout 전에 완료
-   Validator Timeout Fixture만 의도적으로 timeout
-   결과가 Validation ERROR
-   Gate BLOCK
-   Test가 단순히 timeout 값을 늘려 모든 경로를 우회한 것이 아님

가능하면 격리 복사본에서 해당 Test를 반복 실행해 안정성을 확인한다.

반복 횟수는 과도하게 늘리지 않는다.

판정: PASS / FAIL

## 11. Check 7 --- Preservation

실제 파일을 독립 검산한다.

### Event

-   Order-011 당시 기존 13줄이 현재 Event Log의 byte-prefix로 동일
-   기존 prefix SHA-256:
    `19E120D4E8ECC5D6CA21E39859402E631B8E223F121DECF1EFAB774E89627267`
-   새 Event만 append
-   최종 Event 수 20인지 확인

### Evidence Index

-   기존 2줄 prefix 불변
-   기존 prefix SHA-256:
    `A06F69D9B5F6838D697EBB06635A68174886E69FBFE293FDA989A29E7E2B59E6`
-   새 index 1줄 append
-   총 3건 확인

### 기존 Evidence

plan 1.0:
`288E363F3F97AD65937E1AB0E85BB74C88AC3C62BF663B1D1AB5D7221409FC2F`

plan 1.1:
`90B797986357FCCF5C50ACAFCB2B376A858DAD5F7CE3CD8951638C2FE6EC8B38`

직접 재계산해 일치 확인.

### New Evidence

plan 1.2 Evidence도 직접 재계산하여 index와 일치 확인.

판정: PASS / FAIL

## 12. Check 8 --- 17 Test 독립 재현

Beta 원본을 변경하지 않는 격리 복사본에서 전체 Test를 재실행한다.

기대: - 총 17 Test - 17 PASS - 0 FAIL - 0 ERROR

Test 실행 전후 Beta 원본이 변경되지 않았는지 확인한다.

가능하면 Order-012의 신규 Negative Test가 실제 Core를 호출하는지
확인한다.

판정: PASS / FAIL

## 13. Check 9 --- Architecture / Scope

확인:

-   Architecture / Terminology FROZEN 불변
-   Reference 불변
-   Phase 2 없음
-   다른 MVP Test 구현 없음
-   외부 패키지 없음
-   SQLite 없음
-   네트워크/API/Agent 없음
-   기존 Order-010 PASS 보존
-   Order-011 결과 보존

판정: PASS / FAIL

## 14. 새로운 Blocker 검사

Order-012 변경으로 직접 발생한 다음 문제만 확인한다.

-   같은 Plan Version 변조가 여전히 통과
-   Fail-open 경로가 여전히 PASS/PROCEED
-   Owner 우회가 여전히 가능
-   과거 Event/Evidence 변경
-   새로운 Evidence Hash 불일치
-   Architecture/Scope 위반

없으면: `NONE`

새로운 기능 개선이나 LATER 후보를 적극 발굴하지 않는다.

## 15. 최종 판정

이번 Recheck는 다음 중 하나만 사용한다.

### PASS

-   Check 1\~9 모두 PASS
-   새로운 Blocker NONE
-   IMPORTANT 3건 해결 확인
-   Phase 1 수정 루프 종료 가능

### FAIL

-   Check 1\~9 중 하나 이상 실질 FAIL
-   IMPORTANT 미해결
-   Order-012 변경으로 직접적인 문제 발생

### BLOCKED

-   필수 파일 접근 실패
-   Order 불완전
-   독립 검증 수행 불가

`PASS WITH MINOR/IMPORTANT`는 이번 Recheck에서 사용하지 않는다.

## 16. 결과 보고 형식

# Order-013 Important Fix Recheck 결과

### 현재 판정

PASS / FAIL / BLOCKED

### Check Matrix

  Check                    판정   핵심 근거
  ------------------------ ------ -----------
  1 Plan Version 불변성           
  2 변경 근거                     
  3 Fail-open Test                
  4 Hash Test 독립성              
  5 Write Owner                   
  6 Timeout Fixture               
  7 Preservation                  
  8 17 Test 재현                  
  9 Architecture / Scope          

### Important Resolution

-   Important-001: RESOLVED / NOT_RESOLVED
-   Important-002: RESOLVED / NOT_RESOLVED
-   Important-003: RESOLVED / NOT_RESOLVED

### 새로운 Blocker

NONE 또는 상세.

### Test 독립 재현

-   총 Test
-   PASS / FAIL / ERROR
-   Timeout Fixture 반복 결과
-   Beta 원본 변화 여부

### Preservation 독립 검산

-   Event prefix
-   Evidence Index prefix
-   plan 1.0 EVD
-   plan 1.1 EVD
-   plan 1.2 EVD
-   Run 디렉터리

### 파일 변경 확인

모든 Beta 파일: NO 새 파일: NO

### Done

Order-012 IMPORTANT Fix 독립 재확인.

### Now

PASS이면 Local Core MVP Phase 1 수정 루프 종료.

### Next

PASS: → ChatGPT Project Beta 검토 → MVP Test 구현 순서 확정 → 다음 구현
Order

FAIL: → Root Cause → 새로운 Fix 근거 → New Run / Revalidation

### 사용자 승인 필요

NO

## 17. 종료 조건

Check 1\~9와 결과 보고 후 종료한다.

어떤 Beta 파일도 수정하지 않는다.

PASS해도 자동으로 다음 MVP Test 구현이나 Phase 2를 시작하지 않는다.

결과를 ChatGPT Project Beta에 전달한다.

=== ORDER END ===
