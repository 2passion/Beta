# Order-058 — Frozen MVP Runtime Operation Entry Plan

## Metadata
- Order ID: Order-058
- Project: Beta
- Status: APPROVED
- Type: READ-ONLY INVENTORY + OPERATION PLAN
- Local SSOT Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Executor / To: Codex
- Reviewer: Claude Code
- Action: REVIEW_AND_PLAN_ONLY
- Trigger: Order-057 PASS / Local Core MVP FROZEN
- MVP Overall: PASS
- MVP Status: FROZEN
- Phase2: NOT STARTED
- GitHub Role: Freeze Snapshot / Backup / Version History, NOT SSOT

## Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
executor: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: REVIEW_AND_PLAN_ONLY
order: Order-058
project: Beta

mismatch_policy:
- recipient mismatch -> HOLD
- no Beta production write
- no runtime execution
- no architecture change
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## Purpose
FROZEN MVP를 바로 확장하거나 Phase2로 넘어가지 않고, 실제 Runtime Operation에 진입하기 위한 최소 운영 계획을 만든다.

이번 Order의 목표는 구현이 아니라 다음을 명확히 하는 것이다.

1. 현재 FROZEN MVP에서 실제 운영 가능한 실행 진입점 확인
2. 실제 운영 시 입력/출력/상태/Evidence 위치 확인
3. 첫 Runtime Operation의 최소 Scope 정의
4. 운영 중 수집할 Evidence 정의
5. 실패 시 자동 행동과 User Gate 경계 정의
6. Known Limitations KL-1~KL-3의 실제 노출 여부를 운영 Evidence로 관찰하는 방법 정의
7. 운영 전에 추가 구현이 필요한지 여부를 Evidence 기반으로 판정

## Core Principle
```text
FROZEN MVP
   ↓
Runtime Operation 준비
   ↓
최소 실제 사용
   ↓
Runtime Evidence
   ↓
문제/병목/필요성 확인
   ↓
Proposal
   ↓
Review
   ↓
필요한 경우 User Approval
   ↓
그때만 변경
```

새 기능이 필요하다고 미리 가정하지 않는다.

## Hard Boundaries
이번 Order에서 금지:
- Architecture 변경
- MVP Freeze 해제
- Phase2 시작
- EXE/PWA 제작
- Plugin/Adapter/Remote 통합
- 새 Scheduler/Agent/DB
- 기존 Rule 활성화
- Known Limitation 수정 구현
- production side effect
- Test 1~7 재실행
- 새 Runtime Run 생성
- 새 Runtime Evidence 생성
- Git commit/push
- GitHub를 SSOT로 사용

이번 Order는 READ-ONLY inventory와 운영 계획만 만든다.

## Source of Truth
우선순위:
1. FROZEN Architecture SSOT
2. Order-057 Freeze 상태
3. 7 Gates Official Evidence
4. 기존 Asset
5. 기존 Rule/Skill/Script/Validator/Generator
6. Known Limitations
7. 새로운 제안

새 제안은 SSOT가 아니다.

## Step 1 — Frozen Baseline Verification
읽기 전용으로 확인:
- MVP Overall PASS
- MVP FROZEN
- 7/7 OFFICIAL PASS
- official Gate versions
- Known Limitations 3 OPEN / ACCEPTED FOR MVP
- Phase2 NOT STARTED
- Architecture Delta NONE
- Git worktree clean 여부
- Local SSOT와 GitHub Freeze Snapshot 기준 SHA

불일치가 있으면 HOLD하고 운영 계획을 확정하지 않는다.

## Step 2 — Runtime Asset Inventory
Reuse Before Create 원칙으로 실제 운영에 사용할 수 있는 기존 Asset을 검색한다.

최소 분류:
- Classifier
- Router
- Generator
- Scheduler
- Caller
- Script
- Skill
- Rule
- Hook
- Validator
- Gate
- Evidence writer/reader
- Checkpoint/Resume
- Prevention lookup
- User Gate
- Safe Parallel

각 항목에 대해:
- 실제 파일 경로
- 현재 상태
- production 사용 가능 여부
- fixture/test 전용 여부
- 입력
- 출력
- side effect
- 필요한 권한
- 관련 Validator
- 관련 Evidence
를 표로 작성한다.

존재하지 않는 Asset을 있다고 추정하지 않는다.

## Step 3 — Production Readiness Classification
각 Asset을 다음 중 하나로 분류한다.

### READY
현재 FROZEN 계약 안에서 실제 운영에 사용 가능.

### FIXTURE_ONLY
MVP Gate 검증용이며 실제 운영 진입점으로 사용하면 안 됨.

### NEEDS_ADAPTER
핵심 계약은 있지만 실제 사용자 입력/파일 시스템과 연결하는 얇은 경계가 아직 없음.

### NOT_PRESENT
필요해 보이지만 현재 구현 자체가 없음.

`NEEDS_ADAPTER` 또는 `NOT_PRESENT`가 나와도 이번 Order에서 구현하지 않는다.

## Step 4 — Determine Minimum First Runtime Use Case
현재 Asset만으로 가능한 가장 작은 실제 운영 시나리오를 찾는다.

선정 기준:
1. FROZEN Architecture 안
2. 기존 Asset 재사용
3. 실제 side effect 최소
4. rollback/복구 쉬움
5. 개인정보/민감정보 없음
6. 삭제/외부 게시 없음
7. 결과를 Validator로 확인 가능
8. Evidence 수집 가능
9. Known Limitation 노출을 관찰할 수 있음
10. 사용자에게 내부 구조 관리를 요구하지 않음

가능한 시나리오가 없다면 억지로 만들지 말고 `RUNTIME_ENTRY_GAP`으로 보고한다.

## Step 5 — Runtime Workflow
첫 실제 운영 후보에 대해 사용자 관점 Workflow를 설계한다.

목표 UX:
```text
1. 사용자 요청
2. 시스템이 기존 Asset/상태 확인
3. 필요한 경우 승인 1회
4. 자동 실행
5. 자동 Validation
6. 허용 범위 내 자동 Recovery
7. 결과 + 다음 할 일
```

내부:
```text
Request
→ Classify
→ Reuse Search
→ Route
→ Scope/Permission Check
→ AUTO / MANUAL_APPROVAL_REQUIRED / HOLD
→ Execute
→ Validate
→ Evidence
→ Report
```

## Step 6 — Runtime Decision Rules
현재 검증된 세 판정을 그대로 사용한다.

### AUTO
다음이 모두 충족될 때만:
- 기존 Contract
- 입력/출력 명확
- 검증된 Runtime/Fixture 경로
- 제한된 write scope
- Postflight 가능
- Idempotent
- Reason Code/중단 조건 존재
- 승인 Scope 안

### MANUAL_APPROVAL_REQUIRED
- 의미/권한/범위 변경
- 외부 게시
- 삭제/이동 등 위험 side effect
- 제품/Architecture 선택

### HOLD
- SSOT 충돌
- Routing mismatch
- Evidence 불일치
- 보호 파일 위험
- UNKNOWN 안전성
- 반복 실패 / No Blind Retry 조건
- Known Limitation이 실제 안전 판정에 영향을 주는 경우

## Step 7 — Evidence Collection Plan
첫 Runtime Operation에서 최소 수집:

### Request
- request_id
- requested_goal
- approved_scope

### Decision
- classification
- selected route
- reuse result
- AUTO / MANUAL_APPROVAL_REQUIRED / HOLD
- reason code

### Run
- run_id
- task_id
- owner
- start/end
- inputs
- outputs
- side effects

### Validation
- validator
- PASS / FAIL / ERROR
- validation details

### Recovery
- fingerprint
- Prevention lookup
- root cause hypothesis
- confirmed root cause
- fix
- new Run linkage

### Evidence
- Evidence ID
- relevant hashes
- Run/Validation/Gate linkage

현재 계획과 과거 실행 사실을 섞지 않는다.

## Step 8 — Known Limitation Runtime Observation
Known Limitations를 자동 Fix하지 않고 실제 노출만 관찰한다.

### KL-1 Safe Parallel trust boundary
관찰:
- 실제 운영에서 Safe Parallel 사용 여부
- 실제 병렬 Task 존재 여부
- false concurrency 의심 사례
- 별도 OS observer 필요성이 실제로 발생하는가

### KL-2 Windows path edge
관찰:
- 사용자/외부 입력 경로가 실제 write-set에 들어오는가
- reserved/ambiguous path 발생 여부

### KL-3 External dependency completion
관찰:
- 외부 dependency를 실제 운영에서 사용하는가
- 완료 선언을 Evidence Index와 대조해야 하는 사례가 발생하는가

노출이 0이면 기능을 미리 만들지 않는다.

## Step 9 — Runtime Reporting
사용자 기본 보고는 3분 요약 View:

1. 요청한 목표
2. 승인 범위
3. 자동 실행 단계
4. 문제/자동 복구
5. Validation 결과
6. 현재 상태
7. 다음 할 일 / 사용자 판단 필요

Detailed View는 필요할 때만:
- Run IDs
- Events
- Validation
- Evidence
- Hash
- Reason Codes
- Checkpoints
- Recovery chain

새 이중 SSOT를 만들지 않는다.

## Step 10 — Stop / Expansion Criteria
운영 중 다음이 나오면 자동 확장하지 않는다.

### Continue Operation
- 기존 계약으로 정상 처리
- Validation PASS
- Known Limitation 영향 없음

### Improvement Candidate
- 반복되는 수동 단계
- 반복 병목
- 검증된 Recovery 재사용 가능
- 실제 비용/속도/품질 Evidence 존재

### User Gate
- Architecture 변경
- Scope 확대
- 새 외부 연결
- 새 권한
- 데이터 모델 변경
- Known Limitation hardening을 제품 기준으로 채택

## Required Output
A. Frozen Baseline Verification
B. Runtime Asset Inventory
C. READY / FIXTURE_ONLY / NEEDS_ADAPTER / NOT_PRESENT
D. Minimum First Runtime Use Case
E. User Workflow
F. Internal Runtime Workflow
G. AUTO / MANUAL_APPROVAL_REQUIRED / HOLD Rules
H. Evidence Collection Plan
I. Known Limitation Observation Plan
J. Runtime Reporting
K. Runtime Entry Gaps
L. Recommended First Runtime Operation
M. Files Changed — must be NONE
N. Git Changed — must be NONE
O. Phase2 Status — NOT STARTED
P. Done / Now / Next
Q. User Approval Required for first actual Runtime Operation

## Final Decision
다음 중 하나:

### READY FOR RUNTIME USER GATE
현재 FROZEN Asset만으로 최소 실제 운영을 시작할 수 있음.
→ 첫 실제 Runtime Operation Scope를 사용자에게 제시.

### RUNTIME_ENTRY_GAP
실제 운영 진입에 필요한 최소 연결부가 없음.
→ 구현하지 말고 Gap과 최소 Proposal만 보고.
→ User Gate 후 별도 Order.

### HOLD
Frozen baseline/SSOT/Evidence 불일치로 계획 자체를 확정할 수 없음.

## End State
- MVP remains FROZEN
- Phase2 remains NOT STARTED
- Git unchanged
- No production Run
- No new Runtime Evidence
- Next action depends on Order-058 decision
- Actual Runtime Operation requires explicit User Gate

=== ORDER END ===
