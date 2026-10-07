# Order-068 — Runtime TOCTOU + Atomic Authorization Fix & KL-4 Boundary

## Metadata
- Order ID: Order-068
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE + BOUNDARY RECORD
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: FIX_AND_VALIDATE
- Trigger: Order-067 REVISION REQUIRED
- MVP: PASS / FROZEN
- Architecture: v1.0 FROZEN
- Phase2: NOT STARTED
- Actual Runtime / Production Authorization / Beta Git Write: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: FIX_AND_VALIDATE
order: Order-068
project: Beta
mismatch -> HOLD / no implementation / no runtime / no git write
```

## Threat Boundary Decision
### KL-4 — Local Writer Trust Boundary
Production Runtime은 사용자가 승인한 Runtime Request Hash와 Runtime Code Baseline을 사용한다는 운영 가정을 둔다.

동일 Local Writer가 승인/검증 Core 자체를 악의적으로 재작성해 사용자 승인을 위조하는 공격까지 Local Core가 자기 자신만으로 독립 방어하는 것은 현재 MVP Threat Model 밖이다.

- Packet/Git commit 자체는 authorization source 아님
- Production 직전 User Gate에서 Request Hash + Runtime Code Baseline 확인
- KL-4 = OPEN / CANDIDATE FOR ACCEPTANCE
- 해결됨으로 표시 금지
- KL-1~KL-3 유지

## Purpose
Threat Model 안에서 반드시 해결:
1. TOCTOU executor/validator 교체 실행
2. authorization 검사/소비 race + pickle 복제
3. Runtime Code Baseline을 User Gate/Evidence 계약에 포함
4. KL-4 명시
5. 실제 공격 Regression 추가

기존 forged packet/Git, NO_CHANGE, READ-ONLY 등은 보존.

## Fix 1 — Atomic One-shot
`claim_user_gate_authorization` 검사+소비를 하나의 원자 작업으로.

- `threading.Lock` 등 사용
- lock 안에서 exact identity/type, scope/root/hash, consumed 확인과 consume transition
- consumed 후 재사용 불가

### Copy/Serialization
`__reduce__`, `__reduce_ex__`, pickle, copy, deepcopy, clone/state restoration 차단.

### Race Tests
- 2 threads barrier
- 4 threads stress
- artificial delay
- same capability
Expected: exactly one consume, at most one Run, 나머지 계약된 HOLD/APPROVAL_REQUIRED, unhandled exception0.

## Fix 2 — TOCTOU Final Revalidation
Executor subprocess 직전:
- path identity
- current SHA
- approved policy/baseline SHA
재검증. mismatch → process 생성 전 BLOCK.

Validator도 동일.

### Preferred Run-local Snapshot
가능하면 승인 executable bytes를 읽고 SHA 검증 후 Run-local execution snapshot으로 복사 → snapshot SHA 재검증 → snapshot 실행.

새 deployment/cache 시스템 금지. target write0.

### TOCTOU Tests
실제 hook/barrier:
- claim 직후 executor 교체
- policy 검증 후 executor 교체
- executor 후 validator 교체
- boundary→run_task 사이 교체
Expected: malicious process0 / marker0 / BLOCK-HOLD.

## Runtime Code Baseline
Final User Gate payload에 enforcement code baseline 포함.

최소 파일:
- user_gate.py
- cli.py
- runtime_policy.py
- runtime_boundary.py
- executor.py
- validator_runner.py
- gate.py
- file_integrity_executor.py
- file_integrity_validator.py

canonical relative path + SHA 목록의 hash = `runtime_code_baseline_hash`.

Final User Gate 단위:
- runtime_request_hash
- runtime_code_baseline_hash
- approved_git_commit

실행 직전 current enforcement files가 baseline과 일치하는지 확인.

KL-4 때문에 malicious Writer가 baseline 계산 코드까지 바꾸는 공격을 해결했다고 주장하지 않는다. Baseline은 User Gate에서 확인할 운영 Evidence다.

## User Gate Display Contract
향후 표시:
- Target
- Operation
- Target Write NONE
- Network/Publish false
- approved Git commit
- Runtime Request Hash
- Runtime Code Baseline Hash
- Executor SHA
- Validator SHA

## Evidence Contract
향후 Evidence:
- runtime_request_hash
- runtime_code_baseline_hash
- approved_git_commit
- approval_ref
- User Gate decision reference
- executor/validator SHA
- run/validation/gate

이번 Order Production Evidence0.

## KL-4 Recording
기존 Known Limitation 문서/구조가 있으면 최소 반영 가능:
`KL-4 = OPEN / CANDIDATE FOR ACCEPTANCE`

새 Registry 금지. Architecture version 변경 금지.

## Regression Additions
기존154 의미 보존 + 최소:
1. concurrent same authorization → exactly one Run
2. artificial claim delay → exactly one consume
3. pickle → rejected
4. copy/deepcopy → rejected
5. claim 후 executor 실제 교체 → marker0
6. policy validation 후 executor 교체 → marker0
7. executor 후 validator 교체 → marker0
8. boundary→run_task 사이 executable 교체 → marker0
9. runtime code baseline mismatch → HOLD
10. request hash + code baseline Evidence linkage
11. NO_CHANGE does not consume new authorization
12. concurrent same request → defined result, unhandled exception0

Core 자체 편집 capability forgery는 KL-4 Threat Model boundary이며 해결됐다고 주장하지 않는다.

## Existing Regression
- existing154 PASS
- new all PASS
- FAIL0 / ERROR0
- 삭제/완화0
- stability check preferably ×2

## Architecture Compatibility
기존 User Gate/Caller/Executor/Validator/Evidence 책임의 hardening.
새 Agent/Plugin/Adapter/DB/PKI 역할 없음.
Architecture 의미 변경 필요 시 HOLD.

## Production Prohibition
actual Beta-Index Run0 / authorization0 / approval packet0 / Production Evidence0.

## Git
Beta commit/push/tag 금지. read-only Git 허용. 격리 test repo commit 허용.

## Preservation
MVP PASS/FROZEN, 7/7, Architecture/Terminology FROZEN, Phase2 NOT STARTED, KL-1~KL-3 OPEN/ACCEPTED, KL-4 OPEN candidate, GitHub not SSOT.

## Prohibited
actual Runtime/User authorization, Beta git write, Phase2, Architecture change, PKI/HMAC/secret system, new DB/Registry, UI integration, Plugin/Adapter/Remote, EXE/PWA, Known Limitation CLOSED.

## Required Result
A Routing/Preflight
B KL-4 Boundary
C Atomic Authorization
D Serialization/Copy
E TOCTOU Final Revalidation
F Execution Snapshot
G Runtime Code Baseline
H User Gate Display Contract
I Evidence Contract
J Race/TOCTOU Regressions
K Existing154 Regression
L New Regression Total
M NO_CHANGE Preservation
N READ-ONLY Preservation
O Architecture/Known Limitations
P Actual Runtime/Approval
Q Files Changed
R Git Status
S Fix Candidate
T Done/Now/Next
U User Approval Required

## Completion Gate
PASS candidate:
- atomic consume under lock
- concurrent capability at most one Run
- pickle/copy/deepcopy duplication blocked
- executor/validator TOCTOU malicious execution0
- unhandled concurrent exception0
- runtime code baseline generated/checked
- User Gate payload includes request+code baseline
- Evidence contract includes hashes+commit
- KL-4 explicitly bounded, not claimed solved
- existing154 preserved + new attacks PASS
- Production Run/approval/Evidence0
- Beta Git write0
- Architecture Delta NONE
- MVP FROZEN / Phase2 NOT STARTED

Codex 단독 production-ready 확정 금지.

완료 후:
Codex Result → ChatGPT review → Claude READ-ONLY TOCTOU/Atomic Delta Recheck → PASS 시 Closure/State Sync → KL-4 User Acceptance Gate → First Runtime User Gate → Request Hash + Runtime Code Baseline Hash 표시 → 사용자 승인 → 별도 Runtime Order → actual Beta-Index READ_ONLY_INTEGRITY.

## End State
- TOCTOU/Atomic Fix = PASS candidate
- KL-4 OPEN candidate
- Production authorization NOT ISSUED
- Actual Runtime NOT RUN
- MVP FROZEN
- Architecture Delta NONE
- Phase2 NOT STARTED
- Git write NO
- Next = Independent TOCTOU/Atomic Delta Recheck

=== ORDER END ===
