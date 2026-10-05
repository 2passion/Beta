# Beta Order --- Order-005 Architecture v1.0 Final Minor Revision

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-005
-   Project: Beta
-   Status: APPROVED
-   Order Type: Final Minor Revision
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Version: v1.0
-   Architecture Status: DRAFT
-   Terminology: `Terminology.md`
-   Terminology Status: DRAFT
-   Write Owner: Codex
-   Reviewer: Claude Code
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Order-004 READ-ONLY Final Delta Review에서 확인된 Blocker 없는 Minor
Revision만 반영하여 Architecture v1.0 DRAFT를 REVIEW 후보 직전 상태로
정리한다.

이번 Order는 전면 재작성이나 새로운 설계 작업이 아니다.

허용된 수정 묶음은 다음 5개뿐이다.

1.  Architecture에 Terminology SSOT 소유권 연결
2.  일반 User Approval과 Runtime USER-GATE 분리
3.  Terminology의 미검증 Prevention 명칭 정리
4.  Terminology Registry의 내부 충돌 정리
5.  Order-History 3분 요약과 Order-004 결과 갱신

추가로 `Beta-Index.md`의 Now / Next만 실제 상태에 맞게 최소 갱신한다.

## 2. 근거

Order-004 최종 판정:

`PASS WITH MINOR REVISION`

새 Blocker:

`NONE`

따라서 Architecture 구조 재설계, 전체 Cross Review 반복, 새로운 기능
추가는 하지 않는다.

## 3. 역할

Write Owner: Codex

Reviewer: Claude Code

이번 Order에서는 Codex만 허용된 파일을 수정한다.

Claude Code를 자동 호출하지 않는다.

## 4. 실행 전 완전성 검사

-   Order 전체를 먼저 읽는다.
-   마지막 `=== ORDER END ===`를 확인한다.
-   없으면 실행하지 않고 BLOCK한다.
-   Architecture가 `v1.0 / DRAFT`인지 확인한다.
-   Terminology가 `DRAFT`인지 확인한다.
-   수정 전 대상 파일의 크기와 SHA-256을 기록한다.

## 5. 읽기 대상

반드시 읽는다.

1.  `C:\Obsidian\Beta\Beta-Index.md`
2.  `C:\Obsidian\Beta\00_Architecture\Harness-A-Architecture-v1.0.md`
3.  `C:\Obsidian\Beta\00_Architecture\Terminology.md`
4.  `C:\Obsidian\Beta\01_Orders\Order-History.md`
5.  `C:\Obsidian\Beta\01_Orders\Order-004-Architecture-v1.0-Final-Delta-Review.md`

필요한 경우 Order-003을 근거 확인용으로 읽을 수 있다.

## 6. Write Scope

수정 허용:

-   `C:\Obsidian\Beta\00_Architecture\Harness-A-Architecture-v1.0.md`
-   `C:\Obsidian\Beta\00_Architecture\Terminology.md`
-   `C:\Obsidian\Beta\01_Orders\Order-History.md`
-   `C:\Obsidian\Beta\Beta-Index.md`

그 외 파일은 수정하지 않는다.

새 파일을 생성하지 않는다.

## 7. Change 1 --- Architecture에 Terminology SSOT 연결

### 7.1 §3.2 기준 자료

Architecture §3.2의 현재 기준 자료 표에 `Terminology.md`를 추가한다.

의미:

-   분류: Architecture Terminology SSOT Draft
-   사용 방식: 표준 용어 의미, Canonical Name, Alias, Deprecated 표현과
    용어 경계 확인

기존 자료 행을 불필요하게 변경하지 않는다.

### 7.2 §3.4 SSOT 소유 경계

다음 의미를 중복 없이 추가한다.

> `Terminology.md`는 Architecture에서 사용하는 용어의 표준 의미와 표기를
> 소유한다.

그리고 다음 경계를 명시한다.

> Architecture 본문의 용어 설명은 설계 문맥을 이해하기 위한 최소
> 설명이다. 표준 의미와 충돌하면 `Terminology.md`를 확인하고
> Architecture 변경 절차를 통해 Delta를 해소한다.

중요:

-   Terminology가 Architecture 설계 계약 자체를 소유한다고 쓰지 않는다.
-   Architecture가 Terminology의 경쟁 용어 SSOT가 되지 않게 한다.
-   Terminology가 DRAFT임을 고려하여 Architecture 변경 절차 없이 자동
    덮어쓰는 구조를 만들지 않는다.

## 8. Change 2 --- User Approval과 USER-GATE 분리

Architecture 전체에서 문맥을 확인한다.

### 8.1 설계 승인

Architecture §1의 다음 의미:

`Cross Review와 User Gate를 통과해 FROZEN`

을 다음 의미로 정리한다.

`Cross Review와 User Approval을 거쳐 FROZEN`

설계 문서 승인 절차는 일반 `User Approval`을 사용한다.

### 8.2 Beta 구현 Workflow

Architecture §18의 흐름에서 설계 검토 후 승인 의미로 사용된
`USER-GATE`가 있다면 일반 `User Approval`로 정리한다.

예:

`설계 검토 → 필요한 경우 User Approval → Order`

단, Harness Runtime에서 실제 사용자 판단이 필요한 상태를 뜻하는
`USER-GATE`는 변경하지 않는다.

### 8.3 검증

다음 두 의미가 섞이지 않아야 한다.

-   `USER-GATE` = Runtime 사용자 결정 필요 상태
-   `User Approval` = 문서/설계/운영 과정에서 필요한 일반 승인

`MVP Test 6 — User Gate`는 시험 이름이므로 유지한다.

## 9. Change 3 --- 미검증 Prevention 명칭 정리

현재 Terminology §7의 `Prevention Candidate`는 Architecture §5.8의 승격
조건과 충돌한다.

Architecture 원칙:

실제 재검증을 통과한 해결만 `Prevention Candidate`가 될 수 있다.

현재 Terminology 표준화는 아직 여러 후속 Order에서 재발 방지 Evidence가
검증되지 않았다.

따라서 Terminology §7 제목을 다음으로 변경한다.

`Proposed Prevention`

또는 한국어 병기:

`Proposed Prevention — 미검증 예방 제안`

표의 상태도 의미가 명확하도록 정리한다.

-   Problem
-   Root Cause Hypothesis
-   Verified Fix: 아직 아님
-   Proposal: Terminology SSOT + 향후 Terminology Validator
-   Promotion Condition: 후속 Order의 재발 방지 Evidence + 실제 재검증

다음을 명시한다.

> 현재 상태는 Architecture §5.8의 Prevention Candidate 요건을 아직
> 충족하지 않는다.

Prevention Candidate로 자동 승격하지 않는다.

## 10. Change 4 --- Terminology Registry 내부 충돌

### 10.1 Checkpoint

TERM-028에서 Korean Name이 `실행 중간 저장점`인데 `저장점` 자체를
금지하는 자기충돌을 제거한다.

권장:

-   Korean Name: `실행 중간 저장점` 유지
-   Prohibited / Deprecated: `저장점` 자체를 전면 금지하지 않는다.
-   필요하면 `저장점 단독 사용 시 의미 불명확` 정도로 설명한다.

### 10.2 일반어 Alias 오탐 방지

`작업`, `검토`, `검증`, `규칙`, `예방`, `목적`처럼 일반 한국어 단어
하나만으로 Canonical Term을 자동 확정하지 않도록 한다.

특히 TERM-010 Task의 Allowed Alias `작업`은 제거하거나 `작업 계약` /
`Task 계약`처럼 문맥이 명확한 표현으로 바꾼다.

같은 성격의 일반어 Alias를 전수 확인하되, Registry 구조를 전면
재작성하지 않는다.

원칙:

> 의미가 여러 Canonical Term과 겹칠 수 있는 일반어 단독 Alias는 자동
> 정규화용 Allowed Alias로 사용하지 않는다.

필요하면 설명용 한국어명은 유지할 수 있다.

### 10.3 ADR와 Decision

다음 경계를 명확히 한다.

-   `Decision` = 선택 자체
-   `ADR` = 중요한 Architecture Decision을 대안, 이유, 영향과 함께
    보존하는 기록

TERM-031 ADR의 `Not Same As`에 Decision을 추가한다.

TERM-033 Decision의 `Not Same As`에 ADR을 추가한다.

Responsibility도 겹치지 않도록 최소 수정한다.

-   ADR Responsibility: 중요한 Architecture Decision의
    배경·대안·이유·영향을 기록
-   Decision Responsibility: 선택 자체와 적용 범위를 식별하고 관련
    ADR/Evidence에 연결

## 11. Change 5 --- Order-History 갱신

### 11.1 3분 요약

Order-History §1의 3분 요약을 현재 실제 이력까지 갱신한다.

최소 흐름:

``` text
Pre-Order Task 1 — PASS
→ Pre-Order Task 2 — PASS
→ Pre-Order Task 3 — PASS
→ Pre-Order Task 4 — REVISION REQUIRED
→ File-based Order 체계 도입
→ Order-001 — PASS
→ Order-002 — PASS WITH MINOR REVISION
→ Order-003 — PASS
→ Order-004 — PASS WITH MINOR REVISION
→ Order-005 — 현재 Final Minor Revision
```

### 11.2 정식 Order 목록

Order-004 행을 추가한다.

-   Order: Order-004
-   목적: Architecture v1.0 Final Delta Review
-   Reviewer: Claude Code
-   Result: PASS WITH MINOR REVISION

Order-005 행도 추가한다.

-   Order: Order-005
-   목적: Architecture v1.0 Final Minor Revision
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Result: 실행 중에는 RUNNING, 완료 후 실제 결과

Pre-Order Task 1\~4와 기존 Order 결과는 변경하지 않는다.

## 12. Beta-Index 최소 갱신

Order-005 수정과 Validation이 PASS한 뒤에만 갱신한다.

Current Architecture: - Harness-A-Architecture-v1.0.md - Version v1.0 -
Status DRAFT

Terminology: - Terminology.md - Status DRAFT

Done에 최소 반영: - Order-004 Final Delta Review 완료 - Order-005 Final
Minor Revision 완료

Now: - Architecture v1.0 DRAFT Final Minor Revision 검증 완료 -
Terminology DRAFT 정합성 검증 완료 - Claude Code 변경 부분 최종 확인
대기

Next: - Claude Code READ-ONLY 변경 부분 확인 - PASS이면 ChatGPT Project
Beta 최종 DRAFT 검토 - v1.0 REVIEW 후보

Architecture 계약이나 Terminology Registry를 Index에 복사하지 않는다.

## 13. 이번 Order에서 하지 말 것

-   Architecture 전면 재작성
-   Architecture Version 변경
-   Architecture Status를 REVIEW/FROZEN으로 변경
-   Terminology Status를 REVIEW/FROZEN으로 변경
-   새로운 Canonical Term 대량 추가
-   Terminology Validator 구현
-   Deprecated → Replacement Schema 구현
-   Coordinator를 새 Canonical Term으로 추가
-   Evidence 저장 구조 구현
-   Approval 세부 정책 확정
-   Runtime 코드 작성
-   별도 ADR / Decisions.md 생성
-   Visual Guide 생성
-   MVP 구현
-   EXE / PWA 작업
-   Plugin / Adapter 구현
-   Reference 수정
-   B 코드 복사
-   Claude Code 자동 호출

## 14. LATER 유지

Order-004의 다음 LATER 항목은 이번 Order에서 구현하거나 확정하지 않는다.

-   기준 약화/중립 변경 판정 주체의 세부 기준
-   Terminology Responsibility 열 중복 축소
-   Deprecated → Replacement 전용 구조
-   04_Evidence 실제 저장/연결 구조
-   Coordinator의 Terminology 등록 여부
-   Review / Architecture Review 상하 관계 표현
-   Order-History Result 열의 상세 의미 표준화

필요한 경우 향후 별도 Order에서 검토한다.

## 15. Validation

### Architecture / SSOT

-   [ ] §3.2에 Terminology 기준 자료 연결
-   [ ] §3.4에 Terminology 용어 SSOT 소유권 명시
-   [ ] Architecture 용어 설명이 문맥 설명임을 명시
-   [ ] 충돌 시 Terminology 확인 + Architecture 변경 절차
-   [ ] Architecture 설계 계약 소유권 유지

### Approval / USER-GATE

-   [ ] 설계 FROZEN 흐름은 User Approval 사용
-   [ ] Beta 구현 Workflow의 일반 승인은 User Approval 사용
-   [ ] Runtime USER-GATE 의미 유지
-   [ ] MVP Test 6 --- User Gate 유지
-   [ ] 일반 User Approval과 USER-GATE 혼용 없음

### Prevention

-   [ ] Terminology §7이 Proposed Prevention으로 변경
-   [ ] Verified Fix = 아직 아님
-   [ ] Prevention Candidate 요건 미충족 명시
-   [ ] 후속 Evidence와 재검증 후 승격 조건 명시
-   [ ] Terminology Validator 미구현

### Registry

-   [ ] Checkpoint의 `저장점` 자기충돌 제거
-   [ ] Task의 단독 `작업` Alias 자동 정규화 제거
-   [ ] 다의적 일반어 단독 Alias 정책 반영
-   [ ] ADR ≠ Decision 명시
-   [ ] ADR / Decision Responsibility 구별
-   [ ] 34개 Canonical Term 유지
-   [ ] Term ID 중복 없음
-   [ ] Canonical Name 중복 없음

### History / Index

-   [ ] History 3분 요약이 Order-004까지 반영
-   [ ] Order-004 = PASS WITH MINOR REVISION
-   [ ] Order-005 행 존재
-   [ ] 기존 Pre-Order Task 1\~4 보존
-   [ ] 기존 Order-001\~003 결과 보존
-   [ ] Index Now / Next 실제 상태와 일치

### Scope

-   [ ] Architecture v1.0 / DRAFT 유지
-   [ ] Terminology DRAFT 유지
-   [ ] 허용 파일 4개 외 수정 없음
-   [ ] 새 파일 생성 없음
-   [ ] Reference 변경 없음
-   [ ] Runtime 기능 추가 없음
-   [ ] Terminology Validator 구현 없음
-   [ ] Claude Code 자동 호출 없음

필수 Validation 하나라도 실패하면 PASS로 판정하지 않는다. 검사 자체가
정상 수행되지 못하면 ERROR로 구별한다.

## 16. Evidence

작업 완료 후 최소한 다음을 보고한다.

-   Architecture 수정 전/후 크기와 SHA-256
-   Terminology 수정 전/후 크기와 SHA-256
-   Order-History 수정 전/후 크기와 SHA-256
-   Beta-Index 수정 전/후 크기와 SHA-256
-   UTF-8 정상 여부
-   한글 문자오염 여부
-   변경 파일 목록
-   새 파일 목록
-   Reference 변경 여부

## 17. 결과 보고 형식

# Order-005 실행 결과

### 현재 상태

PASS / FAIL / ERROR / BLOCKED

### Architecture

Version: v1.0 Status: DRAFT

### 변경 1 --- Terminology SSOT 연결

PASS / FAIL + 근거

### 변경 2 --- User Approval / USER-GATE 분리

PASS / FAIL + 근거

### 변경 3 --- Proposed Prevention

PASS / FAIL + 근거

### 변경 4 --- Registry 충돌 정리

PASS / FAIL + 근거

### 변경 5 --- History / Index

PASS / FAIL + 근거

### Validation

위 체크리스트 전체 결과.

### Evidence

수정 전후 크기 / SHA-256 / 무결성 / 변경 파일.

### Done

Order-004의 Minor Revision 5개 묶음 반영 완료.

### Now

Architecture v1.0 DRAFT / Terminology DRAFT. Claude Code 변경 부분
READ-ONLY 최종 확인 대기.

### Next

Claude Code 변경 부분만 확인. PASS이면 ChatGPT Project Beta 최종 DRAFT
검토 후 v1.0 REVIEW 후보.

### 사용자 승인 필요

NO

현재는 DRAFT 정리 단계이며 FROZEN 승인 단계가 아니다.

## 18. 종료 조건

승인된 5개 수정 묶음, History/Index 최소 갱신, 전체 Validation이
완료되면 종료한다.

PASS하더라도 다음을 자동 시작하지 않는다.

-   Claude Code 호출
-   REVIEW/FROZEN 승격
-   Terminology Validator 구현
-   Visual Guide 생성
-   MVP/제품 구현
-   EXE/PWA
-   Plugin/Adapter

결과를 ChatGPT Project Beta에 전달하고 다음 판단을 기다린다.

=== ORDER END ===
