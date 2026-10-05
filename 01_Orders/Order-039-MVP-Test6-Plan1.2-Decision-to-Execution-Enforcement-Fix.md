# Order-039 — MVP Test 6 Plan 1.2 Decision-to-Execution Enforcement Fix

## 0. Metadata
- Order ID: Order-039
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- From: ChatGPT
- Action: WRITE
- Trigger: Order-038 REVISION REQUIRED
- Target: MVP Test 6 User Gate Plan 1.2 candidate
- Previous: Plan 1.1 REVISION REQUIRED
- Architecture SSOT / Terminology: FROZEN
- Test 7 Resume: NOT STARTED

## 1. Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: WRITE
order: Order-039
project: Beta

mismatch_policy:
- 현재 실행 주체가 to와 다르면 즉시 HOLD
- 실행/Beta 파일 변경 금지
- ROUTING_MISMATCH 보고
- 올바른 수신자에게 재전달될 때까지 대기
=== ROUTING END ===
```

## 2. Purpose
Order-038에서 확인된 단일 Blocker만 최소 수정한다.

Blocker:
- User Gate Decision이 Scenario A/B의 실제 `routing_entry → run_task` 호출 조건으로 연결되지 않음.
- 따라서 `APPROVAL_REQUIRED` 또는 `HOLD`인데도 Run/Runtime Evidence가 생성될 수 있음.
- Validator가 사후 FAIL/BLOCK하지만 Side Effect가 이미 발생함.

이번 Order는 기존 B1/B2/I1/I2/I3/I4를 재설계하지 않는다.
Plan 1.1에서 독립 PASS한 부분은 보존하고 Decision-to-Execution 연결만 수정한다.

## 3. Order-038 Verified Baseline
독립 검토에서 PASS:
- B1 AUTO = C1~C8 AND
- B2 Approval Scope Binding
- I1 filesystem-based Idempotency
- I2 Test 5 Prevention reuse
- I3/I4 Routing Entry Enforcement
- Validator independent recomputation
- Evidence Integrity
- Regression 66/66
- Preservation
- Architecture Delta NONE

독립 검토에서 FAIL:
- A/B의 `routing_entry(...)`가 `decision == AUTO` 조건 없이 호출됨.
- Scope Expansion → APPROVAL_REQUIRED인데 `RUN_STARTED` 발생.
- C3 false → HOLD인데 `RUN_STARTED` 발생.
- 사후 Validator는 FAIL/BLOCK하지만 사전 Side Effect 0 계약 위반.

## 4. Required Fix — Decision Must Gate Execution

실행 경계는 반드시 다음과 같아야 한다.

```text
User Gate Decision
├─ AUTO
│   └─ routing_entry
│       └─ Routing MATCH
│           └─ run_task
│
├─ APPROVAL_REQUIRED
│   └─ execution 0
│
└─ HOLD
    └─ execution 0
```

A/B를 포함하여 User Gate를 거치는 모든 해당 실행 경로에서:

```python
if decision["decision"] == "AUTO":
    routing_entry(...)
else:
    # no routing_entry
    # no writer
    # no run_task
    # no runtime evidence
```

와 동등한 실제 사전 차단을 구현한다.

단순히 Validator가 사후 적발하는 방식은 불충분하다.

## 5. Required Side-Effect Contract

`APPROVAL_REQUIRED` 또는 `HOLD` 상태에서는 최소한 다음이 모두 0이어야 한다.

- routing_entry call
- writer call
- run_task call
- downstream call
- RUN_STARTED event
- Run directory creation
- Runtime Evidence creation
- managed file write
- Beta write delta

Decision이 AUTO가 아니면 실행 계층에 진입하지 않아야 한다.

## 6. Required Delta Scenarios

### D1 — Normal AUTO
- C1~C8 true
- Decision AUTO
- routing_entry 1
- run_task 1
- Validation PASS
- Gate PROCEED

### D2 — Approval Before Approval
- Decision APPROVAL_REQUIRED
- routing_entry 0
- run_task 0
- RUN_STARTED 0
- Runtime Evidence 0
- write delta 0

승인 기록 후:
- Scope match
- C1~C7 true
- Decision AUTO
- 그때만 실행 1회

### D3 — Scope Expansion
- 기존 approval 존재
- requested_scope > approved_scope
- Decision APPROVAL_REQUIRED

Expected:
- routing_entry 0
- writer 0
- run_task 0
- RUN_STARTED 0
- Runtime Evidence 0
- write delta 0

### D4 — AUTO Condition Failure
최소 C3 `fixture_runtime_pass=False`.

Expected:
- Decision HOLD 또는 현재 계약상 비-AUTO 판정
- routing_entry 0
- run_task 0
- RUN_STARTED 0
- Runtime Evidence 0
- write delta 0

### D5 — HOLD Reason
예: SSOT_CONFLICT.

Expected:
- HOLD
- 모든 실행 Side Effect 0

### D6 — Routing Mismatch
AUTO 조건 자체는 충족하더라도 routing mismatch이면:
- routing_entry는 Gate 검사까지 수행 가능
- writer/run_task/downstream/write는 0
- HOLD / ROUTING_MISMATCH

기존 Plan 1.1 Routing 계약을 훼손하지 않는다.

## 7. Adversarial Mutations

### M1 — Force Decision APPROVAL_REQUIRED
A/B의 입력을 변경해 APPROVAL_REQUIRED를 만들고 end-to-end 실행.
Expected: 실제 Run/Runtime Evidence 0.

### M2 — Force Decision HOLD
C3=false 또는 동등 조건.
Expected: 실제 Run/Runtime Evidence 0.

### M3 — Scope Expansion Attack
이전 approval + 확대 Scope.
Expected: APPROVAL_REQUIRED + execution side effects 0.

### M4 — Remove Decision Guard
격리 복사본에서 새 guard를 제거하거나 우회해 `routing_entry/run_task`가 실행되도록 Mutation.
Expected: Validator FAIL/BLOCK.

Validator는 Decision과 실제 call/run/evidence delta의 일치를 독립 검증해야 한다.

## 8. Validator Delta

Validator는 최소한 다음 invariant를 독립 검증한다.

```text
decision != AUTO
→ routing_entry_count == 0
→ writer_call_count == 0
→ run_task_call_count == 0
→ RUN_STARTED == 0
→ runtime_evidence_delta == 0
→ managed_write_delta == 0
```

그리고:

```text
decision == AUTO
AND routing == MATCH
→ expected execution path may run
```

Routing mismatch의 기존 차단 계약도 유지한다.

Executor의 `decision`, count, result 라벨만 신뢰하지 말고 가능한 실제 Event/filesystem/call-site evidence와 대조한다.

## 9. Preserve Plan 1.1 Fixes

다음은 재설계하지 않고 Regression으로 보존을 확인한다.

- AUTO C1~C8 AND
- approval OR bypass 제거
- Approval Scope containment
- filesystem Idempotency
- Test 5 Prevention Source-chain reuse
- Routing Entry Enforcement
- Routing provenance `ORDER_EXECUTION_CONTEXT`
- Validator independent recomputation
- Mutation G~L protections

기존 검증을 약화하거나 테스트를 삭제해서 PASS시키지 않는다.

## 10. Version / Evidence

Plan 1.0과 Plan 1.1 및 기존 Evidence를 덮어쓰지 않는다.

새 결과:
- Test ID: `MVP-TEST-6`
- Version: `1.2`
- change_reason_ref: `Order-039`
- New Run/Event/Validation/Evidence
- Plan 1.2 candidate

Plan 1.0/1.1 실패 및 후보 기록은 보존한다.

## 11. Regression

기존 66개 Regression을 모두 유지한다.

이번 Decision-to-Execution enforcement용 Delta Test/Mutation을 추가한다.

최종 TOTAL은 66보다 커질 수 있다.
중요한 기준은:
- 기존 66 모두 PASS
- 신규 Delta tests 모두 PASS
- FAIL 0
- ERROR 0

Blind Retry 금지.

## 12. Preservation

반드시 보존:
- Test1 OFFICIAL PASS
- Test2 OFFICIAL PASS
- Test4 OFFICIAL PASS
- Test5 OFFICIAL PASS
- Phase1
- Common Harness/Core
- Architecture/Terminology
- Reference
- Test6 Plan1.0/Evidence
- Test6 Plan1.1/Evidence

금지:
- Test3 시작
- Test7 시작
- Phase2
- Active Rule 승격
- 새 Router/Recovery framework
- Agent/DB/Plugin/Adapter
- Architecture 변경
- Terminology 변경
- 기존 Evidence 덮어쓰기

Architecture Delta = NONE 이어야 한다.

## 13. Files / Scope

Order-038 Blocker 해결에 필요한 최소 파일만 수정한다.

우선 예상:
- `03_Tests/fixtures/user_gate_scenario_executor.py`
- `03_Tests/fixtures/user_gate_validator.py`
- `03_Tests/test_mvp_user_gate.py`
- `03_Tests/fixtures/task_mvp_test_6_user_gate.json`
- 필요한 append-only Run/Event/Evidence
- 필요한 경우 현재 상태/Order History의 candidate 기록

불필요한 새 구조/폴더를 만들지 않는다.

## 14. Required Result

### A. Decision-to-Execution Fix
- 수정한 실제 call path
- AUTO/non-AUTO 분기
- routing_entry/run_task 연결

### B. Side Effect Zero
APPROVAL_REQUIRED/HOLD에서:
- routing count
- writer count
- run_task count
- RUN_STARTED
- Runtime Evidence
- write delta

### C. Delta D1~D6
각 결과.

### D. Mutation M1~M4
각 결과.

### E. Plan 1.1 Preservation
B1/B2/I1/I2/I3/I4가 계속 PASS인지.

### F. Regression
- 기존 66 PASS 여부
- 신규 Test 수
- TOTAL/PASS/FAIL/ERROR

### G. Official Candidate
- Test ID
- Version 1.2
- change_reason_ref Order-039
- Run ID
- Plan SHA
- Executor SHA
- Validator SHA
- Evidence ID/SHA
- Execution/Validation/Gate
- Scenario ID/Evidence count

### H. Preservation
기존 Test/Architecture/Plan1.0/Plan1.1.

### I. Files Changed
수정/생성/삭제.

### J. Done / Now / Next
- Plan1.2 PASS candidate 여부
- Independent Delta Recheck 필요
- Test6 OFFICIAL PASS NOT YET
- Test7 NOT STARTED

## 15. Completion Gate

Plan 1.2 PASS candidate 조건:

- Decision→Execution 사전 Gate 연결
- APPROVAL_REQUIRED side effects 0
- HOLD side effects 0
- Scope Expansion side effects 0
- C3 false side effects 0
- Routing mismatch 기존 보호 유지
- M1~M4 PASS
- Plan1.1 B1/B2/I1/I2/I3/I4 보존
- 기존 66 Regression PASS
- 신규 Delta tests PASS
- Evidence complete
- Preservation PASS
- Architecture Delta NONE
- Scope violation NONE

Codex 단독 OFFICIAL PASS 금지.

완료 후:
Codex Order-039 Result
→ ChatGPT 검토
→ Claude Code READ-ONLY Plan1.2 Delta Recheck
→ PASS 시 Test6 OFFICIAL PASS 후보 확정
→ 별도 상태 Sync
→ Test7 검토

Test7 자동 시작 금지.

## 16. Current State
- Test5 Prevention: OFFICIAL PASS
- Test6 Plan1.0: REVISION REQUIRED
- Test6 Plan1.1: REVISION REQUIRED
- Test6 Plan1.2: NOT RUN
- Test6 OFFICIAL PASS: NOT YET
- Test7 Resume: NOT STARTED
- User Approval: already granted within this narrow fix scope
- Next executor: Codex

=== ORDER END ===
