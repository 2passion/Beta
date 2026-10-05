# Beta Order --- Order-021 MVP Test 1 Reuse Implementation

## 문서 정보

-   Order ID: Order-021
-   Project: Beta
-   Status: APPROVED
-   Type: MVP Test Implementation
-   Architecture / Terminology: FROZEN
-   Baseline: Phase 1 CLOSED + Common Harness reusable
-   Target: MVP Test 1 --- Reuse
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

MVP Test 2에서 검증한 Common Harness를 재사용해 MVP Test 1 Reuse를 최소
구현하고 공식 Runtime Evidence로 검증한다.

질문: 기존 승인 Asset이 있으면 새로 만들지 않는가?

최소 흐름: Asset 목록 JSON → Reuse Search → REUSE/CREATE → 실행 → 독립
Validator → 공식 Evidence. Reference는 Asset이 아니다.

## 2. 근거

Order-020 PASS, Important 2건 RESOLVED, Blocker NONE, Common Harness
재사용 가능, Test 2 공식 PASS 확정 가능. Order-016 Reuse 최소안: 작은
검색 기능, JSON Asset 목록 1개, REUSE_SEARCH Event, Asset/Reference
구별, 일치 Asset이면 REUSE, 없을 때만 CREATE+이유, 복잡 DB 금지.

## 3. Precondition

Architecture/Terminology FROZEN, Phase 1 CLOSED, Order-020 PASS, Test 2
공식 PASS 확정 가능, Common Harness 재사용 가능, Test 1 NOT VERIFIED,
Test 3\~7 NOT VERIFIED, Phase 2 없음, 기존 Asset 검색. 다르면 BLOCK.

## 4. View Sync

Beta-Index: Order-020 PASS, Common Harness loop CLOSED, Test 2 OFFICIAL
PASS, Test 1 IMPLEMENTING/NOT VERIFIED, Now/Next. Order-History:
Order-020 PASS, Test 2 OFFICIAL PASS, Order-021 상태. 과거 결과 변경
금지.

## 5. Reuse Before Create

기존 Beta Asset/Script/Validator/검색 기능/Common Harness를 먼저 검색.
없는 부분만 생성. B Reference는 참고만 하고 Asset 자동 승격 금지.

## 6. Asset/Reference 최소 데이터

MVP Fixture JSON 목록 1개. 필드: - asset_id - capability - path -
sha256 - status: approved \| reference

approved만 실행/재사용 가능. reference는 참고만. 운영 Registry 위치는
미결정. Fixture는 03_Tests/fixtures.

## 7. Reuse Search 계약

필요 시 작은 모듈 1개 수준: - capability 입력 - 목록 읽기 - exact
match - status 확인 - REUSE/CREATE 결정 - 이유 - REUSE_SEARCH payload

AI/의미 검색 금지.

## 8. REUSE_SEARCH Event

payload: requested_capability, matched_asset_ids,
selected_asset_id\|null, decision(REUSE\|CREATE), reason,
selected_path\|null, selected_sha256\|null. 실행 전에 기록. Reference는
REUSE 선택 금지.

## 9. Scenario A --- approved Asset 존재

기대: - REUSE_SEARCH가 RUN_STARTED보다 앞 - REUSE - selected_asset_id -
실행 Executor Hash = Asset SHA - 신규 Asset 생성 없음 - 정상
Run/Validation/Gate/Evidence

## 10. Scenario B --- 일치 Asset 없음

기대: - REUSE_SEARCH - approved match 없음 - CREATE + reason - reason
기록 후에만 합성 신규 실행 허용 - 생성/사용 사실 Evidence 연결
Production Asset 등록 금지.

## 11. Scenario C --- Reference만 일치

기대: - Reference match 확인 가능 - approved match 없음 - Reference
REUSE 금지 - CREATE + reason - Reference 실행 금지/원본 불변

## 12. 중복 방지

Scenario A 전후 Asset 목록 Hash 비교. PASS: 목록/개수 불변, 기존 Asset
사용. FAIL: approved 동일 capability가 있는데 새 Asset 항목/복제/새 실행
파일 생성.

## 13. Common Harness 재사용

MVP Test Plan → Reuse Scenario Executor → 내부 Run/Event → 독립 Reuse
Validator → 기존 Gate → 공식 Evidence. Reuse 전용 새 Harness/DB/STATE
금지.

## 14. Reuse Validator

Executor 자기평가를 신뢰하지 않고 Asset JSON, 전후 Hash, events.jsonl,
REUSE_SEARCH, Event 순서, 실제 Executor Hash, Run/Evidence, Reference
미실행을 직접 검사.

PASS: A: 검색 선행, approved exact match, REUSE, 실행 Hash=Asset Hash,
목록 불변, 중복 없음. B: approved 없음, CREATE, reason, reason 후 신규
실행, Evidence 연결. C: Reference match, approved 없음, Reference REUSE
금지, CREATE, Reference 미실행/불변.

## 15. Negative Test

A: approved 있는데 CREATE로 조작 → Validator FAIL/Gate BLOCK. B:
Reference를 REUSE → FAIL/BLOCK. C: REUSE_SEARCH를 RUN_STARTED 뒤로 이동
→ FAIL/BLOCK. 격리 Test에서 수행.

## 16. Core 변경 최소화

우선순위: 1. 기존 Core 2. Scenario/Fixture 3. 정말 공통 Runtime 기능
필요 시 작은 reuse.py 4. cli.py 변경은 필요 시 최소

Core 변경 시 기존 전체 회귀 수행.

## 17. Test

기존 20개 의미 보존. Reuse 정상/Negative/최소 계약 Test 추가 가능.
기존/신규/총 Test와 PASS/FAIL/ERROR 보고. 삭제/약화 금지.

## 18. 공식 MVP Test 1 Run

전체 Test PASS 후: - Test ID MVP-TEST-1 - Name Reuse - Plan Version
1.0 - change_reason_ref Order-021 기대 Execution PASS / Validation PASS
/ Gate PROCEED / 공식 Evidence+SHA / Scenario A/B/C 연결.

## 19. Evidence

공식 Evidence에 Test
ID/Name/Version/Run/Validator/Validation/Gate/Evidence
위치·Hash/Scenario 경로/Asset 전후 Hash/REUSE_SEARCH/선택 Asset
ID·Hash/Reference 미실행 근거 연결.

## 20. Preservation

작업 전 Phase 1, Test 2 Plan 1.0/1.1, Common Harness,
Architecture/Terminology/Reference 기록. 작업 후 Test 2/Phase
1/Reference 불변, Ownership Harness 동작 불변, Test 1 Evidence만 추가.

## 21. 하지 말 것

Test 3/4/5/6/7, Prevention/Rule, Fingerprint/Retry, USER-GATE,
Scheduler/WAIT, Agent/Skill/Hook, Plugin/Adapter, SQLite/DB, 운영
Registry 위치 결정, Reference 승격, Architecture/Terminology, Phase 2
금지.

## 22. Architecture Delta

기본 NONE. 필요 시 ARCHITECTURE-DELTA 보고 후 해당 구현 중단.

## 23. Index / History

완료 후 최소 갱신. Beta-Index: Order-020 PASS, Test 2 OFFICIAL PASS,
Order-021 결과, Test 1 상태, Now/Next. History: Order-020 PASS, Test 2
OFFICIAL PASS, Order-021 결과. 독립 Review 전 Test 1은
`PASS 후보 — Independent Review 대기`.

## 24. Validation

-   [ ] exact search / approved-reference 구별 / REUSE-CREATE / reason /
    검색 선행
-   [ ] A approved REUSE, Executor Hash=Asset, 중복 없음, 목록 불변
-   [ ] B no approved, CREATE, reason, reason 후 실행, Evidence
-   [ ] C Reference REUSE 금지, CREATE, Reference 불변
-   [ ] Negative 3개 모두 Validator FAIL/Gate BLOCK
-   [ ] 기존 20 Test 의미 유지 + 신규 PASS
-   [ ] Test 2/Phase 1 Evidence 불변
-   [ ] MVP-TEST-1 / Reuse / 1.0 / Order-021 / PASS/PASS/PROCEED /
    Evidence
-   [ ] 다른 Test 미구현
-   [ ] Architecture/Terminology/Reference 불변
-   [ ] 외부 패키지/DB/Agent/Phase 2 없음

하나라도 실패하면 Test 1 PASS 금지. 검사 실패는 ERROR.

## 25. 결과 보고

# Order-021 MVP Test 1 Reuse 결과

-   현재 상태 PASS/FAIL/ERROR/BLOCKED
-   View Sync
-   Reuse 구현 및 재사용 항목
-   생성/수정 파일
-   Scenario A/B/C
-   Negative A/B/C
-   Regression 기존/신규/총/PASS/FAIL/ERROR
-   공식 Test 1: ID/Name/Version/Run/Executor Hash/Validator
    Hash/Validation/Gate/Evidence/SHA/Scenario 연결/Asset Hash
-   Preservation
-   Test 상태: Test 1 PASS 후보-Review 대기, Test 2 PASS, Test 3\~7 NOT
    VERIFIED
-   Architecture Delta / Scope
-   Done/Now/Next PASS Next: Claude READ-ONLY Test 1 Independent Review
    → PASS이면 공식 PASS → 다음 Test 4 Bottleneck.
-   사용자 승인 필요 NO

## 26. 종료 조건

View Sync, 구현, Scenario, Negative Test, Regression, 공식 Run,
Evidence, Preservation, Index/History 후 종료. PASS해도 Claude 호출,
Test 4/다른 Test, Architecture 변경, Phase 2 자동 시작 금지.

=== ORDER END ===
