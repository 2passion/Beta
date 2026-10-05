# Order-042 --- MVP Test 7 Resume Implementation

## 0. Metadata

-   Order ID: Order-042
-   Project: Beta
-   Status: APPROVED
-   Type: WRITE + VALIDATE
-   Root: `C:\Obsidian\Beta`
-   Generator: ChatGPT
-   Writer / To: Codex
-   Reviewer: Claude Code
-   From: ChatGPT
-   Action: WRITE
-   Trigger: Order-041 PASS / Test 6 OFFICIAL PASS
-   Target: MVP Test 7 --- Resume
-   Architecture SSOT / Terminology: FROZEN
-   Test 3 Safe Parallel: NOT VERIFIED
-   GitHub Beta: EXISTS, OUT OF SCOPE

## 1. Execution Routing

``` text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: WRITE
order: Order-042
project: Beta

mismatch_policy:
- 현재 실행 주체가 to와 다르면 즉시 HOLD
- 실행/Beta 파일 변경 금지
- ROUTING_MISMATCH 보고
- 올바른 수신자에게 재전달될 때까지 대기
=== ROUTING END ===
```

## 2. Intent

MVP Test 7 Resume를 최소 구현하고 실제 Runtime Evidence로 검증한다.

검증 질문:

> 작업이 중단된 뒤 이미 완료·검증된 부분을 처음부터 반복하지 않고,
> 마지막으로 검증된 지점과 실제 Side Effect 상태를 확인하여 정확한 다음
> 단계부터 안전하게 재개하는가?

핵심 흐름:

``` text
Task 시작
→ Step 1 실행
→ Validation PASS
→ Checkpoint
→ Step 2 실행
→ Validation PASS
→ Checkpoint
→ 중단
→ Resume 요청
→ Checkpoint 읽기
→ 실제 Side Effect 상태 확인
→ 완료된 Step 재실행 금지
→ 다음 미완료 Step부터 재개
→ Validation
→ Evidence
```

Checkpoint만 믿지 않는다. Side Effect가 있는 작업은 실제 상태를 함께
확인한다.

## 3. Reuse Before Create

새 Resume 시스템을 만들기 전에 기존 Asset/Contract를 검색한다.

우선 재사용: - Common Harness - Task Plan version - Run / Event /
Evidence - Validation - Gate - filesystem snapshot / SHA - Test 6
Idempotency 방식 - Test 5 Prevention - Test 4 Fingerprint / No Blind
Retry - 기존 Checkpoint/Resume 관련 Asset이 있으면 그것

금지: - 새 DB - 새 상태 서버 - 새 Agent - Git을 Resume 핵심으로 도입 -
복잡한 Workflow Engine

필요하면 Fixture 수준의 최소 Resume/Checkpoint helper만 만든다.

## 4. Definitions

### Checkpoint

실행 작업의 안전한 중간 저장 지점.

최소 의미: - 어떤 Task / Plan / Run인지 - 어떤 Step까지
완료·검증됐는지 - 해당 Step의 Validation 상태 - 관련 Evidence - Side
Effect snapshot/reference - 다음 예상 Step

### Chunk

사용자에게 긴 결과를 나눠 전달하는 출력 단위.

Checkpoint와 Chunk는 같은 개념이 아니다. Chunk를 Resume 근거로 사용하지
않는다.

### Resume

마지막 검증된 Checkpoint와 실제 상태를 대조한 뒤 이미 완료된 작업을
반복하지 않고 다음 안전한 지점부터 계속 실행하는 것.

## 5. Minimal Resume Contract

Checkpoint 최소 필드:

-   checkpoint_id
-   task_id
-   plan_version
-   run_id
-   completed_step_ids
-   last_verified_step
-   validation_status
-   evidence_refs
-   side_effect_refs 또는 side_effect_snapshot
-   expected_next_step
-   created_at 또는 순서 정보

복잡한 상태 DB는 만들지 않는다. 기존 JSON/Event/Evidence 구조를 우선
재사용한다.

## 6. Resume Eligibility

Resume 허용 조건:

1.  Task identity 일치
2.  Plan version 일치
3.  Checkpoint 존재
4.  Checkpoint의 마지막 완료 Step이 Validation PASS
5.  Evidence 연결 유효
6.  Side Effect가 실제 상태와 일치
7.  expected_next_step이 Plan/DAG와 일치
8.  이미 완료된 Step을 다시 실행하지 않아도 됨
9.  현재 승인 Scope 안
10. Routing / User Gate 계약 위반 없음

모두 만족할 때만 `RESUME_ALLOWED`.

## 7. HOLD Conditions

다음은 자동 Resume 금지:

-   Checkpoint 없음
-   Checkpoint 손상
-   Task/Plan version 불일치
-   마지막 Step Validation FAIL/ERROR/NOT_RUN
-   Evidence 누락/불일치
-   Side Effect drift
-   이미 완료됐다고 기록됐지만 실제 결과 없음
-   실제 Side Effect는 있는데 Checkpoint에는 없음
-   expected_next_step 불일치
-   승인 Scope 밖
-   Routing mismatch
-   보호 파일 손상 가능성

결과: - `HOLD` - Reason Code - 추가 실행 0 - 임의 복구 0

검증된 Prevention이 적용 가능한 별도 실패라면 기존 계약에 따라 처리할 수
있으나, Resume 자체가 불확실한 상태를 Prevention으로 덮어쓰지 않는다.

## 8. Scenario A --- Normal Resume

Plan: - Step 1 - Step 2 - Step 3 - Step 4

첫 Run: - Step 1 실행 + PASS - Checkpoint - Step 2 실행 + PASS -
Checkpoint - 의도적 중단 - Step 3/4 NOT_RUN

Resume: - Checkpoint와 실제 상태 확인 - Step 1/2 재실행 0 - Step 3부터
실행 - Step 3 PASS - Step 4 PASS - 최종 Gate PROCEED

증명: - Step 1/2 call count 변화 없음 - duplicate write 0 - 새 Resume
Run 또는 Resume execution identity가 명확 - 과거 Run/Checkpoint 보존

## 9. Scenario B --- Checkpoint Says Done, Side Effect Missing

Checkpoint: - Step 2까지 PASS라고 기록

실제 filesystem: - Step 2의 필수 결과가 없음 또는 SHA 불일치

Expected: - HOLD - Reason `SIDE_EFFECT_DRIFT` 또는 동등 - Step 3 실행
0 - Step 1/2 자동 재실행 0 - 임의 Fix 0

Checkpoint를 맹신하면 FAIL.

## 10. Scenario C --- Side Effect Exists, Checkpoint Missing

실제 결과 파일은 존재하지만 Checkpoint에는 완료 기록이 없음.

Expected: - 자동으로 완료라고 추정하지 않음 - HOLD 또는 계약상 안전한
검증 경로 - 단순 파일 존재만으로 Step PASS 승격 금지 - 실행 0

## 11. Scenario D --- Plan Version Changed

Checkpoint는 Plan 1.0, 현재 Task Plan은 1.1.

Expected: - 기존 Checkpoint 자동 재사용 금지 - HOLD /
`PLAN_VERSION_MISMATCH` - 새 Plan에서 Resume 지점을 임의 추론하지 않음 -
Side Effect 0

별도 migration contract가 없다면 자동 migration 금지.

## 12. Scenario E --- Last Step Not PASS

Checkpoint의 마지막 Step Validation: - FAIL 또는 ERROR 또는 NOT_RUN

Expected: - `RESUME_ALLOWED` 금지 - HOLD - 다음 Step 실행 0

FAIL을 완료 지점으로 취급하지 않는다.

## 13. Scenario F --- Idempotent Resume Re-entry

정상 Resume 완료 후 동일 Resume 요청을 다시 실행.

Expected: - 이미 완료된 Step 재실행 0 - duplicate write 0 - duplicate
Evidence 남발 0 - `NO_CHANGE` 또는 동등 결정적 종료

Test 6의 실제 filesystem Idempotency 방식을 재사용한다.

## 14. Scenario G --- Routing / Approval Boundary

Resume 자체는 유효하지만: - Routing mismatch 또는 - Resume가 승인
Scope를 넘어서는 다음 Step을 요구

Expected: - HOLD 또는 APPROVAL_REQUIRED - 실행 0 - 기존
Checkpoint/Evidence 변경 0

Test 6 User Gate/Routing 계약을 재사용한다.

## 15. Adversarial Mutations

### M1 --- Fake PASS Checkpoint

Validation PASS 라벨만 위조하고 실제 Validation/Evidence 없음. Expected:
HOLD / FAIL/BLOCK.

### M2 --- Tampered Evidence

Checkpoint evidence_ref는 존재하지만 SHA 또는 Run 연결 불일치. Expected:
HOLD / FAIL/BLOCK.

### M3 --- Duplicate Completed-Step Execution

Resume executor가 Step 1/2를 다시 실행하도록 강제. Expected: Validator
FAIL/BLOCK.

### M4 --- Skip Next Step

expected_next_step=Step3인데 Step4부터 실행. Expected: Validator
FAIL/BLOCK.

### M5 --- Side Effect Drift Hidden by Counter

executor가 drift=false라고 보고하지만 실제 filesystem이 다름. Expected:
Validator 독립 검사로 FAIL/BLOCK.

### M6 --- Chunk Used as Checkpoint

사용자 출력 Chunk를 Resume 근거로 사용. Expected: NOT_ELIGIBLE / HOLD.

## 16. Validator Independence

Validator는 executor의 Resume result/label/counter를 그대로 신뢰하지
않는다.

독립 확인: - Task/Plan identity - Checkpoint 내용 - Validation record -
Evidence ref/hash - filesystem Side Effect - completed Step 실제
호출/Write 여부 - expected_next_step - resumed Step 순서 - duplicate
writes - Routing/User Gate boundary

Resume 전에 완료된 Step이 재실행됐으면 FAIL.

## 17. Run / Event / Evidence

가능하면 기존 구조를 재사용한다.

필요 Event 예: - CHECKPOINT_CREATED - RUN_INTERRUPTED 또는 동등한 기존
Event - RESUME_REQUESTED - RESUME_DECISION - RESUME_STARTED -
STEP_RESUMED - RESUME_COMPLETED

새 Event 이름이 기존 Terminology/Architecture와 충돌하면 임의 추가하지
말고 기존 표현을 재사용한다.

과거 Run을 덮어쓰지 않는다.

예:

``` text
RUN-001
Step1 PASS
Step2 PASS
INTERRUPTED

RUN-002 또는 명확한 Resume execution
Step3 PASS
Step4 PASS
FINAL PASS
```

실패/중단 사실은 보존한다.

## 18. Official Test 7 Candidate

전체 Regression PASS 후:

-   Test ID: `MVP-TEST-7`
-   Name: `Resume`
-   Version: `1.0`
-   change_reason_ref: `Order-042`
-   New Run
-   Execution PASS
-   Validation PASS
-   Gate PROCEED
-   Official Evidence
-   Scenario A\~G 연결
-   Mutation M1\~M6 검증 근거

Codex 단독 OFFICIAL PASS 금지.

## 19. Regression

기존 Test 1/2/4/5/6 관련 테스트 의미를 모두 보존한다.

신규: - Scenario A\~G - Mutation M1\~M6 - 필요한 최소 Resume contract
tests

보고: - 기존 Test 수 - 신규 Test 수 - TOTAL / PASS / FAIL / ERROR

기존 테스트 삭제/완화 금지. Blind Retry 금지.

## 20. Preservation

반드시 보존: - Test1 OFFICIAL PASS - Test2 OFFICIAL PASS - Test4
OFFICIAL PASS - Test5 OFFICIAL PASS - Test6 OFFICIAL PASS v1.2 -
Phase1 - Common Harness/Core - Architecture/Terminology - Reference -
기존 Run/Event/Evidence

Test3 Safe Parallel은 NOT VERIFIED 상태 유지. Phase2 시작 금지.

## 21. GitHub Boundary

GitHub Beta 저장소는 존재하지만 이번 Resume Test의 구현 수단으로
사용하지 않는다.

금지: - git init/add/commit/push - Git commit을 Checkpoint로 간주 -
GitHub를 Resume SSOT로 사용 - Local Beta 구조 변경

향후 GitHub가 백업/버전관리/복구에 필요한지는 MVP 7 Gates 이후 별도
검토한다.

## 22. Reporting Views

Test 6에서 승인한 원칙 유지: - 원본 = Run/Event/Validation/Evidence -
Summary/Detailed = 파생 View

Summary 3분 View: 1. 어디까지 완료됐는가 2. 어디서 중단됐는가 3. 어떤
Checkpoint가 검증됐는가 4. 실제 상태와 일치하는가 5. 어디서부터
재개했는가 6. 중복 실행이 있었는가 7. 최종 결과/다음 단계

Detailed View: Checkpoint ID, Run ID, Step, Validation, Evidence, SHA,
filesystem delta, Resume Decision, Reason Code.

별도 이중 SSOT를 만들지 않는다.

## 23. Prohibited

-   Test3 Safe Parallel 구현/검증
-   Phase2
-   Architecture/Terminology 변경
-   GitHub 통합
-   새 DB/Agent/Plugin/Adapter
-   대형 Workflow Engine
-   기존 Evidence rewrite
-   중단 Run을 PASS로 변경
-   Checkpoint만 믿고 Side Effect 확인 생략
-   Chunk를 Checkpoint로 취급
-   Scope 밖 자동 실행

## 24. Required Result

A. Routing / Preflight B. Reuse search 결과 C. Resume Contract /
Checkpoint schema D. Scenario A\~G E. Mutation M1\~M6 F. Validator
Independence G. Regression H. Official Candidate ---
ID/version/reason/Run/Plan SHA/Executor SHA/Validator SHA/Evidence
ID/SHA/Execution/Validation/Gate/Scenario I. Preservation J. GitHub
Boundary K. Files Changed L. Done / Now / Next - Test7 PASS candidate
여부 - Independent Review 필요 - Test3 NOT VERIFIED - 사용자 승인 필요
여부

## 25. Completion Gate

Test 7 PASS candidate 조건: - Normal Resume 정확한 다음 Step부터 시작 -
완료 Step 재실행 0 - Side Effect 실제 검증 - drift/missing/extra
state에서 HOLD - Plan mismatch HOLD - non-PASS checkpoint HOLD -
Re-entry idempotent - Routing/User Gate 경계 유지 - M1\~M6 PASS -
Validator independent - Regression PASS - Preservation PASS -
Architecture Delta NONE - GitHub untouched - Evidence complete

완료 후: Codex Result → ChatGPT 검토 → Claude Code READ-ONLY Independent
Review → PASS 시 Test7 OFFICIAL PASS candidate → Closure Sync → 남은
Test3 Safe Parallel 검토

## 26. Current State

-   Test1 Reuse: OFFICIAL PASS
-   Test2 Ownership: OFFICIAL PASS
-   Test3 Safe Parallel: NOT VERIFIED
-   Test4 Bottleneck: OFFICIAL PASS
-   Test5 Prevention: OFFICIAL PASS
-   Test6 User Gate: OFFICIAL PASS v1.2
-   Test7 Resume: NOT VERIFIED / NOT STARTED
-   User approval: already granted for continuation within this scope
-   Next executor: Codex

=== ORDER END ===
