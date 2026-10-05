# Order-051 — MVP Test 3 Safe Parallel Final Enforcement Fix

## Metadata
- Order ID: Order-051
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: WRITE
- Trigger: Order-050 REVISION REQUIRED
- Target: MVP Test 3 Safe Parallel Plan 1.2 candidate
- Architecture / Terminology: FROZEN
- GitHub Beta: OUT OF SCOPE

## Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: WRITE
order: Order-051
project: Beta
mismatch_policy:
- recipient mismatch -> HOLD
- no execution / no Beta writes
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## Intent
Order-050에서 남은 B1/B3/I1/I2만 최소 수정한다.

이미 해결된 항목은 재설계하지 않는다:
- UNKNOWN 기본 유효성 검사
- Per-task Evidence linkage
- Scenario Manifest
- Failure Isolation 독립 도출
- dependency/cycle 기본 검출
- shared mutable resource
- deterministic sequential fallback
- Plan 1.1 기존 Regression

수정 대상:
1. B1 — Runtime/Observation 동일 trust boundary 문제
2. B3 — HOLD 조건보다 WRITE_PATH_UNKNOWN이 먼저 반환되는 판정 순서
3. I1 — wildcard / Windows reserved device / ambiguous Unicode path
4. I2 — Test 2 OWNER_PATTERN 실제 적용

새 Scheduler/Agent/DB/lock service/Plugin/Adapter 금지.

## Fix B1 — Filesystem-backed Independent Concurrency Evidence
새 프로세스/서비스를 먼저 만들지 않는다.

Order-050에서 이미 관측된 filesystem metadata를 제3 관측 근거로 사용한다.

정상 병렬에서는 worker A/B의 실제 산출물/validation/evidence/observation 파일 생성·수정 순서가 교차하고,
가짜 순차 실행에서는 한 worker의 파일군이 끝난 뒤 다른 worker 파일군이 생성됐다.

Validator는 최소 세 계층을 대조한다:

```text
Runtime summary
       ↕
Worker Observation JSONL
       ↕
Filesystem metadata / actual file ordering
```

가능하면 기존 파일의 stat metadata를 사용:
- mtime_ns
- 필요 시 ctime_ns 또는 플랫폼에서 신뢰 가능한 동등 metadata
- actual output/validation/evidence/observation file existence
- per-worker file ownership

Validator가 검증할 최소 invariant:
- A/B worker identity 분리
- runtime/observation 일치
- filesystem 상에서도 두 worker의 실제 작업 파일 생성/수정 순서가 병렬 실행과 모순되지 않음
- 실제 순차 실행인데 runtime+observation만 병렬로 위조하면 filesystem ordering과 불일치
- 각 Task output/validation/evidence는 실제 파일 SHA와 연결

filesystem timestamp resolution/semantics가 검증에 충분하지 않으면 PASS로 추정하지 말고 ERROR/HOLD 또는 다른 기존 독립 관측을 사용한다.

### M14 — Full Fake Parallel
실제 실행은 순차.
Runtime과 Observation JSONL 모두 일관되게:
- 서로 다른 fake worker/thread
- 동일 barrier
- 겹치는 fake timestamps
로 위조.

Filesystem의 실제 file ordering은 순차 사실을 유지.

Expected:
- Validator FAIL
- Gate BLOCK

M14가 PASS하면 B1 미해결.

## Fix B3 — Decision Precedence
판정 우선순위를 명시적으로 강제한다.

### Tier 1 — HOLD
실행 자체를 금지해야 하는 조건을 먼저 전부 평가:
- invalid task identity
- invalid owner / ownership conflict
- permission/scope invalid
- routing mismatch/unknown
- validation_independent invalid/false
- dependency cycle
- unresolved dependency
- 필수 contract field invalid

하나라도 있으면 즉시 최종 Decision = HOLD.
`SEQUENTIAL_REQUIRED`가 이를 가리면 안 된다.

### Tier 2 — SEQUENTIAL_REQUIRED
실행 자체는 가능하지만 병렬만 위험:
- write conflict
- write path identity UNKNOWN
- shared mutable resource conflict
- owner mutable-context conflict
- dependency ordering

### Tier 3 — PARALLEL_ALLOWED
Tier 1 없음 + Tier 2 없음 + 독립성 전체 증명.

Validator recompute도 동일 precedence를 독립 적용한다.

### M15 — HOLD Masking
WRITE_PATH_UNKNOWN과 다음을 각각 결합:
- scope violation
- routing mismatch
- validation_independent=false
- dependency cycle
- invalid owner

Expected:
- HOLD
- execution_count 0
- runtime file 0
- side effect 0

## Fix I1 — Additional Unsafe Windows Path Forms
다음은 identity가 불명확하거나 위험한 path로 취급하여 PARALLEL_ALLOWED 금지:
- wildcard `*`, `?`
- reserved DOS device names: CON, PRN, AUX, NUL, COM1~COM9, LPT1~LPT9 및 extension 변형
- ambiguous/non-ASCII drive or path identity when reliable canonicalization is not available
- 기존 ADS / 8.3 / device / UNC unknown 정책 유지

보수 정책:
- 확실한 conflict → SEQUENTIAL_REQUIRED
- identity UNKNOWN → SEQUENTIAL_REQUIRED 또는 HOLD
- 병렬 허용 금지

형제 prefix처럼 명확히 서로 다른 정상 path는 계속 병렬 가능해야 한다.

### M16 — Unsafe Path Forms
최소:
- wildcard
- NUL / NUL.json
- COM1 / COM1.txt
- ambiguous Unicode/full-width drive/path
- 정상 sibling control

Expected:
- 위험/불명확 path → parallel 0
- 정상 sibling → 기존 병렬 가능 유지

## Fix I2 — Reuse Test 2 OWNER_PATTERN
Test 2/Core의 검증된 owner identifier 계약을 실제 classify와 Validator recompute에 적용한다.

Order-050 확인 기준:
`^[A-Za-z0-9][A-Za-z0-9_-]*$`

단, 실제 Core/Test2 SSOT에서 패턴을 다시 읽고 그것을 기준으로 한다. 위 문자열을 새 독립 규칙으로 복제하지 않는다.

최소:
- owner exactly one identifier
- invalid format → HOLD / OWNERSHIP_CONFLICT 또는 기존 동등 Reason
- classify와 Validator 동일 계약 사용

다음은 허용되면 안 된다:
- `Codex,Claude`
- `Codex Claude`
- `Codex/Claude`
- leading space
- `Co+dex`
- leading hyphen
- 빈 값

### M17 — Invalid Owner Identifier
위 invalid owner들을 실제 contract에 넣는다.

Expected:
- HOLD
- execution 0
- Validator 동일 결과
- PARALLEL_ALLOWED 0

유효 owner control은 기존 동작 유지.

## Preserve Resolved Items
다음은 그대로 유지:
- B2 UNKNOWN 기본 검증
- I2(이전 명칭) Per-task Evidence linkage
- I3 Scenario Manifest 71개
- Failure Isolation 독립 도출
- M1~M13 보호
- actual normal parallel
- dependency/cycle
- shared resource
- scope/routing
- deterministic sequential fallback

## Required Scenarios
A~H 기존 의미 모두 PASS.

특히:
- A 정상 실제 병렬
- H PASS/FAIL isolation
- F/G unsafe 실행 0

## Mutations
기존 M1~M13 보존.
신규:
- M14 Full Fake Parallel
- M15 HOLD Masking
- M16 Unsafe Windows Path Forms
- M17 Invalid Owner Identifier

각 Mutation은 실제 contract/runtime/filesystem 위반을 사용하고 의도한 이유로 FAIL/BLOCK 또는 정상 HOLD되어야 한다.

## Validator Independence
독립 재계산:
- contract field validity
- Test2 owner contract
- HOLD precedence
- dependency/cycle/resolution
- canonical/unknown path
- shared resources
- scope/routing
- runtime concurrency
- worker observation
- filesystem metadata/order
- per-task Run/Output/Validation/Evidence
- failure isolation
- Scenario Manifest

Executor decision/counter를 신뢰하지 않는다.
검사 불능 → ERROR.

## Version / Evidence
Plan1.0/1.1과 기존 Evidence 보존.

새 결과:
- Test ID `MVP-TEST-3`
- Name `Safe Parallel`
- Version `1.2`
- change_reason_ref `Order-051`
- New Run/Event/Validation/Evidence
- Scenario A~H + Manifest

Plan1.0/1.1 REVISION REQUIRED 이력 보존.

## Regression
기존 96개 의미를 모두 보존.
신규 enforcement tests 추가.

기준:
- 기존 96 PASS
- 신규 전부 PASS
- FAIL 0
- ERROR 0

Blind Retry 및 기존 Test 완화 금지.

## Preservation
보존:
- Test1/2/4/5/6/7 OFFICIAL PASS
- Phase1
- Common Harness/Core
- Architecture/Terminology
- Reference
- Test3 Plan1.0/1.1 Evidence
- 기존 Run/Event/Evidence

Architecture Delta = NONE.

## GitHub Boundary
GitHub Beta 범위 밖.
git init/add/commit/push 금지.
coordination/lock/queue/SSOT 사용 금지.

## Prohibited
- Phase2
- Architecture/Terminology 변경
- 대형 Scheduler
- Agent pool
- DB/distributed lock
- Plugin/Adapter
- 기존 Evidence rewrite
- 과거 실패 상태 변경
- MVP 전체 PASS/Freeze 확정

## Result Format
A. B1 Filesystem-backed Concurrency Evidence
B. B3 Decision Precedence
C. I1 Windows Path
D. I2 Test2 OWNER_PATTERN Reuse
E. Existing Resolved Items Preservation
F. Scenario A~H
G. M1~M17
H. Validator Independence
I. Regression
J. Official Candidate — ID/version/reason/Run/Plan SHA/Executor SHA/Validator SHA/Evidence ID/SHA/Execution/Validation/Gate/Scenario/Manifest
K. Preservation
L. GitHub Boundary
M. Files Changed
N. Done / Now / Next

## Completion Gate
Plan1.2 PASS candidate:
- B1 full fake parallel detected
- B3 HOLD precedence enforced
- I1 unsafe/ambiguous path parallel0
- I2 Test2 owner contract actually applied
- Existing resolved items preserved
- A~H PASS
- M1~M17 PASS
- Validator independent
- Regression PASS
- Evidence complete
- Preservation PASS
- Architecture Delta NONE
- GitHub untouched

Codex 단독 OFFICIAL PASS 금지.

완료 후:
Codex Order-051 Result
→ ChatGPT 검토
→ Claude READ-ONLY Plan1.2 Delta Recheck
→ PASS 시 Test3 OFFICIAL PASS candidate
→ Closure Sync
→ MVP 7 Gates Overall Evidence Review
→ MVP PASS / Freeze Gate

## Current State
- Test1 Reuse: OFFICIAL PASS
- Test2 Ownership: OFFICIAL PASS
- Test3 Plan1.0: REVISION REQUIRED
- Test3 Plan1.1: REVISION REQUIRED
- Test3 Plan1.2: NOT RUN
- Test4 Bottleneck: OFFICIAL PASS
- Test5 Prevention: OFFICIAL PASS
- Test6 User Gate: OFFICIAL PASS v1.2
- Test7 Resume: OFFICIAL PASS v1.1
- MVP overall PASS: NOT YET
- MVP Freeze: NOT YET
- User approval: already granted within this fix scope
- Next executor: Codex

=== ORDER END ===
