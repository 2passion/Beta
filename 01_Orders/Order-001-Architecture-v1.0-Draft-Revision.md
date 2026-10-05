# Beta Order --- Order-001 Architecture v1.0 DRAFT Revision

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-001
-   Project: Beta
-   Status: APPROVED
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Version: v1.0
-   Architecture Status: DRAFT
-   Write Owner: Codex
-   Reviewer: Claude Code
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Claude Code Cross Review의 Blocker 1건과 ChatGPT Project Beta가 승인한
수정사항만 최소 범위로 반영한다. Architecture를 전면 재작성하지 않는다.

## 2. 대상

수정: -
`C:\Obsidian\Beta\00_Architecture\Harness-A-Architecture-v1.0.md` -
`C:\Obsidian\Beta\Beta-Index.md` (상태 정보만 최소 갱신)

읽기: - `C:\Obsidian\Beta\01_Orders\Order-History.md`

수정 후에도 Version `v1.0`, Status `DRAFT`를 유지한다.

## 3. 실행 전 완전성 검사

-   이 Order 전체를 먼저 읽는다.
-   마지막 줄의 `=== ORDER END ===` 존재를 확인한다.
-   종료 마커가 없으면 실행하지 않고 BLOCK한다.
-   Architecture 수정 전 크기와 SHA-256을 기록한다.

## 4. 승인된 변경

### Change 1 --- 필수 Validator 우회 방지

-   필수 Validator 목록은 Run 시작 전에 Task 계획 버전에 고정한다.
-   목록이 비어 있으면 Task PASS 불가.
-   Fix로 Validator 목록/완료 기준을 약화·삭제해 PASS하는 것을 금지.
-   기준 변경은 Task 계획 버전 변경으로 기록하고 New Run으로 재검증.
-   Validator는 실행자의 자기평가가 아니라 실제 결과와 고정 기준을 검사.
-   구체적인 Validator 독립 프로세스는 Unresolved.

### Change 2 --- 상태 3축 분리

Execution Status / Validation Status / Gate Decision을 분리한다. RUN은
실제 실행 시도라는 개념을 유지한다. 물리 Schema는 미확정.

### Change 3 --- Recovery 진입 보완

-   Validation FAIL → 결과/제품 Recovery
-   Validator ERROR → Validator/검사환경 Recovery
-   Execution ERROR → Caller/실행환경/Permission Recovery
-   기준 문제 → Decision 또는 필요한 USER-GATE Validator ERROR는 제품
    재시도 횟수에 포함하지 않는다.

### Change 4 --- ORDER / DECISION / APPROVAL

-   ORDER: 승인된 작업 지시/실행 계약
-   DECISION: 중요한 설계·운영 판단과 근거
-   APPROVAL: 승인 사실 기록 물리 구조는 미확정.

### Change 5 --- RUN ↔ Task 계획 버전

각 RUN은 실행 당시 Task 계획 버전을 추적한다.

### Change 6 --- 병렬 Write Scope

Task 계약은 Write Owner, Write Scope, Shared Resources, depends_on을
표현할 수 있어야 한다. Scope 밖 쓰기는 BLOCK 또는 안전한 순차 실행으로
내린다. 공유 원본 기록의 쓰기 책임은 일원화한다. Coordinator 구현은
확정하지 않는다.

### Change 7 --- Gate 용어 정리

-   Gate = Runtime 판정
-   USER-GATE = 사용자 결정 필요 상태
-   MVP 검증 = MVP Test 1\~7
-   문서 검토 = Review Checklist / Architecture Review

MVP Test 1 Reuse / 2 Ownership / 3 Safe Parallel / 4 Bottleneck / 5
Prevention / 6 User Gate / 7 Resume.

### Change 8 --- 경량 Workflow

모든 논리 역할을 별도 단계로 강제하지 않는다. 작은 Task는 역할 통합/생략
가능. 최소 계약: Reuse 확인 → Task 계약 → Run 기록 → 필요한 Validation →
Gate 판정 → Evidence. 자동 최대는 Layer 최대/Agent 최대가 아니다.

### Change 9 --- Beta 운영과 Harness Runtime 분리

Harness 원칙은 One Task One Write Owner. 현재 Beta 운영은 Codex=Write
Owner, Claude Code=Reviewer이며 영구 Runtime 구성요소가 아니다.
Validation과 Review를 구별한다.

### Change 10 --- 중복 SSOT 정리

`Beta-Index.md` 소유: 현재 Architecture/상태, Done/Now/Next, 주요 문서
위치. Architecture 소유: 설계 계약, 데이터 구조, 역할, Workflow,
Validation, Recovery, Prevention, 원칙, Architecture Unresolved. Visual
Guide는 파생 설명 자료. Architecture 3분 요약은 비규범 요약이며 충돌 시
본문 계약 우선. Architecture 내부 Done/Now/Next는 Index 참조로 축소한다.

### Change 11 --- Unresolved 재편

핵심 Unresolved 유지: - Fingerprint 정규화 - 재시도/자동 복구 한도 -
Prevention→Rule 세부 기준 - Approval 재확인 조건 - Checkpoint Side
Effect 재검증 세부 계약 - Validator 독립성 실제 프로세스

지금 원칙 확정: - 과거 Run/Event/Evidence 덮어쓰기 금지. 정정은 새
기록으로 원본과 연결. - Validator는 자기평가/추정 원인이 아니라 실제
결과와 고정 기준 검사.

Later / Implementation Decisions: 구현 언어, 저장 형식,
JSON/SQLite/Markdown 선택, Schema/ID 세부, EXE UI, Agent 인터페이스,
Rule 만료/충돌, Runtime 비용 단위, External Port 실제 Schema, PWA 통신,
Orca, B 코드 재사용 시 세부 라이선스/의존성.

### Change 12 --- Active Rule 승격

Active 전환에는 Evidence + Regression Validation + Gate Decision 필요.
전역/Core Scope는 USER-GATE 필요. Local Scope 자동 활성화 세부 기준은
Unresolved.

### Change 13 --- Decision 기록 경계

Architecture=현재 결정 결과/계약. 향후 Decision 기록=Intent/대안/선택
이유/근거/영향. Evidence=실제 발생 사실 증명. 이번 Order에서
Decisions.md 생성 금지.

### Change 14 --- MVP Test 공통 조건

모든 MVP Test 판정은 입력/계획 버전, Run ID, Validation 결과, Evidence
위치를 연결한다. 체크 표시만으로 PASS 금지. Test 4 전 재시도/중단 기준
필요. Test 6 전 사용자 승인 최소 기준 필요.

### Change 15 --- External Port 최소화

External Port 경계는 유지한다.
`A Local Core → External Port → Adapter → Plugin / Remote / API / External Tool`
세부 항목은 Design Notes 수준이며 실제 Schema/장애 격리는 Later로 이월.
Adapter 구현 금지.

## 5. 이번 Order에서 추가하지 않을 항목

-   비차단 알림
-   기한 있는 Standing Approval
-   여러 Task 전체 Fingerprint 집계
-   Orca 구현
-   B 실패 5분류 직접 복제
-   B Coordinator 복제
-   B 코드 복사

## 6. KEEP

A\>B 경계, B=Reference, TASK/RUN 분리, FAIL Run 보존, FAIL/ERROR 구별,
파생 View, Rule/Hook 비직렬, 독립성 불명확 시 순차/WAIT, Root Cause
가설/확정 구별, Fix 즉시 전역 Rule 승격 금지, Checkpoint/Chunk 구별,
Side Effect 재검증, 사용자 Workflow, Out of Scope를 유지한다.

## 7. Beta-Index 최소 갱신

Architecture 수정/자체 Validation PASS 후에만 갱신한다. - Current
Architecture: Harness-A-Architecture-v1.0.md / v1.0 / DRAFT - Done:
Workspace, Reference 이전, DRAFT 최초 작성, Claude Cross Review, 승인
수정 반영 - Now: v1.0 DRAFT 재검증 완료 / Claude Code 재검토 대기 -
Next: Claude Code 재검토 → Blocker 해소 확인 → 필요 시 최소 수정 → v1.0
REVIEW 후보 Architecture 계약을 Index에 복사하지 않는다.

## 8. 금지

Version 변경, REVIEW/FROZEN 승격, Claude Code 호출, Decisions.md/Visual
Guide/B-Reference-Map 생성,
Intake/Classifier/MVP/EXE/PWA/Plugin/Adapter/Remote/Orca/Git 구현,
Reference 수정, B 코드 복사, Architecture 전면 재작성 금지.

## 9. Validation

### Blocker

-   [ ] 필수 Validator 목록 Run 전 고정
-   [ ] 빈 목록이면 PASS 불가
-   [ ] Fix로 기준 약화 불가
-   [ ] 기준 변경은 Task 계획 버전 변경
-   [ ] Validator 자기평가 의존 금지

### 데이터

-   [ ] Execution / Validation / Gate 구별
-   [ ] RUN ↔ Task 계획 버전 연결
-   [ ] ORDER / DECISION / APPROVAL 위치 설명
-   [ ] Run/Event/Evidence 덮어쓰기 금지
-   [ ] 정정은 새 기록

### Workflow

-   [ ] 경량 Workflow 가능
-   [ ] 최소 필수 계약 명시
-   [ ] FAIL / Validator ERROR / Execution ERROR 분기
-   [ ] 기준 문제 Decision/USER-GATE 경로
-   [ ] 병렬 Write Scope / Shared Resources 고려
-   [ ] Scope 밖 쓰기 처리

### 역할/용어

-   [ ] Beta 운영과 Harness Runtime 구별
-   [ ] Validation과 Review 구별
-   [ ] Gate / USER-GATE / MVP Test / Review Checklist 구별
-   [ ] 기존 12개 역할 경계 유지

### SSOT

-   [ ] Index가 Done/Now/Next 소유
-   [ ] Architecture가 설계 계약 소유
-   [ ] 3분 요약 비규범 표시
-   [ ] 중복 상태 수동 관리 제거

### Unresolved / Rule

-   [ ] 핵심 Unresolved와 Later 구별
-   [ ] 기록 정정 원칙 확정
-   [ ] Validator 독립성 원칙 확정
-   [ ] Active Rule에 Evidence + Regression Validation + Gate
-   [ ] 전역/Core Rule은 USER-GATE

### MVP / External

-   [ ] MVP Test 1\~7 명칭과 의미 유지
-   [ ] 입력/계획 버전 + Run ID + Validation + Evidence 연결
-   [ ] 단순 체크 PASS 금지
-   [ ] External Port 경계 유지
-   [ ] 세부 Schema는 Later
-   [ ] Adapter 구현 없음

### Scope

-   [ ] Version v1.0 유지
-   [ ] Status DRAFT 유지
-   [ ] 전면 재작성 없음
-   [ ] Index 외 기존 파일 수정 없음
-   [ ] 새 파일 생성 없음
-   [ ] Reference 변경 없음
-   [ ] LATER 기능 추가 없음
-   [ ] Claude 재검토 자동 시작 없음

필수 Validation 하나라도 실패하면 PASS로 판정하지 않는다. 검사 자체
실패는 ERROR로 구별한다.

## 10. 수정 전후 Evidence

보고: - 수정 전/후 Architecture 크기와 SHA-256 - 실제 변경 절 - 추가
계약 - 제거/축소한 중복 - Beta-Index 변경 부분 - UTF-8 및 한글 문자오염
여부 - 변경 파일 목록 - 새 파일 목록

## 11. 결과 보고

다음 형식으로 보고한다.

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### Architecture

Version: v1.0 Status: DRAFT

### Blocker 해결

Review-Blocker-001: RESOLVED / NOT_RESOLVED

### Approved Change 1\~15

각 항목 PASS / FAIL + 짧은 근거.

### Validation

위 체크리스트 전체 결과.

### Done

승인된 Cross Review 수정사항 최소 반영.

### Now

Architecture v1.0 DRAFT / Claude Code 재검토 대기.

### Next

Claude Code READ-ONLY 재검토 → Blocker 해소 및 새 Blocker 확인 →
PASS이면 v1.0 REVIEW 후보.

## 12. 종료 조건

승인된 변경만 반영하고 전체 Validation 및 Index 최소 갱신이 끝나면
종료한다. PASS해도 Claude Code 호출, REVIEW/FROZEN 승격, Visual Guide
생성, MVP/제품 구현을 시작하지 않는다.

=== ORDER END ===
