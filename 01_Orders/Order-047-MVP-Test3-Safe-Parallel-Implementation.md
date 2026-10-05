# Order-047 --- MVP Test 3 Safe Parallel Implementation

## Metadata

-   Order ID: Order-047
-   Project: Beta
-   Status: APPROVED
-   Type: WRITE + VALIDATE
-   Root: `C:\Obsidian\Beta`
-   Generator: ChatGPT
-   Writer / To: Codex
-   Reviewer: Claude Code
-   Action: WRITE
-   Trigger: Order-046 PASS / Test 7 OFFICIAL PASS
-   Target: MVP Test 3 --- Safe Parallel
-   Architecture / Terminology: FROZEN
-   GitHub Beta: EXISTS, OUT OF SCOPE

## Execution Routing

``` text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: WRITE
order: Order-047
project: Beta
mismatch_policy:
- recipient mismatch -> HOLD
- no execution / no Beta writes
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## Intent

MVP 7 Gates 중 마지막 미검증 Gate인 Test 3 Safe Parallel을 최소 구현하고
Runtime Evidence로 검증한다.

핵심 질문:

> Task들이 의존성, Write Owner, 파일/경로, 기능 영역, 공유 자원,
> 권한에서 독립적일 때만 병렬 실행하고, 하나라도 충돌하거나 독립성을
> 증명할 수 없으면 병렬 실행하지 않는가?

목표는 "최대한 병렬"이 아니라 "안전한 경우에만 병렬"이다.

## Reuse Before Create

새 병렬 시스템을 만들기 전에 기존 Asset/Contract를 검색한다.

우선 재사용: - Task / Plan / Run / Event / Validation / Evidence -
Common Harness - Test 2 One Task One Owner - Test 6 User Gate /
Routing - Test 7 Resume / Idempotency - Test 4 No Blind Retry /
Fingerprint - 기존 DAG/dependency 표현이 있으면 그것 - 기존 file/path
ownership 또는 write-set 표현이 있으면 그것

금지: - 새 대형 Scheduler - 새 Agent pool - 새 DB - 새 분산 시스템 -
외부 병렬 Agent 통합

필요하면 Fixture 수준의 최소 Safe Parallel
classifier/executor/validator만 만든다.

## Safe Parallel Contract

병렬 실행 허용은 다음 조건을 모두 만족해야 한다.

1.  두 Task의 dependency가 서로 독립
2.  동일 Task가 아님
3.  각 Task의 Write Owner가 정확히 1명
4.  Write Owner가 충돌하지 않음
5.  write set / 파일 / 경로가 겹치지 않음
6.  기능 영역 또는 변경 대상이 충돌하지 않음
7.  공유 mutable resource 충돌 없음
8.  권한/Scope 충돌 없음
9.  선행 Validation/Gate 조건 충족
10. 결과를 각 Task별로 독립 검증 가능

모두 증명된 경우에만 `PARALLEL_ALLOWED`.

하나라도 false이거나 UNKNOWN이면 병렬 실행 금지.

## Three Decisions

-   `PARALLEL_ALLOWED`
-   `SEQUENTIAL_REQUIRED`
-   `HOLD`

### PARALLEL_ALLOWED

독립성이 증명된 Task만 병렬 실행.

### SEQUENTIAL_REQUIRED

작업 자체는 안전하게 수행 가능하지만 병렬로는 안전하지 않음. 병렬
실행하지 않고 결정적 순서로 실행.

### HOLD

계약/권한/SSOT/Evidence가 불명확하거나 안전한 실행 순서를 결정할 수
없음. 실행 0.

## Conflict Model

최소 conflict dimensions:

### Dependency

-   A depends_on B
-   B depends_on A
-   shared prerequisite not complete → 병렬 금지

### Write Ownership

One Task One Owner 유지. 동일 Task에 두 Writer가 있으면 HOLD. 서로 다른
Task라도 동일 Writer가 동시에 동일 mutable context를 안전하게 다룰 수
있다는 검증이 없으면 병렬 금지.

### File / Path

정규화된 write set 기준으로 겹침 검사. - same file - parent/child
destructive overlap - same generated output - same append target if
append operation is not proven atomic/isolated

→ 병렬 금지

단순 문자열 비교만으로 판단하지 말고 canonical/normalized path를
사용한다.

### Functional Domain

파일이 달라도 동일 단일 상태를 동시에 변경하면 충돌로 취급. 예: 같은
registry/index/state를 서로 다른 파일을 통해 변경.

### Shared Resource

공유 mutable resource: - common state file - evidence index - event
log - registry - generated output target 등.

기존 Harness의 append-only 구조가 병렬 안전하다고 실제로 증명되지
않았다면 UNKNOWN/SEQUENTIAL로 둔다.

### Permission / Scope

한 Task가 승인 Scope 밖이면 병렬 실행 금지. Routing mismatch도 병렬 실행
금지.

## Scenario A --- Truly Independent Parallel

Task A와 B: - dependency 없음 - 서로 다른 owner - write set disjoint -
functional domain 독립 - shared mutable resource 없음 또는 격리 -
scope/routing valid

Expected: - PARALLEL_ALLOWED - 두 Task 모두 실행 - 실제
overlap/concurrency Evidence 존재 - 각 Run 독립 - 각 Validation PASS -
Gate PROCEED - 결과 merge/summary에서 충돌 0

"병렬 허용" 라벨만 남기고 실제 순차 실행하면 Test 3 PASS로 간주하지
않는다. 실제 병렬/동시 실행이 있었다는 Runtime Evidence가 필요하다.

## Scenario B --- Dependency Conflict

Task B depends_on Task A.

Expected: - SEQUENTIAL_REQUIRED - 병렬 실행 0 - A 완료/PASS 후 B 실행 -
B가 A보다 먼저 시작하지 않음

## Scenario C --- Same File Conflict

A/B가 동일 파일 또는 canonical path가 겹치는 write set을 가짐.

Expected: - SEQUENTIAL_REQUIRED 또는 계약상 HOLD - concurrent write 0 -
lost update 0 - corruption 0

## Scenario D --- Same Task / Multiple Writer

하나의 Task에 Writer 두 명 또는 동일 Task가 중복 dispatch.

Expected: - HOLD - 실행 0 - `OWNERSHIP_CONFLICT` 또는 동등 Reason

Test 2 계약을 재사용한다.

## Scenario E --- Shared Mutable Resource

A/B의 직접 output은 다르지만 동일 registry/index/event/evidence target
등 공유 mutable resource를 동시에 변경하려 함.

해당 resource의 병렬 안전성이 기존 Evidence로 증명되지 않았다면: -
SEQUENTIAL_REQUIRED - concurrent mutation 0

## Scenario F --- Permission / Scope Conflict

A는 승인 Scope 안, B는 Scope 밖 또는 Routing mismatch.

Expected: - 전체 batch를 무조건 병렬 실행하지 않음 - B =
APPROVAL_REQUIRED 또는 HOLD - B side effect 0 - A를 독립적으로 실행해도
되는지는 batch contract에 따라 명시적으로 결정 - 암묵적으로 A까지
실행하지 않는다

최소 MVP에서는 보수적으로 batch HOLD/SEQUENTIAL을 선택해도 된다.

## Scenario G --- Unknown Independence

write set 또는 dependency 정보가 누락되어 독립성을 증명할 수 없음.

Expected: - PARALLEL_ALLOWED 금지 - SEQUENTIAL_REQUIRED 또는 HOLD -
"충돌이 보이지 않는다"를 "독립이다"로 간주하지 않음

## Scenario H --- Parallel Failure Isolation

A/B가 안전하게 병렬 허용됐으나: - A PASS - B FAIL

Expected: - A의 PASS 사실 보존 - B FAIL을 PASS로 덮어쓰지 않음 - A를
불필요하게 재실행하지 않음 - B만 Recovery/새 Run 대상 - batch 전체를
허위 PASS 처리하지 않음

Test 4/5/7 원칙을 재사용한다.

## Actual Concurrency Evidence

Scenario A에서 최소 다음 중 기존 환경에서 가능한 결정적 Evidence를
사용한다.

-   task start/end timestamps with overlap
-   synchronization barrier
-   concurrent worker/process/thread identity
-   both started before either completed

단순 `parallel=true` 필드만으로는 불충분.

테스트 안정성을 위해 sleep timing만 의존하지 않는다. 가능하면
barrier/event synchronization으로 실제 overlap을 증명한다.

## Deterministic Sequential Fallback

SEQUENTIAL_REQUIRED일 때 실행 순서는 결정적이어야 한다.

우선: 1. dependency topological order 2. 명시된 priority/order 3. stable
task_id ordering 등 기존 계약

임의 순서 금지.

Dependency cycle이 발견되면 HOLD.

## Mutations

### M1 Dependency Hidden

dependency를 decision report에서만 숨기고 실제 Task에는 남김. Expected:
Validator가 실제 Task에서 재계산해 병렬 허용을 FAIL/BLOCK.

### M2 Canonical Path Alias

`A/../target.json` vs canonical target 또는 case/path alias로 동일
파일을 다르게 표현. Expected: conflict 탐지.

Windows 경로 특성을 고려하되 새 범용 filesystem framework는 만들지
않는다.

### M3 Ownership Forgery

report에는 owner가 다르다고 쓰지만 실제 Task owner 충돌. Expected:
FAIL/BLOCK.

### M4 Shared Resource Hidden

직접 write set은 다르지만 실제 shared mutable resource가 같음. Expected:
병렬 금지 또는 Validator FAIL/BLOCK.

### M5 Fake Parallel

report는 PARALLEL_ALLOWED이나 실제 실행은 순차. Expected: 실제
concurrency Evidence 부족으로 FAIL/BLOCK.

### M6 Unsafe Forced Parallel

충돌 Task를 강제로 동시에 실행. Expected: 정상 경로에서는 불가. 격리
Mutation에서는 Validator FAIL/BLOCK.

### M7 Failure Isolation Violation

A PASS/B FAIL 후 A를 다시 실행하거나 batch PASS로 위조. Expected:
FAIL/BLOCK.

### M8 Unknown Treated Independent

필수 independence field를 제거했는데 PARALLEL_ALLOWED로 보고. Expected:
FAIL/BLOCK.

## Validator Independence

Validator는 Scheduler/Executor의 `PARALLEL_ALLOWED` 라벨을 그대로
신뢰하지 않는다.

독립 재계산: - task identity - dependencies - owner -
normalized/canonical write set - functional domain - shared resources -
permission/scope - routing - actual concurrency evidence - start/end
ordering - per-task Run/Validation/Evidence - failure isolation -
sequential fallback order

검사 불능은 ERROR.

## Run / Event / Evidence

기존 구조를 우선 재사용한다.

필요 사실: - parallel decision - conflict reasons - Task A/B start -
Task A/B finish - per-task Run - per-task Validation -
batch/coordination result

새 Event vocabulary가 필요하면 기존 Architecture/Terminology와 충돌하지
않는 최소 표현만 사용한다.

각 Task의 사실을 batch 하나의 PASS/FAIL로 덮어쓰지 않는다.

## Official Test 3 Candidate

전체 검증 후: - Test ID `MVP-TEST-3` - Name `Safe Parallel` - Version
`1.0` - change_reason_ref `Order-047` - New official candidate
Run/Evidence - Scenario A\~H - Mutation M1\~M8 - Execution PASS -
Validation PASS - Gate PROCEED

Codex 단독 OFFICIAL PASS 금지.

## Regression

현재 관련 Regression 82개 의미를 보존한다.

신규 Safe Parallel tests 추가.

보고: - 기존 - 신규 - TOTAL / PASS / FAIL / ERROR

기존 테스트 삭제/완화 금지. Blind Retry 금지.

## Preservation

보존: - Test1 OFFICIAL PASS - Test2 OFFICIAL PASS - Test4 OFFICIAL
PASS - Test5 OFFICIAL PASS - Test6 OFFICIAL PASS v1.2 - Test7 OFFICIAL
PASS v1.1 - Phase1 - Common Harness/Core - Architecture/Terminology -
Reference - 기존 Run/Event/Evidence

Architecture Delta = NONE이어야 한다.

## GitHub Boundary

GitHub Beta는 이번 Safe Parallel Test 범위 밖이다.

금지: - git init/add/commit/push - GitHub를 coordination/lock/queue로
사용 - GitHub를 SSOT로 사용

## Prohibited

-   Phase2
-   Architecture/Terminology 변경
-   대형 Scheduler
-   Agent pool
-   외부 병렬 Agent
-   새 DB/distributed lock service
-   Plugin/Adapter
-   기존 Evidence rewrite
-   다른 Gate 재구현
-   충돌을 숨기기 위한 테스트 완화

## Result Format

A. Routing / Preflight B. Reuse Search C. Safe Parallel Contract D.
Conflict Detection E. Scenario A\~H F. Actual Concurrency Evidence G.
Sequential Fallback H. M1\~M8 I. Validator Independence J. Failure
Isolation K. Regression L. Official Candidate - Test ID/version/reason -
Run ID - Plan/Executor/Validator SHA - Evidence ID/SHA -
Execution/Validation/Gate - Scenario ID/Evidence count M. Preservation
N. GitHub Boundary O. Files Changed P. Done / Now / Next - Test3 PASS
candidate 여부 - Independent Review 필요 - MVP 7 Gates 전체 상태 -
사용자 승인 필요 여부

## Completion Gate

Test3 PASS candidate 조건: - 실제 독립 Task만 PARALLEL_ALLOWED - 실제
concurrency Evidence 존재 - dependency conflict 병렬 금지 - canonical
write conflict 병렬 금지 - ownership conflict HOLD - shared mutable
resource 안전성 미증명 시 병렬 금지 - permission/routing conflict 차단 -
unknown independence 병렬 금지 - deterministic sequential fallback -
cycle HOLD - failure isolation PASS - M1\~M8 PASS - Validator
independent - Regression PASS - Preservation PASS - Architecture Delta
NONE - GitHub untouched - Evidence complete

완료 후: Codex Result → ChatGPT 검토 → Claude Code READ-ONLY Independent
Review → PASS 시 Test3 OFFICIAL PASS candidate → Closure Sync → MVP 7
Gates 전체 Evidence 검토 → MVP PASS 여부 결정

## Current State

-   Test1 Reuse: OFFICIAL PASS
-   Test2 Ownership: OFFICIAL PASS
-   Test3 Safe Parallel: NOT VERIFIED / NOT STARTED
-   Test4 Bottleneck: OFFICIAL PASS
-   Test5 Prevention: OFFICIAL PASS
-   Test6 User Gate: OFFICIAL PASS v1.2
-   Test7 Resume: OFFICIAL PASS v1.1
-   User approval: already granted within this scope
-   Next executor: Codex

=== ORDER END ===
