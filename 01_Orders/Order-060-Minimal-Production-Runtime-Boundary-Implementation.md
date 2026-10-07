# Order-060 — Minimal Production Runtime Boundary Implementation

## Metadata
- Order ID: Order-060
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: IMPLEMENT_AND_VALIDATE
- Trigger: Order-059 READY FOR IMPLEMENTATION USER GATE
- MVP: OVERALL PASS / FROZEN
- Architecture Compatibility: COMPATIBLE_EXTENSION
- Architecture Delta: NONE expected
- Phase2: NOT STARTED
- Actual Production Runtime: NOT AUTHORIZED
- Git Push: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: IMPLEMENT_AND_VALIDATE
order: Order-060
project: Beta
mismatch -> HOLD / no implementation / no runtime
```

## Purpose
FROZEN Architecture를 변경하지 않고 첫 Production Runtime을 위한 최소 경계를 구현·검증한다. 실제 `Beta-Index.md` Production Run은 아직 금지한다.

범위는 정확히 네 기능:
1. Approved Input → Runtime Task Contract
2. Single-file READ_ONLY_INTEGRITY Executor
3. Independent File Integrity Validator
4. Existing Gate + Evidence 연결

## Fixed Decisions
- Target(first actual runtime): `C:\Obsidian\Beta\Beta-Index.md`
- Approved root: `C:\Obsidian\Beta`
- Operation: `READ_ONLY_INTEGRITY`
- Task count 1
- parallel=false
- dependencies=[]
- target side effect=NONE
- network=false
- external_publish=false
- missing file → HOLD / Run0
- exact Executor/Validator path + SHA allowlist
- runtime namespace: `04_Evidence/runtime/read_only_integrity/<request_id>/`
- actual production run only after Independent Review + separate User Gate

Duplicate request:
same request_id + same scope + same Plan hash + existing PASS Evidence → NO_CHANGE / new Run0 / duplicate Evidence0.
새 시점 관찰 → new request_id + new Run/Evidence.

## Reuse
Direct reuse:
- `validator_runner.py`
- `gate.py`
- `event_store.py`

Thin extension:
- `model.py`
- `executor.py`
- `cli.py`

기존 fixture resolver/Test 동작을 약화하지 않는다.

## Minimal New Files
- `runtime_boundary.py`: approval/scope/path/operation/permission/allowlist validation; invalid request → run_task0
- `file_integrity_executor.py`: existence/size/SHA-256, target write 기능 없음
- `file_integrity_validator.py`: path/existence/size/SHA 독립 재계산, mismatch FAIL, 검사 실패 ERROR
- `03_Tests/test_runtime_boundary.py`: V1~V8 + zero-execution/side-effect

더 적은 파일로 가능하면 허용하되 Validator 독립성을 약화하지 않는다.

## Runtime Contract
기존 Plan fields를 재사용하고 최소 `runtime_request`:
```text
request_id
operation=READ_ONLY_INTEGRITY
target_path
approved_root
approval_ref
expected_target_side_effect=NONE
parallel_allowed=false
```
기존 Plan SHA가 runtime_request까지 포함해야 한다.

실제 approval registry를 새로 만들지 않는다. 테스트 approval은 fixture임을 명시. Production에서는 별도 User Gate approval_ref만 허용할 경계를 만든다.

## Path Safety
첫 Runtime은 exact target pinning.
허용: absolute local exact target, approved root 내부, normal file, non-symlink/reparse.
HOLD: 다른 target, relative, wildcard, UNC, device, ADS, reserved/ambiguous, root 밖, symlink/reparse, canonicalization 불확실, missing.

범용 Windows path framework 금지.

## Target Mutation Protection
최소 연결:
- pre-execution SHA/size
- executor observed SHA/size
- post-execution SHA/size
- validator current SHA/size

pre/post mismatch → Validation FAIL / Gate BLOCK.
Executor에 target mutation API를 제공하지 않는다.

## Core Extensions
### model.py
fixture validation 유지 + production exact allowlist 정책 추가. production allowlist 없으면 기존 behavior.

### executor.py
기존 subprocess/timeout/status 재사용 + optional approved runtime request 전달. arbitrary executable/input 금지.

### cli.py
명시적 production runtime entry 분리. Boundary PASS 후에만 run_task. HOLD/APPROVAL_REQUIRED → RUN_STARTED0. Runtime Evidence namespace 연결. 기존 CLI/Test 보존.

범용 shell execution 금지.

## Evidence Chain
최소:
request_id, approval_ref, task_id, plan_version/hash, run_id, executor identity/SHA, validator identity/SHA, target path, pre/executor/post/validator SHA+size, validation status, gate decision, evidence_id.

Fixture Evidence와 Production Runtime Evidence를 구별한다.

## V1~V8
- V1 Normal: 격리 Test target에서 executor/validator 일치 → PASS/PROCEED, target side effect0
- V2 Executor Forgery → Validator FAIL/BLOCK
- V3 Outside Scope → HOLD, run_task0, RUN_STARTED0, Run dir0
- V4 Unsafe Path(relative/wildcard/device/UNC/ADS) → HOLD/Run0
- V5 Missing → HOLD/Run0/side effect0
- V6 isolated target mutation → FAIL/BLOCK
- V7 Approval Missing → APPROVAL_REQUIRED/HOLD, Run0, Runtime Run/Evidence0
- V8 Request/Task/Run/Validation/Evidence ID/SHA tamper → BLOCK

실제 Production `Beta-Index.md`를 V1~V8에 사용하지 않는다.

## Additional Tests
- exact allowlisted Executor/Validator만 허용
- 다른 `.py` → HOLD/BLOCK
- executable SHA mismatch → HOLD/BLOCK
- duplicate request → NO_CHANGE / Run0 / duplicate Evidence0
- 정상 READ_ONLY target hash before==after

## Regression
기존 100개 의미 보존 + 신규 Runtime tests.
Expected:
- existing 100 PASS
- new all PASS
- FAIL0 / ERROR0
기존 Test 삭제/완화 및 Blind Retry 금지.

## Known Limitations
KL-1 parallel=false.
KL-2 exact target/path HOLD.
KL-3 dependencies=[].
세 항목 OPEN / ACCEPTED FOR MVP 유지.

## Preservation
MVP Overall PASS/FROZEN, 7/7, Architecture v1.0 FROZEN, Terminology, Phase1, Test Evidence, Known Limitations, Order-057 Freeze baseline/GitHub Snapshot 보존.
Architecture version 변경 금지.

## Git
이번 Order에서 commit/push 금지.
구현 변경은 local worktree에 남기고 정확히 보고.
Independent Review PASS 후 별도 sync/snapshot 판단.

## Prohibited
실제 Production Runtime/Beta-Index Run, Phase2, Safe Parallel/Resume/Prevention productionization, general Generator/Classifier/Scheduler, Skill/Rule/Hook, Plugin/Adapter/Remote, EXE/PWA, multi-file/write/delete/move, network/publish, Architecture/Terminology 변경, Known Limitation 종료, Git push.

## Required Result
A Routing/Preflight
B Reuse Implementation
C Runtime Boundary
D Executor
E Independent Validator
F Core Extensions
G Safety/Allowlist
H Evidence Chain
I V1~V8
J Duplicate Request
K Target Side Effect
L Existing 100 Regression
M New Regression Total
N Known Limitation Isolation
O Preservation/Architecture Delta
P Files Changed
Q Git Status
R Implementation Candidate
S Done/Now/Next
T User Approval Required

## Completion Gate
PASS candidate:
- four capabilities only
- V1~V8 PASS
- allowlist PASS
- duplicate request NO_CHANGE
- target side effect0
- Validator independent
- Evidence linkage complete
- existing100 PASS + new tests PASS
- Architecture Delta NONE
- MVP FROZEN
- KLs OPEN
- Phase2 NOT STARTED
- actual Production Run0
- Git push0
- scope violation0

Codex 단독 production-ready 확정 금지.

완료 후:
Codex Result → ChatGPT review → Claude READ-ONLY Independent Review → PASS 시 Closure/State Sync → 별도 First Runtime User Gate → 승인 후에만 실제 Beta-Index READ_ONLY_INTEGRITY Run.

## End State
- Minimal Production Runtime Boundary = IMPLEMENTED / PASS candidate
- Actual Production Runtime = NOT RUN
- MVP = FROZEN
- Architecture Delta = NONE
- Phase2 = NOT STARTED
- Git push = NO
- Next = Independent Review
- Actual Runtime requires User Gate

=== ORDER END ===
