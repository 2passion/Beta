# Order-062 — Minimal Production Runtime Boundary Enforcement Fix

## Metadata
- Order ID: Order-062
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: FIX_AND_VALIDATE
- Trigger: Order-061 REVISION REQUIRED
- MVP: PASS / FROZEN
- Architecture: v1.0 FROZEN
- Architecture Delta expected: NONE
- Phase2: NOT STARTED
- Actual Production Runtime: NOT AUTHORIZED
- Git Commit/Push: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: FIX_AND_VALIDATE
order: Order-062
project: Beta
mismatch -> HOLD / no implementation / no production runtime / no git
```

## Purpose
Order-061에서 재현된 **BLOCKER 2 + IMPORTANT 2**만 최소 수정한다. 전체 Runtime Boundary를 재설계하지 않는다.

수정:
1. Core 직접 호출 Boundary/allowlist 우회
2. 실행 시점 self-calculated SHA pin
3. 임의 문자열 approval_ref
4. Duplicate/NO_CHANGE의 Boundary/Evidence 재검증 누락
5. 관련 작은 fail-closed hardening
6. 공격 Regression 추가

## Preserve
V1~V8, fixture/production 기본 분리, 위험 path HOLD, READ-ONLY mutation detection, independent target Validator, evidence verifier, 기존 100 + Runtime 12 tests, KL 격리, FROZEN baseline을 유지한다.

## Fix 1 — Core Production Policy
현재 `run_task(... approved_program_paths={...})`를 호출자가 임의 지정할 수 있다.

수정:
- production executable policy는 caller-supplied path set을 신뢰하지 않는다.
- fixture와 production policy를 분리한다.
- production 실행은 승인된 Runtime contract/entry를 통해서만 가능.
- Core 직접 `run_task` 호출에서도 production policy를 다시 강제.
- arbitrary `approved_program_paths`만으로 production executable 실행 금지.

### B1 Regression
차단:
- missing approval + direct run_task
- outside target + direct run_task
- arbitrary evil executor
- caller-supplied production allowlist
- fixture 경로 production 우회

Expected: HOLD/BLOCK, arbitrary execution0, marker0, invalid production Run0.

## Fix 2 — Real Approved SHA Pin
승인 SHA는 실행 대상 파일과 독립된 신뢰 근거에서 가져온다.

최소 trusted runtime policy/manifest:
- executor exact path + approved SHA-256
- validator exact path + approved SHA-256

실행 직전 current SHA를 approved SHA와 비교.
Mismatch → HOLD/BLOCK.

파일 변경 시 pin 자동 재계산 금지.

### Regression
- modified executor → BLOCK
- replaced/always-PASS validator → BLOCK
- same filename other directory → BLOCK
- approved path different content → BLOCK

## Fix 3 — Exact Approval Gate
First Runtime User Gate는 아직 승인되지 않았다.

따라서:
- Production approval = NOT ISSUED
- 실제 production 호출은 APPROVAL_REQUIRED
- Test fixture approval은 fixture-only token/record
- fixture approval을 production에 사용 금지
- arbitrary `approval_ref="x"` 금지

향후 First Runtime User Gate에서 정확한 approval_ref/hash를 별도 Order로 고정한다.

## Fix 4 — NO_CHANGE Full Reverification
NO_CHANGE 전 반드시:
1. same request_id
2. same approved scope
3. same Plan hash
4. prior Boundary Decision = PROCEED
5. prior Gate = PROCEED
6. prior Validation = PASS
7. full Evidence chain verification PASS
8. executor/validator trusted identity + approved SHA valid
9. target contract identity consistent
10. invalidating FAIL/ERROR/BLOCK history 없음

하나라도 실패 → NO_CHANGE 금지 / HOLD-BLOCK / new Run0.

Regression:
- previous Boundary BLOCK → no NO_CHANGE
- tampered Evidence + recomputed file hash → no NO_CHANGE
- run/validator/executor/evidence identity tamper → HOLD/BLOCK
- previous FAIL → no NO_CHANGE
- genuine prior PASS → NO_CHANGE / Run0 / duplicate Evidence0

## Fix 5 — Strict / Fail-closed
- bool은 실제 bool만
- task_count는 bool이 아닌 exact int 1
- unknown contract fields reject 또는 Evidence에서 제외
- reserved request_id(CON/PRN/AUX/NUL/COM1~9/LPT1~9 등) 거부
- final target observation OSError/delete → handled FAIL/ERROR/BLOCK + decision 기록
- reparse/symlink는 resolve 전 가능한 범위에서 검사, 불확실하면 HOLD
- 범용 Windows path framework 금지

## Evidence Reader
`verify_runtime_evidence`의 검증 의미를 재사용하여 Duplicate 재검증 시 저장된 Runtime Evidence directory/records만으로 필요한 chain을 확인할 최소 reader를 추가한다.

새 일반 Evidence Query/DB 금지.

## Production Entry
명시적 production entry가 필요하면 최소 entry만 추가 가능.
단:
- Production approval NOT ISSUED
- 따라서 실제 호출은 APPROVAL_REQUIRED
- Beta-Index Production Run 0
- arbitrary target/executable 금지

## Tests
기존 112개 의미 보존.

최소 신규 공격 Regression:
1. direct Core bypass
2. evil executor
3. modified approved executor
4. replaced validator
5. arbitrary approval_ref
6. fixture approval in production
7. Boundary BLOCK → duplicate
8. tampered Evidence → duplicate
9. previous FAIL → duplicate
10. genuine PASS → duplicate NO_CHANGE
11. strict bool/int
12. reserved request_id
13. final target deletion/OSError
14. reparse/symlink policy test

기존 Test 삭제/완화 금지.

## Validation
- existing 112 PASS
- new attacks all PASS
- FAIL0
- ERROR0
- No Blind Retry

## Production Runtime Prohibition
이번 Order:
- actual `C:\Obsidian\Beta\Beta-Index.md` Production Run = 0
- production Runtime Evidence = 0
- production approval_ref = NOT ISSUED

테스트는 격리 fixture target만.

## Known Limitations
KL-1~KL-3 OPEN / ACCEPTED FOR MVP 유지.
parallel=false / exact path / dependencies=[] 격리 유지.
CLOSED 금지.

## Preservation
유지:
- MVP PASS/FROZEN
- 7/7 OFFICIAL PASS
- Architecture v1.0/Terminology FROZEN
- Phase1/Test Evidence
- Order-057 Freeze baseline/GitHub Snapshot
- Phase2 NOT STARTED
- Architecture Delta NONE

## Git
commit/push/merge/rebase 금지.
Local worktree 변경만 정확히 보고.

## Prohibited
actual Production Runtime, Beta-Index Runtime Run, production approval 발급, Phase2, Architecture/Terminology 변경, general Generator/Classifier/Scheduler, Safe Parallel/Resume/Prevention productionization, Skill/Rule/Hook, Plugin/Adapter/Remote, EXE/PWA, multi-file/write/delete/move, network/publish, Known Limitation 종료, Git commit/push.

## Required Result
A Routing/Preflight
B Core Enforcement
C Real SHA Pin
D Approval Gate
E NO_CHANGE Reverification
F Strict/Fail-closed
G Evidence Reader
H Production Entry Boundary
I Attack Regressions
J Existing 112 Regression
K New Regression Total
L Actual Production Run
M Known Limitation Isolation
N Preservation/Architecture Delta
O Files Changed
P Git Status
Q Fix Candidate
R Done/Now/Next
S User Approval Required

## Completion Gate
PASS candidate:
- direct bypass blocked
- evil executor0
- independent approved SHA pins enforced
- modified executor/validator blocked
- arbitrary approval blocked
- production approval NOT ISSUED
- NO_CHANGE full-chain revalidation
- BLOCK/tamper/FAIL never NO_CHANGE
- genuine PASS still NO_CHANGE
- strict contract/reserved request/OSError fail-closed
- existing112 PASS + new attacks PASS
- actual Production Run0 / Evidence0
- Architecture Delta NONE
- MVP FROZEN
- Phase2 NOT STARTED
- Git0
- scope violation0

Codex 단독 production-ready 확정 금지.

완료 후:
Codex Result → ChatGPT review → Claude READ-ONLY Delta Recheck → PASS 시 Closure/State Sync → First Runtime User Gate → 정확한 production approval_ref 고정 → 승인 후 actual Beta-Index READ_ONLY_INTEGRITY Run.

## End State
- Runtime Boundary Fix = PASS candidate
- Production approval = NOT ISSUED
- Actual Runtime = NOT RUN
- MVP = FROZEN
- Architecture Delta = NONE
- Phase2 = NOT STARTED
- Git push = NO
- Next = Independent Delta Recheck

=== ORDER END ===
