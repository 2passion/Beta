# Order-067 — Runtime Final User-Gate Independent Delta Recheck

## Metadata
- Order ID: Order-067
- Project: Beta
- Status: APPROVED
- Type: READ-ONLY INDEPENDENT DELTA RECHECK
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer: Codex
- Reviewer / To: Claude Code
- Action: REVIEW_ONLY
- Trigger: Order-066 PASS candidate
- Previous Review: Order-065 REVISION REQUIRED
- MVP: PASS / FROZEN
- Architecture: v1.0 FROZEN
- Phase2: NOT STARTED
- Production Authorization: NOT ISSUED
- Actual Runtime / Beta Git Write: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Claude Code
action: REVIEW_ONLY
order: Order-067
project: Beta
mismatch -> HOLD / no Beta write / no runtime / no git write
```

## Purpose
Order-065 최종 Trust Anchor BLOCKER가 Order-066의 execution-time exact-hash one-shot User Gate로 실제 해결됐는지 독립 검증한다.

집중:
1. capability 위조
2. fixture issuer Production 우회
3. TOCTOU
4. one-shot 동시 소비/race
5. forged packet + malicious commit + forged capability
6. 기존154 Regression 보존

Mutation/Regression은 Beta 밖 격리 복사본/격리 Git repo에서만 수행.

## D1 Capability Construction
실제 공격:
- constructor 직접 호출
- object.__new__
- private field/setattr/reflection
- subclass
- copy/deepcopy
- pickle/serialization
- fake object/dict
- monkeypatch/type confusion
- 다른 process에서 모방 객체

Expected: 외부 User Gate issuer 외에는 유효 capability 생성 불가. fake → APPROVAL_REQUIRED/HOLD / Run0.

Runtime/Writer가 임의 생성 가능하면 BLOCKER.

## D2 Fixture Issuer Production Escape
공격:
- Production context에서 fixture issuer import/call
- test flag/env/path 조작
- test scope 밖에서 fixture issuer
- project root/context 위조
- fixture marker/token을 Production request에 주입
- fixture capability를 Production context로 이동

Expected: Production Run0. “test-only”가 문서가 아니라 코드로 강제되어야 함.

## D3 Request Hash Recalculation
Core가 실행 직전 canonical payload/hash를 재계산하는지 확인.

변조:
target/root/operation, executor/validator/policy SHA, approved commit, network/publish/parallel/dependency, caller hash.

Expected: current hash != authorized hash → HOLD/Run0.

## D4 TOCTOU
authorization 생성 후 실제 사용 직전:
- executor 변경
- validator 변경
- policy 변경
- target 변경
- packet 변경
- runtime working-tree 변경

가능하면 authorization 검증 직후~subprocess 시작 직전 mutation hook으로 재현.

Expected: Core final revalidation → HOLD/BLOCK, malicious execution0, marker0.

## D5 Atomic One-shot
동일 capability로 동시에 2 실행 요청.
threads/processes 가능한 범위 + barrier로 consume 경쟁.

Expected:
- 정확히 1개만 consume/execute
- 나머지 Run0
- 2 Runs이면 BLOCKER

순차 replay test만으로 충분하지 않음.

## D6 Combined Forgery + Capability
동시에 malicious executor, always-pass validator, policy, malicious commit, forged packet, fake/fixture capability, 일관 path/SHA/hash.

Expected: 실제 execution-time User Gate authorization이 아니므로 Run0/marker0.

## D7 Authorization Semantics
정상 격리 fixture:
- exact canonical request hash
- exact project/scope
- one-shot
일 때 최초 1회만 허용.

bool/string/token과 구별되는 capability semantics 확인.

## D8 Packet/Git Role
packet alone, commit alone, packet+commit, dangling/side/tag+packet 모두 User Gate authorization 없이는 Run0.

## D9 Evidence Contract
격리 성공 Run Evidence에:
runtime_request_hash, approval_ref, User Gate decision reference, approved_git_commit, policy/executor/validator SHA, run_id, Validation/Gate 연결 확인.

Production Evidence는 만들지 않음.

## D10 NO_CHANGE
기존 full-chain verifier 보존.
NO_CHANGE가 authorization replay를 유발하지 않아야 함.

## D11 Path Normalization
slash/backslash 정상화 확인 + UNC/device/ADS/reserved/root escape HOLD 유지.

## D12 Regression Quality
신규13이 실제 forged packet/malicious commit/combined forgery/wrong hash/payload mutation/replay를 재현하는지 확인.

Capability forgery, fixture issuer escape, TOCTOU, concurrent consume가 Regression에 없으면 독립 공격하고 PASS 전 Regression 후보로 평가.

## D13 Regression
격리:
- 154 total
- PASS154 / FAIL0 / ERROR0
가능하면 stability check 2회.

## D14 Frozen/Runtime/Git
- MVP PASS/FROZEN / 7/7
- Architecture/Terminology unchanged
- Delta NONE
- Phase2 NOT STARTED
- Production authorization0 / Run0 / Evidence0
- Beta git write0

## Severity
BLOCKER:
- capability forged by Runtime/Writer
- fixture issuer usable in Production
- TOCTOU changed executable/target executes
- one authorization → 2 Runs
- combined forgery + fake capability executes
- actual Production Runtime

IMPORTANT:
- capability boundary only convention
- hash not revalidated immediately before execution
- concurrency/replay not actually tested
- Evidence approval/hash/commit linkage missing
- Regression omits discovered exploit

MINOR:
- fail-closed reporting/naming
- existing events hash-chain limitation
- symlink environment limitation

## Final Decision
PASS:
- D1~D14 PASS
- capability forgery blocked
- fixture issuer escape blocked
- TOCTOU blocked
- concurrent one-shot exactly one execution
- combined forgery blocked
- Regression154/154
- BLOCKER0 / IMPORTANT0
- Beta original changed0

PASS → Order-066 Independent Review PASS → Implementation Closure candidate only. Actual Runtime still requires separate User Gate.

REVISION REQUIRED → Closure/Runtime 금지 + 최소 Fix Scope.
HOLD → 핵심 검증 불가.

## Required Output
1 Final Verdict
2 Beta Files Changed
3 D1~D14
4 Capability Construction
5 Fixture Issuer Escape
6 Hash Recalculation
7 TOCTOU
8 Atomic One-shot Race
9 Combined Forgery
10 Authorization Semantics
11 Packet/Git Role
12 Evidence Contract
13 NO_CHANGE
14 Path Normalization
15 Regression Quality
16 Regression
17 Frozen/Runtime/Git
18 BLOCKER/IMPORTANT/MINOR
19 Done/Now/Next
20 User Approval Required

## End State
- READ-ONLY review
- MVP FROZEN
- Production authorization NOT ISSUED
- actual Runtime NOT RUN
- Production Evidence0
- Phase2 NOT STARTED
- Beta Git write NO
- PASS → Closure candidate only
- first Runtime requires separate User Gate

=== ORDER END ===
