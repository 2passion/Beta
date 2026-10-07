# Order-073 — KL-4 User Acceptance State Sync + First Runtime Gate Preparation

## Metadata
- Project: Beta
- Status: USER APPROVED
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer/To: Codex
- Reviewer: Claude Code
- Action: SYNC_DECISION_AND_PREPARE_GATE
- Trigger: Order-072 CLOSED/PASS + User KL-4 Acceptance
- MVP: PASS/FROZEN
- Runtime Boundary: CLOSED/VERIFIED
- Phase2: NOT STARTED
- Actual Runtime/Authorization: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
order: Order-073
action: SYNC_DECISION_AND_PREPARE_GATE
mismatch -> HOLD
```

## User Decision
KL-4 Local Writer Trust Boundary를 `OPEN / ACCEPTED FOR MVP`로 수용한다.
RESOLVED/CLOSED가 아니며 MVP Threat Model의 알려진 한계로 유지한다.
근거: Order-071 PASS + Order-072 Closure + User decision.
실제 필요성이 Runtime Evidence로 확인되면 Hardening Proposal을 검토한다.

Known examples:
- same-process `_ISSUER`
- malicious Core rewrite
- malicious `__pycache__`/`.pyc`

운영 보완: Final User Gate에서 Runtime Request Hash + Runtime Code Baseline Hash + Approved Git Commit 확인.

## Purpose
1. KL-4 수용을 기존 SSOT/History/Evidence에 동기화
2. First Runtime User Gate payload/hash 준비
3. 실제 Runtime/authorization/Evidence는 0 유지

## Preflight
- Order-072 CLOSED/PASS
- Closure commit `790841d4506fb0590dbeeac3f3764841a97c6a28`
- local HEAD == origin/main
- Runtime Boundary CLOSED/VERIFIED
- Production Run0 / Authorization NOT ISSUED
- Phase2 NOT STARTED
불일치 → HOLD.

## State Sync
기존 구조 재사용:
- KL-4 = OPEN / ACCEPTED FOR MVP
- accepted_by = User
- scope = MVP only
- resolved=false
- closed=false
- hardening_trigger = Runtime Evidence에서 실제 필요성 확인

새 DB/Registry 금지.

## Acceptance Evidence
기존 Evidence 구조에 KL-4 id/name, previous/new state, User decision reference, Closure commit, Architecture unchanged, Production Run0, known examples, mitigation을 연결.

## First Runtime Candidate
```text
Target: C:\Obsidian\Beta\Beta-Index.md
Operation: READ_ONLY_INTEGRITY
Approved Root: C:\Obsidian\Beta
Task count: 1
Parallel: false
Dependencies: []
Target Write: NONE
Network: false
External Publish: false
```
이번 Order에서는 실행 금지.

## Gate Payload
계산/준비:
- target_path / approved_root / operation
- target_side_effect=NONE
- parallel=false / dependencies=[]
- network=false / external_publish=false
- approved_git_commit
- policy path/SHA
- executor path/SHA
- validator path/SHA
- runtime_code_baseline_hash
- canonical runtime_request_hash

Closure commit을 baseline 후보로 사용:
`790841d4506fb0590dbeeac3f3764841a97c6a28`

Runtime Core 변경 금지.

## Gate Display
다음 User Gate에 실제 값을 표시:
Target / Operation / Approved Root / Target Write / Network-Publish /
Approved Git Commit / Runtime Request Hash / Runtime Code Baseline Hash /
Executor SHA / Validator SHA / KL-4 state.

사용자 승인 전 authorization0 / Run0 / Production Evidence0.
Gate artifact 자체는 authorization source가 아니다.

## Validation
- State/History/Evidence consistency
- KL-4 exact state
- Architecture/Terminology unchanged
- Production0
- git diff --check
- request hash deterministic
- code baseline deterministic
- payload completeness

Decision-only sync이므로 Runtime Core 변경이 없으면 전체178 Regression 재실행하지 않는다.
Core 변경 발생 → HOLD.

## Git Snapshot
Validation PASS 후 state/decision/gate preparation만 commit/push 허용.
Runtime Core 변경/관련 없는 파일 포함 금지.
권장 commit: `beta: accept KL-4 for MVP and prepare first runtime gate`
fast-forward only; force/rebase 금지.

First Runtime approved_git_commit은 기존 Runtime contract를 읽어 Closure commit 또는 Decision commit 중 정확한 의미를 판정. 추정 금지. 불명확 → HOLD.

## Metrics
Timing: preflight → state sync → evidence → gate payload → validation → git snapshot → report.
Token/Cost 근거 없으면 NOT_AVAILABLE.
State/Document/Evidence delta 측정. Code/Test delta0 예상.
retry/blind_retry/blocker/important/minor/unexpected_exception/review_side_effect/recovery/user_gate 기록.
이번 user_gate_count=1은 KL-4 Acceptance Gate이며 First Runtime Gate와 구분.

## Prohibited
actual Runtime, execution authorization, Production Evidence, Runtime Core 변경,
Architecture/Terminology 변경, Phase2, KL-4 CLOSED/RESOLVED, force/rebase, unrelated commit.

## Required Result
A Preflight
B KL-4 State Sync
C Acceptance Evidence
D First Runtime Candidate
E Gate Payload
F Gate Hashes
G Gate Display Summary
H Validation
I Production Status
J Git Snapshot
K Post-Push
L Architecture/Phase2
M Files Changed
N Metrics Summary
O Stage Metrics
P Token/Cost
Q Size
R Efficiency
S Final Status
T Done/Now/Next
U User Approval Required

## Final Decision
- PASS / READY FOR FIRST RUNTIME USER GATE
- REVISION REQUIRED
- HOLD

## End State
- KL-4 OPEN / ACCEPTED FOR MVP
- Runtime Boundary CLOSED / VERIFIED
- Production Runtime NOT RUN
- Production Authorization NOT ISSUED
- First Runtime Gate Payload READY
- Phase2 NOT STARTED
- Next = FIRST RUNTIME USER GATE

=== ORDER END ===
