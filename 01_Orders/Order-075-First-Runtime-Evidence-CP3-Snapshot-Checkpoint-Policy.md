# Order-075 — First Runtime Evidence CP3 Snapshot + Checkpoint Policy Candidate

## Metadata
- Order ID: Order-075
- Project: Beta
- Status: USER APPROVED
- Type: STATE SYNC + VERIFIED CHECKPOINT + GIT SNAPSHOT + POLICY CANDIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: SNAPSHOT_EVIDENCE_AND_PREPARE_REVIEW
- Trigger: Order-074 First Production Runtime PASS candidate + User Checkpoint Policy Approval
- Runtime Boundary: CLOSED / VERIFIED
- First Production Runtime: PASS candidate / Run1
- KL-4: OPEN / ACCEPTED FOR MVP
- Phase2: NOT STARTED
- Metrics: REQUIRED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: SNAPSHOT_EVIDENCE_AND_PREPARE_REVIEW
order: Order-075
project: Beta
mismatch -> HOLD / no snapshot / no runtime / no git write
```

## User Decision
사용자는 다음 운영 방식을 승인했다.

> 검증된 상태만 Commit/Push하여 Checkpoint로 승격하고, 장애 시 가장 가까운 Verified Checkpoint를 복구 기준점으로 사용한다. 실패 Evidence와 실제 Side Effect가 있는 상태는 자동 Rollback하지 않는다.

Checkpoint 유형:
- CP1 Baseline
- CP2 Verified Implementation
- CP3 Evidence Snapshot
- CP4 Closure

NO_CHANGE:
CP2/CP3/CP4가 실질적으로 같은 상태라면 중복 Commit/Push를 만들지 않는다.

이번 Order는 첫 실제 적용:
`CP3 — First Production Runtime Evidence Snapshot`

## Important Status Boundary
Order-074 결과:
- First Production Runtime = PASS candidate
- Run = 1
- Independent Validator = PASS
- Gate = PROCEED
- Target Side Effect = 0
- Production Evidence = CREATED
- Independent Evidence Review = NOT YET

따라서 이번 Git Snapshot은:
`PENDING INDEPENDENT REVIEW`
상태를 고정하는 Checkpoint다.

Git Commit/Push 자체가 Evidence를 VERIFIED/CLOSED로 승격하지 않는다.

## Purpose
1. Order-074 실제 Runtime 결과를 State/History에 정확히 반영
2. 생성된 Production Evidence 원본을 변경 없이 검산
3. CP3 Checkpoint record 생성
4. Checkpoint Policy를 Candidate Rule로 기록
5. 승인 범위만 Git Commit/Push
6. Claude Independent Evidence Review가 사용할 immutable Git SHA 제공
7. 두 번째 Runtime은 실행하지 않음

## Step 1 — Preflight
확인:
- Order-074 PASS candidate
- Request ID `BETA-FIRST-RUNTIME-001`
- Run ID `RUN-e367a795-4922-4b50-8fff-0630502cf387`
- Evidence ID `EVD-a400e86b-b082-4f4c-8a6b-47a8f25cb619`
- Evidence SHA `9DAC2856BCA0C0B2B40178FD2F6AE88D06F2DF127C18BBD54B44329CC8CA561A`
- Target before/after SHA same
- side effect0
- retry0 / blind retry0
- current Production Runtime count remains 1
- no second Run
- current git status / HEAD / origin

Mismatch → HOLD.
Runtime 재실행 금지.

## Step 2 — Evidence Integrity Before Snapshot
기존 Evidence를 READ-ONLY로 독립 재계산 가능한 범위에서 확인:
- approval packet SHA
- Evidence body SHA
- Events SHA
- Task Plan SHA
- snapshot SHA
- target before/after observations
- Run/Validation/Gate IDs
- Evidence linkage

기존 Evidence 내용 수정 금지.
불일치 → HOLD하고 원본 보존.

## Step 3 — State Sync
기존 State/Index/History 형식 재사용.

정확한 상태:
- First Production Runtime = PASS CANDIDATE
- Actual Run Count = 1
- Production Evidence = CREATED / PENDING INDEPENDENT REVIEW
- Target Side Effect = 0
- Independent Runtime Evidence Review = NOT RUN
- Runtime Closure = NOT CLOSED
- Phase2 = NOT STARTED
- Next = Claude READ-ONLY Independent Evidence Review

PASS CANDIDATE를 VERIFIED/CLOSED로 자동 승격 금지.

## Step 4 — CP3 Checkpoint Record
기존 Evidence/State 구조를 재사용하여 최소 Checkpoint record를 만든다.

논리 필드:
```text
checkpoint_id
checkpoint_type = CP3_EVIDENCE_SNAPSHOT
order_id = Order-075
source_order = Order-074
git_commit = populated after commit
validation_status
evidence_ref
runtime_request_id
run_id
architecture_version/hash reference
rollback_eligible
production_run_count = 1
review_status = PENDING_INDEPENDENT_REVIEW
created_at
```

`rollback_eligible` 의미:
이 Checkpoint는 원본 Evidence/상태 복구 기준점이다.
이미 발생한 실제 Run 사실을 지우는 rollback 용도가 아니다.

새 DB 금지.

## Step 5 — Checkpoint Policy Candidate
기존 Rule/Decision/State 구조에서 적절한 위치를 찾아 **Candidate**로만 기록한다.

### Candidate Policy
#### CP1 — Baseline
큰 변경 시작 전 마지막 Verified remote-aligned 상태.

#### CP2 — Verified Implementation
구현 + 필수 Validation PASS 후.
구현 실패 시 복구 기준.

#### CP3 — Evidence Snapshot
실제 Runtime/중요 Side Effect 직후 원본 Evidence 보존.
Independent Review 전 상태를 그대로 고정.

#### CP4 — Closure
Independent Review + State Sync PASS 후 최종 안정 상태.

### Automatic Checkpoint Eligibility
모두 만족해야 자동 Commit/Push 후보:
1. approved Order scope
2. required Validators PASS
3. FAIL/ERROR overwrite 없음
4. unexpected side effect 없음
5. Architecture change 없음 또는 별도 승인 완료
6. unrelated files 없음
7. `git diff --check` PASS
8. remote divergence 없음
9. Evidence에 checkpoint/commit 연결 가능
10. fast-forward push only

하나라도 실패 → HOLD.

### Rollback Policy
자동 rollback 금지:
- 실제 Runtime Evidence 생성 후
- 외부 Side Effect 발생
- delete/move/publish
- User approval state 변경
- SSOT conflict/meaning ambiguity

이 경우:
HOLD → facts/evidence preserve → Root Cause → Recovery Plan.

자동 Recovery 후보:
원인과 성공한 복구법이 이미 검증된 임시 artifact/cache 등으로 제한.

### NO_CHANGE
동일 content/state/evidence가 이미 동일 Checkpoint 의미로 remote에 있으면 중복 Commit/Push 금지.

이번 Order에서 Policy는 Candidate이며 Active Rule로 승격하지 않는다.
실제 CP3/CP4 Evidence를 확보한 뒤 별도 Review/Promotion.

## Step 6 — Git Commit Scope
허용:
- Order-074 문서
- Order-075 문서
- First Runtime approval packet
- `BETA-FIRST-RUNTIME-001` Production Evidence
- 필요한 State/Index/History 변경
- CP3 Checkpoint record
- Checkpoint Policy Candidate record

금지:
- Runtime Core 코드 변경
- Test 변경
- Architecture/Terminology 변경
- unrelated files

Commit 전 exact file list 보고/검증.

권장 message:
`beta: snapshot first production runtime evidence`

## Step 7 — Git Push
Validation PASS 후:
- origin/main
- fast-forward only
- no force/rebase/history rewrite
- remote divergence → HOLD

Push 후:
- local HEAD == origin/main == remote main
- worktree expected clean
- commit contains only approved scope

## Step 8 — Independent Review Handoff
Claude에게 다음 CP3 Git SHA를 기준점으로 제공할 준비:
- commit SHA
- Request ID
- Run ID
- Evidence ID/SHA
- target SHA
- approval packet SHA
- Events SHA
- Task Plan SHA
- Runtime Code Baseline Hash
- Approved Runtime Git baseline
- side effect0
- Production Run count1

Claude Review에서는 Beta 원본 READ-ONLY.
새 Runtime 실행 금지.

## Step 9 — Metrics
Timing:
preflight → evidence verification → state sync → checkpoint record/policy candidate → git commit → push/postflight → report.

Token/Cost:
근거 없으면 NOT_AVAILABLE.

Size:
- Evidence files/bytes
- Checkpoint files/bytes
- State/Document delta
- Git commit files/lines/bytes
- Code/Test delta expected0

Efficiency:
retry_count
blind_retry_count
blocker/important/minor
unexpected_exception_count
review_side_effect_count
recovery_action_count
user_gate_count
checkpoint_count
production_run_count

이번 Order에서는:
- production_run_count는 기존 사실 1
- 새 Runtime count = 0
- checkpoint_count 성공 시 1
- user_gate_count = 0 (이번 Order 자체 새 Gate 없음)

## Prohibited
- second Runtime
- Runtime retry
- Evidence 원본 수정
- Production Evidence VERIFIED/CLOSED 승격
- Checkpoint Policy Active 승격
- automatic rollback
- Runtime Core/Test/Architecture 변경
- Phase2
- force/rebase/history rewrite
- unrelated commit

## Required Result
A Routing/Preflight
B Evidence Integrity
C State Sync
D CP3 Record
E Policy Candidate
F Checkpoint Eligibility
G Git Scope
H Commit
I Push
J Postflight
K Independent Review Handoff
L Runtime/Phase2 Preservation
M Files Changed
N Metrics Summary
O Stage Metrics
P Token/Cost
Q Size
R Efficiency
S Final Status
T Done/Now/Next
U User Approval Required

## Completion Gate
PASS / CP3 CREATED:
- Order-074 evidence identity verified
- original evidence unchanged
- Run count remains1
- state = PENDING INDEPENDENT REVIEW
- CP3 record created
- Policy remains Candidate
- Runtime Core/Test/Architecture delta0
- commit scope exact
- fast-forward push success
- local/remote SHA equal
- second Runtime0
- Phase2 NOT STARTED

## End State
성공 시:
- First Runtime = PASS CANDIDATE
- Production Evidence = CREATED / PENDING INDEPENDENT REVIEW
- CP3 Evidence Snapshot = CREATED / PUSHED
- Checkpoint Policy = CANDIDATE
- Production Run Count = 1
- New Runtime in Order-075 = 0
- Next = Claude Independent Runtime Evidence Review
- PASS review 후 CP4 Runtime Closure 후보

=== ORDER END ===
