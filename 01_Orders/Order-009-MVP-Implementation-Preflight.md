# Beta Order --- Order-009 MVP Implementation Preflight

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-009
-   Project: Beta
-   Status: APPROVED
-   Order Type: READ-ONLY MVP Implementation Preflight
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Status: FROZEN
-   Terminology: `Terminology.md`
-   Terminology Status: FROZEN
-   Reviewer / Analyst: Claude Code
-   Write Owner for FROZEN Architecture: Codex
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

FROZEN Architecture를 변경하지 않고, Local Core MVP 구현을 시작하기 전에
실제로 지금 결정해야 하는 Implementation Decision만 식별한다.

목표는 "모든 Later 항목 결정"이 아니다.

목표: 1. MVP 첫 구현의 최소 Scope를 제안한다. 2. 구현 시작 전에 반드시
결정해야 하는 항목을 구별한다. 3. 구현 후 Evidence로 미뤄도 되는 항목을
구별한다. 4. 기존 Asset / Reference에서 재사용할 후보를 찾되 자동
승격하지 않는다. 5. MVP Test 1\~7을 실제로 검증할 최소 실행 구조를
제안한다. 6. 아직 코드를 작성하지 않는다.

## 2. 권한

이번 Order는 READ-ONLY다.

Claude Code는: - Architecture 수정 금지 - Terminology 수정 금지 -
Beta-Index 수정 금지 - Order-History 수정 금지 - 새 파일 생성 금지 -
Core / Test 코드 작성 금지 - Reference 수정 금지 - B 코드 복사 금지 -
MVP 구현 시작 금지

결과는 채팅 보고만 한다.

## 3. 기준 자료

반드시 읽는다.

1.  `C:\Obsidian\Beta\Beta-Index.md`
2.  `C:\Obsidian\Beta\00_Architecture\Harness-A-Architecture-v1.0.md`
3.  `C:\Obsidian\Beta\00_Architecture\Terminology.md`
4.  `C:\Obsidian\Beta\01_Orders\Order-History.md`
5.  `C:\Obsidian\Beta\01_Orders\Order-008-Architecture-v1.0-FROZEN-State-Transition.md`

Reference: 6. `C:\Obsidian\Beta\Reference\harness-visual-review.html` 7.
`C:\Obsidian\Beta\Reference\harness_loop_full_korean-main.zip`

Reference는 비교/Reuse 후보 탐색에만 사용한다. 자동 Asset 승격이나 코드
복사를 하지 않는다.

## 4. 실행 전 검사

-   Order 마지막 `=== ORDER END ===` 확인
-   Architecture v1.0 FROZEN 확인
-   Terminology FROZEN 확인
-   Order-008 PASS 확인
-   MVP / Runtime 구현이 아직 시작되지 않았는지 확인

전제가 다르면 BLOCK한다.

## 5. Preflight 분류

Architecture §25의 Unresolved / Later 항목을 다음 세 그룹으로 분류한다.

### DECIDE-BEFORE-MVP

첫 MVP 코드를 쓰기 전에 반드시 결정해야 함.

### DEFER-UNTIL-EVIDENCE

첫 MVP 구현/실행 Evidence가 나온 뒤 결정해도 됨.

### OUT-OF-MVP

현재 MVP Scope 밖. 제품화/외부연결 단계까지 보류.

각 항목에: - 분류 - 이유 - 결정하지 않을 경우 첫 MVP가 막히는지 - 최소
결정 수준 을 적는다.

## 6. 우선 검토할 Implementation Decisions

최소한 다음을 검토한다.

-   Local Core 구현 언어
-   MVP의 최소 물리 저장 형식
-   JSON / SQLite / Markdown / 혼합 방식
-   최소 데이터 Schema와 ID 생성 규칙
-   Validator 실행 방식
-   Evidence 최소 저장 방식
-   Task / Run / Event / Validation의 최소 필드
-   MVP Test 1\~7을 검증할 실행 시나리오
-   Fingerprint MVP 최소 형태
-   재시도 중단 기준의 MVP 최소값
-   User Approval / USER-GATE MVP 최소 기준
-   Checkpoint / Resume MVP 최소 구현 범위

다음은 기본적으로 OUT-OF-MVP 후보로 검토한다.

-   EXE UI
-   PWA
-   Plugin
-   Adapter
-   Desktop Commander 상시 연동
-   Orca
-   External Port 실제 Schema
-   외부 병렬 Agent
-   복잡한 Database
-   Terminology Validator

단, 실제로 MVP Test 1\~7을 막는다는 근거가 있으면 이유를 제시한다.

## 7. MVP 최소 Scope

FROZEN Architecture 전체를 한 번에 구현하지 않는다.

다음 질문에 답한다.

-   MVP 첫 Vertical Slice는 무엇인가?
-   어떤 역할을 실제 별도 모듈로 만들 필요가 있는가?
-   어떤 역할은 논리 책임으로만 두고 하나의 코드 경로에서 합쳐도 되는가?
-   Rule / Script / Validator로 해결할 수 있는 부분은 무엇인가?
-   Agent가 첫 MVP에 반드시 필요한가?
-   Scheduler / Caller / Gate를 처음부터 별도 프로그램으로 만들어야
    하는가?
-   파일 기반 상태 전달을 어디까지 재사용할 수 있는가?

최소비용·최대효과 관점에서 제안한다.

## 8. Reuse Before Create 검사

현재 Beta Asset과 B Reference를 기능 기준으로 비교한다.

최소 확인: - Task 기반 실행 - depends_on - 파일 / Scope 충돌 검사 - 구현
/ 검증 분리 - 병렬 Coordinator 아이디어 - Retry 제한 - STATE / LOG -
Skill 기반 절차 - 파일 기반 세션 전달

결과를 다음으로 분류한다.

-   REUSE-CANDIDATE
-   ADAPT-CANDIDATE
-   DO-NOT-USE-NOW
-   NEED-LICENSE-REVIEW

중요: Reference를 Asset으로 자동 승격하지 않는다. B의 구조/명칭/코드를
그대로 복제하지 않는다.

## 9. MVP Test 1\~7 실행 설계

각 Test에 대해 최소 실행 시나리오를 제안한다.

1.  Reuse
2.  Ownership
3.  Safe Parallel
4.  Bottleneck
5.  Prevention
6.  User Gate
7.  Resume

각 Test마다: - 입력 - Task 계획 버전 - 예상 Run - Validator - PASS
기준 - FAIL 기준 - 필요한 Evidence - 테스트를 위해 구현해야 하는 최소
기능 을 적는다.

단순 체크리스트 PASS는 금지한다.

## 10. 데이터 최소 모델

MVP에서 필요한 최소 논리 데이터만 제안한다.

기준: PROJECT / ORDER / TASK / RUN / EVENT / VALIDATION / EVIDENCE

PREVENTION / RULE / ASSET은 MVP Test에 필요한 최소 범위만 포함할 수
있다.

다음을 구별한다. - 원본 데이터 - 파생 View - 구현 편의를 위한 임시 캐시

STATE / DAG / LOG / PROGRESS / DASHBOARD를 독립 SSOT로 만들지 않는다.

## 11. 구현 구조 후보

최대 2개 후보만 비교한다.

각 후보에: - 구조 - 장점 - 단점 - MVP Test 1\~7 적합성 - 유지보수
난이도 - 외부 의존성 - 사용자 수동 작업 을 설명한다.

이번 Order에서 최종 구현 기술을 확정하지 않는다. User Gate가 필요한 결정
후보만 표시한다.

## 12. Decision 후보

Preflight 결과에서 실제로 MVP 시작 전에 필요한 Decision만 추출한다.

각 Decision: - Decision ID 후보 - Intent - 선택해야 하는 항목 - 선택지 -
최소 권장안 - 근거 - 미결정 시 영향 - User Approval 필요 여부

불필요한 Decision 문서를 늘리지 않는다.

## 13. Architecture Delta 검사

Preflight 중 FROZEN Architecture와 충돌하는 구현 요구가 발견되면:

-   구현 편의로 Architecture를 수정하지 않는다.
-   `ARCHITECTURE-DELTA`로 별도 보고한다.
-   위치
-   충돌 내용
-   왜 MVP가 막히는지
-   Change Proposal 필요 여부 를 기록한다.

없으면: `NONE`

## 14. 결과 보고 형식

# Order-009 MVP Implementation Preflight 결과

### 현재 판정

READY / READY WITH DECISIONS / NOT READY / BLOCKED

### FROZEN 기준 확인

-   Architecture v1.0 FROZEN
-   Terminology FROZEN
-   Order-008 PASS
-   MVP 구현 미착수

### DECIDE-BEFORE-MVP

표 형식.

### DEFER-UNTIL-EVIDENCE

표 형식.

### OUT-OF-MVP

표 형식.

### MVP 최소 Scope

첫 Vertical Slice와 포함/제외 범위.

### Reuse Map

REUSE / ADAPT / DO-NOT-USE-NOW / NEED-LICENSE-REVIEW.

### MVP Test 1\~7

각 Test의 실행 시나리오와 Evidence.

### 최소 데이터 모델

원본 / 파생 View / 임시 캐시 구별.

### 구현 구조 후보

최대 2개.

### Decision 후보

MVP 시작 전에 실제 필요한 것만.

### Architecture Delta

NONE 또는 상세.

### 파일 변경 확인

모든 Beta 파일: NO 새 파일: NO

### Done

MVP Implementation Preflight 완료.

### Now

FROZEN Architecture 기준으로 MVP 착수 전 Decision 검토.

### Next

필요 Decision에 대한 ChatGPT Project Beta 검토 → 필요한 경우 User
Approval → 승인 후 별도 MVP Implementation Order

### 사용자 승인 필요

Preflight 결과에 따라 표시.

## 15. 종료 조건

분석과 보고 후 종료한다.

다음을 자동 시작하지 않는다. - 파일 수정 - Decision 확정 - Architecture
변경 - MVP 구현 Order 생성 - MVP 구현 - 코드 작성 - Test 작성 -
EXE/PWA - Plugin/Adapter

결과를 ChatGPT Project Beta에 전달하고 다음 판단을 기다린다.

=== ORDER END ===
