# Order-063 — Minimal Production Runtime Boundary Enforcement Independent Delta Recheck

## Metadata
- Order ID: Order-063
- Project: Beta
- Status: APPROVED
- Type: READ-ONLY INDEPENDENT DELTA RECHECK
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer: Codex
- Reviewer / To: Claude Code
- Action: REVIEW_ONLY
- Trigger: Order-062 Fix PASS candidate
- Previous Review: Order-061 REVISION REQUIRED
- MVP: PASS / FROZEN
- Architecture: v1.0 FROZEN
- Phase2: NOT STARTED
- Production Approval: NOT ISSUED
- Actual Runtime / Git write: NOT AUTHORIZED

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Claude Code
action: REVIEW_ONLY
order: Order-063
project: Beta
mismatch -> HOLD / no Beta write / no runtime / no git
```

## Purpose
Order-061의 BLOCKER 2 + IMPORTANT 2가 Order-062에서 실제 해결됐는지 독립 Delta Recheck한다. 전체 Runtime Boundary를 처음부터 재검토하지 않는다.

집중:
1. Core direct-call bypass
2. Trusted SHA policy와 policy 자체의 trust anchor
3. Production approval enforcement
4. NO_CHANGE full-chain reverification
5. strict/fail-closed
6. 신규 공격 Regression 품질
7. 기존 112 보존
8. FROZEN baseline / Production Run0

Mutation/Regression은 Beta 밖 격리 복사본에서만 수행한다.

## D1 — Core Direct-call Bypass
독립 재현:
- run_task 직접 호출
- caller-supplied approved_program_paths
- evil_exec.py
- missing approval
- outside target
- fixture executable production 우회
- runtime_request 없는 production executable
- context/flag 조작

Expected: HOLD/BLOCK, arbitrary execution0, marker0, invalid production Run0. Core가 Boundary 밖에서도 production policy를 강제해야 한다.

## D2 — Trusted SHA Policy / Trust Anchor
`runtime_policy.json`에 SHA가 있다는 사실만으로 trusted라고 인정하지 않는다.

확인:
- policy file path/identity/integrity가 무엇에 고정되는가
- runtime_policy.py가 임의 policy path를 허용하는가
- policy JSON 변경이 자동 승인되는가
- executor/validator + policy JSON 동시 변경이 통과하는가
- policy loader 우회/주입 가능 여부
- policy가 FROZEN/approval 기준과 어떻게 연결되는가

P1 executor만 변경 → BLOCK.
P2 validator만 변경 → BLOCK.
P3 **executor/validator 변경 + runtime_policy.json SHA도 함께 변경** → 반드시 BLOCK/HOLD.
P4 다른 policy path/loader 주입 → BLOCK.
P5 policy 삭제/손상 → fail-closed, Production Run0.

P3가 PASS하면 BLOCKER.

원칙:
> 검증 대상이 자기 승인값을 자유롭게 재정의할 수 있으면 독립 pin이 아니다.

## D3 — Production Approval
현재 approval = NOT_ISSUED.

공격:
missing, arbitrary `x`, random UUID, fixture token, forged approval-like file, plan/policy에 approval_ref 삽입, caller가 approval status 주입.

Expected: 전부 APPROVAL_REQUIRED/HOLD, Production Run0. First Runtime User Gate 전 어떤 값도 자동 승인 금지.

## D4 — NO_CHANGE Full-chain
prior:
- Boundary BLOCK
- Validation FAIL
- Gate BLOCK
- request/run ID 변조
- executor/validator identity/SHA 변조
- Evidence ID/SHA 변조
- Boundary event 변조
- 내용 변조 후 JSON/hash 재계산
- trusted policy 변경
- FAIL→PASS label 뒤집기

후 동일 request 재진입.

Expected: NO_CHANGE 금지 / HOLD-BLOCK / new Run0.

Genuine prior PASS만 NO_CHANGE / Run0 / duplicate Evidence0.

저장 Evidence만으로 독립 검증 가능한지 확인.

## D5 — Strict / Fail-closed
- bool exact
- task_count exact int 1, bool 금지
- unknown/missing fields
- reserved request_id
- final target delete/OSError
- reparse/symlink before resolve
- identity 확인 불가 → HOLD

처리되지 않은 예외 대신 계약된 FAIL/ERROR/HOLD/BLOCK을 남기는지 확인.

## D6 — Fixture/Production Separation
- fixture resolver 의미 유지
- fixture approval production 불가
- production policy가 fixture를 자동 승격하지 않음
- Test1~7 의미 유지

## D7 — Evidence Reader Independence
Duplicate 판단 reader가 메모리 core_result 없이 저장된 Plan/Event/Evidence/Validation/Gate/Boundary record로 chain을 검증하는지 확인한다.

현재 policy/current file만 보고 과거 승인 사실을 잘못 재구성하지 않는지 확인.

## D8 — Attack Regression Quality
신규 15개 Test가 실제 공격을 만드는지 코드 수준 확인:
direct call, evil executable, modified executor, replaced validator, arbitrary approval, duplicate tamper 등.
단순 mock return만 확인하는 테스트면 불충분.

## D9 — Regression
격리 복사본:
- 기존 112
- 신규 15
- TOTAL 127 / PASS127 / FAIL0 / ERROR0

가능하면 stability check로 2회 연속 실행. 이는 Blind Retry가 아니라 명시적 비결정성 검사.

## D10 — READ-ONLY Preservation
Order-061에서 PASS한 target mutation detection, executor write API 없음, validator current read가 유지되는지 확인.

## D11 — Known Limitations
KL-1 parallel=false, KL-2 exact path/unsafe HOLD, KL-3 dependencies=[].
OPEN / ACCEPTED 유지.

## D12 — Frozen / Git / Runtime
- MVP PASS/FROZEN
- 7/7
- Architecture/Terminology 불변
- Architecture Delta NONE
- Phase2 NOT STARTED
- Production Run0 / Evidence0
- approval NOT_ISSUED
- Git commit/push0
- local worktree implementation changes only

## Severity
BLOCKER:
- direct bypass 성공
- arbitrary executable 실행
- P3 policy+program 동시 변경 PASS
- arbitrary approval production 실행
- tampered Evidence NO_CHANGE
- actual Production Runtime 발생
- FROZEN baseline 위반

IMPORTANT:
- policy trust anchor가 승인 기준과 연결되지 않음
- Evidence reader 독립성 부족
- unsafe strict/fail-closed 누락
- 공격 Regression이 실제 공격 미재현
- 기존112 의미 훼손

MINOR:
- fail-closed이지만 보고/예외/명명 개선

## Final Decision
PASS:
- D1~D12 PASS
- P1~P5 PASS
- NO_CHANGE attacks PASS
- Regression 127/127
- BLOCKER0 / IMPORTANT0
- Beta original changed by review0

PASS 의미:
- Order-062 Fix Independent Review PASS
- Runtime Boundary Implementation Closure candidate
- actual Runtime은 여전히 NOT AUTHORIZED
- 다음 = Closure/State Sync → First Runtime User Gate

REVISION REQUIRED:
BLOCKER/IMPORTANT 존재. Closure/approval/runtime 금지 + 최소 Fix Scope 보고.

HOLD:
핵심 파일/정책/Evidence 검증 불가.

## Required Output
1 Final Verdict
2 Beta Files Changed
3 D1~D12
4 Core Direct-call Bypass
5 Trusted SHA Policy / Trust Anchor
6 P1~P5
7 Production Approval
8 NO_CHANGE Reverification
9 Strict/Fail-closed
10 Fixture/Production Separation
11 Evidence Reader
12 Attack Regression Quality
13 Regression
14 READ-ONLY Preservation
15 Known Limitation Isolation
16 Frozen/Git/Runtime
17 BLOCKER/IMPORTANT/MINOR
18 Done/Now/Next
19 User Approval Required

## End State
- READ-ONLY review
- MVP FROZEN
- Production approval NOT_ISSUED
- actual Runtime NOT RUN
- production Evidence0
- Phase2 NOT STARTED
- Git push NO
- PASS → closure candidate only
- first Runtime requires separate User Gate

=== ORDER END ===
