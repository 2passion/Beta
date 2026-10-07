# Order-059 — Minimal Production Runtime Boundary Proposal

## Metadata
- Order ID: Order-059
- Project: Beta
- Status: APPROVED
- Type: READ-ONLY DESIGN PROPOSAL
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Executor / To: Codex
- Reviewer: Claude Code
- Action: REVIEW_AND_PROPOSE_ONLY
- Trigger: Order-058 RUNTIME_ENTRY_GAP
- MVP: OVERALL PASS / FROZEN
- Phase2: NOT STARTED
- Implementation: NOT AUTHORIZED
- Git Write/Push: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
executor: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: REVIEW_AND_PROPOSE_ONLY
order: Order-059
project: Beta
mismatch -> HOLD / no write / no implementation / no git
```

## Purpose
Order-058의 `RUNTIME_ENTRY_GAP`을 해결하기 위한 **최소 Production Runtime Boundary 설계 Proposal**을 작성한다. 구현은 하지 않는다.

첫 실제 Runtime 후보:
> 사용자가 승인한 비민감 로컬 파일 1개의 READ-ONLY 무결성 관찰(size + SHA-256)

## Preserve Order-058 Findings
- FROZEN MVP / 7/7 OFFICIAL PASS
- 완전한 production Runtime Asset 없음
- Core Caller/Validator/Gate/Evidence primitive 일부 재사용 가능
- Classifier/Router/Scheduler/Resume/Prevention/User Gate/Safe Parallel은 fixture 중심
- Production Generator 없음
- non-fixture executable은 현재 Core 경계에서 허용되지 않음
- production input/executable boundary가 없어 실제 Operation 실행 불가

## Design Principle
```text
User-approved Request
→ Minimal Runtime Boundary
→ Single Read-only Task Contract
→ File Integrity Executor
→ Independent Validator
→ Existing Gate
→ Existing Evidence primitives
→ Report
```

대형 Runtime 시스템을 만들지 않는다.

## Scope — Four Capabilities Only
1. **Approved Input → Runtime Task Contract**
   - target path
   - operation=`READ_ONLY_INTEGRITY`
   - approved scope/root
   - owner
   - request/approval identity
   - 범용 자연어 Classifier/Generator 아님

2. **Single-file Read-only Executor**
   - existence / size / SHA-256
   - target write/move/delete/external transfer 금지
   - Task 1개, parallel=false

3. **Independent File Integrity Validator**
   - approved/canonical path
   - existence
   - size
   - SHA-256 재계산
   - PASS/FAIL/ERROR

4. **Existing Gate + Evidence Connection**
   - 기존 Gate/Event Store/Run/Validation/Evidence primitive 우선 재사용
   - 새 Evidence 시스템/DB 금지

## Explicitly Out of Scope
Safe Parallel/Resume/Prevention productionization, general Generator/Classifier/Scheduler, Skill/Rule/Hook, Plugin/Adapter/Remote, EXE/PWA, Phase2, multi-file, write/delete/move, external publication, personal/sensitive-data workflow.

## Reuse Before Create Review
실제 파일을 읽고 재사용 가능성을 판정:
- `02_Core/beta_core/model.py`
- `executor.py`
- `validator_runner.py`
- `gate.py`
- `event_store.py`
- `cli.py`

각각:
- direct reuse
- thin extension
- fixture restriction 때문에 직접 사용 불가
로 구분한다.

## Minimal Contract
기존 model/Plan schema를 먼저 읽고 중복 필드를 만들지 않는다.

후보:
```text
request_id
task_id
operation
target_path
approved_root
owner
approval_ref
expected_side_effect=NONE
parallel_allowed=false
dependencies=[]
```

## Safety Contract
모두 충족해야 실행 가능:
1. READ_ONLY_INTEGRITY
2. target 정확히 1개
3. approved_root 내부
4. 존재
5. path ambiguity/symlink/reparse 불확실 → HOLD
6. 민감 파일 → HOLD
7. target side effect 0
8. external communication 0
9. dependencies=[]
10. parallel=false
11. independent Validator
12. approval_ref 존재
13. Evidence chain 가능

## Path Policy
첫 Runtime은 보수적으로:
- absolute local path only
- approved_root 아래
- wildcard/relative/UNC/ADS/device/reserved/ambiguous path 금지
- symlink/reparse 확인 불가 → HOLD
- 범용 Windows path framework 금지

## Known Limitation Isolation
- KL-1: `parallel=false`
- KL-2: 위험/불명확 path는 실행 전 HOLD
- KL-3: `dependencies=[]`

Known Limitation을 수정/CLOSE하지 않는다.

## User Gate Contract
첫 Runtime은 명시적 User Gate 필요:
- 대상 파일
- approved_root
- READ_ONLY_INTEGRITY
- Runtime Evidence 기록 범위

승인 Scope 안에서는 중간 재승인 최소화.

## Proposed File Boundary
새 파일이 정말 필요할 때 최소 후보:
```text
02_Core/beta_core/runtime_boundary.py
02_Core/beta_core/file_integrity_executor.py
02_Core/beta_core/file_integrity_validator.py
```
그러나 기존 파일의 작은 extension으로 가능한지 먼저 비교. 이번 Order에서는 생성하지 않는다.

## Evidence Namespace
기존 구조를 우선 확인한다. 필요할 경우 최소 후보:
`04_Evidence/runtime/`
새 DB 금지.

## Runtime Flow
```text
User Approval
→ Request Contract
→ Boundary Validation
→ Task Contract
→ Run Started
→ Read-only Executor
→ Independent Validator
→ Evidence
→ Gate
→ Report
```
Boundary FAIL → HOLD / Run0 / target side effect0.
Validation FAIL/ERROR → Run 보존 / Gate BLOCK / No Blind Retry.

## Idempotency
Runtime 관찰은 시점 Evidence일 수 있으므로 같은 파일/Scope 재관찰 시 새 Run을 무조건 금지하지 않는다. 기존 Run semantics와 비교해 결정안을 제시한다. target side effect는 항상 0.

## First Runtime Candidate
```text
Target: C:\Obsidian\Beta\Beta-Index.md
Operation: READ_ONLY_INTEGRITY
Task count: 1
Parallel: false
Dependencies: []
Target write: 0
External communication: 0
Validation: independent size + SHA-256
Evidence: production/runtime namespace
```
이번 Order에서는 실행 금지.

## Future Validation V1~V8
- V1 Normal: executor/validator size+SHA 일치 → PASS
- V2 Executor Forgery: SHA 위조 → FAIL
- V3 Outside Scope → HOLD / Run0
- V4 relative/wildcard/device/UNC/ADS → HOLD
- V5 Missing File → HOLD 또는 계약상 ERROR / side effect0
- V6 Write Attempt/target mutation → FAIL/BLOCK
- V7 Approval Missing → APPROVAL_REQUIRED/HOLD / Run0
- V8 Run/Validation/Evidence identity/hash mismatch → BLOCK

## Architecture Compatibility
실제 FROZEN Architecture와 Core를 읽고 둘 중 하나로 판정:

### COMPATIBLE_EXTENSION
현재 Architecture 의미 변경 없이 최소 Runtime 연결부 추가 가능.

### ARCHITECTURE_CHANGE_REQUIRED
fixture-only 실행이 제품 경계로 정의돼 production executable 허용 자체가 의미 변경.

추정 금지. 후자면 구현하지 말고 Architecture Change Proposal + User Gate.

## Minimal Implementation Estimate
코드 작성 없이:
- touched files
- new files
- 각 책임
- tests
- Evidence namespace
- 예상 Architecture delta
를 구성요소 수로 보고한다.

## Required Output
A. Frozen Baseline
B. Order-058 Gap Confirmation
C. Reuse Review
D. Minimal Runtime Boundary Contract
E. Safety Contract
F. Path Policy
G. Known Limitation Isolation
H. User Gate Contract
I. Proposed File Boundary
J. Evidence Namespace
K. Runtime Flow
L. Idempotency Decision
M. First Runtime Candidate
N. Future Validation V1~V8
O. Architecture Compatibility
P. Minimal Implementation Scope Estimate
Q. Risks / Open Decisions
R. Files Changed = NONE
S. Git Changed = NONE
T. Phase2 = NOT STARTED
U. Final Decision
V. User Approval Required

## Final Decision
- `READY FOR IMPLEMENTATION USER GATE`
- `ARCHITECTURE CHANGE USER GATE`
- `HOLD`

## End State
- MVP remains FROZEN
- no production code changed
- no Runtime Run/Evidence
- Git unchanged
- Phase2 NOT STARTED
- implementation requires explicit User Gate

=== ORDER END ===
