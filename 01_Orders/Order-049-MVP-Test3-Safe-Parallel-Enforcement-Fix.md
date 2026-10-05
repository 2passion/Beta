# Order-049 — MVP Test 3 Safe Parallel Enforcement Fix

## Metadata
- Order ID: Order-049
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: WRITE
- Trigger: Order-048 REVISION REQUIRED
- Target: MVP Test 3 Safe Parallel Plan 1.1 candidate
- Architecture / Terminology: FROZEN
- GitHub Beta: OUT OF SCOPE

## Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: WRITE
order: Order-049
project: Beta
mismatch_policy:
- recipient mismatch -> HOLD
- no execution / no Beta writes
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## Intent
Order-048의 B1/B2/I1/I2/I3만 최소 수정한다. 이미 PASS한 실제 병렬 실행, dependency/cycle, 기본 path conflict, ownership, shared resource, sequential fallback, failure isolation은 재설계하지 않는다.

수정:
1. B1 Fake Parallel 독립 검증
2. B2 UNKNOWN 값 검증
3. I1 Windows 특수 alias 보수 처리
4. I2 per-task Evidence 내부 연결
5. I3 Scenario Hash Manifest
6. 가능하면 Test 2 Ownership 계약 재사용

새 Scheduler/Agent pool/DB/distributed lock/Plugin/Adapter 금지.

## B1 — Independent Concurrency Observation
executor의 timestamp/thread/barrier self-report만으로 병렬을 증명하지 않는다.

Scenario A/H worker가 executor summary와 별개의 관측 근거를 직접 남긴다:
- worker별 append-only Event 또는 marker
- worker identity
- barrier arrival/release
- start/completion
- 관측 시각/순서
- 독립 파일이면 SHA

Validator는 runtime concurrency record와 별도 worker observation을 교차검증한다.

PASS:
- 서로 다른 worker identity
- 동일 synchronization token
- 두 worker 모두 barrier 도달
- 둘 다 시작한 뒤 어느 한쪽도 완료되지 않은 구간 존재
- worker observation과 runtime record 일치
- Task별 output/Run/Validation/Evidence 독립

sleep만으로 증명 금지.

### M9 Consistent Fake Parallel
실제 순차 실행 + runtime에 fake thread id/shared barrier/겹치는 fake timestamps 기록.
Expected: 별도 observation과 불일치 → Validator FAIL / Gate BLOCK.

worker observation까지 executor summary와 같은 경로에서 임의 생성해 위조할 수 있으면 독립 관측으로 인정하지 않는다.

## B2 — UNKNOWN Must Not Become Safe
필수 field는 존재와 값 유효성을 모두 검사한다.

최소:
- task_id non-empty
- owner non-empty / single
- functional_domain non-empty
- write_set 명시/해석 가능
- shared_resources 명시
- requested_scope valid/non-empty
- approved_scope valid
- routing_to / actual_actor non-empty/comparable
- independent_validation explicit true
- dependencies 상태/충족 여부 확인 가능

UNKNOWN / None / empty / unresolved → PARALLEL_ALLOWED 금지.

안전한 순차 가능 → SEQUENTIAL_REQUIRED.
권한/identity/dependency 판단 불가 → HOLD.

### M10 Unknown Inputs
- routing_to=None / actual_actor=None
- functional_domain=None / ""
- requested_scope=[]
- unresolved external dependency
Expected: 모두 PARALLEL_ALLOWED 아님.

## I1 — Windows Path Conservative Policy
새 범용 filesystem framework를 만들지 않는다.

지원/검증:
- same file
- `..`
- case-insensitive
- `/` vs `\`
- parent/child
- trailing dot/space
- `\\?\` prefix
- base가 명확한 relative vs absolute
- 안전하게 증명 가능한 UNC/local alias

신뢰성 있게 해석하기 어려운:
- NTFS ADS
- 8.3 short name
- 불명확 UNC/device
- base 불명확 relative
는 병렬 허용하지 않는다.

conflict proven → SEQUENTIAL_REQUIRED.
alias UNKNOWN → SEQUENTIAL_REQUIRED 또는 HOLD.
PARALLEL_ALLOWED 금지.

### M11 Windows Special Alias
끝 점/공백, `\\?\`, relative/absolute, UNC, ADS, 8.3/unknown 검증.
같은 대상이면 conflict, 불확실하면 UNKNOWN fallback, unsafe parallel 0.

## I2 — Per-task Evidence Linkage
Scenario A/H 각 Task에서 Validator가:
- unique task_id
- unique run_id
- Task contract ↔ Run
- Run ↔ output
- actual output SHA ↔ Evidence.output_sha256
- output status ↔ Validation consistency
- Validation ↔ Evidence
- Evidence ↔ task/run identity
를 독립 확인한다.

Batch result/recovery candidates도 per-task Validation에서 도출하거나 Validator가 독립 재계산한다.

동일 run_id 공유 금지.

가능하면 Test 2 Ownership과 기존 Run/Evidence linkage 계약을 재사용한다.

### M12 Evidence Linkage Attack
- same run_id
- output_sha256 위조
- output status/Validation 모순
- Evidence task_id/run_id 변조 + SHA 재계산
Expected: FAIL/BLOCK.

## I3 — Scenario Manifest
Test 7의 검증된 Manifest 방식을 재사용한다.

Official Evidence 또는 Validation output에 Scenario tree 전체:
- scenario_id
- relative_path
- sha256

요구:
- actual files 전체 포함
- missing 0
- nonexistent 0
- mismatch 0
- unlinked 0

### M13 Manifest Attack
내용 변조 / 미등록 추가 / 등록 삭제 / manifest hash 위조 중 최소 3종 → FAIL/BLOCK.

## Ownership Reuse
Test 2의 실제 Ownership Asset/Contract를 먼저 검색한다.
안전하게 재사용 가능하면 One Task One Owner 판정을 공유한다.
Architecture 변경이 필요하면 새 추상화를 만들지 말고 현 구현 유지 + 이유 Evidence.
owner identity case sensitivity도 Test 2 계약과 일치.

## Failure Isolation Derivation
Scenario H 기본 동작은 유지.
가능한 최소 범위에서 batch_result와 recovery_candidates를 per-task Validation에서 도출하거나 Validator가 독립 재계산.

- all PASS → batch PASS
- 일부 FAIL → PARTIAL_FAILURE
- recovery candidate = FAIL Task만
- PASS Task rerun 0

하드코딩 상수만으로 증명 금지.

## Preserve
PARALLEL_ALLOWED / SEQUENTIAL_REQUIRED / HOLD, topological fallback, cycle HOLD, stable task_id fallback, shared resource conflict, Routing/Scope boundary, barrier 병렬 실행, failure isolation, M1~M8 의미를 유지한다.

## Mutations
기존 M1~M8 + 신규 M9~M13.
실제 Event/Evidence/filesystem/contract 위반이어야 한다.

## Validator Independence
독립 재계산:
- Task contract validity / UNKNOWN
- dependency graph/cycle/resolution
- ownership
- canonical/unknown path
- domain/shared resource
- scope/routing
- runtime concurrency record
- independent worker observation
- sequential order
- per-task run/output/validation/evidence linkage
- batch/failure isolation derivation
- scenario manifest

검사 불능 → ERROR.

## Version / Evidence
Plan1.0/Evidence 보존.

새 결과:
- `MVP-TEST-3`
- `Safe Parallel`
- Version `1.1`
- change_reason_ref `Order-049`
- New Run/Event/Validation/Evidence
- Scenario A~H + Manifest

Plan1.0 REVISION REQUIRED 이력 보존.

## Regression
기존 91 의미 보존 + 신규 Enforcement tests.
기존 91 PASS / 신규 전부 PASS / FAIL0 / ERROR0.
기존 Test 삭제/완화 및 Blind Retry 금지.

## Preservation
Test1/2/4/5/6/7 OFFICIAL PASS, Phase1, Common Harness/Core, Architecture/Terminology, Reference, Test3 Plan1.0/Evidence, 기존 Run/Event/Evidence 보존.
Architecture Delta NONE.

## GitHub Boundary
GitHub Beta 범위 밖. git init/add/commit/push 및 coordination/lock/queue/SSOT 사용 금지.

## Prohibited
Phase2, Architecture/Terminology 변경, 대형 Scheduler, Agent pool, DB/lock service, Plugin/Adapter, 기존 Evidence rewrite, Plan1.0 이력 변경, Test 완화, MVP 전체 PASS/Freeze 확정.

## Result Format
A. B1 Independent Concurrency Observation
B. B2 UNKNOWN Validation
C. I1 Windows Path Policy
D. I2 Per-task Evidence Linkage
E. I3 Scenario Manifest
F. Ownership Reuse
G. Failure Isolation Derivation
H. Scenario A~H
I. M1~M13
J. Validator Independence
K. Regression
L. Official Candidate — ID/version/reason/Run/Plan SHA/Executor SHA/Validator SHA/Evidence ID/SHA/Execution/Validation/Gate/Scenario/Manifest
M. Preservation
N. GitHub Boundary
O. Files Changed
P. Done / Now / Next

## Completion Gate
Plan1.1 PASS candidate:
- B1 fake parallel 독립 탐지
- B2 UNKNOWN never parallel
- I1 special/unknown Windows path unsafe parallel0
- I2 per-task Evidence linkage
- I3 Scenario Manifest
- Ownership reuse 검토
- Failure isolation derivation
- A~H PASS
- M1~M13 PASS
- Validator independent
- Regression PASS
- Preservation PASS
- Architecture Delta NONE
- GitHub untouched
- Evidence complete

Codex 단독 OFFICIAL PASS 금지.

완료 후:
Codex Order-049 Result
→ ChatGPT 검토
→ Claude READ-ONLY Plan1.1 Delta Recheck
→ PASS 시 Test3 OFFICIAL PASS candidate
→ Closure Sync
→ MVP 7 Gates 전체 Evidence Review
→ MVP PASS / Freeze Gate

## Current State
- Test1 Reuse: OFFICIAL PASS
- Test2 Ownership: OFFICIAL PASS
- Test3 Plan1.0: REVISION REQUIRED
- Test3 Plan1.1: NOT RUN
- Test4 Bottleneck: OFFICIAL PASS
- Test5 Prevention: OFFICIAL PASS
- Test6 User Gate: OFFICIAL PASS v1.2
- Test7 Resume: OFFICIAL PASS v1.1
- MVP overall PASS: NOT YET
- MVP Freeze: NOT YET
- User approval: already granted within this fix scope
- Next executor: Codex

=== ORDER END ===
