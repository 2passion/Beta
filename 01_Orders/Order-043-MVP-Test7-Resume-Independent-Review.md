# Order-043 --- MVP Test 7 Resume Independent Review

## Metadata

-   Order ID: Order-043
-   Project: Beta
-   Status: APPROVED
-   Type: READ-ONLY INDEPENDENT REVIEW
-   Root: `C:\Obsidian\Beta`
-   Generator: ChatGPT
-   Writer: Codex
-   Reviewer / To: Claude Code
-   Action: REVIEW_ONLY
-   Trigger: Order-042 Plan 1.0 PASS candidate
-   Architecture / Terminology: FROZEN
-   Test 3 Safe Parallel: NOT VERIFIED
-   GitHub Beta: OUT OF SCOPE

## Execution Routing

``` text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Claude Code
action: REVIEW_ONLY
order: Order-043
project: Beta
mismatch_policy:
- recipient mismatch -> HOLD
- no review/execution/Beta writes
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## Purpose

Order-042의 MVP Test 7 Resume Plan 1.0을 실제 Checkpoint, Validation,
Evidence, filesystem Side Effect, Step 실행 순서 기준으로 독립 검증한다.
Codex PASS candidate 보고를 신뢰 전제로 삼지 않는다.

핵심: 1. 완료 Step을 Resume 후 재실행하지 않는가 2. Checkpoint를 실제
Validation/Evidence/Side Effect와 대조하는가 3. 정확한 다음 Step부터
재개하는가 4. Interrupted Run과 Resume 실행 identity를 구별·보존하는가
5. drift/missing state에서 HOLD하는가 6. Plan mismatch/non-PASS
checkpoint를 Resume하지 않는가 7. 재진입이 idempotent한가 8. Chunk와
Checkpoint를 구별하는가 9. Routing/User Gate 경계가 유지되는가

## Boundary

Claude는 READ-ONLY Reviewer다. Beta 원본,
Plan/Fixture/Validator/Evidence/Index/History 수정과 Beta 내 새
Run/Evidence 생성을 금지한다. Test3, Phase2, Architecture/Terminology
변경, Active Rule, Git/GitHub 작업, 새 DB/Agent/Plugin/Adapter/Workflow
Engine 금지. Mutation/Regression은 Beta 밖 격리 복사본에서만.

## Candidate Baseline

-   `MVP-TEST-7 / Resume`
-   Version `1.0`
-   reason `Order-042`
-   Run `RUN-d4d46c20-870c-4c87-a439-5f947f6a1927`
-   Plan SHA
    `9ACF4CE7B60513FD13F76DDE68491560F0348DFD376DAED247D24E729EF7ABF7`
-   Executor SHA
    `5AFADC084754AD9223C469EEE13F06D3AB3487F53A19B342E4BC1A5C8C6498CC`
-   Validator SHA
    `74B1B8295CF18AB8BA45C25A7A902902018612F6A7A9B072F2F28CE9954418C8`
-   Evidence `EVD-64daa642-c62f-4ccc-848c-efc7f95ae5e3`
-   Evidence SHA
    `283DB91D58D6525DC15AF211D934EBB99D77C6BD22A1E0858B807BB39D378600`
-   Execution PASS / Validation PASS / Gate PROCEED
-   Regression claimed 77/77 PASS

모두 검증 대상이다.

## Check 1 --- Checkpoint Contract

실제 Checkpoint에서 checkpoint_id, task_id, plan_version, run_id,
completed_step_ids, last_verified_step, validation_status,
evidence_refs, side_effect_refs/snapshot, expected_next_step, 순서
정보를 확인한다. PASS/완료 라벨만 믿지 않고 실제 Validation PASS,
Evidence 존재/SHA, Side Effect 존재/SHA와 연결해야 한다.

## Check 2 --- Interrupted Run Preservation

정상 Scenario A에서 Step1 PASS → Step2 PASS → Checkpoint → 중단 →
Step3/4 NOT_RUN을 실제 Event/Evidence로 추적한다. 최초 Interrupted
실행과 Resume 실행 identity가 명확히 구별되어야 한다. 중단 사실을 Resume
성공으로 rewrite하면 BLOCKER.

## Check 3 --- Exact Resume Point

last_verified_step=Step2, expected_next_step=Step3이면 실제 Resume
시작은 Step3이어야 한다. - Step1 Resume call 0 - Step2 Resume call 0 -
Step3 실행 - Step4 순차 실행 - 최종 PASS Step1/2 재실행 또는 Step4부터
시작하면 FAIL.

## Check 4 --- Actual Side Effect Verification

Checkpoint의 side-effect 경로/SHA/필수 파일 집합을 실제 filesystem과
비교한다. Scenario B: Checkpoint says done but result missing/drift →
SIDE_EFFECT_DRIFT/HOLD, Step3 실행0, Step1/2 자동 재실행0, Fix0.

## Check 5 --- Missing Checkpoint / Extra State

실제 결과 파일은 있지만 Checkpoint가 없으면 자동 완료 추정 금지.
CHECKPOINT_MISSING 또는 동등 HOLD, 실행0.

## Check 6 --- Chunk Separation

`record_type=CHUNK` 또는 동등 출력 기록은 Checkpoint가 아니다.
CHUNK_NOT_CHECKPOINT/HOLD, Resume0.

## Check 7 --- Plan Version Boundary

Checkpoint Plan과 현재 Plan 불일치 → PLAN_VERSION_MISMATCH/HOLD,
migration0, Resume0. 별도 migration contract 없이 지점 추론 금지.

## Check 8 --- Last Step Validation Boundary

마지막 Step이 FAIL/ERROR/NOT_RUN인 경우 각각 RESUME_ALLOWED 금지, HOLD,
다음 Step0.

## Check 9 --- Idempotent Resume Re-entry

Resume 완료 후 동일 요청 재진입: - completed/resumed Step 재실행0 -
duplicate write0 - duplicate Evidence0 - NO_CHANGE 또는 결정적 종료 실제
filesystem/Evidence delta로 확인하며 executor counter만 믿지 않는다.

## Check 10 --- Routing / User Gate

Routing mismatch → HOLD/ROUTING_MISMATCH/Resume0/write0/evidence0.
Approval Scope expansion → APPROVAL_REQUIRED/승인 전
Resume0/Checkpoint·Evidence 변경0. Test6 계약 우회 금지.

## Mutation M1\~M6

-   M1 Fake PASS Checkpoint: 실제 Validation/Evidence 없음 →
    FAIL/BLOCK/HOLD
-   M2 Tampered Evidence SHA/Run link → FAIL/BLOCK/HOLD
-   M3 Step1/2 강제 재실행 → Validator FAIL/BLOCK
-   M4 expected Step3인데 Step4부터 실행 → FAIL/BLOCK
-   M5 executor drift=false지만 실제 filesystem mismatch → FAIL/BLOCK
-   M6 Chunk as Checkpoint → NOT_ELIGIBLE/HOLD 또는 FAIL/BLOCK

각 Mutation이 의도한 위반 때문에 실패하는지 확인.

## Validator Independence

독립 대조: - Task/Plan identity - Checkpoint schema - Validation
record - Evidence ref/hash - filesystem Side Effect ref/hash - completed
Step 실제 호출 - Resume 시작점/순서 - duplicate writes/Evidence -
Routing/User Gate

가능하면 결과 라벨/counter 위조 Mutation으로 독립성을 확인.

## Event / Run / Evidence Semantics

실제 Event에서 기존 표현을 우선 확인한다. Checkpoint, interruption,
Resume request/decision/start/completion이 추적 가능해야 한다. 과거
Run/Event/Evidence는 append-only 보존하고 Interrupted 상태를 PASS로
rewrite하지 않는다. Resume 성공은 새로운 사실로 추가한다. 현재 계획과
과거 실행 사실을 혼합하지 않는다.

## Evidence Integrity

실제 파일에서 Plan/Executor/Validator/Evidence SHA,
Run/Event/Validation/Gate linkage, Scenario A\~G 연결, Scenario Evidence
Hash, unlinked/mismatch를 재계산한다.

## Regression

Beta 밖 격리 복사본: - 기존 70 - 신규 7 - TOTAL 77 - PASS 77 - FAIL 0 -
ERROR 0 기존 Test 삭제/완화 금지. Blind Retry 금지.

## Preservation

Test1/2/4/5/6 OFFICIAL PASS, Phase1, Common Harness/Core,
Architecture/Terminology, Reference, 기존 Run/Event/Evidence 보존. Test3
NOT VERIFIED, Phase2 없음, Architecture Delta NONE.

## GitHub Boundary

GitHub Beta는 범위 밖. git init/add/commit/push 없음, Git commit을
Checkpoint로 사용하지 않음, GitHub를 Resume SSOT로 사용하지 않음.

## Severity

BLOCKER: - 완료 Step 재실행 - Checkpoint만 믿고 drift 무시 - Checkpoint
없는 파일을 자동 PASS - Plan mismatch 자동 Resume - FAIL/ERROR/NOT_RUN을
완료 지점으로 Resume - expected_next_step 건너뛰기 - Interrupted 기록
rewrite - Routing/User Gate 우회 - Evidence 무결성 실패

IMPORTANT: - Validator 독립 검증 부족 - Idempotency가 실제
filesystem/Evidence가 아닌 label/counter 중심 - 최초 Interrupted 실행과
Resume identity 불명확 - Chunk/Checkpoint 경계 불완전 -
Preservation/Regression 불충분

MINOR: 의미를 바꾸지 않는 보고/명명 문제.

## Final Decision

PASS 조건: - Check1\~10 PASS - M1\~M6 PASS - Validator Independence
PASS - Event/Run/Evidence semantics PASS - Evidence Integrity PASS -
Regression 77/77 PASS - Preservation PASS - BLOCKER0 / IMPORTANT0 - Beta
original changes by review0

PASS이면 Test7 Plan1.0 Independent Review PASS, Test7 OFFICIAL PASS
candidate, Resume Review/Fix Loop closure candidate를 제안한다. Claude는
상태 파일을 수정하지 않는다.

REVISION REQUIRED이면 Test7 OFFICIAL PASS와 Test3 시작을 금지하고
재현/영향/최소 수정 Scope를 보고한다.

## Required Output

1.  Final Verdict
2.  Beta Files Changed by Review
3.  Check1\~10
4.  Interrupted Run / Resume identity
5.  Exact Resume Point
6.  M1\~M6
7.  BLOCKER / IMPORTANT / MINOR
8.  Validator Independence
9.  Event/Run/Evidence Semantics
10. Evidence Integrity
11. Regression
12. Preservation / Architecture Delta
13. GitHub Boundary
14. Done / Now / Next
15. User Approval Required

## End State

-   Writer Order-042: Codex
-   Reviewer Order-043: Claude Code
-   Mode: READ-ONLY
-   Test7 Plan1.0: PASS candidate
-   Test7 OFFICIAL PASS: NOT YET
-   Test3 Safe Parallel: NOT VERIFIED
-   GitHub Beta: OUT OF SCOPE
-   User approval required: NO

=== ORDER END ===
