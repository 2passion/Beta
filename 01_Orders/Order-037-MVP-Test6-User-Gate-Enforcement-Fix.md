# Order-037 — MVP Test 6 User Gate Enforcement Fix

## 0. Metadata
- Order ID: Order-037
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: WRITE
- Trigger: Order-036 REVISION REQUIRED
- Target: MVP Test 6 User Gate Plan 1.1 candidate
- Architecture SSOT / Terminology: FROZEN
- Test 7: NOT STARTED

## 1. Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: WRITE
order: Order-037
project: Beta

mismatch_policy:
- 현재 실행 주체가 to와 다르면 즉시 HOLD
- 실행/Beta 파일 변경 금지
- ROUTING_MISMATCH 보고
- 올바른 수신자에게 재전달될 때까지 대기
=== ROUTING END ===
```
Routing Header는 아직 Active Rule이 아니다.

## 2. Intent
Order-036에서 확인된 Test 6 enforcement 결함만 최소 수정한다.

- B1: `approval_granted` OR 우회
- B2: Approval Scope 미연결
- I1: Idempotency가 실제 Write가 아닌 label/counter 수준
- I2: Recovery Boundary가 hard-coded label 수준
- I3: Routing Evidence가 실제 호출/Write와 연결되지 않음
- I4: Routing이 실제 실행 앞단 차단 경로가 아님

새 대형 Router/Recovery/Agent/DB/Plugin/Adapter를 만들지 않는다.
기존 Test 5 Prevention과 Common Harness를 우선 재사용한다.

## 3. Order-036 Facts
Claude READ-ONLY review:
- Verdict: REVISION REQUIRED
- Beta changes: NO
- Evidence Integrity: PASS
- Regression: 60/60 PASS
- Preservation: PASS

실제 결함:
- `if approval_granted or all(AUTO_KEYS)` OR 우회
- Approval Record Scope와 Request Scope 미비교
- 실제 duplicate write를 Validator가 놓침
- Recovery가 hard-coded object/count
- Routing count/executor identity가 실제 호출 경계와 미연결
- Routing이 실제 entry gate가 아닌 독립 함수

## 4. Fix B1 — AUTO = C1..C8 AND
AUTO는 반드시:
`C1 AND C2 AND C3 AND C4 AND C5 AND C6 AND C7 AND C8`

C1~C8:
1. existing_contract
2. io_clear
3. fixture_runtime_pass
4. bounded_change_scope
5. postflight_possible
6. idempotent
7. reason_and_stop_defined
8. within_approved_scope

`approval_granted` 자체는 AUTO 우회 조건이 아니다.
승인은 C8을 성립시키는 근거 중 하나일 뿐이다.

Required:
- 전부 true → AUTO 가능
- 하나라도 false → AUTO 금지
- approval=true + C1~C8 false → AUTO 금지
- HOLD reason은 approval보다 우선

## 5. Fix B2 — Approval Bound to Scope
최소 계약:
```text
approval:
  approval_id
  approved_scope
  approval_status

request:
  requested_scope
```

`within_approved_scope = approval_status==APPROVED AND requested_scope contained in approved_scope`

기존 구조를 재사용하고 새 권한 DB는 만들지 않는다.

Required:
- 동일/허용된 더 좁은 Scope → 기존 승인 재사용 가능
- 확대/다른 의미·권한 Scope → APPROVAL_REQUIRED
- boolean approval만 있고 Scope 불명확 → AUTO 금지

## 6. Fix I1 — Real Idempotency
동일 승인+입력+상태 재진입 시 실제 write path 기준:
- 불필요 Write 0
- duplicate file 0
- duplicate Evidence 0
- NO_CHANGE 또는 결정적 종료

Validator는 executor의 counter만 신뢰하지 않고 filesystem before/after snapshot, 실제 생성/수정 파일, Evidence delta를 독립 비교한다.
실제 rewrite/add Mutation을 PASS시키면 안 된다.

## 7. Fix I2 — Reuse Test 5 Prevention
새 Recovery 시스템을 만들지 않는다.
Test 6은 “자동복구 호출 가능 여부”만 Gate한다.

기존 Test 5 Prevention 계약/Asset을 재사용하여:
`recovery_allowed = fingerprint_applicable AND prevention_verified AND scope_match AND fix_contract_valid AND postflight_possible`

전부 true일 때만 `AUTO_RECOVERY_ALLOWED`.

신규/미확인 Root Cause:
- HOLD
- `NEW_ROOT_CAUSE_UNCONFIRMED` 또는 동등 Reason
- auto fix 0
- unauthorized new run 0

`verified=True` 같은 라벨만으로 통과 금지.
안전하게 Test 5 Asset을 재사용할 수 없으면 새 Recovery를 만들지 말고 HOLD 후 보고한다.

## 8. Fix I3/I4 — Routing Entry Enforcement
대형 Router가 아니라 최소 entry boundary:

```text
expected_to + actual_executor + action
              ↓
         routing check
        ↙             ↘
      MATCH          MISMATCH
       allow           HOLD
```

Mismatch에서 writer/run_task/downstream 호출 불가.

Evidence는 가능한 실제 호출 지점에서:
- writer_call_count
- run_task_call_count
- beta_write_delta
- downstream_call_count
를 측정한다. 상수 count 금지.

actual executor를 신뢰성 있게 자동 감지할 기존 Asset이 없으면 새 identity infrastructure를 만들지 않는다.
Order execution context의 identity를 입력 계약으로 사용하고 `IDENTITY_SOURCE=ORDER_EXECUTION_CONTEXT`처럼 provenance를 명시한다. OS/process identity라고 과장하지 않는다.

## 9. Required Scenarios / Mutations
A Normal AUTO: C1~C8 true → AUTO/run once/PASS.
B Approval Required: 승인 전 side effect 0. 승인 후에도 C1~C7 true + Scope match일 때만 AUTO.
C HOLD: SSOT conflict/Evidence missing → all side effects 0.
D Scope Expansion: 기존보다 큰 requested_scope → APPROVAL_REQUIRED/write0.
E Idempotent Re-entry: duplicate write/evidence 0/NO_CHANGE.
F Routing Mismatch: HOLD/writer0/run0/write0/downstream0.

G Approval OR Bypass: approval=true, C1~C8 false → AUTO 금지.
H Single Condition Missing: C1~C8 각각 하나씩 false 전수 → 모두 AUTO 금지.
I Scope Reuse Attack: 이전 approval + expanded scope → APPROVAL_REQUIRED.
J Real Duplicate Write: 실제 rewrite/add 강제 → Validator FAIL/BLOCK.
K Fake Recovery Labels: 라벨 위조 + 실제 Prevention 불충족 → HOLD/auto fix0.
L Routing False Report: 실제 routing inputs와 결과 라벨 불일치 → Validator 독립 재계산 FAIL/BLOCK.

## 10. Validator Independence
Validator는 executor 라벨을 그대로 신뢰하지 않는다.
독립 재계산:
- AUTO C1~C8
- Scope match
- Routing match
- filesystem delta
- Evidence delta
- Recovery eligibility inputs

불일치 → FAIL.
검사 자체 불능 → ERROR.

## 11. Version / Evidence
기존 Plan 1.0/Evidence 덮어쓰기 금지.

새 결과:
- Test ID `MVP-TEST-6`
- Version `1.1`
- change_reason_ref `Order-037`
- New RUN/Event/Validation/Evidence

Plan 1.0 기록은 보존한다.

## 12. Regression / Preservation
관련 전체 Regression 실행.

보존:
- Test1 OFFICIAL PASS
- Test2 OFFICIAL PASS
- Test4 OFFICIAL PASS
- Test5 OFFICIAL PASS
- Phase1
- Common Harness/Core
- Architecture/Terminology/Reference
- Test6 Plan1.0/Evidence

기존 테스트 삭제/완화 금지. Blind Retry 금지.

## 13. Prohibited
Architecture/Terminology 변경, Test3/7, Phase2, 대형 Router, 새 Agent/DB/Plugin/Adapter, 새 Recovery framework, Active Rule 승격, 기존 Evidence 덮어쓰기, Scope 밖 기능 추가.

## 14. Required Result
A. Routing: entry enforcement, identity source, mismatch side effects, actual counters/delta.
B. B1: C1~C8 AND, OR 제거, Mutation G/H.
C. B2: approval/request Scope 비교, Mutation I.
D. I1: actual write path/filesystem diff, Mutation J.
E. I2: 재사용 Test5 Asset/contract, Mutation K, 새 Recovery 구현 NO.
F. I3/I4: actual entry gate/counters, Mutation L.
G. Scenario A~F: Decision/Execution/Validation/Gate/Side Effect.
H. Regression: TOTAL/PASS/FAIL/ERROR.
I. Official Candidate: ID/version/reason/Run/Plan SHA/Executor SHA/Validator SHA/Evidence/SHA/Execution/Validation/Gate/Scenario.
J. Preservation.
K. Files Changed: 수정/생성/삭제.
L. Done/Now/Next: Plan1.1 candidate, Delta Recheck, approval need, Test7 NOT STARTED.

## 15. Completion Gate
Plan 1.1 PASS candidate는 모두 충족해야 한다:
- B1/B2 resolved
- I1 resolved
- I2 실제 Test5 재사용 경계로 enforcement
- I3/I4 최소 routing contract 안에서 resolved
- A~F PASS
- G~L PASS
- independent Validator recomputation PASS
- Regression/Preservation PASS
- Architecture delta NONE
- Scope violation NONE
- Evidence complete

Codex 단독 OFFICIAL PASS 금지.

Codex Result → ChatGPT 검토 → Claude READ-ONLY Delta Recheck → PASS 시 Test6 OFFICIAL PASS 후보 확정 → 이후 상태 Sync → Test7 검토.

Test7 자동 시작 금지.

## 16. Current State
- Test5 Prevention: OFFICIAL PASS
- Test6 Plan1.0: REVISION REQUIRED
- Test6 Plan1.1: NOT RUN
- Test7: NOT STARTED
- User Approval: already granted within this fix scope
- Next executor: Codex

=== ORDER END ===
