# Order-065 — Runtime Trust Anchor Independent Delta Recheck

## Metadata
- Order ID: Order-065
- Project: Beta
- Status: APPROVED
- Type: READ-ONLY INDEPENDENT DELTA RECHECK
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer: Codex
- Reviewer / To: Claude Code
- Action: REVIEW_ONLY
- Trigger: Order-064 Trust Anchor Fix PASS candidate
- Previous Review: Order-063 REVISION REQUIRED
- MVP: PASS / FROZEN
- Architecture: v1.0 FROZEN
- Phase2: NOT STARTED
- Production Approval: NOT ISSUED
- Actual Runtime / Beta Git Write: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Claude Code
action: REVIEW_ONLY
order: Order-065
project: Beta
mismatch -> HOLD / no Beta write / no runtime / no git write
```

## Purpose
Order-063의 Trust Anchor BLOCKER와 NO_CHANGE/Regression IMPORTANT가 Order-064에서 실제 해결됐는지 독립 검증한다.

최우선 질문:
> 공격자가 Runtime 코드, Policy, Approval Packet, Git Commit을 함께 조작해도 User Gate 승인 없이 Production eligibility를 만들 수 있는가?

Mutation/Regression은 Beta 밖 격리 복사본/격리 Git repo에서만 수행한다.

## D1 — Approval Packet Trust Boundary
Packet 존재 자체가 승인인지 공격한다.

U1: 공격자가 `04_Evidence/runtime/approvals/<ref>.json` 형식 packet 직접 생성.
U2: 정상 packet 복사/수정하여 target/commit/SHA 변경.

Expected: 실제 User Gate 승인 사실이 없으므로 HOLD.

확인:
- Runtime이 packet 자기 생성 불가
- packet path arbitrary input 여부
- approval_ref만으로 packet 생성 시 통과 여부
- packet identity/integrity가 User Gate 사실과 어떻게 연결되는가

Packet 존재 자체가 approval이면 BLOCKER.

## D2 — Approved Git Commit Trust Boundary
G1: 악성 executor/validator/policy를 새 commit하고 forged packet이 그 commit/SHA를 정확히 가리킴.
G2: 정상 packet의 commit/SHA를 악성 commit 기준으로 일관 변경.
G3: 새 branch/tag/commit + forged packet.

Expected: User Gate가 그 commit을 승인한 독립 근거가 없으므로 HOLD.

원칙:
> Commit 존재와 User 승인 Commit은 다르다.

## D3 — Combined Full Forgery
동시에:
- executor 변경
- validator 변경
- runtime_policy 변경
- malicious Git commit 생성
- approval packet 생성/변경
- packet commit/path/SHA를 악성 baseline과 일치
- approval_ref도 일관 구성

Expected: User Gate anchor 부재 → HOLD / Run0 / marker0.

PASS/PROCEED면 BLOCKER.

## D4 — User Gate Anchor Representation
현재 Production approval은 NOT_ISSUED.

Production eligibility의:
- User Gate 승인 사실
- approval_ref
- approved_git_commit
연결이 Runtime 코드/호출자가 임의 생성할 수 없는지 확인.

검토:
- Order/Closure 등 외부 승인 사실에 고정되는가
- trusted immutable input인가
- Runtime caller argument로 주입 가능한가
- approval packet 내부 값만으로 승인 사실을 구성하는가

정상 Beta에서는 현재 어떤 Production request도 실행되면 안 된다.

## D5 — Git Baseline Verification
확인:
- repo root exact
- full 40-char commit
- commit 존재
- `git show <commit>:<path>` blob
- blob/current/packet SHA
- runtime working-tree 변경
- policy/executor/validator 동시 변경
- nonexistent/mismatched commit
- policy path injection
- Git command failure fail-closed

## D6 — Runtime Policy
- approval_status/ref 자체 발급 없음
- policy edit alone approval 불가
- loader/path 고정
- arbitrary POLICY_PATH override 차단
- strict schema
- policy + executable 동시 변경은 User Gate anchor 때문에 차단

## D7 — NO_CHANGE Stored Artifacts
실제 공격:
- executor_result.json 변조/rehash
- runs 삭제
- checkpoint state_sha mismatch
- validator stdout/record 변조
- Boundary/Gate/Validation 변조
- approval packet 변경
- approved commit mismatch

Expected: NO_CHANGE 금지 / HOLD-BLOCK / new Run0.

Genuine PASS만 NO_CHANGE / Run0 / duplicate Evidence0.

## D8 — Consistent Multi-artifact Tamper
executor_result, checkpoint SHA, validator output, Evidence body/index, events 관련 필드를 서로 일관되게 다시 쓰고 hash도 재계산.

Expected: User Gate/Git baseline/current target과 독립 대조 가능한 범위는 차단.

Order-064가 명시적으로 제외한 events 전체 완전 일관 재작성 + hash-chain 없음은 기존 MINOR로 유지하며 새 BLOCKER로 확대하지 않는다.

## D9 — Actual-file Regression Quality
신규14가 실제 file modification, simultaneous policy modification, approval edit, policy replacement/deletion, Git commit mismatch, executor_result tamper, runs deletion을 수행하는지 확인. 핵심 공격을 hash mock으로 대체하면 IMPORTANT.

## D10 — Regression
격리:
- 기존127 + 신규14 = 141
- PASS141 / FAIL0 / ERROR0
가능하면 stability check 2회.

## D11 — READ-ONLY Preservation
target write API 없음, pre/executor/post/validator observation, mutation detection, network=false, publish=false, exact target/path 유지.

## D12 — Known Limitations
KL-1~KL-3 OPEN / ACCEPTED 유지. events full rewrite/symlink 실증 제한은 기존 hardening candidate.

## D13 — Frozen / Git / Runtime
Beta 원본:
- MVP PASS/FROZEN / 7/7
- Architecture/Terminology 불변
- Architecture Delta NONE
- Phase2 NOT STARTED
- Production approval0 / Run0 / Evidence0
- Beta commit/push/tag0
- local implementation changes only

## Trust Rule
> Approval Packet은 승인 내용을 담을 수 있지만 그 파일 자체가 “사용자가 승인했다”는 유일한 증거가 될 수 없다.

> Git Commit은 코드 기준선이 될 수 있지만 임의 Commit이 존재한다는 사실만으로 승인된 Commit이 되지 않는다.

따라서 User Gate 사실 → approval_ref + approved commit 연결의 독립성이 핵심이다.

## Severity
BLOCKER:
- forged packet만으로 Production eligibility
- malicious commit + forged packet PASS
- combined full forgery PASS
- policy/program/packet/commit을 같은 Writer가 바꿔 자기 승인
- actual Production Runtime
- Frozen baseline 위반

IMPORTANT:
- User Gate anchor가 Runtime caller에 의해 주입 가능
- NO_CHANGE artifact 검증 누락
- 실제 공격 Regression 불충분
- Git baseline fail-open

MINOR:
- events full consistent rewrite without hash-chain
- symlink environment limitation
- 현재 Scope 밖 hardening

## Final Decision
PASS:
- D1~D13 PASS
- U1/U2, G1~G3, Combined Forgery PASS
- Regression 141/141
- BLOCKER0 / IMPORTANT0
- Beta original changed by review0

PASS 의미:
- Order-064 Independent Review PASS
- Implementation Closure candidate
- actual Runtime은 여전히 NOT AUTHORIZED
- 다음 = Closure/State Sync → First Runtime User Gate

REVISION REQUIRED:
BLOCKER/IMPORTANT 존재. Closure/approval/runtime 금지 + 최소 Fix Scope 보고.

HOLD:
핵심 코드/Git/Evidence 검증 불가.

## Required Output
1 Final Verdict
2 Beta Files Changed
3 D1~D13
4 Approval Packet Trust Boundary
5 Approved Git Commit Trust Boundary
6 U1/U2 + G1~G3
7 Combined Full Forgery
8 User Gate Anchor Representation
9 Git Baseline Verification
10 Runtime Policy
11 NO_CHANGE Reverification
12 Multi-artifact Tamper
13 Regression Quality
14 Regression
15 READ-ONLY Preservation
16 Known Limitations
17 Frozen/Git/Runtime
18 BLOCKER/IMPORTANT/MINOR
19 Done/Now/Next
20 User Approval Required

## End State
- READ-ONLY review
- MVP FROZEN
- Production approval NOT ISSUED
- actual Runtime NOT RUN
- Production Evidence0
- Phase2 NOT STARTED
- Beta Git write NO
- PASS → closure candidate only
- first Runtime requires separate User Gate

=== ORDER END ===
