# Order-064 — Runtime Trust Anchor + Evidence Reverification Fix

## Metadata
- Order ID: Order-064
- Project: Beta
- Status: USER APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: FIX_AND_VALIDATE
- Trigger: Order-063 REVISION REQUIRED + User Trust-Anchor Decision
- MVP: PASS / FROZEN
- Architecture: v1.0 FROZEN
- Phase2: NOT STARTED
- Production Approval: NOT ISSUED
- Actual Runtime: NOT AUTHORIZED
- Trust Anchor: User-approved Git Commit SHA + User Gate record
- Git/GitHub: approval-baseline Evidence + backup/version history, NOT SSOT

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: FIX_AND_VALIDATE
order: Order-064
project: Beta
mismatch -> HOLD / no implementation / no runtime / no unauthorized git push
```

## User Decision
사용자가 승인:
- Git Commit SHA + User Gate 승인 기록을 Production Runtime Trust Anchor로 사용
- `C:\Obsidian\Beta`는 Local SSOT 유지
- Git/GitHub는 승인 Runtime 기준선 Evidence + 백업/이력
- OS ACL, PKI, 별도 서명 서버는 현재 만들지 않음

## Purpose
Order-063 잔여:
1. BLOCKER: policy + program 동시 수정으로 자기 승인
2. IMPORTANT: NO_CHANGE가 executor_result/runs를 검증하지 않음
3. IMPORTANT: 일부 공격 Regression이 mock 중심
만 최소 수정한다.

## Trust Model
```text
User Gate
→ approved_git_commit
→ approved policy/executor/validator identities
→ current Git blobs + current files
→ all match = eligible
→ mismatch = HOLD
```

현재 working-tree SHA를 자동 승인값으로 쓰지 않는다.
`runtime_policy.json`의 approval_status만으로 Production 승인 금지.

## Current Phase
이번 Order에서는:
- Production approval = NOT ISSUED
- actual Runtime = 0
- Production Evidence = 0
- Order-064 변경은 아직 approved baseline이 아님

## Git Trust Anchor
향후 First Runtime User Gate에서 고정:
- approval_ref
- approved_git_commit
- target_path / approved_root / operation
- policy path + SHA
- executor path + SHA
- validator path + SHA
- parallel=false
- dependencies=[]

Production 실행 전:
1. repo root 확인
2. approved commit 존재
3. 승인 runtime file의 commit blob 확인
4. current file = approved commit blob
5. approval packet SHA들과 일치
6. runtime 관련 working-tree 변경 없음
7. approval_ref exact match

불일치 → HOLD / Run0.

전체 repo clean을 강제할 필요는 없지만 승인 Runtime 실행 경로는 approved commit과 같아야 한다.

## User Gate Approval Record
새 DB/Registry 금지.

향후 최소 후보:
`04_Evidence/runtime/approvals/<approval_ref>.json`

필드:
```text
approval_ref
approved_git_commit
target_path
approved_root
operation
policy_path / policy_sha256
executor_path / executor_sha256
validator_path / validator_sha256
parallel_allowed=false
dependencies=[]
approved_at
```

이 record는 User Gate Closure/Order가 생성한다.
Runtime 코드가 자기 발급 금지.
이번 Order에서는 실제 Production approval record 생성 금지.

## Runtime Policy
`runtime_policy.json`은 정책 데이터이지 승인 SSOT가 아니다.

수정:
- policy approval_status만으로 실행 금지
- policy가 User Gate record + approved Git baseline과 일치해야 함
- policy loader/path 고정
- arbitrary POLICY_PATH override Production에서 차단
- strict schema
- policy SHA도 approval record/commit과 비교

## P3/P4/P5
P3:
executor/validator 실제 변경 + policy SHA/approval 실제 변경.
Expected: approval record/Git baseline mismatch → HOLD / Run0 / marker0.

P4:
다른 policy path/loader 주입 → HOLD.

P5:
policy 삭제/손상 → HOLD/ERROR / Run0.

## NO_CHANGE Full Reverification
추가 필수:
- `runs/<run_id>/executor_result.json` 존재
- 실제 executor_result SHA 계산
- CHECKPOINT_RECORDED.state_sha256과 일치
- executor result request/run/target identity 일치
- validator record/output 존재 + identity
- validator observation과 current target size/SHA 일치
- Boundary PROCEED
- Validation PASS
- Gate PROCEED
- Evidence body/index/events linkage
- approved Git baseline + approval packet 유효
- runs missing/tamper → HOLD

Genuine prior PASS만 NO_CHANGE.

## Event Tamper Boundary
events 전체 일관 위조를 막기 위한 새 PKI/hash-chain은 이번 범위 밖.
대신 executor_result/checkpoint + Evidence + Validation/Gate + approval baseline을 교차검증.
기존 events 전체 위조 한계는 hardening candidate로 보존.

## Actual-file Attack Regression
mock 중심을 실제 파일 공격으로 보강:
1. executor 실제 수정 only → HOLD
2. validator 실제 수정 only → HOLD
3. executor 수정 + policy SHA 수정 → HOLD
4. validator 교체 + policy SHA 수정 → HOLD
5. policy approval status/ref 편집 → 승인 불가
6. policy path 실제 대체 → HOLD
7. policy 삭제/깨짐 → HOLD
8. executor_result 실제 변조 + rehash → duplicate HOLD
9. runs 실제 삭제 → duplicate HOLD
10. checkpoint state SHA mismatch → duplicate HOLD
11. validator record/output 변조 → duplicate HOLD
12. genuine PASS → NO_CHANGE
13. approved Git baseline mismatch → HOLD
14. uncommitted runtime file change → HOLD

Beta 원본 파일을 공격하지 않는다. Beta 밖 격리 복사본/fixture에서만 수행.

## Test Approval Simulation
실제 Production approval은 발급하지 않는다.
격리 test repo에서 fixture-only User Gate approval packet + baseline commit으로 검증 가능.
Test approval은 Production에서 무효.

## Regression
기존 127 의미 보존 + 신규/교체 trust-anchor/duplicate tests.
- existing127 PASS
- new all PASS
- FAIL0 / ERROR0
- Test 삭제/완화 없음
가능하면 stability check 2회.

## READ-ONLY Preservation
target mutation detection, executor target-write API 없음, validator current read, exact path, network=false, publish=false 유지.

## Known Limitations
KL-1~KL-3 OPEN / ACCEPTED 유지.
Order-063 MINOR(events full rewrite, symlink 실증 제한 등)는 hardening candidate로 보존.

## Architecture Compatibility
기존 Runtime/User Gate/Evidence/Git backup 구조의 enforcement로 유지.
Git이 SSOT가 되어야 하거나 새 승인 데이터 모델/서명 서비스가 필요하면 HOLD → Architecture Change Proposal.

## Git Policy
Local Beta:
- commit/push/tag 금지
- branch rewrite 금지

허용:
- read-only Git 명령
- Beta 밖 격리 test repo의 test-only commit

Order-064 변경은 아직 approved runtime baseline이 아니다.

## Production Runtime Prohibition
- actual Beta-Index Runtime Run0
- Production approval record0
- Production Runtime Evidence0
- actual approval_ref NOT ISSUED

## Preservation
MVP PASS/FROZEN, 7/7, Architecture/Terminology FROZEN, Phase1 Evidence, Order-057 Freeze baseline/GitHub Snapshot, Phase2 NOT STARTED, Architecture Delta NONE 유지.

## Prohibited
actual Runtime/approval, Beta Git commit/push/tag, GitHub SSOT 승격, Phase2, Architecture 변경, PKI/signing/ACL 시스템, general Generator/Classifier/Scheduler, Safe Parallel/Resume/Prevention productionization, Plugin/Adapter/Remote, EXE/PWA, Known Limitation 종료.

## Required Result
A Routing/Preflight
B Trust Anchor Implementation
C User Gate Approval Record Boundary
D Runtime Policy Role
E P3/P4/P5
F NO_CHANGE Full Reverification
G Actual-file Attack Tests
H Git Baseline Verification
I Existing127 Regression
J New Regression Total
K READ-ONLY Preservation
L Known Limitations
M Architecture Compatibility
N Actual Production Run/Approval
O Files Changed
P Git Status
Q Fix Candidate
R Done/Now/Next
S User Approval Required

## Completion Gate
PASS candidate:
- simultaneous policy+program modification blocked
- policy edit cannot issue approval
- policy path injection blocked
- Git baseline mismatch blocked
- approval packet required and cannot self-issue
- executor_result/runs/checkpoint/validator tamper blocks NO_CHANGE
- genuine PASS NO_CHANGE
- actual-file attacks PASS
- existing127 preserved + new tests PASS
- Production Run0 / approval0
- Beta Git commit/push/tag0
- Architecture Delta NONE
- MVP FROZEN / Phase2 NOT STARTED

Codex 단독 production-ready 확정 금지.

완료 후:
Codex Result → ChatGPT review → Claude READ-ONLY Trust Anchor Delta Recheck → PASS 시 Closure/State Sync → First Runtime User Gate → User Gate가 approval record + approved Git baseline 고정 → 별도 actual Runtime Order → 그때만 Beta-Index READ_ONLY_INTEGRITY 실행.

## End State
- Trust Anchor Fix = PASS candidate
- Production approval NOT ISSUED
- Actual Runtime NOT RUN
- Local SSOT = `C:\Obsidian\Beta`
- Git = approval-baseline Evidence + backup/version history, NOT SSOT
- MVP FROZEN
- Architecture Delta NONE
- Phase2 NOT STARTED
- Next = Independent Trust Anchor Delta Recheck

=== ORDER END ===
