# Order-044 --- MVP Test 7 Resume Evidence Enforcement Fix

## 0. Metadata

-   Order ID: Order-044
-   Project: Beta
-   Status: APPROVED
-   Type: WRITE + VALIDATE
-   Root: `C:\Obsidian\Beta`
-   Generator: ChatGPT
-   Writer / To: Codex
-   Reviewer: Claude Code
-   From: ChatGPT
-   Action: WRITE
-   Trigger: Order-043 REVISION REQUIRED
-   Target: MVP Test 7 Resume Plan 1.1 candidate
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
order: Order-044
project: Beta

mismatch_policy:
- 현재 실행 주체가 to와 다르면 즉시 HOLD
- 실행/Beta 파일 변경 금지
- ROUTING_MISMATCH 보고
- 올바른 수신자에게 재전달될 때까지 대기
=== ROUTING END ===
```

## 2. Intent

Order-043에서 확인된 Test 7 Resume의 IMPORTANT 4건과 직접 연결된
실행경로 Minor만 최소 수정한다.

실제 Resume 핵심 동작은 이미 PASS했으므로 재설계하지 않는다.

수정 대상: 1. I1 --- Interrupted Run 보존/identity를 Validator가 강제 2.
I2 --- Checkpoint ↔ Evidence의 run_id/task_id/SHA 연결을 Validator가
강제 3. I3 --- Resume re-entry Idempotency를 현재
filesystem/Evidence에서 독립 측정 4. I4 --- Scenario A\~G 파일 Hash를
Official Evidence에 연결 5. Minor --- HOLD Scenario가 가능한 경우 실제
`resume()` Gate를 통과하고 RESUME_DECISION을 남기도록 정렬

새 Resume 시스템, DB, Agent, Workflow Engine을 만들지 않는다.

## 3. Order-043 Verified Baseline

Order-043 독립 검토에서 실제 동작 PASS: - 정확한 Resume Point - 완료
Step 1/2 재실행 0 - Step3 → Step4 순차 실행 - Side Effect drift → HOLD -
Checkpoint missing → HOLD - Chunk → HOLD - Plan mismatch → HOLD -
FAIL/ERROR/NOT_RUN → HOLD - Routing mismatch / Scope expansion → 실행
0 - Regression 77/77 - Preservation PASS - Architecture Delta NONE

Order-043 Important: - I1 Interrupted/Resume identity 미검증 - I2
Evidence Run/Task linkage 미검증 - I3 re-entry filesystem/Evidence 현재
상태 독립 측정 부족 - I4 Scenario Hash가 Official Evidence에 연결되지
않음

## 4. Fix I1 --- Interrupted / Resume Identity Enforcement

Validator는 Scenario A와 관련 Resume Scenario에서 실제 Event를 읽어 최소
다음을 확인한다.

-   최초 execution identity 존재
-   `RUN_INTERRUPTED` 또는 승인된 동등 Event 존재
-   Interrupted identity가 중단 상태로 보존
-   Resume identity 존재
-   Interrupted identity != Resume identity
-   Step1/2는 Interrupted identity 소유
-   Step3/4는 Resume identity 소유
-   Checkpoint1/2는 Interrupted identity
-   Resume 이후 Checkpoint는 Resume identity
-   Event 순서가 논리적으로 일치
-   Interrupted Event를 PASS/COMPLETED로 rewrite하지 않음

Validator는 단순 executor report를 신뢰하지 않는다.

### Mutation M7

`RUN_INTERRUPTED` Event 삭제 또는 `RUN_COMPLETED`로 변조. Expected:
Validator FAIL / Gate BLOCK.

### Mutation M8

Resume Event/Checkpoint가 Interrupted run_id를 재사용하도록 변조.
Expected: Validator FAIL / Gate BLOCK.

## 5. Fix I2 --- Checkpoint ↔ Evidence Linkage

Validator는 각 Checkpoint의 Evidence Reference를 실제 파일과 연결해
확인한다.

최소: - Evidence 존재 - Evidence SHA 일치 - Checkpoint.task_id ==
Evidence.task_id 또는 실제 계약상 동등 identity - Checkpoint.run_id ==
Evidence.run_id - Validation이 해당 Run/Step에 연결 - Side Effect
reference가 해당 Step/Evidence와 연결 - `CHECKPOINT_RECORDED` Event의
checkpoint identity/SHA가 실제 Checkpoint와 일치

SHA만 맞으면 PASS시키지 않는다.

### Mutation M9

Evidence의 run_id 또는 task_id를 가짜 값으로 바꾸고 모든 관련 SHA를
일관되게 다시 계산한다. Expected: Validator FAIL / Gate BLOCK.

## 6. Fix I3 --- Real Re-entry Idempotency Measurement

Test 6에서 검증한 filesystem snapshot 방식을 재사용한다.

Resume 완료 후 동일 Resume 요청 재진입 시 Validator가 **현재
filesystem과 Evidence tree를 직접 다시 측정**한다.

최소: - managed file set - file SHA snapshot - Run directory count -
Runtime Evidence count - Checkpoint count - relevant Event count

비교: - before re-entry - after re-entry - Validator 실행 시 현재 실제
상태

Executor가 기록한 `before_reentry` / `after_reentry` 값만 믿지 않는다.

Expected: - NO_CHANGE - duplicate write 0 - duplicate Evidence 0 -
duplicate Checkpoint 0 - duplicate Run/Event 0

### Mutation M10

정상 Resume 완료 후 추가 Evidence/파일/Checkpoint를 생성하거나 기존
파일을 rewrite. Expected: Validator FAIL / Gate BLOCK.

## 7. Fix I4 --- Scenario Hash Manifest in Official Evidence

Scenario A\~G 전체 검증 파일을 Official Evidence에서 추적할 수 있게
한다.

가능하면 기존 Test 4\~6의 Evidence linkage 방식을 재사용한다.

Official Evidence 또는 연결된 Validation output에 최소: - scenario_id -
relative_path - sha256

목록/manifest를 포함한다.

요구: - Scenario 파일 전체가 manifest에 포함 - manifest에 없는 Scenario
파일 0 - 존재하지 않는 manifest entry 0 - SHA mismatch 0

별도 DB를 만들지 않는다.

### Mutation M11

Scenario 파일 하나를 변조하거나 추가/삭제. Expected: Official
Evidence/Validator 검증 FAIL / Gate BLOCK.

## 8. Minor Fix --- HOLD Paths Through Actual Resume Gate

가능한 HOLD Scenario는 단순 `inspect_checkpoint()` 결과만 저장하지 말고
실제 `resume()` entry를 통과시켜 실행 차단을 증명한다.

최소 대상: - Checkpoint missing - Plan mismatch - non-PASS last step -
Routing mismatch - Scope expansion - Chunk case가 실제 Resume entry에서
처리 가능한 경우

Expected: - `RESUME_DECISION` 또는 기존 동등 Event 기록 - Decision =
HOLD / APPROVAL_REQUIRED - Step execution 0 - write/evidence side effect
0

단, 이 정렬을 위해 Architecture/Event vocabulary를 변경하지 않는다. 기존
Event 표현으로 불가능하면 현재 계약을 유지하고 이유를 보고한다.

## 9. Preserve Existing Resume Behavior

다음은 재설계하지 않는다.

-   Checkpoint schema
-   exact resume point
-   Step1/2 duplicate execution prevention
-   Step3→Step4 ordering
-   side-effect drift detection
-   Checkpoint missing behavior
-   Chunk separation
-   Plan mismatch boundary
-   non-PASS boundary
-   Routing/User Gate integration
-   Test 6 Idempotency reuse
-   GitHub exclusion

## 10. Validator Independence

Validator가 독립적으로 확인:

-   Checkpoint schema
-   Task/Plan identity
-   Interrupted/Resume identity
-   Event sequence
-   Validation record
-   Evidence path/SHA/run_id/task_id
-   CHECKPOINT_RECORDED linkage
-   Side Effect path/SHA
-   expected_next_step
-   actual resumed steps
-   completed Step non-reexecution
-   current filesystem/Evidence snapshot
-   duplicate Run/Event/Evidence/Checkpoint
-   Scenario manifest
-   Routing/User Gate

검사 불능은 ERROR.

## 11. Required Scenarios

기존 A\~G 모두 다시 PASS해야 한다.

A Normal Resume B Side Effect Drift C Missing Checkpoint / Chunk D Plan
Version Mismatch E Last Step non-PASS F Idempotent Re-entry G Routing /
Approval Boundary

기존 의미를 약화하지 않는다.

## 12. Mutations

기존 M1\~M6 보존.

신규: - M7 Interrupted Event delete/rewrite - M8 Resume identity reuses
Interrupted run_id - M9 Evidence run_id/task_id tamper with hashes
recomputed - M10 post-resume extra/rewrite filesystem or Evidence - M11
Scenario file tamper/add/delete against manifest

모든 Mutation은 의도한 위반 때문에 FAIL/BLOCK해야 한다.

## 13. Version / Evidence

기존 Plan 1.0과 Evidence는 보존한다.

새 결과: - Test ID: `MVP-TEST-7` - Name: `Resume` - Version: `1.1` -
change_reason_ref: `Order-044` - New official candidate Run - New
Event/Validation/Evidence - Scenario A\~G - Scenario Hash Manifest

Plan 1.0의 REVISION REQUIRED 이력은 보존한다.

## 14. Regression

기존 77개 Test를 모두 보존한다.

신규 Enforcement Test를 추가한다.

최종 기준: - 기존 77 PASS - 신규 Test 전부 PASS - FAIL 0 - ERROR 0

기존 Test 삭제/완화 금지. Blind Retry 금지.

## 15. Preservation

보존: - Test1 OFFICIAL PASS - Test2 OFFICIAL PASS - Test4 OFFICIAL
PASS - Test5 OFFICIAL PASS - Test6 OFFICIAL PASS v1.2 - Phase1 - Common
Harness/Core - Architecture/Terminology - Reference - Test7
Plan1.0/Evidence - 기존 Run/Event/Evidence

Test3 Safe Parallel = NOT VERIFIED 유지. Phase2 없음. Architecture Delta
= NONE.

## 16. GitHub Boundary

GitHub Beta는 이번 Order 범위 밖이다.

금지: - git init/add/commit/push - GitHub 업로드 - Git commit을
Checkpoint로 사용 - GitHub를 Resume SSOT로 사용

## 17. Prohibited

-   Test3 구현/검증
-   Phase2
-   Architecture/Terminology 변경
-   새 DB/Agent/Plugin/Adapter
-   새 Resume/Recovery framework
-   기존 Evidence rewrite
-   Plan1.0 실패 이력 변경
-   Scope 밖 자동 실행

## 18. Required Result

### A. I1 Interrupted/Resume Identity

Event/Run identity 검증과 M7/M8.

### B. I2 Evidence Linkage

Checkpoint↔Evidence run_id/task_id/SHA/recorded-event linkage와 M9.

### C. I3 Idempotency

실제 filesystem/Evidence snapshot과 M10.

### D. I4 Scenario Manifest

manifest count / mismatch / unlinked와 M11.

### E. HOLD Entry Alignment

실제 resume entry를 통과한 HOLD/APPROVAL_REQUIRED 결과.

### F. Existing A\~G

각 Scenario 결과.

### G. M1\~M11

각 결과.

### H. Validator Independence

독립 재계산 항목.

### I. Regression

기존 / 신규 / TOTAL / PASS / FAIL / ERROR.

### J. Official Candidate

-   Test ID
-   Version 1.1
-   change_reason_ref Order-044
-   Run ID
-   Plan SHA
-   Executor SHA
-   Validator SHA
-   Evidence ID/SHA
-   Execution/Validation/Gate
-   Scenario ID
-   Scenario manifest count

### K. Preservation

기존 Test/Architecture/Plan1.0.

### L. GitHub Boundary

untouched 여부.

### M. Files Changed

수정/생성/삭제.

### N. Done / Now / Next

-   Plan1.1 PASS candidate 여부
-   Independent Delta Recheck 필요
-   Test7 OFFICIAL PASS NOT YET
-   Test3 NOT VERIFIED

## 19. Completion Gate

Plan 1.1 PASS candidate 조건:

-   I1 resolved
-   I2 resolved
-   I3 resolved
-   I4 resolved
-   HOLD entry alignment 검증
-   A\~G PASS
-   M1\~M11 PASS
-   Validator independent
-   Regression PASS
-   Evidence complete
-   Preservation PASS
-   Architecture Delta NONE
-   GitHub untouched
-   Scope violation NONE

Codex 단독 OFFICIAL PASS 금지.

완료 후: Codex Order-044 Result → ChatGPT 검토 → Claude Code READ-ONLY
Plan1.1 Delta Recheck → PASS 시 Test7 OFFICIAL PASS candidate → Closure
Sync → Test3 Safe Parallel 검토

Test3 자동 시작 금지.

## 20. Current State

-   Test1 Reuse: OFFICIAL PASS
-   Test2 Ownership: OFFICIAL PASS
-   Test3 Safe Parallel: NOT VERIFIED
-   Test4 Bottleneck: OFFICIAL PASS
-   Test5 Prevention: OFFICIAL PASS
-   Test6 User Gate: OFFICIAL PASS v1.2
-   Test7 Resume Plan1.0: REVISION REQUIRED
-   Test7 Resume Plan1.1: NOT RUN
-   Test7 OFFICIAL PASS: NOT YET
-   User approval: already granted within this fix scope
-   Next executor: Codex

=== ORDER END ===
