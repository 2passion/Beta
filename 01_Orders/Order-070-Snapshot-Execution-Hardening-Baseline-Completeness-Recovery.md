# Order-070 — Snapshot Execution Hardening + Baseline Completeness + Reviewer Side-Effect Recovery

## Metadata
- Order ID: Order-070
- Project: Beta
- Status: APPROVED
- Type: RECOVERY + WRITE + VALIDATE + METRICS
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: RECOVER_FIX_VALIDATE
- Trigger: Order-069 REVISION REQUIRED
- MVP: PASS / FROZEN
- Phase2: NOT STARTED
- Production Runtime/Authorization: NOT AUTHORIZED
- Beta Git Write: NOT AUTHORIZED
- Metrics: REQUIRED / OBSERVATION ONLY

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: RECOVER_FIX_VALIDATE
order: Order-070
project: Beta
mismatch -> HOLD / no write / no runtime / no git write
```

## Purpose
Order-069 최소 Fix:
1. Reviewer Side Effect 복구
2. Snapshot 자체 변조/module shadowing 차단
3. Runtime Code Baseline 완전성 보강
4. 실제 공격 Regression
5. 비용/시간/코드/문서 Metrics 계속 수집

## Step 0 — Reviewer Side-Effect Recovery
정확한 대상:
`C:\Obsidian\Beta\FILE-INTEGRITY-INDEPENDENT`

Order-069 Evidence: 145B, untracked, Reviewer test artifact, 기존 파일 변경0.

삭제 전 exact path / regular file / size 145B / git untracked 확인.
모두 일치할 때 이 파일 1개만 삭제 허용.
불일치 → HOLD.

삭제 후 artifact 없음, git status 해당 항목 없음, 가능한 동일 방식으로 Order-069 시작 tree hash `cca27a798b2d000f` 복구 확인.
다른 rollback/delete 금지.

## Fix 1 — Snapshot Execution Hardening
Executor/Validator 모두:
- snapshot 생성
- SHA 확인
- **subprocess 직전 snapshot SHA 재확인**
- mismatch → process 생성 전 BLOCK

가능하면 검증 bytes와 실행 bytes 동일성 강화.

### Python Isolated Execution
Python snapshot 실행은 isolated mode `-I`를 검토/적용.
user site/environment path 영향 차단.
snapshot dir `json.py` 등 sibling module shadowing 실제 공격으로 검증.

### Snapshot Directory
- Run 전용
- caller path 금지
- exclusive create
- 예상 파일만 존재
- 실행 직전 unexpected sibling `.py`/shadow candidate → BLOCK
- lifecycle/cleanup 명확화

새 deployment/cache 시스템 금지.

## Fix 2 — Snapshot Evidence / NO_CHANGE
Evidence에 최소 executor snapshot SHA, validator snapshot SHA, 필요한 snapshot identity를 연결.

정책 선택:
- snapshot 보존 시 NO_CHANGE에서 SHA/identity 확인
또는
- snapshot cleanup 시 Evidence에 당시 SHA를 남기고 NO_CHANGE가 파일 존재를 요구하지 않음

둘 중 하나를 명확히 계약하고 Test.

## Fix 3 — Runtime Code Baseline Completeness
반드시 포함:
- model.py
- event_store.py
- __init__.py

더 단순/안전하면 `02_Core/beta_core/*.py` 중 Production Runtime Core 전체를 deterministic manifest 대상으로.
fixture/test, __pycache__ 제외.
runtime_policy.json 기존 검증 유지.
신규 Production Core `.py` 추가 시 baseline hash 변화 여부 검증.

수동 목록 누락이 반복되지 않도록 한다.

## Required Regressions
기존166 의미 보존 + 실제 공격:
1. Executor snapshot post-hash 변조 → marker0
2. Validator snapshot 변조 → marker0
3. Executor snapshot dir json.py shadow → marker0
4. Validator snapshot dir module shadow → marker0
5. model.py 변경 → Run0
6. event_store.py 변경 → Run0
7. __init__.py 변경 → Run0
8. 신규 Production Core .py → baseline hash 변화
9. snapshot Evidence SHA linkage
10. NO_CHANGE snapshot contract
11. snapshot cleanup/lifecycle
12. unexpected snapshot sibling → BLOCK

핵심 공격 mock hash 대체 금지.

## Severity
Snapshot 변조/shadowing은 이번 Fix에서 **BLOCKER-class regression**으로 취급.
이유: 최종 BLOCK이어도 악성 process가 이미 실행되면 안전 실패.

## Preserve
Atomic authorization, copy/pickle protections, original-file TOCTOU, Request/Baseline binding, NO_CHANGE, concurrent request, READ-ONLY, KL-1~KL-3, KL-4 OPEN candidate, FROZEN state 보존.

## Metrics
Order-069 방식 유지.

### Timing
순차 측정:
preflight/recovery → code analysis → implementation → targeted attacks → regression #1 → regression #2 → preservation → report.

**Regression을 공격 작업과 동시에 실행하지 않는다.**

### Token/Cost
MEASURED / ESTIMATED / NOT_AVAILABLE 구분.
실제 usage/가격 근거 없으면 NOT_AVAILABLE.

### Size
code/test/document files, lines, bytes.
Order-070 delta + 가능하면 Order-058~070 cumulative delta.

### Efficiency
retry_count
blind_retry_count
blocker_count
important_count
minor_count
unexpected_exception_count
review_side_effect_count
recovery_action_count
user_gate_count

Order-069 Reviewer artifact:
- historical review_side_effect_count = 1
- 이번 복구 성공 시 recovery_action_count = 1

### Reports
3-Minute Summary + Detailed View + Stage Metrics Table:
`Stage | Time | Tokens | Cost | Code/Doc Delta | Result`

이번 데이터만으로 성능 Rule 자동 생성 금지.

## Validation
- existing166 PASS
- new all PASS
- FAIL0 / ERROR0
- 가능하면 stability ×2
- heavy attack와 Regression 병렬 실행 금지

## Production Prohibition
actual Beta-Index Run0 / Production authorization0 / approval packet0 / Production Evidence0.

## Git
Beta commit/push/tag 금지. read-only Git 허용. 격리 test repo commit 허용.

## Architecture
Architecture Delta NONE. Phase2 NOT STARTED. 새 DB/Agent/Plugin/Adapter/PKI 금지.

## Required Result
A Routing/Preflight
B Reviewer Side-Effect Recovery
C Snapshot Final Revalidation
D Python Isolated Execution
E Snapshot Directory Safety
F Snapshot Evidence/NO_CHANGE
G Baseline Completeness
H Attack Regressions
I Existing166 Regression
J New Regression Total
K Preservation
L Architecture/Known Limitations
M Actual Runtime/Approval
N Files Changed
O Git Status
P Fix Candidate
Q Metrics 3-Minute Summary
R Stage Metrics Table
S Detailed Timing
T Token/Cost
U Code/Document Size
V Validation Metrics
W Efficiency/Recovery Metrics
X Bottleneck Observation
Y Done/Now/Next
Z User Approval Required

## Completion Gate
PASS candidate:
- stray artifact safely removed/recovery verified
- snapshot post-check tamper malicious execution0
- executor/validator shadowing malicious execution0
- baseline complete/deterministic
- snapshot Evidence/NO_CHANGE contract explicit
- existing166 + new tests PASS
- Production Run/auth/Evidence0
- Beta Git write0
- Architecture Delta NONE
- MVP FROZEN / Phase2 NOT STARTED
- Metrics no fabricated token/cost

Codex 단독 production-ready 확정 금지.

완료 후:
Codex Result → ChatGPT review → Claude READ-ONLY Snapshot/Baseline Delta Recheck + Metrics → PASS 시 Closure/State Sync → KL-4 User Acceptance Gate → First Runtime User Gate.

## End State
- Snapshot/Baseline Fix = PASS candidate
- Reviewer side effect recovered
- KL-4 OPEN candidate
- Production Runtime NOT RUN
- MVP FROZEN
- Phase2 NOT STARTED
- Git write NO
- Metrics observation continues

=== ORDER END ===
