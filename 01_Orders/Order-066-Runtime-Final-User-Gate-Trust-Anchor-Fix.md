# Order-066 — Runtime Final User-Gate Trust Anchor Fix

## Metadata
- Order ID: Order-066
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: FIX_AND_VALIDATE
- Trigger: Order-065 REVISION REQUIRED
- Decision: Final Trust Anchor = execution-time User Gate
- MVP: PASS / FROZEN
- Architecture: v1.0 FROZEN
- Phase2: NOT STARTED
- Actual Runtime / Production Approval / Beta Git Write: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: FIX_AND_VALIDATE
order: Order-066
project: Beta
mismatch -> HOLD / no implementation / no runtime / no git write
```

## Decision
Production Runtime 실행 권한의 최종 근거는 **실행 직전 User Gate**다.

Git Commit SHA와 Approval Packet은 승인 내용/사후 추적 Evidence이지, 그것들만으로 실행 권한을 만들 수 없다.

## Purpose
Order-065의 최종 BLOCKER만 최소 수정:
- forged packet authorization
- malicious commit + forged packet
- Combined Full Forgery
- User Gate 사실 독립성
- 승인 근거 Evidence 누락
- forged-packet Regression 누락
- path slash/backslash MINOR

이미 해결된 NO_CHANGE/Core enforcement/READ-ONLY는 보존.

## Runtime Flow
```text
Runtime 준비
→ canonical Request Payload/Hash
→ FINAL USER GATE
→ exact Request Hash 승인
→ 동일 Request에 한해 1회 실행
→ Validation
→ Evidence
```

저장 Packet/Commit만으로 Production 실행 금지.

## Request Hash
canonical payload 최소:
- request_id
- target_path
- approved_root
- operation
- target_side_effect=NONE
- parallel=false
- dependencies=[]
- approved_git_commit
- policy path/SHA
- executor path/SHA
- validator path/SHA
- network=false
- external_publish=false

canonical JSON 규칙 고정 + SHA-256 = `runtime_request_hash`.
Payload 변경 시 기존 승인 무효.

## Final User Gate
실행 직전 표시 가능해야 할 값:
- Target
- Operation
- Approved Root
- Target Write
- Network/External Publish
- Git Baseline
- Executor SHA
- Validator SHA
- Runtime Request Hash

사용자는 exact `runtime_request_hash`를 승인.

승인 전: Run0 / executable0 / Production Evidence Run0.
승인 후: current hash exact match일 때만 1회 실행.

## Ephemeral Authorization
PKI/HMAC/비밀키 시스템은 만들지 않는다.

Local Core는 **외부 User Gate가 실행 시점에 제공하는 ephemeral authorization input**을 요구해야 한다.

필수:
- stored packet 자체에서 authorization 재생성 불가
- Runtime 코드가 authorization 자기 생성 불가
- caller의 `approved=true`/임의 문자열 우회 불가
- exact request hash에 bound
- 다른 hash 재사용 불가
- one-shot consumption 후 재사용 불가
- 장기 실행 권한으로 저장되지 않음

실제 ChatGPT/Codex UI integration은 이번 범위 밖.
Test에서는 fixture-only external user-gate callback/input 사용.

## Approval Packet
Packet은 approval evidence일 뿐 authorization source가 아니다.

향후 기록 후보:
- approval_ref
- runtime_request_hash
- approved_git_commit
- paths/SHAs
- approved_at
- related User Gate decision/order reference

Packet 존재/복사/위조/수정만으로 실행 금지.

## Git Role
Git commit은 baseline Evidence.
임의 commit/branch/tag/dangling commit 존재만으로 승인 금지.
Forged packet + malicious commit도 execution-time User Gate authorization 없으면 Run0.

## Combined Full Forgery
공격자가 Runtime code, policy, malicious commit, forged packet, SHA/ref를 모두 일관 구성해도 User Gate authorization 없으면:
- APPROVAL_REQUIRED/HOLD
- Run0
- marker0

## Replay Protection
- authorization bound to exact request hash
- changed payload/hash → invalid
- consumed one-shot authorization 재사용 금지
- 새 actual Run은 새 execution authorization 필요
- NO_CHANGE는 새 실행이 아니므로 authorization replay 수단이 아님

장기 token DB 금지.

## Evidence Contract
향후 actual Run Evidence에:
- approval_ref
- runtime_request_hash
- approved_git_commit
- User Gate decision reference
- policy/executor/validator SHA
- run_id
- Validation/Gate
를 연결할 준비.

이번 Order Production Evidence0.

## Required Attack Regressions
기존141 의미 보존 + 실제 공격:
1. forged packet only → Run0
2. copied/modified packet → Run0
3. malicious commit + forged packet → Run0
4. packet+commit/SHA 일관 변경 → Run0
5. dangling/side/tag commit + packet → Run0
6. Combined Full Forgery → Run0/marker0
7. arbitrary approved=true/string → Run0
8. fixture User Gate authorization wrong hash → Run0
9. correct fixture User Gate hash → isolated fixture execution allowed
10. 승인 후 payload 변경 → Run0
11. consumed authorization replay → Run0
12. packet 삭제/변조가 authorization source 아님
13. Evidence contract approval hash/commit/reference 확인

핵심 공격은 실제 file/Git/packet mutation. Hash mock으로 대체 금지.

## Path Normalization
`C:/Obsidian/Beta`와 `C:\Obsidian\Beta`를 Windows canonical 비교에서 동일 root로 안전하게 정규화.
UNC/device/ADS/reserved/ambiguous는 계속 HOLD.
기존 exact-target 안전성 약화 금지.

## Preserve NO_CHANGE
Order-064의 executor_result/runs/checkpoint/validator/Boundary/Gate/Validation/Evidence 검증 유지.
NO_CHANGE는 새 실행이 아니므로 side effect0/Run0.

## Regression
- existing141 PASS
- new attacks all PASS
- FAIL0 / ERROR0
- 기존 Test 삭제/완화 금지
- 가능하면 stability check 2회

## Architecture
기존 User Gate 논리 책임을 Production Runtime admission에 강제하는 것.
새 UI/Plugin/Adapter/Remote/PKI/DB 역할 추가 금지.
Architecture 의미 변경 필요 시 HOLD.

## Git
Beta commit/push/tag 금지. read-only Git만.
격리 test repo의 test-only commit 허용.

## Production Prohibition
- actual Beta-Index Runtime Run0
- actual Production approval packet0
- actual execution authorization0
- Production Evidence0

## Preservation
MVP PASS/FROZEN, 7/7, Architecture/Terminology FROZEN, Phase2 NOT STARTED, KL-1~KL-3 OPEN/ACCEPTED, GitHub not SSOT 유지.

## Prohibited
actual Runtime/User authorization, Beta git write, Phase2, Architecture change, PKI/HMAC/secret system, DB/Registry, UI integration, Plugin/Adapter/Remote, EXE/PWA, Known Limitation 종료.

## Required Result
A Routing/Preflight
B Request Hash
C Final User Gate Enforcement
D Ephemeral Authorization
E Packet Role
F Git Role
G Combined Full Forgery
H Replay Protection
I Evidence Contract
J Path Normalization
K Attack Regressions
L Existing141 Regression
M New Regression Total
N NO_CHANGE Preservation
O READ-ONLY Preservation
P Architecture/Known Limitations
Q Actual Runtime/Approval
R Files Changed
S Git Status
T Fix Candidate
U Done/Now/Next
V User Approval Required

## Completion Gate
PASS candidate:
- packet alone never authorizes
- Git commit alone never authorizes
- forged packet + malicious commit never authorizes
- Combined Full Forgery without execution-time User Gate → Run0
- exact request-hash User Gate authorization required
- wrong hash/replay/payload mutation blocked
- correct fixture User Gate authorization works only in isolated test
- approval hash/commit/ref Evidence contract ready
- path normalization fixed safely
- existing141 preserved + new attacks PASS
- Production Run0 / approval0 / Evidence0
- Beta Git write0
- Architecture Delta NONE
- MVP FROZEN / Phase2 NOT STARTED

Codex 단독 production-ready 확정 금지.

완료 후:
Codex Result → ChatGPT review → Claude READ-ONLY Final Trust Anchor Delta Recheck → PASS 시 Closure/State Sync → First Runtime User Gate에서 actual request hash 제시 → 사용자 승인 → approved baseline/approval evidence 고정 → 별도 Runtime Order → actual Beta-Index READ_ONLY_INTEGRITY 실행.

## End State
- Final User-Gate Trust Anchor Fix = PASS candidate
- Production authorization NOT ISSUED
- Actual Runtime NOT RUN
- MVP FROZEN
- Architecture Delta NONE
- Phase2 NOT STARTED
- Git write NO
- Next = Independent Final Trust Anchor Delta Recheck

=== ORDER END ===
