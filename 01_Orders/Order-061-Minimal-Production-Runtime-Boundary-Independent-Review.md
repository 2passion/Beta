# Order-061 — Minimal Production Runtime Boundary Independent Review

## Metadata
- Order ID: Order-061
- Project: Beta
- Status: APPROVED
- Type: READ-ONLY INDEPENDENT REVIEW
- Local SSOT Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer: Codex
- Reviewer / To: Claude Code
- Action: REVIEW_ONLY
- Trigger: Order-060 Implementation PASS candidate
- MVP Overall: PASS
- MVP Status: FROZEN
- Architecture: v1.0 FROZEN
- Architecture Delta expected: NONE
- Phase2: NOT STARTED
- Actual Production Runtime: NOT AUTHORIZED
- Git Write/Push: NOT AUTHORIZED

## Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Claude Code
action: REVIEW_ONLY
order: Order-061
project: Beta

mismatch_policy:
- recipient mismatch -> HOLD
- no Beta original write
- no production runtime
- no git write/push
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## Purpose
Order-060에서 구현한 Minimal Production Runtime Boundary가 실제로 승인 범위와 안전 계약을 만족하는지 독립 검증한다.

Codex의 PASS candidate 보고를 신뢰 전제로 삼지 않는다.

이번 Review에서 확인할 핵심:
1. Runtime Boundary 우회 불가
2. Production/Fixture 실행 경계 분리
3. exact executable/validator allowlist + SHA pin
4. READ-ONLY target side effect 0
5. Independent Validator
6. Request→Plan→Run→Validation→Evidence linkage
7. duplicate request idempotency
8. V1~V8 실제 재현
9. 기존 100 Regression 보존 + 신규 12
10. Architecture/Frozen baseline 보존

## Review Boundary
Claude Code는 READ-ONLY Reviewer다.

금지:
- Beta 원본 수정
- production Runtime 실행
- 실제 `Beta-Index.md` Runtime Run
- production Runtime Evidence 생성
- implementation fix
- Architecture/Terminology 변경
- Phase2
- Git commit/push
- Known Limitation 변경

필요한 Mutation/Regression은 Beta 밖 격리 복사본에서만 수행한다.

## Candidate Baseline
Order-060 보고:
- Minimal Production Runtime Boundary = IMPLEMENTED / PASS candidate
- actual Production Runtime = NOT RUN
- existing Regression = 100 PASS
- new Runtime tests = 12 PASS
- total = 112 PASS / 0 FAIL / 0 ERROR
- Architecture Delta = NONE
- Phase2 = NOT STARTED
- Git push = NO

변경 파일:
- `02_Core/beta_core/model.py`
- `02_Core/beta_core/executor.py`
- `02_Core/beta_core/cli.py`
- `02_Core/beta_core/runtime_boundary.py`
- `02_Core/beta_core/file_integrity_executor.py`
- `02_Core/beta_core/file_integrity_validator.py`
- `03_Tests/test_runtime_boundary.py`

모두 검증 대상이다.

## Check 1 — Scope / Reuse
확인:
- 승인된 네 기능만 구현됐는가
- general Generator/Classifier/Scheduler가 추가되지 않았는가
- Safe Parallel/Resume/Prevention productionization이 없는가
- 기존 `validator_runner.py`, `gate.py`, `event_store.py`를 재사용하는가
- 새 DB/Registry/Plugin/Adapter/Remote가 없는가

Scope 확대 발견 시 IMPORTANT/BLOCKER.

## Check 2 — Boundary Cannot Be Bypassed
가장 중요한 공격 검증 중 하나.

실제 call graph를 추적:
```text
runtime request
→ runtime_boundary
→ boundary decision
→ run_task
→ executor
→ validator
→ evidence/gate
```

확인:
- Production mode에서 boundary PASS 없이는 `run_task`가 호출되지 않는가
- CLI 내부 다른 path/flag로 production executor를 직접 호출할 수 없는가
- `run_task()` 직접 호출 시 production executable 정책이 다시 방어하는가
- runtime_request 없이 production executable 실행이 가능한가
- fixture mode를 악용해 production executable을 실행할 수 없는가

### Mutation B1
Boundary를 우회하여 `run_task()` 또는 executor를 직접 호출:
- production executable
- missing/invalid runtime_request
- invalid approval_ref

Expected:
- HOLD/BLOCK
- production Run 0 또는 실행 전 차단
- target side effect 0

Boundary가 CLI에만 있고 Core 호출로 우회 가능하면 BLOCKER.

## Check 3 — Fixture / Production Separation
확인:
- 기존 fixture resolver 의미가 약화되지 않음
- production exact allowlist가 fixture allowlist를 넓히지 않음
- fixture program을 production으로 자동 승격하지 않음
- production program을 fixture 경로로 우회하지 못함
- 기존 Test1~7 fixture semantics 유지

## Check 4 — Executable / Validator Allowlist
독립 확인:
- exact approved path
- SHA-256 pin
- executor와 validator 각각 검증
- 다른 `.py` 차단
- 같은 filename 다른 directory 차단
- approved file 내용을 바꿔 SHA mismatch 발생 시 차단
- path alias/symlink/reparse로 다른 executable을 가리키지 못함

### Mutation A1
Approved executor를 복사한 다른 경로 → BLOCK.

### Mutation A2
Approved path의 executor 내용 변경 → SHA mismatch → BLOCK.

### Mutation A3
Validator를 다른 script/SHA로 교체 → BLOCK.

## Check 5 — Approval / Scope Contract
확인:
- approval_ref missing → APPROVAL_REQUIRED/HOLD / Run0
- target exact pin
- approved_root
- operation exact match
- task count 1
- parallel false
- dependencies empty
- target write false
- network false
- external_publish false

approval_ref 문자열 존재만으로 실제 Production 승인으로 취급되지 않는지 확인한다.
현재 실제 approval registry가 없으므로 **Production Operation은 별도 User Gate 전까지 실행 불가**라는 경계가 코드/운영 계약에서 유지돼야 한다.

## Check 6 — Path Safety
격리 환경에서:
- outside root
- relative
- wildcard
- UNC
- device namespace
- ADS
- reserved/ambiguous
- symlink/reparse
- missing file
를 각각 검증.

Expected:
- HOLD
- run_task 0
- RUN_STARTED 0
- target side effect 0

첫 Runtime exact target 정책이 실제로 강제되는지 확인한다.

## Check 7 — READ-ONLY / Mutation Detection
Executor 코드에서 target write API가 없는지 확인.

정상:
- before SHA/size == after SHA/size

공격:
- preflight 후 외부/Mutation fixture로 target 변경
- Executor result만 원래 값으로 위조

Expected:
- independent Validator가 current state를 재계산
- FAIL/BLOCK
- mutation 사실 보존

### Mutation R1
Executor 실행 중 target 변경 + executor result 위조.
Expected: Validator FAIL/BLOCK.

## Check 8 — Validator Independence
Validator가 Executor JSON의 값을 그대로 비교만 하지 않고 실제 target을 다시 읽는지 확인:
- canonical path
- existence
- size
- SHA-256
- preflight / before / after / current relation

검사 불능 → ERROR.

Validator가 Executor와 동일 함수/결과를 그대로 재사용해 독립성이 사라지면 IMPORTANT/BLOCKER.

## Check 9 — Evidence Linkage
실제 test Evidence에서:
```text
request
→ approval
→ Task/Plan SHA
→ Run
→ Executor identity/SHA
→ Validator identity/SHA
→ target observations
→ Validation
→ Gate
→ Evidence ID/SHA
```
를 추적한다.

### Mutation E1
request_id 변조 + 관련 JSON hash 재계산.

### Mutation E2
run_id 변조.

### Mutation E3
executor/validator identity 또는 SHA 변조.

### Mutation E4
Evidence ID/SHA linkage 변조.

Expected: Validator/Evidence integrity FAIL 또는 Gate BLOCK.

단순 파일 hash만 맞추면 통과하는 구조인지 확인한다.

## Check 10 — Duplicate Request / Idempotency
동일:
- request_id
- approval scope
- Plan hash
- existing PASS Evidence

재진입:
- NO_CHANGE
- Run 0
- duplicate Evidence 0

같은 request_id인데 contract/Plan hash가 다르면:
- HOLD

기존 PASS Evidence가 FAIL/ERROR이면 NO_CHANGE로 잘못 처리하지 않는지 확인한다.

## Check 11 — V1~V8 Independent Reproduction
Beta 밖 격리 복사본에서 V1~V8을 독립 재현한다.

Expected:
- V1 PASS/PROCEED
- V2 FAIL/BLOCK
- V3 HOLD/Run0
- V4 HOLD/Run0
- V5 HOLD/Run0
- V6 FAIL/BLOCK
- V7 APPROVAL_REQUIRED/HOLD + Run0
- V8 BLOCK

실제 Production `Beta-Index.md`를 사용하지 않는다.

## Check 12 — Regression
격리 복사본에서:
- 기존 100
- 신규 12
- TOTAL 112
- PASS 112
- FAIL 0
- ERROR 0

기존 Test 삭제/완화 여부도 확인한다.

## Check 13 — Known Limitation Isolation
- KL-1: parallel false
- KL-2: exact target + unsafe path HOLD
- KL-3: dependencies empty

Known Limitations는 OPEN / ACCEPTED FOR MVP 유지.
새로 해결됐다고 주장하지 않는다.

## Check 14 — Frozen Baseline / Git
확인:
- MVP Overall PASS 유지
- MVP FROZEN
- 7/7 OFFICIAL PASS
- Architecture/Terminology 변경 없음
- 기존 Runtime Evidence 변경 없음
- Phase2 NOT STARTED
- actual Production Run 0
- Production Runtime Evidence 0
- Git commit/push 0
- local implementation changes만 worktree에 존재

## Severity

### BLOCKER
- Boundary 우회로 production executable 실행 가능
- invalid/missing approval에서 Run 발생
- outside/unsafe path 실행
- arbitrary executable/validator 실행 가능
- executable SHA pin 우회
- target mutation을 PASS
- Evidence linkage 위조를 PASS
- 실제 Production Runtime이 이미 실행됨
- Architecture/Frozen baseline 위반

### IMPORTANT
- Validator 독립성 부족
- fixture/production 경계 모호
- duplicate request가 중복 Run/Evidence 생성
- 기존 100 Regression 의미 훼손
- scope 확대
- Known Limitation 상태 변경

### MINOR
- 비차단 명명/보고/향후 hardening

## Final Decision

### PASS
조건:
- Check1~14 PASS
- V1~V8 PASS
- Mutation B1/A1~A3/R1/E1~E4 PASS
- Regression 112/112
- BLOCKER 0
- IMPORTANT 0
- Beta original files changed by review = 0

의미:
- Minimal Production Runtime Boundary = Independent Review PASS
- Implementation closure candidate
- 실제 Runtime 실행은 여전히 NOT AUTHORIZED
- 다음 = Closure/State Sync 후 First Runtime User Gate

### REVISION REQUIRED
BLOCKER/IMPORTANT 하나라도 존재.
- production-ready 금지
- actual Runtime 금지
- 최소 Fix Scope 보고

### HOLD
핵심 파일/Evidence를 검증할 수 없음.

## Required Output
1. Final Verdict
2. Beta Files Changed by Review
3. Check1~14
4. Boundary Bypass
5. Fixture/Production Separation
6. Allowlist/SHA Pin
7. Approval/Scope
8. Path Safety
9. READ-ONLY/Mutation
10. Validator Independence
11. Evidence Linkage
12. Duplicate Request
13. V1~V8
14. Mutations B1/A1~A3/R1/E1~E4
15. Regression
16. Known Limitation Isolation
17. Preservation / Architecture Delta
18. Git / Production Run Status
19. BLOCKER / IMPORTANT / MINOR
20. Done / Now / Next
21. User Approval Required

## End State
- Review mode = READ-ONLY
- MVP remains FROZEN
- actual Production Runtime = NOT RUN
- Production Runtime Evidence = 0
- Phase2 = NOT STARTED
- Git push = NO
- PASS → implementation closure candidate only
- actual first Runtime still requires separate User Gate

=== ORDER END ===
