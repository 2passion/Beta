# Beta Order --- Order-016 MVP Test Implementation Sequence Review

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-016
-   Project: Beta
-   Status: APPROVED
-   Order Type: READ-ONLY MVP Test Sequence Review
-   Architecture: Harness-A-Architecture-v1.0.md / FROZEN
-   Terminology: Terminology.md / FROZEN
-   Baseline: Local Core MVP Phase 1 CLOSED
-   Reviewer / Analyst: Claude Code
-   File Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

Phase 1 Review/Fix 수정 루프 종료 후, FROZEN Architecture의 MVP Test
1\~7 구현 순서를 확정하기 위한 READ-ONLY 검토다. 구현하지 않는다.

목표: 1. 각 Test의 공식 의미 확인 2. Phase 1 기능/Evidence 재사용 3.
추가 최소 기능 식별 4. 의존관계 구성 5. 가장 작은 다음 구현 단위 제안 6.
불필요한 Agent/Plugin/병렬/DB 방지

## 2. 권한

READ-ONLY. Core/Test/Evidence/Architecture/Terminology/Index/History
수정, 새 파일, 코드 작성, Phase 2/MVP Test 구현, Architecture Decision
확정, Git 금지.

## 3. Precondition

-   Architecture v1.0 FROZEN
-   Terminology FROZEN
-   Order-015 PASS
-   shared timeout RESOLVED
-   Phase 1 Review/Fix Loop CLOSED
-   Phase 2 미착수
-   현재 Core/Test/Evidence 상태 확인 다르면 BLOCKED.

## 4. 읽을 대상

SSOT: Architecture, Terminology, Beta-Index, Order-History. Phase 1:
02_Core/beta_core/\*.py, 03_Tests/test_phase1.py, fixtures,
04_Evidence/phase1의 Event/Index/plan 1.0\~1.3 Evidence. 최근 검증:
Order-010\~015. B Reference는 반드시 필요할 때만 읽고 자동 채택 금지.

## 5. 공식 번호 유지

-   MVP Test 1 --- Reuse
-   MVP Test 2 --- Ownership
-   MVP Test 3 --- Safe Parallel
-   MVP Test 4 --- Bottleneck
-   MVP Test 5 --- Prevention
-   MVP Test 6 --- User Gate
-   MVP Test 7 --- Resume

Implementation Sequence와 공식 번호를 구별한다.

## 6. 각 Test 검토 형식

각 Test에: - Official Test ID / Name - Architecture 목적 - Phase 1
기반 - 이미 증명된 부분 - 미증명 부분 - 추가 최소 기능 - Fixture -
Validator - PASS / FAIL 기준 - Evidence - 선행 의존성 - 난이도
LOW/MEDIUM/HIGH - 사용자 승인 필요 여부 - 지금/나중 구현 권고

Phase 1 단위 Test를 MVP Test 전체 PASS로 간주 금지.

## 7. Test 1 --- Reuse

검토: - Reuse Before Create Runtime 증명 방식 - Asset 검색 결과
Event/Evidence 최소 구조 - Asset 없을 때 신규 생성 허용 -
Asset/Reference 구별 - Asset Registry 실제 필요 여부와 최소 필드 복잡한
Asset DB 금지.

## 8. Test 2 --- Ownership

Phase 1의 write_owner, 계약 사전 BLOCK, Scope를 재사용. 검토: - 이미
증명한 범위 - 추가 필요 범위 - 두 Owner 합성 시 BLOCK Evidence - Scope
밖 쓰기를 Ownership에 포함할지 Safe Parallel과 분리할지

## 9. Test 3 --- Safe Parallel

후반 구현 후보. 검토: depends_on, write_scope, shared_resources, 파일
겹침, 공유 Runtime 자원, 독립성 불명확 시 순차/WAIT. 실제 병렬 Agent
불필요. 결정적 합성 Task/process로 검증. 새 Coordinator/File Lock 기본
제안 금지.

## 10. Test 4 --- Bottleneck

검토: - Fingerprint 최소 구조 - 동일 실패 반복 감지 - 새 변경 근거 없는
Blind Retry 차단 - Retry 숫자는 Test Fixture 값 - FAIL / Validator ERROR
/ Execution ERROR 구별 - Event/Evidence Order-013 FAIL→014 Fix→015
PASS는 참고 Evidence일 뿐 Runtime Test PASS를 대신하지 않음.

## 11. Test 5 --- Prevention

Proposed Prevention / Verified Fix / Prevention Candidate / Rule 승격을
구별. 최소 검증: - 과거 Verified Fix 검색 - 다음 합성 Task에서 재사용 -
Validator 확인 - Evidence 연결 Terminology 표준화는 아직 Proposed
Prevention이므로 자동 Fixture 사용 금지.

## 12. Test 6 --- User Gate

승인된 최소 사유: 1. Write Scope 확대 2. 권한 확대 3. 필수
Validator/완료 기준 약화 4. 재시도 한도 초과 5. 전역/Core Rule 활성화

검토: - 중요할 때만 USER-GATE - 일반 작업 자동 진행 - Approval을 Task
ID/plan_version/action/scope에 연결 - plan_version 변경 시 이전 Approval
자동 재사용 금지 UI 불필요, CLI/Fixture로 검증.

## 13. Test 7 --- Resume

Phase 1 Checkpoint + state hash 재사용. 검토: - 중단 후 New Run - 마지막
Checkpoint - 실제 Side Effect 재검증 - 이미 적용된 Side Effect skip -
Checkpoint만 있고 Side Effect 없으면 재실행 - 완료 작업 처음부터 반복
금지 합성 Fixture 사용.

## 14. Implementation DAG

다음 후보를 실제 코드/Evidence로 검증한다.

Foundation → MVP Test 2 Ownership → MVP Test 1 Reuse → MVP Test 4
Bottleneck → MVP Test 5 Prevention → MVP Test 6 User Gate → MVP Test 7
Resume → MVP Test 3 Safe Parallel

더 작은 의존관계가 가능하면 수정 제안. 병렬 구현 후보는 독립성 명확할
때만 표시.

## 15. 다음 구현 Order 후보

한 번에 1\~7 전체 구현 금지. 최대 2개 후보. 각 후보: - 대상 Test - 지금
적합한 이유 - 기존 코드 재사용 - 예상 새 파일 - 예상 Test 수 범위 -
Evidence - Risk - User Approval 필요 여부

최소비용·최대효과 기준으로 하나 권장.

## 16. Asset / Data 최소화

새 구조 전에 확인: - 기존 JSON/JSONL 충분? - Registry 꼭 필요? - 새
Entity 필요, 아니면 Event payload로 충분? - 파생 View를 SSOT로 만들고
있나? - Test 때문에 Production 구조 과설계하나? SQLite/복잡
DB/Agent/Plugin/Adapter 기본 제외.

## 17. Decision Gate

사용자 승인 NO: - D-MVP-001\~005 승인 범위 - FROZEN Architecture Test
그대로 구현 - Scope 확대 없음

YES: - Architecture 의미 변경 - USER-GATE 기준 변경 - 외부 의존성/권한
추가 - 새로운 저장 기술 - Scope 확대

불필요한 질문 금지.

## 18. Architecture Delta

충돌 발견 시 ARCHITECTURE-DELTA 보고. 없으면 NONE. Architecture 수정
금지.

## 19. 결과 보고

# Order-016 MVP Test Implementation Sequence Review 결과

### 현재 판정

READY / READY WITH DECISION / NOT READY / BLOCKED

### Phase 1 Baseline

재사용 가능한 Core/Test/Evidence.

### MVP Test Matrix

  -----------------------------------------------------------------------
  Official    이미 확보   추가 필요   의존성      난이도      사용자 승인
  Test                                                        
  ----------- ----------- ----------- ----------- ----------- -----------

  -----------------------------------------------------------------------

### Test 1\~7

각각 §6 형식.

### Implementation DAG

공식 번호를 유지한 구현 순서.

### 다음 구현 Order 후보

최대 2개.

### 권장 후보

하나.

### Asset / Data 변경

최소안.

### Architecture Delta

NONE 또는 상세.

### 사용자 승인 필요

YES / NO + 이유.

### 파일 변경 확인

모든 Beta 파일: NO 새 파일: NO

### Done

MVP Test 1\~7 구현 순서 검토 완료.

### Now

FROZEN Architecture + Phase 1 CLOSED 기준 다음 구현 준비.

### Next

권장 후보 ChatGPT Beta 검토 → 필요 시 User Approval → 다음 구현 Order.

## 20. 종료 조건

분석/보고 후 종료. 어떤 Beta 파일도 수정하지 않는다. MVP Test 구현,
Phase 2, Architecture 변경, Registry 생성, Agent/Plugin/Adapter,
제품화를 자동 시작하지 않는다.

=== ORDER END ===
