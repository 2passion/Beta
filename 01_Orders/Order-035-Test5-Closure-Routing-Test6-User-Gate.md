# Order-035 — Test 5 Closure Sync + Execution Routing Contract + MVP Test 6 User Gate

## 0. Metadata
- Order ID: Order-035
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE
- Root: `C:\Obsidian\Beta`
- Architecture SSOT / Terminology: FROZEN
- Generator: ChatGPT
- Writer: Codex
- Independent Reviewer: Claude Code
- Previous Review: Order-034 PASS
- Target: MVP Test 6 — User Gate

## 1. Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: WRITE
order: Order-035
project: Beta

mismatch_policy:
- 현재 실행 주체가 to와 다르면 즉시 HOLD
- 실행 및 Beta 파일 변경 금지
- ROUTING_MISMATCH 보고
- 올바른 수신자에게 재전달될 때까지 대기
=== ROUTING END ===
```
이 Header는 아직 Active Rule이 아니라 Order 수준 실행 계약 후보다.

## 2. Intent
반드시 순서대로 수행한다.
1. MVP Test 5 Prevention 종료 상태를 실제 Beta 상태 파일에 동기화한다.
2. Execution Routing Contract를 적용하고 Evidence를 남긴다.
3. 앞 단계가 PASS한 경우에만 MVP Test 6 User Gate를 구현·실행·검증한다.

새 대형 Router/Agent/DB/Plugin/Adapter/Phase 2를 만들지 않는다. 기존 Gate, Validator, Generator, Evidence, Prevention, Common Harness를 우선 재사용한다.

## 3. Approved Operating Model
사용자가 승인한 장기 방향:
- 사용자 Workflow: 요청 → 필요한 경우 승인 1회 → 승인 범위 안 자동 진행 → 결과/다음 할 일 확인.
- 내부 SSOT/Contract/Classifier/Router/Gate/Generator/Writer/Validator/Evidence/Prevention/Recovery/Independent Review 책임은 유지.
- 승인된 범위에서는 Evidence 기반으로 중간 승인 없이 진행.
- 의미·권한·범위가 바뀔 때만 사용자 Gate.
- 검증된 Prevention만 자동 복구.
- 새로운 실패는 임의 Fix하지 않고 진단 후 보고.
- Summary와 Detailed는 같은 Evidence에서 생성.
이 Order는 전체 장기 자동화 시스템을 구현하지 않고 Test 6 최소 범위만 검증한다.

## 4. Step 0 — Routing Preflight
확인:
- actual executor = Codex
- expected `to` = Codex
- Order 전체와 `=== ORDER END ===` 확인
- Root 확인
- Architecture/Terminology FROZEN 확인

불일치 시:
- HOLD
- Reason Code `ROUTING_MISMATCH`
- Writer 호출 0 / Beta Write 0 / 다음 단계 0

## 5. Step 1 — Test 5 Closure Sync
새 파일 생성 전에 기존 상태 파일/Asset을 검색한다. 최소 후보:
- `Beta-Index.md`
- `01_Orders\Order-History.md`
- 실제 존재하는 State/Progress/MVP status View

추측하여 새 상태 파일을 만들지 않는다.

반영할 확정 상태:
- Test 1 Reuse: OFFICIAL PASS
- Test 2 Ownership: OFFICIAL PASS
- Test 3 Safe Parallel: NOT VERIFIED
- Test 4 Bottleneck: OFFICIAL PASS
- Test 5 Prevention: OFFICIAL PASS
- Prevention Review/Fix Loop: CLOSED
- Test 6 User Gate: NOT VERIFIED
- Test 7 Resume: NOT VERIFIED
- Order-032 B1/I1/I2/I3: RESOLVED
- Order-034 Claude Independent Review: PASS, Check 1~13 PASS, New Blocker NONE

Test 5 official baseline:
- ID `MVP-TEST-5`, Version `1.1`, reason `Order-033`
- Run `RUN-a6f06583-94f1-45f5-9cf4-58d7e0a795fe`
- Plan SHA `0A9CD66E8A25D9505CBA67C3C5740C9E52CE959729FD27B6C46A2D6568205699`
- Executor SHA `0E5A376E184970286D21C14AE64CE26441CC166A0504FE58FC0FBA20DF7BC3E8`
- Validator SHA `3C452F60019AF2E40EFD3C09D2EA9DAB09F4EBAD6D233994FD53C049AE4D8ABB`
- Evidence `EVD-b0da574a-38f3-4eb1-ba4f-a25695efa60b`
- Evidence SHA `9AEB03C68A322B5A467E2CFBCA7E92A834BB013A0EFDB09BDE2071CF17B1F490`
- Execution PASS / Validation PASS / Gate PROCEED
- Scenario `SCN-4ddfb5fe-b5f3-4521-bddc-f5dbb9869146`, Evidence 15, mismatch 0

Closure Sync 결과:
- `SYNCED`: 필요한 변경 후 검증 완료
- `NO_CHANGE`: 이미 동일, 불필요한 Write 0
- `HOLD`: 실제 SSOT/Evidence와 충돌
HOLD이면 Test 6 시작 금지.

## 6. Step 2 — Routing Runtime Evidence
가능하면 기존 Event/Evidence 구조를 재사용한다.
최소 기록:
`expected_to`, `actual_executor`, `action`, `routing_result`, `mismatch_reason`, `write_allowed`, `order_id`.

정상: Codex→Codex / WRITE / MATCH / write_allowed=true.

격리 Fixture:
expected_to=Claude Code, actual_executor=Codex.
Expected: HOLD / ROUTING_MISMATCH / Writer 0 / Beta Write 0 / 다음 단계 0.
이번에는 Active Rule로 승격하지 않는다.

## 7. Step 3 — MVP Test 6 User Gate
목표: 사용자 판단이 필요 없는 작업은 승인 Scope 안에서 자동 진행하고, 의미·권한·범위가 달라지는 중요한 결정에서만 사용자에게 질문하는지 검증한다.

실행 판정:
- `AUTO`
- `APPROVAL_REQUIRED`
- `HOLD`

### AUTO 조건 — 8개 모두 필요
1. 기존 Contract 존재
2. 입력/출력 명확
3. Fixture Runtime PASS
4. 적용 경로/변경 범위 제한
5. Postflight 검증 가능
6. 재실행 시 중복 Write 없음
7. Failure Reason Code와 Stop Condition 정의
8. 현재 승인 Scope 안

### APPROVAL_REQUIRED
- 승인 Scope 확대
- 목표/의미 변경
- Architecture/SSOT 결정
- 제품 설계 선택
- 삭제·이동·외부 게시 등 권한 확대
- 보호 파일 위험 변경
- 실제 데이터 충돌에서 사용자 선택 필요

승인 전 Side Effect=0. 승인 후 동일 Scope에서 중복 승인 요청 금지.

### HOLD
- Routing mismatch
- SSOT 충돌
- 필수 Evidence 없음
- Validator ERROR
- 실행 계약 위반
- 안전한 자동조치가 없는 신규 실패
- 보호 파일 손상 가능성

HOLD 후 추가 Side Effect=0, 사실/Reason Code 보고, 임의 Fix 금지.

## 8. Approved Scope / Stop Conditions
Approved:
- Test 5 Closure Sync
- Routing Contract + 격리 Fixture
- Test 6 최소 Plan/Fixture/Validator/Evidence
- 기존 Common Harness/Asset 재사용
- 필요한 Index/History 상태 갱신
- 승인 Scope 안의 Verified Prevention 재사용

Stop:
- Architecture/Terminology 변경 필요
- 기존 공식 Evidence와 실제 상태 충돌
- Test 1/2/4/5 Evidence 손상
- Test 3/7 우회
- Phase 2
- 새 대형 Router/DB/Agent/Plugin/Adapter 필요
- 삭제/대량 이동/외부 게시 필요
- 신규 Root Cause 미확인 상태에서 Fix 필요
- Scope 밖 기능 필요

## 9. Required Scenarios
### A — AUTO
승인 Scope 안의 결정적 작업.
Expected: AUTO / 질문 0 / 실행 1 / Validation PASS / Evidence / Gate PROCEED.

### B — APPROVAL_REQUIRED
승인 전: Side Effect 0, 필요한 결정만 요청.
승인 Fixture 후: Scope 기록, 같은 결정 중복 질문 0, 실행/Validation/Evidence PASS.

### C — HOLD
SSOT 충돌 또는 필수 Evidence 누락.
Expected: HOLD / Side Effect 0 / Reason Code / 임의 Fix 0.

### D — Scope Expansion
기존 승인 밖 변경.
Expected: APPROVAL_REQUIRED / 새 승인 전 Write 0.

### E — Idempotent Re-entry
동일 승인/상태/입력 재처리.
Expected: 중복 Write 0 / 중복 Evidence 남발 0 / NO_CHANGE 또는 결정적 종료.

### F — Routing Mismatch
Expected: HOLD / ROUTING_MISMATCH / Write 0 / 다음 작업 0.

## 10. Recovery
자동 복구는 승인 Scope 안에서:
동일/적용 가능한 Fingerprint + Verified Prevention + Scope 일치 + Fix contract 검증 + Postflight 가능일 때만 허용.

Flow:
FAIL → Fingerprint → Prevention Search → Verified Prevention → Fix → New RUN → Revalidation → Evidence.

자동 복구 금지:
의미 불명확, SSOT 선택, 실제 데이터 충돌, 제품 설계 선택, 보호 파일 위험, 권한 확대, 신규 Root Cause 미확인.
이 경우 진단까지만 하고 APPROVAL_REQUIRED 또는 HOLD.

## 11. Reporting Contract
원본은 Run/Event/Validation/Evidence 하나로 유지한다. Summary/Detailed를 별도 SSOT로 만들지 않는다.

Summary View — 3분:
1. 목표
2. 승인 범위
3. 자동 실행 단계
4. 문제/자동 복구
5. 실제 검증 결과
6. 현재 상태
7. 다음 할 일/사용자 판단

Detailed View:
Order/Task/Run/Event/Evidence ID, Validator/Gate, Hash, Fingerprint, Root Cause, Prevention, 승인 Scope, Routing, 변경 파일, Regression.

## 12. Validation / Regression
검증:
- Closure Sync 정확성
- Routing MATCH
- Mismatch→HOLD/Write0
- AUTO 8조건
- 승인 전 실행 0
- 승인 후 동일 Scope 중복 승인 0
- HOLD 후 Side Effect 0
- Scope Expansion 새 승인
- 재진입 중복 Write 0
- Scenario A~F
- Test 1/2/4/5, Common Harness/Core, Architecture/Terminology 보존

필수 Validator 전부 PASS해야 한다. Validator 자체 실패는 ERROR.
기존 관련 전체 Regression을 실행하며 기존 Test를 삭제/완화하지 않는다.
FAIL/ERROR면 Test 6 Official PASS 금지. Blind Retry 금지.

## 13. Prohibited
Architecture/Terminology 변경, Test 3/7 구현, Phase 2, 대형 Router, 상시 Agent, 복잡 DB, Plugin/Adapter, Desktop Commander 상시 통합, Active Rule 자동 승격, Prevention→Rule 자동 승격, 공식 FAIL Run 삭제/덮어쓰기, Evidence 조작, Scope 밖 자동 실행.

## 14. Result Format
A. Routing — expected/actual/result/mismatch fixture  
B. Closure Sync — 파일, before/after, SYNCED/NO_CHANGE/HOLD  
C. Reuse — 재사용 Asset과 신규 생성 이유  
D. Test 6 Contract — AUTO/APPROVAL_REQUIRED/HOLD/Scope/Stop  
E. Scenario A~F — Execution/Validation/Gate/Side Effect/approval/duplicate write  
F. Recovery — Prevention Search/자동복구/신규진단  
G. Regression — TOTAL/PASS/FAIL/ERROR  
H. Official Candidate — Test ID/version/reason/Run/Plan SHA/Executor SHA/Validator SHA/Evidence/SHA/Execution/Validation/Gate  
I. Preservation — Test1/2/4/5, Phase1, Common Harness/Core, Architecture/Terminology/Reference  
J. Files Changed — 수정/생성/삭제  
K. Done/Now/Next — 사용자 승인 필요 여부 포함

## 15. Completion Gate
Test 6 `PASS candidate` 조건:
- Closure Sync PASS
- Routing runtime PASS
- Scenario A~F PASS
- 필수 Validator PASS
- Regression PASS
- Preservation PASS
- Architecture delta NONE
- Scope violation NONE
- Evidence complete

Codex 단독으로 OFFICIAL PASS 확정 금지.

Codex Result → ChatGPT 검토 → Claude Code READ-ONLY Independent Review → PASS 시 Test 6 OFFICIAL PASS → User Gate Review/Fix Loop CLOSED.

Test 7 Resume 자동 시작 금지.

## 16. Current State
- User Approval: YES
- Write Owner: Codex
- Reviewer: Claude Code
- Next Gate: Order-035 Codex execution result review
- Test 6 Official Status: NOT YET VERIFIED

=== ORDER END ===
