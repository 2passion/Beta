# Order-040 --- MVP Test 6 Plan 1.2 Independent Delta Recheck

## Metadata

-   Order ID: Order-040
-   Project: Beta
-   Status: APPROVED
-   Type: READ-ONLY INDEPENDENT DELTA RECHECK
-   Root: `C:\Obsidian\Beta`
-   Generator: ChatGPT
-   Writer: Codex
-   Reviewer / To: Claude Code
-   Action: REVIEW_ONLY
-   Trigger: Order-039 Plan 1.2 PASS candidate
-   Architecture SSOT / Terminology: FROZEN
-   Test 7: NOT STARTED

## Execution Routing

``` text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Claude Code
action: REVIEW_ONLY
order: Order-040
project: Beta
mismatch_policy:
- recipient mismatch -> HOLD
- no review/execution/Beta writes
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## Purpose

Order-038에서 발견된 단일 Blocker인 Decision-to-Execution 사전 Gate
미연결이 Order-039 / Plan 1.2에서 실제 해결됐는지 독립 재검증한다.
Claude Code는 READ-ONLY Reviewer다.

Plan 1.1에서 독립 PASS한 B1/B2/I1/I2/I3/I4는 보존 여부만 확인하고, Plan
1.2의 Decision→Execution enforcement, Side Effect Zero, M1\~M4,
Regression 70개, Evidence 29개를 집중 검증한다.

## Review Boundary

Beta 원본, Plan, Fixture, Validator, Evidence, Index/History를 수정하지
않는다. Beta에 새 Run/Evidence를 생성하지 않는다. Test3/Test7, Phase2,
Architecture/Terminology 변경, Active Rule 승격, 새
Router/Recovery/Agent/DB/Plugin/Adapter를 금지한다.
Mutation/Regression은 Beta 밖 격리 복사본에서만 수행한다.

## Candidate Baseline

-   Test ID `MVP-TEST-6`
-   Version `1.2`
-   change_reason_ref `Order-039`
-   Run `RUN-41d67f4a-5551-4149-b02f-96e58d23a7fb`
-   Plan SHA
    `CA3DB94A638549ACF9347E71223DEB484315CB0DECFD3F478F800C491C46CEBC`
-   Executor SHA
    `CE4039A2EB6CFF2A3B5932E697CD90FD11FAEA3F3C4608853C52118C1FD570EB`
-   Validator SHA
    `5D18FBF55EECCA95BC768157793A02B2732DFB915D5339B8B2C71F36E5538879`
-   Evidence `EVD-9cca4f2f-1bce-4c42-ab5c-0d5502532320`
-   Evidence SHA
    `6C8AA602328CD9764F0C88002239176E8169C644262D4D9CE8ACAF3BC71F3B9D`
-   Scenario `SCN-42e179cb-59c0-4797-9add-aa75e0838b3c`
-   Scenario Evidence 29
-   Execution PASS / Validation PASS / Gate PROCEED
-   Regression claimed 70/70 PASS

모두 검증 대상이며 신뢰 전제값이 아니다.

## Critical Decision-to-Execution Delta

실제 실행 경로가 반드시 다음이어야 한다.

``` text
User Gate Decision
├─ AUTO
│  └─ routing_entry
│     ├─ MATCH → run_task
│     └─ MISMATCH → HOLD / run_task 0
├─ APPROVAL_REQUIRED → routing_entry 0 / execution 0
└─ HOLD              → routing_entry 0 / execution 0
```

핵심 invariant:

``` text
decision != AUTO
→ routing_entry_count == 0
→ writer_call_count == 0
→ run_task_call_count == 0
→ RUN_STARTED == 0
→ runtime_evidence_delta == 0
→ managed_write_delta == 0
```

Validator의 사후 탐지만으로 PASS시키지 않는다. 실제 실행 호출 전에
차단되어야 한다.

## D1\~D6

D1 Normal AUTO: C1\~C8 true → AUTO → routing 1 → MATCH → run_task 1 →
PASS/PROCEED.

D2 Approval Required: 승인 전 APPROVAL_REQUIRED이며
routing/writer/run/RUN_STARTED/Runtime Evidence/write 모두 0. 승인 후
Scope match + C1\~C7 true일 때만 AUTO.

D3 Scope Expansion: 기존 approval + 확대 requested_scope →
APPROVAL_REQUIRED → 모든 실행 Side Effect 0.

D4 C3=false: non-AUTO → routing/run/RUN_STARTED/Runtime Evidence/write
모두 0.

D5 SSOT_CONFLICT: HOLD → 모든 실행 Side Effect 0.

D6 Routing mismatch: User Gate AUTO까지 허용, routing 검사 1회 가능,
mismatch 후 writer/run/downstream/write 0, HOLD/ROUTING_MISMATCH.

## Mutation M1\~M4

-   M1 Force APPROVAL_REQUIRED → 실제 Run/Evidence/Write 0.
-   M2 Force HOLD/C3=false → 실제 Run/Evidence/Write 0.
-   M3 Scope Expansion Attack → APPROVAL_REQUIRED / execution layer 진입
    0.
-   M4 격리 복사본에서 Decision Guard 제거/우회 → 실제 Run 발생 시
    Validator FAIL / Gate BLOCK.

## Plan 1.1 Preservation

다음을 재설계하지 말고 보존 여부를 확인한다. - AUTO C1\~C8 AND -
approval OR bypass 제거 - Approval Scope containment - filesystem
Idempotency - Test5 Prevention Source-chain reuse - Routing Entry
Enforcement/provenance - Validator independent recomputation - Mutation
G\~L protections

## Validator Independence

Validator는 executor의 decision/counter/PASS label을 그대로 신뢰하지
않는다. User Gate inputs, actual routing call, run_task call,
RUN_STARTED Event, Runtime Evidence delta, filesystem write delta,
Routing result와 기존 C1\~C8/Scope/Recovery/Idempotency invariants를
독립 대조한다. `decision != AUTO`인데 실제 Run이 있으면 반드시
FAIL/BLOCK. 검사 불능이면 ERROR.

## Evidence Integrity

실제 파일에서 Plan/Executor/Validator/Evidence SHA,
Run/Event/Validation/Gate linkage, Scenario ID, Scenario Evidence 29개,
mismatch/unlinked를 재계산한다.

보존값: - Plan1.0 SHA
`8D30B1D0974FA2A95CCE9AD9C200B469D58D45F98DAC942F6759B179CE429399` -
Plan1.1 SHA
`B7AEFB7F23ABF22772E6F304C5EBF1CDCD5B4B029ED6D8E966749A20E412343C` -
Plan1.0 Evidence SHA
`7388323F9550645BFB96C2CBE50425169250AB1BCBB1AE7EF1A6776C95361365` -
Plan1.1 Evidence SHA
`F713B58CD146E197926C3FE850BE8F5B8A2274941FE39C0CB8BE5BFF0D56CB46`

## Regression

Beta 밖 격리 복사본에서 실행: - 기존 66: 66 PASS - 신규 Delta: 4 PASS -
TOTAL 70 / PASS 70 / FAIL 0 / ERROR 0

기존 테스트 삭제/완화 금지. Blind Retry 금지.

## Preservation

Test1/2/4/5 OFFICIAL PASS, Phase1, Common Harness/Core,
Architecture/Terminology, Reference, Test6 Plan1.0/1.1 및 Evidence를
보존한다. Test3/Test7 NOT STARTED, Phase2/Active Rule/새
Router·Recovery·Agent·DB·Plugin·Adapter 없음. Architecture Delta = NONE.

## GitHub Boundary

GitHub Beta 저장소가 생성되었지만 이번 Order 범위에는 포함하지 않는다. -
Git init/push/commit 금지 - GitHub를 SSOT로 승격하지 않음 - GitHub
때문에 Local Beta 구조 변경 금지 - GitHub 정책은 별도 설계/승인 대상으로
유지

이번 Test6 Review의 기준은 `C:\Obsidian\Beta`의 승인 SSOT와 실제
Evidence다.

## Severity

BLOCKER: APPROVAL_REQUIRED/HOLD/Scope Expansion/C3=false인데 실제 실행
발생, Routing mismatch 후 run/write 발생, Decision Guard 제거를
Validator가 탐지하지 못함, Evidence 무결성 실패, Architecture/SSOT 무단
변경.

IMPORTANT: 실제 Event/filesystem/call path가 아닌 선언 counter만으로
Side Effect Zero 증명, Validator 독립 재계산 미흡, Plan1.1 safety
regression, Preservation/Regression 불충분.

MINOR: 의미를 바꾸지 않는 보고/명명 문제.

## Final Decision

PASS 조건: - Critical Delta PASS - D1\~D6 PASS - M1\~M4 PASS - Plan1.1
Preservation PASS - Validator Independence PASS - Evidence Integrity
PASS - Regression 70/70 PASS - Preservation PASS - BLOCKER 0 / IMPORTANT
0 - Beta original changes by review 0

PASS이면 `MVP Test 6 User Gate Plan 1.2 = Independent Review PASS`,
`Test6 = OFFICIAL PASS candidate`,
`User Gate Review/Fix Loop = closure candidate`를 제안할 수 있다.
Claude는 상태 파일을 수정하지 않는다. OFFICIAL PASS 반영은 후속 Write
Order에서 수행한다.

REVISION REQUIRED이면 Test6 OFFICIAL PASS 및 Test7 시작을 금지하고
재현/영향/최소 수정 Scope를 보고한다.

## Required Output

1.  Final Verdict
2.  Beta Files Changed by Review
3.  Critical Decision-to-Execution Delta
4.  D1\~D6
5.  M1\~M4
6.  Plan1.1 Preservation
7.  BLOCKER / IMPORTANT / MINOR
8.  Validator Independence
9.  Evidence Integrity
10. Regression
11. Preservation / Architecture Delta
12. GitHub Boundary respected
13. Done / Now / Next
14. User Approval Required

## End State

-   Writer Order-039: Codex
-   Reviewer Order-040: Claude Code
-   Review Mode: READ-ONLY
-   Test6 Plan1.0: REVISION REQUIRED
-   Test6 Plan1.1: REVISION REQUIRED
-   Test6 Plan1.2: PASS candidate
-   Test6 OFFICIAL PASS: NOT YET
-   Test7: NOT STARTED
-   GitHub Beta: OUT OF SCOPE for this Order
-   User approval required: NO

=== ORDER END ===
