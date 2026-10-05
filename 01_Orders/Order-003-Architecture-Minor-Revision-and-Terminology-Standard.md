# Beta Order --- Order-003 Architecture Minor Revision and Terminology Standard

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-003
-   Project: Beta
-   Status: APPROVED
-   Order Type: Architecture Minor Revision + Terminology SSOT Draft
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Version: v1.0
-   Architecture Status: DRAFT
-   Write Owner: Codex
-   Reviewer: Claude Code
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Order-002 재검토에서 확인된 최소 수정사항을 반영하고, 반복된 용어 혼동을
예방하는 Terminology SSOT를 만든다.

목표: 1. Validator 기준 변경 우회 가능성을 닫는다. 2. Gate 계열 잔여
용어를 표준화한다. 3. Order-History View Drift를 실제 상태에 맞춘다. 4.
Canonical Term을 한 곳에서 정의하여 문자 오류·오탐·잘못된
Routing/Validation·유지보수 병목을 예방한다. 5. 용어를 Intent / ADR /
Result / Evidence에 추적 가능하게 연결한다.

이번 작업은 Architecture 전면 재작성이나 Terminology Validator 구현이
아니다.

## 2. ADR --- Terminology 표준화

**Decision:** `C:\Obsidian\Beta\00_Architecture\Terminology.md`를
Architecture 용어 SSOT DRAFT로 생성한다.

**Reason:** Order-002에서 `Review Gate`, `MVP Gate`, `Decision Gate` 등
용어 Drift가 실제 Evidence로 확인됐다. 같은 정의를 여러 문서에
독립적으로 반복하면 SSOT가 분산된다.

**SRP 소유권:** - Terminology = 무슨 뜻인가 - Architecture = 어떻게
설계됐는가 - Decision/ADR = 왜 결정했는가 - Evidence = 실제로 무엇이
확인됐는가 - Beta-Index = 현재 어디까지 왔는가

**Result:** Terminology에는 Intent/ADR/Result/Evidence 본문을 복사하지
않고 추적 Reference만 연결한다. Terminology Validator는 Prevention
Candidate이며 이번 Order에서는 구현하지 않는다.

## 3. 실행 전 검사

-   Order 전체를 읽고 마지막 `=== ORDER END ===`를 확인한다.
-   없으면 실행하지 않고 BLOCK한다.
-   Architecture가 `v1.0 / DRAFT`인지 확인한다.
-   수정 전 Architecture, Beta-Index, Order-History의 크기와 SHA-256을
    기록한다.

## 4. 읽기 대상

1.  `C:\Obsidian\Beta\Beta-Index.md`
2.  `C:\Obsidian\Beta\00_Architecture\Harness-A-Architecture-v1.0.md`
3.  `C:\Obsidian\Beta\01_Orders\Order-History.md`
4.  `C:\Obsidian\Beta\01_Orders\Order-001-Architecture-v1.0-Draft-Revision.md`
5.  `C:\Obsidian\Beta\01_Orders\Order-002-Architecture-v1.0-Draft-ReReview.md`

## 5. Write Scope

수정 허용: - `00_Architecture\Harness-A-Architecture-v1.0.md` -
`Beta-Index.md` - `01_Orders\Order-History.md`

신규 생성 허용: - `00_Architecture\Terminology.md`

그 외 파일은 생성·수정하지 않는다.

## 6. Minor Revision

### 6.1 Validator 판정 로직

Architecture에 다음 계약을 중복 없이 추가한다.

> Validator의 판정 기준 또는 판정 로직 변경도 Validation 기준 변경으로
> 취급하며, Task 계획 버전 변경과 New Run 재검증 대상이다.

### 6.2 기준 약화 승인 경계

다음을 추가한다.

> 필수 Validator 또는 완료 기준을 약화·축소하는 Task 계획 변경은 Write
> Owner 단독으로 확정할 수 없다. Gate 판정을 거치며 필요한 경우
> USER-GATE로 올린다.

Validator 추가·기준 강화·의미가 변하지 않는 중립 변경까지 모두
USER-GATE로 강제하지 않는다. 세부 Approval 기준은 기존 Unresolved를
따른다.

### 6.3 Gate 계열 용어

Architecture에서 문맥을 확인하여 정리한다. - `Review Gate` →
`Architecture Review Checklist` - 문서 검토 의미의 `MVP Gate` →
`MVP Test` - Runtime 사용자 결정 의미의 `Decision Gate` →
`USER-GATE 상황` 또는 `USER-GATE` - `MVP Test 6 — User Gate`는 시험
이름이므로 유지 - 일반적인 `User Approval`은 Runtime USER-GATE로 강제
변환하지 않음 - 실제 Runtime Gate를 의미하는 일반 표현은 불필요하게
변경하지 않음 - 목차와 본문 제목을 일치시킨다.

### 6.4 Beta-Index 용어

-   `MVP 7개 Gate 정의` → `MVP Test 1~7 정의`
-   `## 10. 다음 Gate` → `## 10. 다음 단계`
-   Now/Next를 실제 상태에 맞게 최소 갱신
-   Architecture 계약을 Index에 복사하지 않음

### 6.5 Order-History Drift

-   Order-001 Result → `PASS`
-   Order-002 행 추가: READ-ONLY Re-Review / Claude Code /
    `PASS WITH MINOR REVISION`
-   Order-003 행 추가: Architecture Minor Revision + Terminology
    Standard / Codex / Claude Code / 실행 중에는 RUNNING, 완료 후 실제
    결과
-   Pre-Order Task 1\~4는 변경하지 않는다.

## 7. Terminology.md 계약

### 7.1 Header

최소: - Project: Beta - Document: Terminology Standard - Role:
Architecture Terminology SSOT Draft - Status: DRAFT - Parent
Architecture: Harness-A-Architecture-v1.0.md - Write Owner: Codex -
Reviewer: Claude Code

Terminology는 용어 의미를 소유하며 Architecture 설계 계약을 대신하지
않는다.

### 7.2 Term 구조

각 표준 용어는 최소한 다음을 가진다. - Term ID - Canonical Name - Korean
Name 또는 설명용 한글명 - Description - Purpose - Responsibility -
Allowed Aliases - Prohibited / Deprecated Terms - Not Same As - Trace
References: Intent / ADR or Decision / Result / Evidence

Trace Reference에는 본문을 복사하지 않고 문서·Order·Review·Architecture
절 등 추적 가능한 참조만 기록한다. JSON Schema는 만들지 않는다.

### 7.3 최소 Canonical Terms

다음을 최소 등록한다.

Gate, USER-GATE, MVP Test, Architecture Review, Review Checklist,
Validation, Validator, Review, Order, Task, Run, Event, Evidence, Asset,
Reference, Archive, Prevention, Rule, Hook, Skill, Script, Agent,
Classifier, Router, Generator, Scheduler, Caller, Checkpoint, Chunk,
Intent, ADR, Result, Decision, Approval.

Architecture에서 이미 쓰는 핵심 용어를 추가할 수 있으나 새로운 Runtime
기능을 만들지 않는다.

### 7.4 핵심 표준 정의

**Gate:** Runtime에서 Validation, Permission, Approval, Risk, Evidence를
바탕으로 다음 진행 여부를 판정하는 논리 역할. 결정값은 PROCEED / WAIT /
BLOCK / USER-GATE. MVP Test나 Architecture Review와 다르다.

**USER-GATE:** 사용자 결정이 필요한 Runtime 상태. 일반 문서 User
Approval, Architecture Review, MVP Test와 다르다.

**MVP Test:** MVP에서 Architecture 원칙이 실제 실행 Evidence로
검증되는지 확인하는 시험. Runtime Gate가 아니다.

**Architecture Review:** Architecture의 일관성·완전성·책임
경계·누락·모순을 검토하는 활동. Validation이나 Runtime Gate가 아니다.

**Validation:** 실제 결과를 사전에 고정된 기준과 비교하는 검사. Review와
다르다.

**Review:** 설계·코드·Decision의 적절성·일관성·완전성을 검토하는 활동.
Validation과 다르다.

**Asset:** Beta에서 실제 실행·재사용하도록 승인된 자산. **Reference:**
현재 설계·비교 참고자료이며 자동으로 Asset이 아니다. **Archive:** 현재
기준에서는 사용하지 않지만 추적·복구를 위해 보존하는 과거자료.

### 7.5 Alias / 문자 오류 정책

-   Canonical Name을 기본 저장·표시 용어로 사용한다.
-   명시된 Allowed Alias만 Canonical Term으로 정규화할 수 있다.
-   미등록 유사어·오타·축약어를 AI가 임의로 Canonical Term으로 확정하지
    않는다.
-   불명확한 용어는 WARNING 또는 HOLD 후보로 취급한다.
-   프로젝트 내부 약어를 최소화한다.
-   과거 Evidence/Order 원문을 현재 표준에 맞추기 위해 조용히 덮어쓰지
    않는다.
-   Deprecated 예: `Review Gate`, `MVP Gate`, Runtime 사용자 결정 의미의
    `Decision Gate`.

### 7.6 Traceability

흐름: `Intent → ADR / Decision → Result → Evidence`

책임: - Intent = 왜 시작했는가 - ADR/Decision = 대안과 선택 이유 -
Result = 결정 결과 무엇이 바뀌었는가 - Evidence = 실제로 무엇이
확인됐는가

Terminology에는 내용을 중복 복사하지 않고 Reference만 연결한다.

첫 Evidence 최소 연결: - Order-002 Re-Review의 용어 잔여 발견 -
Order-003의 표준화 결정과 수정 결과

### 7.7 SSOT / SRP

-   Terminology.md → 용어 의미와 표준 표현
-   Architecture → 설계 계약
-   Beta-Index → 현재 Architecture / Done / Now / Next / 주요 위치
-   Order-History → 시간순 Timeline View
-   Order → 승인된 실행 계약
-   Evidence → 실제 실행·검증 사실
-   향후 Decision 기록 → Intent / Alternatives / Decision / Reason /
    Impact

같은 정의를 여러 문서에서 독립 SSOT로 관리하지 않는다. Architecture에는
이해에 필요한 최소 문맥 설명을 유지할 수 있다.

### 7.8 Prevention Candidate

기록: - Problem: Gate 계열 용어 혼재가 Review에서 반복 탐지됨 - Root
Cause Hypothesis: Canonical Terminology SSOT 부재 - Verified Fix: 아직
아님 - Candidate: Terminology SSOT + 향후 Terminology Validator

이번 Order에서 Validator를 구현하지 않는다. 여러 Order에서 재발 방지
Evidence가 확보된 뒤 Prevention/Rule 승격을 검토한다.

## 8. 하지 말 것

-   Architecture Version 변경
-   Architecture/Terminology를 REVIEW 또는 FROZEN으로 승격
-   Terminology Validator 구현
-   Python/JavaScript/SQL/JSON Schema 구현
-   별도 ADR/Decisions.md 생성
-   Visual Guide 생성
-   MVP/EXE/PWA 구현
-   Plugin/Adapter 구현
-   Reference 수정
-   B 코드 복사
-   Claude Code 자동 호출

## 9. Validation

### Architecture

-   [ ] Validator 판정 기준/로직 변경도 기준 변경으로 취급
-   [ ] 로직 변경 시 Task 계획 버전 변경 + New Run 재검증
-   [ ] 기준 약화/축소를 Write Owner 단독 확정 금지
-   [ ] Gate 판정 및 필요한 경우 USER-GATE
-   [ ] `Review Gate` 잔여 제거
-   [ ] 문서 검토 의미의 `MVP Gate` 잔여 제거
-   [ ] Runtime 사용자 결정 의미의 `Decision Gate` 잔여 제거
-   [ ] 목차와 본문 제목 일치

### Terminology

-   [ ] Terminology.md 존재 / DRAFT
-   [ ] 최소 Canonical Terms 등록
-   [ ] Description / Purpose / Responsibility
-   [ ] Allowed Alias / Deprecated 정책
-   [ ] Not Same As 관계
-   [ ] Intent / ADR / Result / Evidence Trace Reference 구조
-   [ ] 중복 본문 대신 Reference 연결
-   [ ] 미등록 오타/유사어 자동 확정 금지
-   [ ] Terminology Validator 미구현

### History / Index

-   [ ] Order-001 = PASS
-   [ ] Order-002 = PASS WITH MINOR REVISION
-   [ ] Order-003 행 존재
-   [ ] Pre-Order Task 1\~4 변경 없음
-   [ ] Index `MVP Test 1~7` 표준화
-   [ ] Index `다음 단계` 표준화
-   [ ] Index Now / Next 실제 상태와 일치

### Scope

-   [ ] Architecture v1.0 / DRAFT 유지
-   [ ] 허용 파일 외 수정 없음
-   [ ] Reference 변경 없음
-   [ ] Runtime 기능 추가 없음
-   [ ] 새 구현 코드 없음
-   [ ] Claude Code 자동 호출 없음

필수 Validation 하나라도 실패하면 PASS로 판정하지 않는다. 검사 자체
실패는 ERROR로 구별한다.

## 10. 결과 보고

다음 형식으로 보고한다.

# Order-003 실행 결과

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### Architecture

Version: v1.0 Status: DRAFT

### Minor Revision

-   Validator 로직 변경 계약: PASS / FAIL
-   기준 약화 승인 경계: PASS / FAIL
-   Gate 계열 용어 정리: PASS / FAIL
-   Index 용어 정리: PASS / FAIL
-   History Drift 정정: PASS / FAIL

### Terminology SSOT

-   생성 여부
-   등록 Term 수
-   Canonical / Alias / Deprecated 정책
-   Traceability 구조
-   Prevention Candidate 상태

### Validation

위 체크리스트 전체 결과.

### Evidence

-   수정 전/후 Architecture 크기와 SHA-256
-   수정 전/후 Index 크기와 SHA-256
-   수정 전/후 History 크기와 SHA-256
-   Terminology 크기와 SHA-256
-   UTF-8 / 한글 문자오염 여부
-   변경/생성 파일 목록

### Done

Order-002의 Minor Revision과 Terminology SSOT DRAFT 생성 완료.

### Now

Architecture v1.0 DRAFT / Terminology DRAFT. Claude Code 최소 범위
READ-ONLY 확인 대기.

### Next

Claude Code가 Order-003 변경 범위만 확인. PASS하면 ChatGPT Project Beta
검토 후 v1.0 REVIEW 후보.

### 사용자 승인 필요

NO

현재는 DRAFT 검토 단계이며 FROZEN 승인을 요청하지 않는다.

## 11. 종료 조건

승인된 변경, Terminology DRAFT, History/Index 최소 갱신, 전체
Validation까지 완료하면 종료한다.

PASS하더라도 다음을 자동 시작하지 않는다: - Claude Code 호출 -
REVIEW/FROZEN 승격 - Terminology Validator 구현 - Visual Guide 생성 -
MVP/제품 구현

결과를 ChatGPT Project Beta에 전달하고 다음 판단을 기다린다.

=== ORDER END ===
