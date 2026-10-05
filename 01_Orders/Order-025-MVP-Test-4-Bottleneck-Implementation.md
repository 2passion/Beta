# Beta Order --- Order-025 MVP Test 4 Bottleneck Implementation

## 문서 정보

-   Order ID: Order-025
-   Project: Beta
-   Status: APPROVED
-   Type: MVP Test Implementation
-   Architecture / Terminology: FROZEN
-   Baseline: Phase 1 CLOSED + Common Harness reusable
-   Target: MVP Test 4 --- Bottleneck
-   Write Owner: Codex
-   Reviewer: Claude Code
-   Root: C:`\Obsidian`{=tex}`\Beta`{=tex}

## 1. Intent

Test 1 Reuse와 Test 2 Ownership OFFICIAL PASS를 보존하며 Test 4
Bottleneck을 최소 구현한다.

질문: 같은 실패를 새로운 해결 조치 없이 반복하지 않는가?

흐름: FAIL/ERROR → Fingerprint → 동일 실패 검색 → 변경 근거 확인 → Blind
Retry BLOCK 또는 New Run 허용 → Evidence.

Prevention은 구현하지 않는다.

## 2. 근거

Order-024 PASS. Test 1/2 OFFICIAL PASS 가능. Order-016은 Fingerprint,
동일 실패 감지, 근거 없는 Blind Retry 차단, FAIL/Validator
ERROR/Execution ERROR 구별을 요구한다. Retry 숫자는 Fixture 값이지 전역
Rule이 아니다.

## 3. Precondition

Architecture/Terminology FROZEN, Phase 1 CLOSED, Order-024 PASS, Test
1/2 OFFICIAL PASS, Test 4 NOT VERIFIED, Test 3/5/6/7 NOT VERIFIED,
Common Harness reusable, Phase 2 없음, 기존 Asset 검색 완료. 다르면
BLOCK.

## 4. View Sync

Index/History에 Order-024 PASS, Test 1/2 OFFICIAL PASS, Test 4
IMPLEMENTING/NOT VERIFIED, 다른 Test NOT VERIFIED, Now/Next를 최소 반영.
과거 결과 변경 금지.

## 5. Reuse Before Create

Common Harness, EventStore, Run/Validation/Gate/Evidence,
plan_version/hash, change_reason_ref, 기존 FAIL/ERROR, JSON/JSONL
재사용. 새 DB/Retry Engine/Agent/Scheduler 금지.

## 6. Fingerprint

동일 실패 비교용 결정적 식별값. 최소 입력: - failure_class -
failing_component - normalized_reason - validator_id 또는 executor
identity - relevant criteria/version

SHA-256 등 결정적 Hash 사용. run_id/event_id/timestamp/임시
절대경로/무관 UUID 제외. 같은 원인은 Run ID가 달라도 같은
Fingerprint여야 한다.

## 7. 실패 클래스

최소: - EXECUTION_ERROR - VALIDATION_FAIL - VALIDATION_ERROR 서로 합치지
않는다. Gate BLOCK 자체는 Root Failure로 Fingerprint하지 않는다.

## 8. Event

가능하면 기존 payload 사용. 최소: FAILURE_FINGERPRINT: failure_class,
fingerprint, normalized_reason, source_run_id, plan_version.
RETRY_DECISION: fingerprint, prior_matching_run_ids,
change_reason_ref\|null, decision(BLOCK_BLIND_RETRY\|ALLOW_NEW_RUN),
reason.

## 9. Blind Retry

동일 Fingerprint + 새로운 변경 근거 없음: - Executor/Validator 재실행
금지 - 정상 New Run 금지 - BLOCK_BLIND_RETRY - Evidence - 과거 실패 보존

동일 Fingerprint + 실제 변경: - 새 plan_version/추적 가능한 계획 변경 -
change_reason_ref 필수 - ALLOW_NEW_RUN - New Run - 과거 실패 보존

reason 문자열만 추가한 우회 금지.

## 10. Retry Limit

Fixture 값: - 계획 버전당 제품 New Run 최대 3 - Validator ERROR 최대 2 -
Execution ERROR 최대 2 전역 Rule 아님. 한도 초과 시 BLOCK까지만.
USER-GATE 실제 처리는 Test 6 범위.

## 11. Scenario A --- Validation FAIL, 근거 없음

첫 Run: 결정적 Validator FAIL → Fingerprint F1 → Gate BLOCK. 동일
재시도: 같은 failure/reason, 새 reason 없음. 기대: 같은 F1,
BLOCK_BLIND_RETRY, Executor/Validator 재실행 없음, 정상 New Run 없음,
과거 FAIL Evidence 보존.

## 12. Scenario B --- 같은 FAIL + 실제 변경

F1 실패 후: - 새 plan_version - 실제 Fixture/criteria/원인 관련 계획
변경 - change_reason_ref=Order-025-Scenario-B-Fix 기대: ALLOW_NEW_RUN,
새 Run, 수정 후 PASS/PROCEED, 과거 F1 보존. Prevention 등록 금지.

## 13. Scenario C --- Validator ERROR

첫 Validator ERROR → VE1 → BLOCK. 동일 오류 + 근거 없음 → 같은 VE1 →
Blind Retry BLOCK.

## 14. Scenario D --- Execution ERROR

첫 Executor ERROR → EE1 → BLOCK. 동일 오류 + 근거 없음 → 같은 EE1 →
Blind Retry BLOCK. Validation FAIL과 같은 Fingerprint 금지.

## 15. Scenario E --- 다른 실패

Validation FAIL과 Execution ERROR 또는 다른 normalized reason 비교.
기대: 다른 Fingerprint, 잘못된 동일 실패 차단 없음.

## 16. Normalization

결정적 최소 규칙만: 공백 정리, 명시적 Run/Event ID 제거, 명확히 변동하는
합성 Runtime Root 제거. AI/LLM/의미 추론 금지.

## 17. Common Harness

MVP Test Plan → Bottleneck Scenario Executor → 내부 Run/Event/Evidence →
독립 Validator → 기존 Gate → 공식 Evidence. 전용 Harness/DB/STATE 금지.

## 18. Validator

Executor 자기평가 불신. 직접 확인: events.jsonl, Run ID, failure_class,
reason, fingerprint, RETRY_DECISION, plan_version, change_reason_ref,
Run 폴더, 실행 여부, FAIL/ERROR/PASS Evidence.

PASS: A 동일 FAIL+근거 없음 → 같은 Fingerprint+재실행 차단 B 실제
변경+근거 → New Run+성공+과거 FAIL 보존 C Validator ERROR 반복 → 같은
Fingerprint+차단 D Execution ERROR 반복 → 같은 Fingerprint+차단 E 다른
실패 → 다른 Fingerprint

## 19. Negative

A Fingerprint에 run_id 포함 → 같은 실패 Fingerprint 달라짐 → FAIL. B
동일 Fingerprint+근거 없음인데 New Run 허용 → FAIL/BLOCK. C reason
문자열만 추가, 실제 Plan/Fix 변경 없음인데 ALLOW → FAIL/BLOCK. D
Validation FAIL과 Execution ERROR를 같은 Fingerprint로 조작 →
FAIL/BLOCK.

## 20. Retry Limit Test

Validator ERROR 2, Execution ERROR 2, 계획 버전당 New Run 3 한도를 합성
검증. 초과 → BLOCK. USER-GATE 구현 금지. 필요하면
user_gate_required_reason 같은 Evidence 표시만.

## 21. Core 변경 최소화

기존 Core/Harness → Fixture/Scenario → 꼭 필요할 때 작은 fingerprint.py
또는 bottleneck.py → cli.py 최소 변경 순서. 역할마다 프로그램 생성 금지.

## 22. Regression

기존 26개 의미 유지. 정상 Bottleneck Scenario, Negative A\~D, Retry
Limit Test 추가. 기존/신규/총/PASS/FAIL/ERROR 보고. 기존 Test 삭제/약화
금지.

## 23. 공식 Test 4

전체 PASS 후: - mvp_test_id MVP-TEST-4 - Name Bottleneck - Plan Version
1.0 - change_reason_ref Order-025 기대 Execution PASS / Validation PASS
/ Gate PROCEED / Evidence+SHA / Scenario A\~E+Retry Limit 연결. 내부
실패 Scenario를 PASS로 덮어쓰지 않는다.

## 24. Preservation

Phase1, Test1 Plan1.0/1.1, Test2 Plan1.0/1.1, Common Harness,
Architecture/Terminology/Reference 기록 후 작업. 기존 Evidence/Run 불변,
Test4만 추가, Test1/2 PASS 유지.

## 25. 하지 말 것

Test5 Prevention, Test6 User Gate 실제 Workflow, Test7 Resume, Test3
Safe Parallel, Prevention/Rule 활성화, Agent/Skill/Hook, Plugin/Adapter,
SQLite/DB, Architecture/Terminology, 기존 Evidence rewrite, Phase2 금지.

## 26. Architecture Delta

기본 NONE. 충돌 시 ARCHITECTURE-DELTA 보고 후 중단.

## 27. View/History

완료 후 Index/History 최소 갱신. 독립 Review 전 Test4 =
`PASS 후보 — Independent Review 대기`.

## 28. Validation

-   [ ] Fingerprint 결정적, run/event/time 제외
-   [ ] 실패 클래스 구별
-   [ ] 같은 실패 같은 Fingerprint / 다른 실패 다른 Fingerprint
-   [ ] 동일 실패+근거 없음 BLOCK, 재실행 없음
-   [ ] 실제 변경+새 version+reason → New Run/Revalidation
-   [ ] 과거 FAIL 보존
-   [ ] Validation FAIL / Validator ERROR / Execution ERROR 구별
-   [ ] Negative A\~D 모두 FAIL/BLOCK
-   [ ] Retry Limit 초과 BLOCK, USER-GATE 미구현
-   [ ] 기존 26 Test 의미 유지 + 신규 PASS
-   [ ] MVP-TEST-4/Bottleneck/1.0/Order-025 공식
    PASS/PASS/PROCEED/Evidence
-   [ ] Test1/2/Phase1/Architecture/Reference 불변
-   [ ] Test3/5/6/7 미구현
-   [ ] 외부 패키지/DB/Agent/Phase2 없음

하나라도 실패하면 Test4 PASS 금지. 검사 자체 실패는 ERROR.

## 29. 결과 보고

# Order-025 MVP Test 4 Bottleneck 결과

-   현재 상태
-   View Sync
-   Bottleneck 구현/Fingerprint/Retry Decision
-   생성/수정 파일
-   Scenario A\~E
-   Negative A\~D
-   Retry Limit
-   Regression
-   공식 Test4 ID/Name/Version/reason/Run/Plan·Executor·Validator
    Hash/Validation/Gate/Evidence/SHA/Scenario
-   Preservation
-   상태: Test1 PASS, Test2 PASS, Test3 NOT VERIFIED, Test4 PASS
    후보-Review 대기, Test5\~7 NOT VERIFIED
-   Architecture Delta/Scope
-   Done/Now/Next

PASS Next: Claude READ-ONLY Test4 Independent Review → PASS이면 Test4
OFFICIAL PASS → Test5 Prevention. 사용자 승인 필요 NO.

## 30. 종료 조건

View Sync, 구현, Scenario, Negative, Retry Limit, Regression, 공식 Run,
Evidence, Preservation, Index/History 후 종료. PASS해도
Claude/Test5/다른 Test/Architecture/Phase2 자동 시작 금지.

=== ORDER END ===
