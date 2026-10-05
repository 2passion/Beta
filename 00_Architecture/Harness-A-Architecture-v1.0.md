# Harness A Architecture

## 문서 정보

| 항목 | 값 |
|---|---|
| Project | Beta |
| Document | Harness A Architecture |
| File | `Harness-A-Architecture-v1.0.md` |
| Version | v1.0 |
| Status | FROZEN |
| Role | Architecture SSOT Draft |
| Stage | DESIGN |
| Write Owner | Codex |
| Reviewer | Claude Code |
| File Root | `C:\Obsidian\Beta` |
| Reference | `harness-visual-review.html`<br>`harness_loop_full_korean-main.zip` |

이 문서는 Beta에서 설계하는 Harness A의 현재 Architecture 기준 초안이다. 현재까지 승인된 설계 원칙과 경계를 압축·구조화하며, 과거 대화 전체를 복제하지 않는다.

`DRAFT`는 검토 중인 현재 설계 기준이라는 뜻이다. 구현 완료, 실행 성공 또는 `FROZEN`을 뜻하지 않는다. 이 문서의 계획과 규칙은 Runtime Evidence가 아니며, 구현 결과는 별도 Run, Validation, Evidence로 증명해야 한다.

---

## 목차

1. 3분 요약과 시각 구조
2. 목적, Scope와 성공 기준
3. 문서 권위와 기준 자료
4. 시스템 경계: A와 B
5. 핵심 Architecture 원칙
6. 자동화 선택 원칙
7. 논리 역할과 책임 경계
8. 논리 데이터 모델
9. 파생 View와 SSOT 규칙
10. 정상·병렬 Workflow
11. Validation과 Gate
12. Recovery Workflow
13. Prevention과 Rule 수명주기
14. 중단과 재개
15. 외부 연결 경계
16. Downloads Intake 방향
17. Asset / Reference / Archive
18. 구현 Workflow와 변경 통제
19. MVP Test 1~7
20. 사용자 Workflow와 기본 View
21. 제품화 Roadmap
22. 문서·버전·추적 규칙
23. 설계 단계 경계
24. Out of Scope
25. Unresolved
26. Decision 후보
27. Architecture Review Checklist
28. 상태 참조
29. 문서 종료

---

## 1. 3분 요약과 시각 구조

Harness A는 사용자의 요청을 기존 자산 우선으로 준비하고, 허용된 범위 안에서 실행하며, 독립된 검증과 Evidence를 통해 다음 단계로 넘기는 Local Core 중심 시스템이다.

이 3분 요약과 시각 구조는 빠른 이해를 위한 비규범 요약이다. 요약과 본문 계약이 충돌하면 해당 본문 계약을 따른다.

핵심 계약은 다음과 같다.

- A가 현재 Architecture의 기준이며, 외부 Harness B는 Reference다.
- 새 기능을 만들기 전에 기존 Asset, Rule, Skill, Hook, Script, Generator, Validator, Tool을 검색한다.
- 한 Task에는 하나의 Write Owner만 둔다.
- 의존관계, 파일, 기능 영역, 공유 자원, 권한이 독립적인 작업만 병렬 실행한다.
- 가장 단순하고 확실한 로컬 수단을 우선하며, 필요한 경우에만 Agent나 외부 연결을 사용한다.
- Task 계획과 실제 Run 이력을 구별한다. 실패한 Run을 나중의 PASS로 덮어쓰지 않는다.
- 필수 Validator가 모두 PASS해야 Task를 PASS로 판정할 수 있다.
- 반복 실패는 Blind Retry하지 않고 Fingerprint, Root Cause, Fix, New Run, Revalidation 순서로 처리한다.
- 한 번 성공한 Fix를 즉시 전역 Rule로 승격하지 않는다. 적용 범위와 회귀 검증이 필요하다.
- STATE, DAG, LOG, PROGRESS, DASHBOARD는 원본 기록에서 생성하는 파생 View다.
- 외부 Plugin, Adapter, Remote, API는 Core의 필수 요소가 아니다. 현재는 External Port 경계만 설계한다.
- 사용자에게는 중요한 `USER-GATE` 상황에서만 질문한다.
- MVP PASS와 제품화 승격은 Runtime Evidence로 증명한다.

현재 단계는 `DESIGN`이다. 이 문서가 Cross Review와 User Approval을 거쳐 `v1.0 FROZEN`이 되기 전에는 Local Core 구현을 확정하지 않는다.

### 1.1 전체 Architecture 구조도

```text
User
→ A Local Core
→ Control / Execution / Quality
→ Validation / Gate
→ Recovery / Prevention
```

외부 연결은 Core 내부 구조와 분리한다.

```text
A Local Core
→ External Port
→ Adapter
→ Plugin / Remote / API / External Tool
```

### 1.2 데이터 구조도

```text
PROJECT
→ TASK
→ RUN
→ EVENT

RUN
→ VALIDATION
→ EVIDENCE

FAIL
→ Fingerprint
→ Root Cause
→ Fix
→ New Run
→ PASS
→ Prevention
→ Rule Candidate
```

### 1.3 핵심 흐름 한눈에 보기

사용자 Workflow:

```text
목표 입력
→ 자동 준비
→ 필요한 경우만 사용자 승인
→ 자동 실행
→ 자동 검증
→ 허용 범위 내 자동 복구
→ 결과 확인
```

정상 Workflow:

```text
Request
→ Reuse Search
→ Task
→ Run
→ Validation
→ Gate
→ Next / Complete
```

Recovery Workflow:

```text
FAIL
→ Fingerprint
→ Prevention Search
→ Root Cause
→ Fix
→ New Run
→ Revalidation
→ Evidence
→ Prevention Candidate
```

제품화 Roadmap:

```text
Architecture
→ Cross Review
→ User Approval
→ FROZEN
→ Local Core MVP
→ MVP Test 1~7
→ Runtime Evidence
→ MVP Freeze
→ EXE
→ 실제 운영
→ 필요한 기능만 확장
```

---

## 2. 목적, Scope와 성공 기준

### 2.1 목적

Harness A는 AI 기반 개발 작업에서 다음을 일관되게 수행하기 위한 시스템이다.

- 기존 자산과 규칙을 먼저 발견하고 재사용한다.
- 작업의 범위, 소유권, 순서, 권한을 명확히 한다.
- 자동화 가능한 작업은 허용 범위 안에서 자동 처리한다.
- 실행 사실과 검증 근거를 보존한다.
- 실패를 원인 중심으로 복구하고 검증된 해결을 재사용한다.
- 중단 후 검증된 지점부터 안전하게 재개한다.
- 사용자는 내부 구조 대신 현재 상태와 중요한 결정에 집중한다.

### 2.2 Architecture 성공 기준

이 Architecture는 다음 질문에 일관된 답을 제공해야 한다.

1. 무엇이 현재 기준이고 무엇이 Reference인가?
2. 누가 쓸 수 있고 누가 검토하는가?
3. 어떤 작업을 재사용하고 어떤 경우 새로 만드는가?
4. 작업은 어떤 순서와 권한으로 실행되는가?
5. 실제로 무엇이 실행되었고 어떤 결과가 발생했는가?
6. 무엇을 근거로 PASS, FAIL, ERROR 또는 중단을 판정하는가?
7. 실패 후 어디서 어떻게 다시 시작하는가?
8. 어떤 해결을 어떤 범위에서 다음 작업에 재사용할 수 있는가?
9. 언제 사용자 결정이나 외부 연결이 필요한가?

### 2.3 구현 성공과의 구별

Architecture 문서의 완성은 구현 성공이 아니다. 구현, MVP Test, EXE 및 외부 확장은 각각 별도의 Task, Run, Validation, Evidence를 필요로 한다.

### 2.4 현재 Scope

현재 Scope는 Harness A Architecture v1.0 DRAFT의 설계 계약을 정리하는 것이다. Local Core, Validator 프로그램, Intake Script, Plugin, Adapter 또는 사용자 애플리케이션을 구현하지 않는다. 상세 제외 범위는 `24. Out of Scope`를 따른다.

---

## 3. 문서 권위와 기준 자료

### 3.1 문서 우선순위

1. 최신 `FROZEN` Architecture SSOT
2. 승인된 Decision / Rule
3. 현재 Order / Task
4. 실제 Evidence
5. 승인된 Asset
6. Reference
7. Archive
8. 과거 Chat 및 새로운 AI 제안

현재 `FROZEN` Architecture가 없으므로 이 `v1.0 DRAFT`가 검토를 위한 최신 통합 초안이다. DRAFT 내용은 Review와 User Approval에서 변경될 수 있다.

### 3.2 현재 기준 자료

| 자료 | 분류 | 사용 방식 |
|---|---|---|
| `Beta-Index.md` | 프로젝트 계약 / Index | Beta의 목적, 위치, 문서 우선순위, 버전 규칙 확인 |
| `Terminology.md` | Architecture Terminology SSOT Draft | 표준 용어 의미, Canonical Name, Alias, Deprecated 표현과 용어 경계 확인 |
| `Reference/harness-visual-review.html` | A 설계 검토 Reference | 역할 경계, 데이터 관계, 검증 쟁점, 사용자 흐름 보완 |
| `Reference/harness_loop_full_korean-main.zip` | B 외부 Reference | Harness, Loop, Gate, 재개, 병렬 운용 아이디어 비교 |

Reference에서 관찰한 설명이나 기능은 자동으로 A의 승인 기능 또는 구현 사실이 되지 않는다.

### 3.3 충돌 처리

- 이 Markdown Architecture와 파생 HTML Visual Guide가 충돌하면 Markdown Architecture를 따른다.
- Architecture와 구현이 다르면 구현을 정당화하지 말고 Delta로 기록한다.
- 구현 Evidence가 Architecture 변경 필요성을 보이면 Change Proposal과 Review를 거친다.
- Dashboard나 상태 화면은 원본 Evidence를 대체하지 않는다.

### 3.4 SSOT 소유 경계

- `Beta-Index.md`: 현재 Architecture와 상태, Done / Now / Next, 주요 문서 위치를 소유한다.
- `Terminology.md`: Architecture에서 사용하는 용어의 표준 의미와 표기를 소유한다.
- Architecture: 설계 계약, 데이터 구조, 역할, Workflow, Validation, Recovery, Prevention, 원칙과 Architecture Unresolved를 소유한다.
- Visual Guide: Architecture를 설명하는 파생 자료이며 SSOT가 아니다.
- Architecture 내부에는 운영 상태를 중복 기록하지 않고 `Beta-Index.md`를 참조한다.
- Architecture 본문의 용어 설명은 설계 문맥을 이해하기 위한 최소 설명이다. 표준 의미와 충돌하면 `Terminology.md`를 확인하고 Architecture 변경 절차를 통해 Delta를 해소한다.

---

## 4. 시스템 경계: A와 B

### 4.1 A

Harness A는 Beta에서 설계하는 개선 시스템이며, 현재 Architecture의 기준이다.

### 4.2 B

`harness_loop_full_korean-main.zip` 등 외부 자료는 Harness B Reference다. B의 명칭, Layer, 코드, 실행 방식은 A의 필수 구조가 아니다.

### 4.3 관계

`A > B`

이는 A가 B의 라이선스나 저작권보다 우선한다는 뜻이 아니다. 설계 의사결정에서 A의 목적과 승인 원칙이 기준이며 B는 비교·검토 자료라는 뜻이다.

B에서 기능이나 코드를 직접 재사용하려면 별도 Task에서 다음을 확인한다.

- A의 실제 필요성
- 기존 A Asset과의 중복
- 채택 이유와 변경 범위
- 원본 버전과 Provenance
- 라이선스 및 고지 의무
- 보안과 유지보수 영향
- 독립 Validation과 Evidence

현재 B ZIP에는 MIT License 문서가 포함되어 있으나, 이 사실만으로 특정 코드의 A 편입을 승인하지 않는다.

### 4.4 B Reference 정책

B에서 비교할 수 있는 예는 다음과 같다.

- Task 기반 작업 분할과 의존관계
- DAG(Directed Acyclic Graph, 방향성 비순환 그래프)
- 안전한 병렬 실행과 Coordinator 개념
- 구현과 검증의 분리
- Retry 제한
- 상태와 실행 기록
- Skill 기반 단계화
- 파일 기반 세션 전달

다음은 자동으로 하지 않는다.

- B의 폴더 구조, 명칭 또는 코드를 복제
- B의 모든 Layer를 A에 강제 적용
- B를 A의 Runtime Dependency로 사용
- B의 기능을 자동으로 Asset 등록

B 기능의 채택 검토 순서는 다음과 같다.

```text
Reference 검토
→ 기존 A Asset 검색
→ 필요성 확인
→ 중복 확인
→ 필요한 경우 라이선스 / 의존성 확인
→ A 방식으로 채택 여부 결정
→ 구현 또는 승인된 재사용
→ Validation
→ Evidence
→ Asset 등록
```

---

## 5. 핵심 Architecture 원칙

### 5.1 Reuse Before Create

새로 만들기 전에 기존 Asset, Rule, Skill, Hook, Script, Generator, Validator, Tool을 검색한다. 재사용하지 않는다면 중복 여부와 새 생성 이유를 남긴다.

### 5.2 Local First

로컬에서 빠르고 확실하게 처리할 수 있는 작업은 로컬에서 처리한다. Local First는 무조건 로컬만 사용한다는 뜻이 아니며, 실제 요구와 Evidence가 있을 때 외부 연결을 검토할 수 있다.

### 5.3 One Task One Owner

하나의 Task에는 하나의 Write Owner만 둔다.

Harness Runtime 원칙은 `One Task One Write Owner`다.

현재 Beta 운영 역할:

- Codex: Write Owner
- Claude Code: Reviewer

이 배치는 현재 Beta 운영의 역할이며 Harness의 영구 Runtime 구성요소가 아니다. 향후 역할은 바뀔 수 있지만 같은 Task에서 동시에 여러 Write Owner를 두지 않는다.

### 5.4 Parallel Only When Independent

다음 충돌이 모두 없다고 확인된 작업만 병렬 실행한다.

- 의존관계
- 파일
- 기능 영역
- 공유 자원
- 권한

Owner가 다르다는 사실만으로 독립성이 증명되지는 않는다.

### 5.5 Least Privilege

Task 수행에 필요한 최소 Scope와 최소 권한만 사용한다. 실패나 편의를 이유로 Scope 또는 권한을 자동 확대하지 않는다.

### 5.6 No Blind Retry

같은 실패를 새로운 근거, 변경 또는 가설 없이 반복하지 않는다.

### 5.7 Root Cause Before Fix

반복 병목은 증상만 우회하지 않고 원인을 분석한 뒤 수정한다. 가설과 확인된 원인을 구별한다.

### 5.8 Verified Fix Before Prevention

실제 재검증을 통과한 해결만 Prevention Candidate로 만든다.

### 5.9 Evidence Before Promotion

Evidence 없이 다음 승격을 확정하지 않는다.

- Rule 활성화
- MVP PASS
- MVP Freeze
- EXE 승격
- PWA 승격
- 외부 연결 확대

### 5.10 User Only at USER-GATE

자동 처리 가능한 일은 승인된 범위 안에서 자동 진행한다. 범위 확대, 권한 확대, 중요한 데이터 변경, 복구 한도 초과, 상충하는 선택 등 사용자 판단이 필요한 경우에만 `USER-GATE`로 멈춘다.

---

## 6. 자동화 선택 원칙

자동화를 많이 한다는 것이 Agent를 많이 사용한다는 뜻은 아니다. 가능한 한 단순하고 확실한 수단을 선택한다.

기본 검토 순서:

`Rule → Script → 기존 Validator → Hook → 기존 Skill → Generator → 필요한 Agent → External Port / Adapter → USER-GATE`

이 순서는 절대적인 비용 순위가 아니다. 다음 값은 Runtime Evidence로 측정한다.

- 실행 시간
- AI 호출 여부와 호출 수
- 입력·출력 또는 토큰 사용량
- 성공률과 오류율
- 재시도 횟수
- 유지보수 비용
- 사용자 질문 횟수

`Local`, `Skill`, `Hook`, `Plugin` 등의 이름만으로 비용이나 품질을 단정하지 않는다.

---

## 7. 논리 역할과 책임 경계

다음 12개는 논리적 책임이다. 12개의 프로그램 또는 12개의 Agent를 만든다는 의미가 아니다. 한 구성요소가 여러 책임을 구현할 수 있지만, 판정·호출·검증의 경계는 추적 가능해야 한다.

| 역할 | 책임 | 하지 않는 일 |
|---|---|---|
| Classifier | 요청, Task, 오류의 종류·위험·난이도 분류 | 직접 실행하거나 파일 수정 |
| Router | 기존 자산을 고려해 처리 경로 선택 | 우선순위와 실행 허가를 임의 결정 |
| Generator | 필요한 Task, Plan, 문서, 설정 초안 생성 | 초안을 승인된 Rule이나 완료 결과로 승격 |
| Scheduler | 우선순위, 의존관계, 실행 순서, 안전한 병렬 후보 결정 | 실행 대상을 직접 호출 |
| Caller | 확정된 Asset 또는 실행 수단을 지정 입력으로 호출 | 실패를 이유로 Scope·권한 확대 |
| Script | 결정적이고 반복 가능한 로컬 작업 수행 | 문맥이 필요한 정책 결정 |
| Skill | 재사용 가능한 표준 절차와 지식 정의 | 독립 실행 주체라고 자동 간주 |
| Agent | 문맥 판단, 복잡한 계획, 코딩, Root Cause 분석 | 모든 단순 작업 독점 |
| Rule | 조건, 허용·금지, 자동 행동 기준 정의 | Event를 직접 감시하거나 실행 |
| Hook | 특정 Event에서 정해진 동작 호출 | 새로운 정책 결정 |
| Validator | 실제 결과를 기준과 비교하고 근거와 판정 반환 | 검증 중 대상 결과 수정 또는 근거 없는 PASS |
| Gate | Validation, Permission, Approval, Risk에 따라 진행 결정 | 모든 판정을 사용자에게 전가 |

Gate의 최소 결정값은 다음과 같다.

- `PROCEED`
- `WAIT`
- `BLOCK`
- `USER-GATE`

Rule과 Hook은 Workflow 전체가 반드시 통과하는 직렬 Layer가 아니다. 조건과 Event에 따라 필요한 시점에 적용된다.

용어와 책임 경계:

- **Gate**: Runtime 조건에 따른 판정이다.
- **USER-GATE**: 사용자 결정이 필요한 Runtime 상태다.
- **MVP 검증**: `MVP Test 1~7`의 실행과 판정이다.
- **문서 검토**: `Review Checklist` 또는 `Architecture Review`다.
- **Validation**: 실제 결과를 고정된 기준과 비교한다.
- **Review**: 문서나 Architecture의 일관성·완전성·적합성을 검토하며 Validation과 구별한다.

---

## 8. 논리 데이터 모델

### 8.1 원본 개념

| 개념 | 의미 | 핵심 규칙 |
|---|---|---|
| PROJECT | 프로젝트의 범위와 목표 | Task의 상위 범위를 제공 |
| ORDER | 승인된 작업 지시 또는 실행 계약 | 허용된 변경과 Scope를 고정 |
| DECISION | 중요한 설계·운영 판단과 근거 | Architecture에 반영된 선택을 추적 |
| APPROVAL | 특정 대상·범위에 대한 승인 사실 | Decision과 실행 권한의 근거를 보존 |
| TASK | 현재 해야 할 작업 계약 | 목표, Write Owner, Write Scope, Shared Resources, `depends_on`, 완료 기준, 계획 버전을 고정 |
| RUN | Task의 한 번의 실제 실행 시도 | 실행 당시 Task 계획 버전을 추적하고 이전 실패를 덮어쓰지 않음 |
| EVENT | 실제로 발생한 사실 | 과거 사실의 원본으로 보존 |
| ASSET | Beta에서 실제 실행·재사용하도록 승인된 자산 | Reference와 구별하고 상태·범위를 관리 |
| VALIDATION | Run 결과에 대한 검사 | Validator, 기준, 결과, 실행 상태를 기록 |
| EVIDENCE | 실행과 Validation 결과를 확인할 근거 | 판정과 추적 가능한 위치로 연결 |
| PREVENTION | 과거 문제에서 배운 검증된 해결 지식 | 문제 유형, 해결, 적용 범위, Evidence를 연결 |
| RULE | 미래 실행에 적용할 조건과 행동 정책 | 후보·검증·활성 상태를 구별 |
| REFERENCE | 현재 설계·비교에 사용하는 참고자료 | 자동으로 Asset이 되지 않음 |
| ARCHIVE | 현재 기준에서 제외되어 보존하는 과거자료 | 현재 설계 또는 실행 입력으로 자동 사용하지 않음 |

### 8.2 Task와 Run의 구별

Task는 무엇을 해야 하는지 정의한다. Run은 실제로 무엇을 시도했는지 기록한다.

예:

`Run-001 FAIL → Fix → Run-002 PASS`

`Run-002 PASS`는 `Run-001 FAIL`을 삭제하거나 PASS로 바꾸지 않는다.

각 RUN은 실행 당시의 Task 계획 버전을 추적한다. 완료 기준이나 Validator 기준이 바뀌면 계획 버전을 변경하고 New Run으로 다시 검증한다.

### 8.3 연결과 식별자

중요한 객체는 이름이 아니라 고유 ID로 연결한다. 전체 단어 기반 ID를 우선한다.

- `Project-001`
- `Task-001`
- `Run-001`
- `Decision-001`
- `Asset-001`
- `Reference-001`
- `Validation-001`
- `Evidence-001`
- `Prevention-001`
- `Rule-001`

내부 축약어는 최소화한다. 실제 ID 규칙과 저장 형식은 구현 전에 결정한다.

### 8.4 추가 관계

- PROJECT는 여러 TASK를 포함할 수 있다.
- ORDER는 승인된 실행 계약을 제공하고 TASK는 그 허용 범위 안에서 구체화된다.
- DECISION은 중요한 판단과 근거를, APPROVAL은 승인 사실을 기록한다. 물리 저장 구조는 아직 확정하지 않는다.
- TASK는 여러 RUN을 가질 수 있다.
- RUN은 사용한 ASSET, 발생한 EVENT, VALIDATION, EVIDENCE와 연결된다.
- VALIDATION은 대상 RUN과 판정 근거를 가리킨다.
- PREVENTION은 문제 유형, 검증된 Fix, 적용 Scope, 회귀 Evidence를 연결한다.
- RULE은 근거가 된 PREVENTION과 활성 범위를 추적한다.

과거 RUN, EVENT, EVIDENCE는 덮어쓰지 않는다. 오류를 정정할 때는 원본을 보존하고 새 기록을 원본과 연결한다.

별도 저장 객체의 정확한 물리 Schema는 아직 확정하지 않는다.

---

## 9. 파생 View와 SSOT 규칙

다음은 독립된 원본 데이터가 아니다.

- STATE
- DAG
- LOG
- PROGRESS
- DASHBOARD

이들은 PROJECT, TASK, RUN, EVENT, VALIDATION, EVIDENCE 등의 원본을 읽어 생성하는 View 또는 Projection이다.

규칙:

1. 같은 사실을 여러 파일에 수동으로 중복 관리하지 않는다.
2. 파생 View가 원본과 다르면 원본을 기준으로 Delta를 표시한다.
3. Dashboard의 PASS 표시는 연결된 필수 Validation과 Evidence가 없으면 승격 근거가 아니다.
4. 과거 사실은 현재 Task 계획만으로 재구성하지 않는다.
5. View 재생성 방식과 원본 우선순위는 구현 단계에서 검증한다.

---

## 10. 정상·병렬 Workflow

기본 흐름:

```text
User Request
→ 기존 SSOT 확인
→ 기존 Asset / Rule 검색
→ Classifier
→ Router
→ 필요한 경우 Generator
→ Task
→ Scheduler
→ Caller
→ Script / Skill / 필요한 Agent
→ Run
→ Validator
→ Gate
→ 다음 Task 또는 완료
```

위 흐름은 논리 책임을 보여준다. 모든 작은 Task에서 12개 역할을 별도 단계나 별도 구성요소로 강제하지 않으며, 안전한 경우 역할을 통합하거나 불필요한 단계를 생략할 수 있다. 자동 최대는 Layer 최대 또는 Agent 최대를 뜻하지 않는다.

최소 필수 계약:

```text
Reuse 확인
→ Task 계약
→ Run 기록
→ 필요한 Validation
→ Gate 판정
→ Evidence
```

### 10.1 단계별 계약

1. **User Request**: 원하는 결과, 제약, 완료 기준을 확인한다.
2. **SSOT / Reuse 확인**: 현재 기준과 기존 Asset·Rule을 먼저 찾는다.
3. **분류와 경로 선택**: 작업의 종류, 위험, 필요한 처리 경로를 정한다.
4. **Task 계약**: 입력, 출력, 권한, Validation, 금지 사항과 함께 Write Owner, Write Scope, Shared Resources, `depends_on`을 고정한다.
5. **Scheduling**: 선행관계와 충돌을 검사하고 순서를 정한다.
6. **Execution**: Caller가 확정된 수단을 최소 권한으로 호출하고 RUN을 남긴다.
7. **Validation**: 실행자 의도와 분리된 기준으로 실제 결과를 검사한다.
8. **Gate**: 근거에 따라 진행, 대기, 중단 또는 사용자 결정을 선택한다.
9. **Completion**: 결과, Evidence, 미해결 사항과 다음 행동을 전달한다.

### 10.2 Rule과 Hook

Rule은 각 단계에서 적용할 조건이다. Hook은 특정 Event가 발생했을 때 정해진 검사나 작업을 호출한다. 둘을 Workflow 끝에 한 번씩 거치는 고정 Layer로 모델링하지 않는다.

### 10.3 병렬 Workflow

병렬 실행은 기본 목표가 아니라 독립성이 확인된 Task의 처리 방식이다.

```text
Task 후보
→ 선행관계 확인
→ 파일 충돌 확인
→ 기능 영역 충돌 확인
→ 공유 자원 충돌 확인
→ 권한 충돌 확인
→ 독립 Task만 병렬 배정
→ 각 Task 별도 Run
→ 각 결과 별도 Validation / Evidence
→ Gate에서 통합 가능 여부 판정
```

- Scheduler가 안전한 병렬 후보를 결정하고 Caller가 확정된 대상을 호출한다.
- 각 Task는 하나의 Write Owner를 유지한다.
- 같은 파일이나 공유 자원을 쓰는 Task는 동시에 실행하지 않는다.
- Write Scope 밖 쓰기가 필요하면 실행을 `BLOCK`하거나 충돌 없는 안전한 순차 실행으로 내린다.
- 공유 원본 기록의 쓰기 책임은 하나로 일원화한다. 이를 위한 Coordinator 구현은 현재 확정하지 않는다.
- 병렬 결과를 합치는 행위도 별도 Validation 대상이다.
- 독립성이 불명확하면 순차 실행 또는 `WAIT`를 선택한다.

---

## 11. Validation과 Gate

### 11.1 상태 3축

다음 세 축을 분리한다.

- **Execution Status**: 실행 시도의 진행·성공·오류 상태
- **Validation Status**: 검사 실행과 `NOT_RUN / RUNNING / PASS / FAIL / ERROR` 상태
- **Gate Decision**: `PROCEED / WAIT / BLOCK / USER-GATE` 판정

RUN은 실제 실행 시도라는 개념을 유지한다. 세 축의 물리 Schema는 아직 확정하지 않는다.

### 11.2 Validation 최소 상태

| 상태 | 의미 |
|---|---|
| `NOT_RUN` | Validator를 실행하지 않음 |
| `RUNNING` | Validator 실행 중 |
| `PASS` | 대상 결과가 기준을 충족함 |
| `FAIL` | 대상 결과가 기준을 충족하지 못함 |
| `ERROR` | Validator 자체가 정상적으로 검사를 수행하지 못함 |

`FAIL`과 `ERROR`를 구별한다. 검사 환경이 고장난 상태를 제품 실패로 기록하지 않고, 제품이 기준을 위반한 상태를 검사 오류로 숨기지 않는다.

### 11.3 필수 Validator 고정 계약

- 필수 Validator 목록은 RUN 시작 전에 해당 Task 계획 버전에 고정한다.
- 필수 Validator 목록이 비어 있으면 Task를 PASS로 판정할 수 없다.
- 쉬운 검사 하나가 PASS했다고 필수 기능 검사를 생략하지 않는다.
- 필수 Validator가 모두 PASS하지 않았다면 Task 전체를 PASS로 간주하지 않는다.
- `0 tests`, 미활성 Gate, 검사 미실행을 PASS로 해석하지 않는다.
- Fix로 필수 Validator 목록이나 완료 기준을 약화·삭제해 PASS하는 것을 금지한다.
- Validator의 판정 기준 또는 판정 로직 변경도 Validation 기준 변경으로 취급하며, Task 계획 버전 변경과 New Run 재검증 대상이다.
- 필수 Validator 또는 완료 기준을 약화·축소하는 Task 계획 변경은 Write Owner 단독으로 확정할 수 없다. Gate 판정을 거치며 필요한 경우 `USER-GATE`로 올린다.
- Validator 추가, 기준 강화 또는 의미가 변하지 않는 중립 변경을 모두 `USER-GATE`로 강제하지 않는다. 세부 Approval 기준은 Unresolved를 따른다.
- Validator 목록 또는 완료 기준 변경은 Task 계획 버전 변경으로 기록하고 New Run으로 재검증한다.
- Validator는 실행자의 자기평가나 추정 원인이 아니라 실제 결과와 고정된 기준을 검사한다.
- Validator 독립성을 구현하는 구체적인 프로세스는 Unresolved다.
- 각 판정은 재현 가능한 Evidence 위치와 연결한다.

### 11.4 Gate 판정

Gate는 다음을 함께 검토한다.

- 필수 Validation 상태
- 필요한 Permission
- 필요한 Approval
- Risk와 복구 가능성
- Evidence 완전성

자동으로 판단 가능한 조건은 자동 Gate에서 처리하고, 중요한 결정만 `USER-GATE`로 올린다.

---

## 12. Recovery Workflow

기본 흐름:

```text
Validation FAIL
→ Fail Event
→ Fingerprint
→ 동일 실패 여부 확인
→ 기존 Prevention 검색
→ Root Cause Hypothesis
→ 원인 확인
→ Confirmed Root Cause
→ Fix
→ New Run
→ Revalidation
→ PASS
→ Evidence
→ Prevention Candidate
```

Recovery 진입은 실패 종류에 따라 분리한다.

```text
Validation FAIL
→ 결과 / 제품 Recovery

Validator ERROR
→ Validator / 검사환경 Recovery

Execution ERROR
→ Caller / 실행환경 / Permission Recovery

기준 문제
→ Decision 또는 필요한 USER-GATE
```

Validator ERROR는 제품 재시도 횟수에 포함하지 않는다.

### 12.1 Fingerprint

Fingerprint는 오류 종류, 대상, 단계, 환경 등 반복 실패를 비교할 최소 정보를 정규화한 식별값이다. 세부 정규화 방식은 아직 Unresolved다.

### 12.2 가설과 확인된 원인

- `Root Cause Hypothesis`: 증거로 검증해야 하는 원인 후보
- `Confirmed Root Cause`: 관찰 또는 시험으로 확인된 원인

가설을 확인된 사실처럼 기록하지 않는다.

### 12.3 재시도 중단

동일 Fingerprint가 새로운 해결 조치나 근거 없이 반복되면 Blind Retry를 중단한다. 환경 문제, Validator 오류, 불명확한 기준과 실제 제품 결함을 먼저 구별한다.

재시도 횟수나 자동 복구 한도의 정확한 값은 구현 전에 Risk와 Runtime Evidence를 기준으로 정한다.

---

## 13. Prevention과 Rule 수명주기

기본 흐름:

```text
Verified Fix
→ Prevention Candidate
→ 기존 Prevention / Rule / Asset 검색
→ 적용 Scope 확인
→ 회귀 검증
→ Rule Candidate
→ Verified
→ Active
```

### 13.1 Prevention

과거 문제에서 배운 검증된 해결 지식이다. 최소한 다음을 포함한다.

- 정규화된 문제 유형
- 확인된 Root Cause
- 적용한 Fix
- 적용 조건과 제외 조건
- 성공한 New Run과 Evidence
- 회귀 검증 결과

### 13.2 Rule

미래 실행에 적용할 조건과 행동 정책이다. Rule은 후보, 검증, 활성, 비활성 또는 폐기 상태를 구별할 수 있어야 한다.

한 번 성공한 Fix를 즉시 전역 Rule로 만들지 않는다. 국소 해결인지 일반화 가능한 해결인지 별도 검증한다.

Rule이 `Active`로 전환되려면 Evidence, Regression Validation, Gate Decision이 모두 필요하다. 전역 또는 Core Scope Rule 활성화에는 `USER-GATE`가 필요하다. Local Scope 자동 활성화의 세부 기준은 Unresolved다.

---

## 14. 중단과 재개

### 14.1 Checkpoint와 Chunk

- **Checkpoint**: 실행 작업의 안전한 중간 저장 지점
- **Chunk**: 사용자에게 긴 결과를 전달하는 출력 분할 단위

작업 완료 위치와 결과 전달 위치를 구별한다.

### 14.2 재개 규칙

- 중단 후 완료된 작업을 처음부터 반복하지 않는다.
- 마지막으로 검증된 Checkpoint부터 재개한다.
- Side Effect가 있는 작업은 Checkpoint 표기만 믿지 않고 실제 외부 상태를 확인한다.
- 이미 적용된 Side Effect가 중복되지 않도록 멱등성 또는 사전 상태 검사를 사용한다.
- 재개 후 실행은 새로운 RUN으로 추적한다.

정확한 Checkpoint 저장 형식은 구현 전에 결정한다.

---

## 15. 외부 연결 경계

Beta의 기본 구조는 Local Core 중심이다.

```text
A Local Core
→ External Port
→ Adapter
→ Plugin / Remote / API / External Tool
```

### 15.1 현재 계약

- Plugin, Adapter, Desktop Commander Remote, 외부 API, 외부 병렬 Agent는 Core의 필수 구성요소가 아니다.
- 현재 단계에서는 Adapter나 Plugin을 구현하지 않는다.
- 향후 필요성이 Evidence로 확인되면 Core를 특정 제품에 결합하지 않고 External Port를 통해 연결한다.

### 15.2 External Port Design Notes

다음은 향후 계약을 검토할 때 사용할 비규범 Design Notes다.

- 요청 ID와 계약 버전
- 요청 범위와 권한
- 입력과 기대 출력
- 시간 제한과 취소
- 성공, 대상 실패, 연결 오류, 시간 초과 구별
- Evidence 위치
- 중복 요청 처리

실제 Port Schema와 장애 격리 방식은 Later / Implementation Decision으로 이월한다. 현재 확정 계약은 External Port 경계를 유지하고 Adapter를 구현하지 않는 것까지다.

---

## 16. Downloads Intake 방향

Downloads는 여러 프로젝트가 공유하는 수신 위치이며 SSOT가 아니다.

향후 개념 흐름:

```text
Downloads
→ Project Classifier
→ Beta
→ Document Classifier
→ Order / Reference / Evidence
→ 지정 폴더
```

### 16.1 분류 책임

- **Project Classifier**: 어느 프로젝트의 파일인지 판정
- **Document Classifier**: 해당 프로젝트 안에서 어떤 종류의 문서인지 판정

### 16.2 Intake 원칙

- AI Agent 분류보다 명확한 Metadata, Rule, Script를 우선한다.
- 판정이 불명확하면 자동 이동하지 않는다.
- 승인되어 `C:\Obsidian\Beta`에 들어온 파일을 기준으로 한다.
- 자동 덮어쓰기를 기본 허용하지 않는다.
- Source, Destination, 크기, Hash 등 이동 Evidence를 남길 수 있어야 한다.

현재 Intake Script는 구현하지 않는다. 이 절은 Architecture 방향만 정의한다.

---

## 17. Asset / Reference / Archive

| 분류 | 의미 | 실행·재사용 |
|---|---|---|
| Asset | Beta에서 실제 실행·재사용하도록 승인된 자산 | 승인 Scope 안에서 가능 |
| Reference | 현재 설계·비교에 사용하는 참고자료 | 자동 실행·재사용 금지 |
| Archive | 현재 기준에서 제외되어 추적·복구 목적으로 보존하는 과거자료 | 현재 입력으로 자동 사용 금지 |

현재 Reference:

- `harness-visual-review.html`: A 설계 검토용 시각 Reference
- `harness_loop_full_korean-main.zip`: B 외부 Reference

Reference를 Asset으로 승격하려면 별도 검토, 승인, Validation, Evidence가 필요하다. ZIP은 자동 압축 해제하거나 실행하지 않는다.

---

## 18. 구현 Workflow와 변경 통제

기본 흐름:

```text
User Request
→ SSOT / Asset 확인
→ 설계 검토
→ 필요한 경우 User Approval
→ Order
→ Task
→ 구현
→ Validator
→ Evidence
→ Review
→ 완료
```

### 18.1 현재 역할

- Codex: Write Owner
- Claude Code: Reviewer

이는 현재 Beta 운영 역할이며 Harness Runtime의 영구 구성요소가 아니다. Reviewer의 Architecture Review는 실제 결과를 검사하는 Validation과 구별한다. 구현자는 Architecture SSOT와 Order Scope를 임의로 확대하지 않는다.

### 18.2 Architecture 변경

구현 중 Architecture 변경이 필요하면 다음 흐름을 사용한다.

```text
Implementation Evidence
→ Change Proposal
→ Review
→ 필요한 경우 User Approval
→ 새 Architecture Version
```

구현 편의를 위해 현재 Architecture를 조용히 변경하거나 Dashboard만 맞추지 않는다.

---

## 19. MVP Test 1~7

| Test | 이름 | 확인 질문 |
|---|---|---|
| MVP Test 1 | Reuse | 기존 기능이 있으면 새로 만들지 않는가? |
| MVP Test 2 | Ownership | 하나의 Task에 하나의 Write Owner가 유지되는가? |
| MVP Test 3 | Safe Parallel | 독립성이 확인된 Task만 병렬 실행되는가? |
| MVP Test 4 | Bottleneck | 같은 실패를 근거 없이 반복하지 않는가? |
| MVP Test 5 | Prevention | 검증된 해결 경험이 다음 작업에서 재사용되는가? |
| MVP Test 6 | User Gate | 중요한 결정에서만 사용자에게 질문하는가? |
| MVP Test 7 | Resume | 중단 후 완료 부분을 반복하지 않고 정확한 지점에서 재개하는가? |

모든 MVP Test 판정은 입력과 Task 계획 버전, Run ID, Validation 결과, Evidence 위치를 연결한다. 이름이나 체크 표시만으로 PASS를 선언하지 않는다.

- MVP Test 4를 실행하기 전에 재시도와 중단 기준이 필요하다.
- MVP Test 6을 실행하기 전에 사용자 승인의 최소 기준이 필요하다.

MVP PASS는 MVP Test 1~7 모두의 실행 Evidence로 증명한다.

---

## 20. 사용자 Workflow와 기본 View

비개발자인 사용자가 내부 Router, Caller, Agent 구조를 직접 관리하지 않도록 한다.

기본 사용자 Workflow:

1. 원하는 결과를 말한다.
2. 시스템이 현재 SSOT와 기존 자산을 확인하고 준비한다.
3. 중요한 결정이 있을 때만 사용자가 승인한다.
4. 허용 범위 안에서 자동 실행한다.
5. 자동 검증한다.
6. 문제가 있으면 허용된 복구 범위 안에서 원인을 확인하고 재실행한다.
7. 사용자가 결과와 Evidence를 확인한다.

기본 화면은 다음 정보를 우선한다.

- 현재 작업
- 실제 진행 상태
- Validation 상태
- 병목과 실패 분류
- 사용자 승인 필요 여부
- 마지막 Evidence
- 결과와 다음 단계

내부 Agent, Router, Caller, 상세 Event는 필요할 때 펼쳐 본다. 진행률은 완료된 원본 기록에서 계산하며, 결과 전달 완료와 작업 실행 완료를 필요하면 분리해 보여준다.

---

## 21. 제품화 Roadmap

기본 순서:

```text
Architecture SSOT
→ Cross Review
→ User Approval
→ v1.0 FROZEN
→ Local Core MVP
→ MVP Test 1~7
→ Runtime Evidence
→ MVP Freeze
→ Windows EXE
→ 실제 운영
→ Evidence 분석
→ 필요한 기능만 확장
```

PWA, Plugin, Adapter, Remote 통합, Orca 및 외부 병렬 실행은 미리 확정하지 않는다. 실제 운영 Evidence로 필요성, 보안, 비용, 유지보수 효과가 확인된 경우에만 별도 Gate에서 검토한다.

Roadmap 항목은 계획이다. 해당 Task의 Evidence가 없으면 완료 사실로 표시하지 않는다.

---

## 22. 문서·버전·추적 규칙

### 22.1 문서 형식

- Architecture SSOT: Markdown
- 사용자용 Visual Guide: HTML
- Markdown Architecture가 기준이며 HTML은 파생 설명 자료다.

### 22.2 Version과 Status

Version과 Status를 분리한다.

```text
v1.0 DRAFT
→ v1.0 REVIEW
→ v1.0 FROZEN
```

FROZEN 이후 작은 Architecture 변경:

`v1.0 → v1.1`

큰 Architecture 변경:

`v1.x → v2.0`

상태 변경만으로 Version을 올리지 않는다.

### 22.3 추적 정보

Architecture는 현재 결정 결과와 설계 계약을 기록한다. 향후 중요한 Decision 기록은 가능한 경우 다음을 연결한다.

- **Intent**: 왜 시작했는가?
- **Alternatives**: 어떤 대안을 검토했는가?
- **Decision / Reason**: 무엇을 왜 선택했는가?
- **Evidence**: 결정 근거 또는 실제 발생 사실을 무엇으로 확인하는가?
- **Impact**: 어떤 범위와 후속 작업에 영향을 주는가?

Evidence는 실제 발생 사실을 증명하며 Decision의 선택 이유를 대신하지 않는다.

### 22.4 작성 원칙

- 몇 개월 뒤에도 약 3분 안에 핵심을 찾을 수 있게 한다.
- 프로젝트 내부 약어를 최소화한다.
- 표준 기술 약어는 처음 등장할 때 의미를 설명한다.
- 현재 계획과 과거 실행 사실을 섞지 않는다.
- Done / Now / Next를 구별한다.
- 문서 종료를 명확히 표시한다.

---

## 23. 설계 단계 경계

이 문서의 Version은 `v1.0`, Status는 `DRAFT`다. DRAFT는 설계 검토 단계이며 Local Core MVP 구현 또는 Runtime 검증 완료를 의미하지 않는다.

현재 Architecture 상태와 운영 Done / Now / Next의 원본은 `Beta-Index.md`를 따른다. 이 문서에서는 운영 상태를 중복 관리하지 않는다.

---

## 24. Out of Scope

현재 다음 작업은 하지 않는다.

- Local Core MVP 코딩
- Windows EXE 제작
- PWA 제작
- Plugin 구현
- Adapter 구현
- Intake Script 구현
- Desktop Commander 상시 연동
- Orca 기본 통합
- 복잡한 Database 구축
- B 구조 또는 코드의 자동 복사
- Reference의 자동 Asset 승격
- 사용자용 HTML Visual Guide 생성

---

## 25. Unresolved

### 25.1 핵심 Unresolved

- Fingerprint 세부 정규화 방식
- 재시도 횟수와 자동 복구 한도
- Prevention에서 Rule로 승격하는 세부 기준
- 사용자 승인 대상과 Approval 재확인 조건의 세부 목록
- Checkpoint Side Effect 재검증의 세부 계약
- Validator 독립성을 구현하는 실제 프로세스
- Local Scope Rule 자동 활성화의 세부 기준

### 25.2 Later / Implementation Decisions

- Local Core의 정확한 구현 언어
- 실제 물리 저장 형식과 JSON, SQLite, Markdown 또는 혼합 방식 선택
- 데이터 Schema와 ID 생성 세부 규칙
- EXE 사용자 인터페이스 기술
- Agent 호출 인터페이스
- Rule의 만료, 비활성화, 충돌 해결 방식
- Runtime 비용 측정 가능 범위와 단위
- External Port의 실제 Schema와 장애 격리 방식
- PWA 통신 방식
- Orca 필요성
- B 코드 직접 재사용 시 세부 라이선스와 의존성 검토

### 25.3 현재 확정된 기록·검증 원칙

- 과거 RUN, EVENT, EVIDENCE는 덮어쓰지 않는다. 정정은 새 기록을 원본과 연결한다.
- Validator는 실행자의 자기평가나 추정 원인이 아니라 실제 결과와 고정된 기준을 검사한다.

Unresolved 항목은 구현 과정에서 조용히 확정하지 않는다. 필요한 시점에 Decision 또는 Change Proposal로 올리고 Review와 필요한 User Approval을 거친다.

---

## 26. Decision 후보

Architecture는 현재 결정 결과와 계약을 기록한다. 모든 세부 사항을 별도 ADR(Architecture Decision Record)로 만들지는 않는다. 다음 표는 현재 Architecture 전체 방향에 반영된 중요한 결정이다.

| Intent | Decision | Reason | Result |
|---|---|---|---|
| A의 목적이 외부 구현에 끌려가지 않게 한다 | A를 기준, B를 Reference로 둔다 | 외부 구조의 자동 복제와 불필요한 결합을 막기 위해서다 | B 채택은 별도 검토·Validation·Evidence를 거친다 |
| 단순 작업의 비용과 실패 가능성을 줄인다 | Local Core와 Reuse Before Create를 우선한다 | 기존의 결정적 수단이 새 Agent 구현보다 단순하고 검증하기 쉽다 | 자동화 선택 전에 기존 Asset과 Rule을 검색한다 |
| 실행 이력을 정확히 보존한다 | TASK와 RUN, 현재 View와 EVENT/EVIDENCE를 구별한다 | 현재 계획이 과거 실패와 실행 사실을 덮지 않게 하기 위해서다 | 재시도는 새 RUN으로 남고 View는 원본에서 파생된다 |
| 검증 신뢰성을 유지한다 | 실행, Validator, Gate 책임을 구별한다 | 실행자의 의도와 검사 오류가 PASS 판정에 섞이지 않게 하기 위해서다 | 필수 Validator PASS와 Evidence가 승격 조건이 된다 |
| 외부 도구 변화가 Core에 퍼지지 않게 한다 | External Port 경계만 먼저 설계한다 | 필요성이 확인되지 않은 Plugin과 Adapter를 Core 필수 요소로 만들지 않기 위해서다 | 실제 연결은 Runtime Evidence 이후 별도 결정한다 |

별도 `Decisions.md`는 이번 Task에서 생성하지 않는다. 향후 Decision 문서가 필요하면 별도 Order와 Review를 거친다.

향후 Decision 기록은 `Intent / Alternatives / Decision / Reason / Evidence / Impact`를 구별한다. Evidence는 실제 발생 사실의 증명이며 설계 선택의 설명과 혼합하지 않는다.

---

## 27. Architecture Review Checklist

`v1.0 REVIEW`로 상태를 바꾸기 전에 다음을 확인한다.

- [ ] A가 Architecture 기준이고 B가 Reference라는 경계가 일관적인가?
- [ ] 승인된 핵심 원칙이 빠짐없이 반영되었는가?
- [ ] 12개 논리 역할의 책임과 금지 경계가 충돌하지 않는가?
- [ ] Task, Run, Validation, Evidence가 구별되는가?
- [ ] 파생 View가 원본 SSOT처럼 서술되지 않았는가?
- [ ] FAIL과 ERROR, 가설과 확인된 원인이 구별되는가?
- [ ] Recovery와 Prevention에 New Run 및 Revalidation이 포함되는가?
- [ ] 필수 Validator를 우회해 PASS할 수 없도록 되어 있는가?
- [ ] External Port가 특정 제품 구현을 선확정하지 않는가?
- [ ] Out of Scope와 Unresolved가 구현 사실처럼 서술되지 않았는가?
- [ ] MVP Test 1~7이 실행 Evidence를 요구하는가?
- [ ] 문서가 현재 계획과 과거 사실을 구별하는가?

이 체크리스트는 Review 준비용이다. 체크 표시만으로 `REVIEW` 또는 `FROZEN`으로 승격하지 않는다.

---

## 28. 상태 참조

현재 Architecture와 Status, Done / Now / Next의 원본은 `Beta-Index.md`다. 이 Architecture는 운영 상태를 수동으로 중복 관리하지 않는다.

---

## 29. 문서 종료

이 문서는 Beta 프로젝트의 Harness A Architecture v1.0 DRAFT다.

구현 또는 승격 판단은 이 문서만으로 완료되지 않으며, 해당 Task의 Validation과 Evidence가 필요하다.

=== DOCUMENT END ===
