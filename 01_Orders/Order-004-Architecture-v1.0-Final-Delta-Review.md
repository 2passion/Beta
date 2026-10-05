# Beta Order --- Order-004 Architecture v1.0 Final Delta Review

## 문서 정보

-   Document: Beta Order
-   Order ID: Order-004
-   Project: Beta
-   Status: APPROVED
-   Order Type: READ-ONLY Final Delta Review
-   Architecture: `Harness-A-Architecture-v1.0.md`
-   Architecture Version: v1.0
-   Architecture Status: DRAFT
-   Terminology: `Terminology.md`
-   Terminology Status: DRAFT
-   Reviewer: Claude Code
-   Write Owner for Architecture/Terminology: Codex
-   File Root: `C:\Obsidian\Beta`

## 1. Intent

Order-003에서 실제로 변경된 범위만 독립적으로 최종 확인한다.

이번 Review의 목적은 Architecture 전체를 다시 처음부터 Cross Review하는
것이 아니다.

다음 네 변경 영역과 그 경계만 확인한다.

1.  Validator 판정 로직 변경 및 기준 약화 승인 계약
2.  Gate 계열 용어 정리
3.  `Terminology.md`의 SSOT / SRP와 Canonical Terminology
4.  Beta-Index / Order-History 상태 정합성

추가로 Architecture의 짧은 용어 설명과 Terminology SSOT가 서로 충돌하지
않는지만 확인한다.

## 2. 역할과 권한

Reviewer: Claude Code

Write Owner: Codex

이번 Order에서 Claude Code는 READ-ONLY Reviewer다.

어떤 Beta 파일도 생성·수정·삭제·이동·이름 변경하지 않는다.

수정이 필요하면 직접 고치지 않고: - 위치 - 문제 - 근거 - 최소 수정안

만 보고한다.

## 3. 실행 전 완전성 검사

-   이 Order 전체를 먼저 읽는다.
-   마지막 `=== ORDER END ===`를 확인한다.
-   종료 마커가 없으면 실행하지 않고 `BLOCKED`로 보고한다.
-   Architecture가 `v1.0 / DRAFT`인지 확인한다.
-   Terminology가 `DRAFT`인지 확인한다.
-   파일 변경 없이 Review 가능한지 확인한다.

## 4. 반드시 읽을 파일

1.  `C:\Obsidian\Beta\Beta-Index.md`
2.  `C:\Obsidian\Beta\00_Architecture\Harness-A-Architecture-v1.0.md`
3.  `C:\Obsidian\Beta\00_Architecture\Terminology.md`
4.  `C:\Obsidian\Beta\01_Orders\Order-History.md`
5.  `C:\Obsidian\Beta\01_Orders\Order-003-Architecture-Minor-Revision-and-Terminology-Standard.md`

필요한 경우 Order-001 / Order-002를 근거 확인 목적으로 읽을 수 있다.

Reference 원본은 이번 Delta Review의 직접 대상이 아니다.

## 5. Review 범위 1 --- Validator 계약

다음만 확인한다.

-   Validator 판정 기준 또는 판정 로직 변경이 Validation 기준 변경으로
    취급되는가?
-   해당 변경이 Task 계획 버전 변경과 연결되는가?
-   변경 후 New Run 재검증이 필요한가?
-   필수 Validator 또는 완료 기준 약화·축소를 Write Owner가 단독 확정할
    수 없는가?
-   Gate 판정을 요구하는가?
-   필요한 경우 USER-GATE로 올리는가?
-   기준 강화나 의미가 변하지 않는 중립 변경까지 불필요하게 USER-GATE로
    강제하지 않는가?
-   기존 Validator 고정 계약과 모순이 없는가?

판정: PASS / PARTIAL / FAIL

## 6. Review 범위 2 --- Gate 계열 Terminology

Architecture와 Terminology를 대조한다.

표준 경계:

-   Gate = Runtime 진행 판정 역할
-   USER-GATE = 사용자 결정 필요 Runtime 상태
-   MVP Test = MVP 실행 검증 시험
-   Architecture Review = Architecture 검토 활동
-   Review Checklist = Review 항목 목록
-   Validation = 실제 결과와 고정 기준 비교
-   Review = 설계·코드·Decision의 적절성 검토

확인:

-   Architecture에 `Review Gate`가 현재 표준 용어처럼 남아 있지 않은가?
-   문서 검토 의미의 `MVP Gate`가 남아 있지 않은가?
-   Runtime 사용자 결정 의미의 `Decision Gate`가 남아 있지 않은가?
-   `MVP Test 6 — User Gate`는 시험 이름으로 올바르게 유지되는가?
-   일반 `User Approval`과 Runtime `USER-GATE`를 무조건 같은 개념으로
    처리하지 않는가?
-   목차와 본문 제목이 일치하는가?

과거 Order/Evidence 안의 과거 표현은 수정 대상이 아니다.

판정: PASS / PARTIAL / FAIL

## 7. Review 범위 3 --- Terminology SSOT / SRP

`Terminology.md`가 다음 책임을 지키는지 확인한다.

Terminology: 용어 의미와 표준 표현

Architecture: 설계 계약

Beta-Index: 현재 Architecture / Done / Now / Next / 주요 위치

Order-History: 시간순 Timeline View

Order: 승인된 실행 계약

Evidence: 실제 실행·검증 사실

Decision / ADR: 왜 결정했는가

확인:

-   Terminology가 Architecture 설계 계약을 대신하지 않는가?
-   Architecture가 Terminology와 별도의 경쟁 용어 SSOT가 되지 않는가?
-   Architecture의 짧은 설명은 문맥 설명 수준인가?
-   표준 의미가 충돌하면 Terminology 확인 + Architecture 변경 절차로
    Delta를 해소하도록 되어 있는가?
-   같은 Intent/ADR/Result/Evidence 본문을 Terminology에 복제하지
    않는가?
-   Trace Reference 방식이 사용되는가?

판정: PASS / PARTIAL / FAIL

## 8. Review 범위 4 --- Canonical Term Registry

34개 Canonical Term을 확인한다.

필수 Term:

Gate USER-GATE MVP Test Architecture Review Review Checklist Validation
Validator Review Order Task Run Event Evidence Asset Reference Archive
Prevention Rule Hook Skill Script Agent Classifier Router Generator
Scheduler Caller Checkpoint Chunk Intent ADR Result Decision Approval

확인:

-   34개가 모두 존재하는가?
-   Term ID가 중복되지 않는가?
-   Canonical Name이 중복되지 않는가?
-   각 Term에 Description / Purpose / Responsibility가 있는가?
-   Allowed Aliases가 있는가?
-   Prohibited / Deprecated Terms를 표현할 수 있는가?
-   Not Same As가 있는가?
-   Trace References가 있는가?
-   Alias와 Canonical Name 사이에 명백한 충돌이 없는가?
-   서로 다른 두 Canonical Term이 같은 의미로 정의되어 있지 않은가?

판정: PASS / PARTIAL / FAIL

## 9. Review 범위 5 --- Alias / 문자 오류 정책

확인:

-   Canonical Name이 기본 저장·표시 용어인가?
-   명시된 Allowed Alias만 자동 정규화 가능한가?
-   미등록 유사어·오타·축약어를 AI가 임의 확정하지 못하게 되어 있는가?
-   불명확한 용어가 WARNING 또는 HOLD 후보인가?
-   프로젝트 내부 약어 최소화 원칙과 일치하는가?
-   과거 Evidence / Order 원문을 현재 표준에 맞추기 위해 조용히 덮어쓰지
    않는가?

판정: PASS / PARTIAL / FAIL

## 10. Review 범위 6 --- Traceability

다음 흐름이 실제 문서에 있는지 확인한다.

`Intent → ADR / Decision → Result → Evidence`

확인:

-   Intent = 왜 시작했는가
-   ADR / Decision = 대안과 선택 이유
-   Result = 무엇이 바뀌었는가
-   Evidence = 실제 무엇이 확인됐는가

또한:

-   Terminology에 본문 복제 대신 Reference가 연결되는가?
-   Order-002 용어 Drift 발견이 추적되는가?
-   Order-003 Terminology Decision이 추적되는가?
-   Order-003 Result가 Order-History와 연결되는가?
-   Architecture 반영 위치가 추적되는가?

판정: PASS / PARTIAL / FAIL

## 11. Review 범위 7 --- Prevention Candidate

현재 상태가 과장되지 않았는지 확인한다.

기대 상태:

Problem: Gate 계열 용어 혼재

Root Cause Hypothesis: Canonical Terminology SSOT 부재

Verified Fix: 아직 아님

Candidate: Terminology SSOT + 향후 Terminology Validator

확인:

-   Terminology SSOT 생성만으로 Verified Fix라고 선언하지 않는가?
-   Terminology Validator가 이미 구현됐다고 쓰지 않는가?
-   여러 후속 Order에서 재발 방지 Evidence를 확인한 뒤 승격하도록 되어
    있는가?

판정: PASS / PARTIAL / FAIL

## 12. Review 범위 8 --- Index / History 정합성

확인:

### Beta-Index

-   현재 Architecture = v1.0 DRAFT
-   Terminology 위치가 주요 위치에 연결됨
-   `MVP Test 1~7` 용어 사용
-   `다음 단계` 용어 사용
-   Now / Next가 Order-003 이후 실제 상태와 일치

### Order-History

-   Pre-Order Task 1\~4 유지
-   Order-001 = PASS
-   Order-002 = PASS WITH MINOR REVISION
-   Order-003 = PASS
-   File-based Order 시작이 Order-001로 유지

View Drift가 있으면 실제 실행 실패와 구별한다.

판정: PASS / PARTIAL / FAIL

## 13. 새로운 Blocker 검사

Order-003 변경으로 다음 문제가 새로 생겼는지만 확인한다.

-   Architecture와 Terminology 정의 충돌
-   Canonical Term 충돌
-   Validator 계약 모순
-   SSOT 소유권 충돌
-   Order-History가 Evidence 원본처럼 승격됨
-   Terminology가 Runtime 기능을 새로 정의함
-   Architecture 또는 Terminology가 REVIEW/FROZEN으로 잘못 승격됨

없으면: `NONE`

## 14. 중요도 분류

### BLOCKER

v1.0 REVIEW 후보 전에 반드시 수정해야 하는 계약·SSOT·안전성 문제.

### IMPORTANT

REVIEW 전에 고치는 것이 적절한 작은 일관성 또는 명확성 문제.

### LATER

현재 REVIEW 후보를 막지 않는 구현·자동화·장기 개선 사항.

### KEEP

현재 구조에서 유지해야 할 설계.

## 15. 최종 판정

다음 중 하나만 선택한다.

### PASS

-   Review 범위 1\~8 모두 PASS
-   새로운 Blocker 없음
-   REVIEW 전에 반드시 수정할 IMPORTANT 없음

### PASS WITH MINOR REVISION

-   Blocker 없음
-   작은 명칭/Trace/View Drift 등 최소 수정 필요

### REVISION REQUIRED

-   기존 계약 미반영
-   새로운 Blocker
-   SSOT/SRP 충돌
-   REVIEW 전에 해결해야 할 실질적 문제 존재

### BLOCKED

-   Order 불완전
-   파일 읽기 실패
-   Review 자체 수행 불가

## 16. 결과 보고 형식

# Order-004 Final Delta Review 결과

### 현재 판정

PASS / PASS WITH MINOR REVISION / REVISION REQUIRED / BLOCKED

### Review 범위

  범위                      판정   근거
  ------------------------- ------ ------
  Validator 계약                   
  Gate 계열 Terminology            
  Terminology SSOT / SRP           
  Canonical Term Registry          
  Alias / 문자 오류 정책           
  Traceability                     
  Prevention Candidate             
  Index / History 정합성           

### 새로운 Blocker

NONE 또는 상세.

### IMPORTANT

NONE 또는 상세.

### LATER

NONE 또는 상세.

### KEEP

유지할 핵심 구조.

### Terminology 충돌 검사

Architecture와 Terminology 사이 충돌 여부.

### History / Index Drift

NONE 또는 상세.

### 파일 변경 확인

-   Architecture: NO
-   Terminology: NO
-   Beta-Index: NO
-   Order-History: NO
-   Order-003: NO
-   Reference: NO
-   새 파일: NO

### Done

Order-003 변경 범위 READ-ONLY Delta Review 완료.

### Now

Architecture v1.0 DRAFT / Terminology DRAFT.

### Next

판정에 따라:

PASS: → ChatGPT Project Beta 최종 DRAFT 검토 → v1.0 REVIEW 후보

PASS WITH MINOR REVISION: → Codex 최소 수정 → 변경 부분만 재확인 → v1.0
REVIEW 후보

REVISION REQUIRED: → ChatGPT Project Beta 검토 → 새 수정 Order

### 사용자 승인 필요

NO

현재는 REVIEW 후보 판단 단계이며 FROZEN 승인 단계가 아니다.

## 17. 종료 조건

결과 보고 후 종료한다.

PASS하더라도 다음을 시작하지 않는다.

-   파일 수정
-   Architecture / Terminology REVIEW 승격
-   FROZEN 승격
-   Codex 호출
-   Terminology Validator 구현
-   Visual Guide 생성
-   MVP 구현
-   EXE / PWA 작업
-   Plugin / Adapter 구현

결과를 ChatGPT Project Beta에 전달하고 다음 판단을 기다린다.

=== ORDER END ===
