# Beta Terminology Standard

## 문서 정보

| 항목 | 값 |
|---|---|
| Project | Beta |
| Document | Terminology Standard |
| Role | Architecture Terminology SSOT Draft |
| Status | FROZEN |
| Parent Architecture | `Harness-A-Architecture-v1.0.md` |
| Write Owner | Codex |
| Reviewer | Claude Code |

Terminology는 Beta Architecture에서 사용하는 용어의 의미와 표준 표현을 소유한다. Architecture의 설계 계약, Decision의 선택 이유, Evidence의 실제 사실, `Beta-Index.md`의 현재 상태를 대신하지 않는다.

---

## 1. 목적과 범위

이 문서는 용어 Drift, 문자 오류, 오탐, 잘못된 Routing 또는 Validation, 유지보수 병목을 줄이기 위한 Canonical Terminology SSOT DRAFT다.

- Canonical Name과 허용 Alias를 정의한다.
- 혼동되는 용어 사이의 경계를 정의한다.
- Deprecated 표현을 명시한다.
- 관련 Intent, ADR 또는 Decision, Result, Evidence의 위치만 연결한다.
- 새로운 Runtime 기능이나 물리 Schema를 정의하지 않는다.
- Terminology Validator를 구현하지 않는다.

---

## 2. SSOT / SRP 소유권

| 문서 | 단일 책임 |
|---|---|
| `Terminology.md` | 용어 의미와 표준 표현 |
| `Harness-A-Architecture-v1.0.md` | 설계 계약 |
| `Beta-Index.md` | 현재 Architecture, Done / Now / Next, 주요 위치 |
| `Order-History.md` | 시간순 Timeline View |
| Order | 승인된 실행 계약 |
| Evidence | 실제 실행·검증 사실 |
| 향후 Decision 기록 | Intent, Alternatives, Decision, Reason, Impact |

같은 정의를 여러 문서에서 독립 SSOT로 관리하지 않는다. Architecture에는 이해에 필요한 최소 문맥 설명을 유지할 수 있으나, 표준 의미가 충돌하면 Terminology의 정의를 확인하고 Architecture 변경 절차로 Delta를 해소한다.

---

## 3. Canonical Term Registry

각 행은 `Term ID / Canonical Name / Korean Name / Description / Purpose / Responsibility / Allowed Aliases / Prohibited or Deprecated Terms / Not Same As / Trace References` 구조를 따른다.

| Term ID | Canonical Name | Korean Name | Description | Purpose | Responsibility | Allowed Aliases | Prohibited / Deprecated Terms | Not Same As | Trace References |
|---|---|---|---|---|---|---|---|---|---|
| TERM-001 | Gate | 실행 판정 관문 | Runtime에서 Validation, Permission, Approval, Risk, Evidence를 바탕으로 다음 진행 여부를 판정하는 논리 역할 | 안전한 진행 결정 | `PROCEED / WAIT / BLOCK / USER-GATE` 중 결정 | 실행 관문 | Review Gate, MVP Gate | MVP Test, Architecture Review | Architecture §7, §11; Order-003 §7.4 |
| TERM-002 | USER-GATE | 사용자 결정 필요 상태 | 사용자 판단이 필요한 Runtime 상태 | 자동 처리 범위를 넘어선 결정을 사용자에게 올림 | 범위·권한·위험 등 필요한 결정을 요청 | 사용자 관문 | Runtime 의미의 Decision Gate | 일반 User Approval, MVP Test, Architecture Review | Architecture §5.10, §7, §11; Order-003 §6.3 |
| TERM-003 | MVP Test | 최소 제품 검증 시험 | Architecture 원칙이 MVP에서 실제 실행 Evidence로 검증되는지 확인하는 시험 | MVP 가설 검증 | 입력·계획 버전·Run·Validation·Evidence 연결 | MVP 검증 시험 | MVP Gate | Runtime Gate | Architecture §19; Order-003 §7.4 |
| TERM-004 | Architecture Review | Architecture 검토 | Architecture의 일관성·완전성·책임 경계·누락·모순을 검토하는 활동 | 설계 품질 검토 | 설계 문제와 수정 필요성을 판정 | Architecture Cross Review | Review Gate | Validation, Runtime Gate | Architecture §7, §18, §27; Order-002 §8 |
| TERM-005 | Review Checklist | 검토 체크리스트 | Review에서 확인할 항목 목록 | 검토 범위 누락 방지 | 확인 항목을 구조화하되 상태 승격을 대신하지 않음 | Architecture Review Checklist | Review Gate | Gate Decision, Validation 결과 | Architecture §27; Order-002 §10 |
| TERM-006 | Validation | 검증 | 실제 결과를 사전에 고정된 기준과 비교하는 검사 | 결과 적합성 확인 | 실제 결과·기준·상태·Evidence 연결 | 결과 검증, Validation 검사 | Review | Architecture Review, Gate | Architecture §11; Order-001 §4 Change 1 |
| TERM-007 | Validator | 검증기 | 실제 결과와 고정된 기준을 검사하고 Validation 결과를 반환하는 논리 역할 | 독립적 판정 생성 | 자기평가가 아닌 관찰 결과 검사 | 검증 도구 | Reviewer | Review, Gate | Architecture §7, §11; Order-003 §6.1 |
| TERM-008 | Review | 검토 | 설계·코드·Decision의 적절성·일관성·완전성을 검토하는 활동 | 품질과 판단의 타당성 확인 | 문제와 근거 및 권고를 제시 | 설계 검토, 코드 검토 | Validation | Runtime Gate | Architecture §7, §18; Order-002 §6 |
| TERM-009 | Order | 실행 계약 | 승인된 작업 지시와 Scope를 기록한 계약 | 실행 권한과 경계 고정 | Write Scope·금지사항·Validation·종료조건 정의 | 작업 지시 | Task | Decision, Approval | Architecture §8; Order-003 전체 |
| TERM-010 | Task | 작업 계약 | 현재 수행할 구체적 작업 단위 | 목표와 완료 기준 고정 | Owner·Write Scope·Shared Resources·depends_on·계획 버전 관리 | 작업 계약, Task 계약 | Order | Run, Project | Architecture §8, §10 |
| TERM-011 | Run | 실행 시도 | 특정 Task 계획 버전에 대한 실제 한 번의 실행 | 시도별 사실 보존 | 실행 상태와 사용한 계획 버전 및 결과 추적 | 실행 회차 | Task 실행 결과 | Task, Event | Architecture §8, §11 |
| TERM-012 | Event | 발생 사실 | 실제로 발생한 사실의 기록 | 시간순 사실 보존 | 과거 기록을 덮어쓰지 않고 정정 기록 연결 | 사건 기록 | Log 항목 | Task 계획, View | Architecture §8, §9 |
| TERM-013 | Evidence | 근거 | 실제 실행 또는 Validation 사실을 확인할 수 있는 자료 | 주장과 판정 검증 | Run·Validation·Result와 추적 가능하게 연결 | 실행 근거 | 보고 | Decision 이유, Reference | Architecture §8, §11; Order-003 §7.6 |
| TERM-014 | Asset | 승인 자산 | Beta에서 실제 실행·재사용하도록 승인된 자산 | 검증된 재사용 | 승인 Scope와 상태 관리 | 실행 자산 | 참고자료 | Reference, Archive | Architecture §8, §17 |
| TERM-015 | Reference | 참고자료 | 현재 설계·비교에 사용하는 자료 | 비교와 학습 | 자동 실행 또는 Asset 승격 금지 | 참조 자료 | Asset | Asset, Archive | Architecture §4, §17 |
| TERM-016 | Archive | 보존 자료 | 현재 기준에서 제외되어 추적·복구를 위해 보존하는 과거자료 | 역사와 복구 보존 | 현재 실행 입력으로 자동 사용하지 않음 | 보관 자료 | Reference | Asset, Reference | Architecture §8, §17 |
| TERM-017 | Prevention | 예방 지식 | 과거 문제에서 배운 검증된 해결 지식 | 재발 방지 | 문제 유형·Root Cause·Fix·Scope·회귀 Evidence 연결 | 예방 지식, Prevention 지식 | Rule | 단일 Fix, Rule | Architecture §13, §25 |
| TERM-018 | Rule | 실행 규칙 | 미래 실행에 적용할 조건과 행동 정책 | 일관된 행동 제어 | 후보·검증·활성·범위 상태 관리 | 실행 규칙, Rule 정책 | Prevention | Prevention, Hook | Architecture §7, §13 |
| TERM-019 | Hook | 이벤트 훅 | 특정 Event에서 정해진 동작을 호출하는 연결 | 필요한 시점의 자동 호출 | 정책을 새로 정하지 않고 기존 동작 호출 | 자동 발동 장치 | Rule | Rule, Script | Architecture §7, §10.2 |
| TERM-020 | Skill | 표준 작업 절차 | 재사용 가능한 절차와 지식을 정의한 자산 유형 | 반복 작업의 일관성 | 절차·지식 제공 | 표준 작업 절차, Skill 절차 | Agent | Script, Agent | Architecture §7 |
| TERM-021 | Script | 결정적 스크립트 | 결정적이고 반복 가능한 로컬 작업 수단 | 단순 반복 자동화 | 정해진 입력에 정해진 절차 수행 | 자동화 스크립트 | Skill | Skill, Agent | Architecture §6, §7 |
| TERM-022 | Agent | 판단 수행자 | 문맥 판단, 복잡한 계획, 코딩, Root Cause 분석을 수행하는 역할 또는 수단 | 비정형 문제 처리 | 필요한 경우에만 판단 수행 | AI Agent | 자동화 전체 | Script, Skill | Architecture §6, §7 |
| TERM-023 | Classifier | 분류기 | 요청·Task·오류의 종류, 위험, 난이도를 분류하는 논리 역할 | 올바른 처리 준비 | 분류만 수행하고 직접 수정하지 않음 | 분류 역할 | Router | Router, Caller | Architecture §7 |
| TERM-024 | Router | 경로 선택기 | 기존 자산을 고려해 처리 경로를 선택하는 논리 역할 | 적합한 처리 방식 선택 | 실행 허가나 우선순위를 대신 정하지 않음 | 라우터 | Classifier | Classifier, Scheduler | Architecture §7 |
| TERM-025 | Generator | 생성기 | 필요한 Task·Plan·문서·설정 초안을 생성하는 논리 역할 | 필요한 산출물 초안 생성 | 초안을 승인된 결과로 자동 승격하지 않음 | 생성 역할 | Agent | Agent, Script | Architecture §7 |
| TERM-026 | Scheduler | 순서 관리자 | 우선순위, 의존관계, 실행 순서, 안전한 병렬 후보를 결정하는 논리 역할 | 충돌 없는 순서 결정 | Write Scope·Shared Resources·depends_on 고려 | 스케줄러 | Coordinator | Caller, Gate | Architecture §7, §10.3 |
| TERM-027 | Caller | 호출기 | 확정된 Asset 또는 실행 수단을 지정 입력으로 호출하는 논리 역할 | 통제된 실행 시작 | Scope와 권한을 임의 확대하지 않음 | 실행 호출기 | Executor | Scheduler, Agent | Architecture §7, §12 |
| TERM-028 | Checkpoint | 실행 중간 저장점 | 실행 작업의 안전한 중간 저장 지점 | 중단 후 안전한 재개 | 마지막 검증 지점과 Side Effect 확인 | 중간 저장 지점 | 저장점 단독 사용 시 의미 불명확 | Chunk | Architecture §14 |
| TERM-029 | Chunk | 전달 분할 단위 | 긴 결과를 사용자에게 전달하는 출력 묶음 | 전달 크기 관리 | 실행 완료 위치와 분리해 추적 | 출력 묶음 | 결과 조각 | Checkpoint | Architecture §14 |
| TERM-030 | Intent | 의도 | 무엇을 해결하려고 시작했는지 설명 | 판단 목적 보존 | 문제와 목표를 명시 | 설계 Intent, 작업 Intent | Goal | Decision, Result | Architecture §22.3; Order-003 §1 |
| TERM-031 | ADR | Architecture 결정 기록 | Architecture Decision Record로서 대안·선택·이유·영향을 기록 | 중요한 설계 판단 보존 | 중요한 Architecture Decision의 배경·대안·이유·영향을 기록 | Architecture Decision Record | 단순 회의록 | Decision, Order, Evidence | Architecture §22.3; Order-History §3 |
| TERM-032 | Result | 결과 | 실행 또는 결정으로 무엇이 바뀌었는지 나타내는 결과 | 변화 상태 표현 | 관련 Evidence와 연결 | 결과 상태 | Evidence | Evidence, Decision | Order-003 §7.6; Order-History §5 |
| TERM-033 | Decision | 결정 | 중요한 설계·운영 판단과 그 선택 | 대안 중 선택 고정 | 선택 자체와 적용 범위를 식별하고 관련 ADR·Evidence에 연결 | 설계 판단 | ADR 본문 | ADR, Approval, Evidence | Architecture §8, §22.3, §26 |
| TERM-034 | Approval | 승인 | 특정 대상과 범위에 대한 승인 사실 | 권한 있는 동의 추적 | 승인 대상·Scope·조건을 기록 | 사용자 승인 | USER-GATE | Decision, USER-GATE | Architecture §8, §11, §25 |

---

## 4. 핵심 표준 경계

### 4.1 Gate 계열

- **Gate**는 Runtime 판정 역할이다.
- **USER-GATE**는 사용자 결정이 필요한 Runtime 상태다.
- **MVP Test**는 Architecture 원칙을 실제 실행 Evidence로 확인하는 시험이며 Runtime Gate가 아니다.
- **Architecture Review**는 Architecture를 검토하는 활동이며 Validation이나 Runtime Gate가 아니다.
- **Review Checklist**는 Review 항목 목록이며 Gate Decision을 대신하지 않는다.

`MVP Test 6 — User Gate`의 `User Gate`는 시험 이름으로 유지한다. 일반 문서의 User Approval은 자동으로 Runtime `USER-GATE`로 해석하지 않는다.

### 4.2 검사와 검토

- **Validation**은 실제 결과와 사전에 고정된 기준을 비교한다.
- **Validator**는 그 검사를 수행하고 결과를 반환한다.
- **Review**는 설계·코드·Decision의 적절성과 완전성을 검토한다.

### 4.3 자료 분류

- **Asset**은 실제 실행·재사용 승인을 받은 자산이다.
- **Reference**는 현재 설계·비교 자료이며 자동으로 Asset이 아니다.
- **Archive**는 현재 기준에서 제외되어 추적·복구 목적으로 보존하는 자료다.

---

## 5. Alias와 문자 오류 정책

- Canonical Name을 기본 저장·표시 용어로 사용한다.
- Registry에 명시된 Allowed Alias만 Canonical Term으로 정규화할 수 있다.
- 의미가 여러 Canonical Term과 겹칠 수 있는 일반어 단독 Alias는 자동 정규화용 Allowed Alias로 사용하지 않는다.
- 미등록 유사어, 오타, 축약어를 AI가 임의로 Canonical Term으로 확정하지 않는다.
- 불명확한 용어는 `WARNING` 또는 `HOLD` 후보로 취급한다.
- 프로젝트 내부 약어를 최소화한다.
- 과거 Evidence와 Order 원문을 현재 표준에 맞추기 위해 조용히 덮어쓰지 않는다.
- Deprecated 표현은 `Review Gate`, `MVP Gate`, Runtime 사용자 결정 의미의 `Decision Gate`다.

---

## 6. Traceability

기본 흐름:

`Intent → ADR / Decision → Result → Evidence`

책임:

- Intent: 왜 시작했는가
- ADR / Decision: 어떤 대안을 검토했고 무엇을 왜 선택했는가
- Result: 결정 또는 실행 결과 무엇이 바뀌었는가
- Evidence: 실제로 무엇이 확인됐는가

Terminology에는 위 본문을 복사하지 않고 다음 추적 Reference만 연결한다.

| 추적 대상 | Reference |
|---|---|
| Order-002 Re-Review의 Gate 계열 용어 잔여 발견 | `Order-002-Architecture-v1.0-Draft-ReReview.md` §8, §13 |
| Order-003 Terminology 표준화 Decision | `Order-003-Architecture-Minor-Revision-and-Terminology-Standard.md` §2, §6, §7 |
| Order-003 수정 Result | `Order-History.md` §5의 Order-003 Result |
| 현재 Architecture 반영 위치 | `Harness-A-Architecture-v1.0.md` §5.10, §7, §11, §19, §27 |

---

## 7. Proposed Prevention — 미검증 예방 제안

| 항목 | 상태 |
|---|---|
| Problem | Gate 계열 용어 혼재가 Review에서 반복 탐지됨 |
| Root Cause Hypothesis | Canonical Terminology SSOT 부재 |
| Verified Fix | 아직 아님 |
| Proposal | Terminology SSOT + 향후 Terminology Validator |
| Promotion Condition | 후속 Order의 재발 방지 Evidence + 실제 재검증 |

현재 상태는 Architecture §5.8의 Prevention Candidate 요건을 아직 충족하지 않는다. 이번 Order에서는 Terminology Validator를 구현하지 않는다. 여러 Order에서 재발 방지 Evidence가 확보되고 실제 재검증을 통과한 뒤 Prevention Candidate 또는 Rule 승격을 검토한다.

---

## 8. 문서 종료

이 문서는 Beta Architecture Terminology SSOT DRAFT다.

=== DOCUMENT END ===
