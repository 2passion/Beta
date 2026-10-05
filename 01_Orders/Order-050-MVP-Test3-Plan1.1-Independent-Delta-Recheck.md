# Order-050 — MVP Test 3 Plan 1.1 Independent Delta Recheck

## Metadata
- Order ID: Order-050
- Project: Beta
- Status: APPROVED
- Type: READ-ONLY INDEPENDENT DELTA RECHECK
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer: Codex
- Reviewer / To: Claude Code
- Action: REVIEW_ONLY
- Trigger: Order-049 Plan 1.1 PASS candidate
- Architecture / Terminology: FROZEN
- GitHub Beta: OUT OF SCOPE

## Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Claude Code
action: REVIEW_ONLY
order: Order-050
project: Beta
mismatch_policy:
- recipient mismatch -> HOLD
- no review/execution/Beta writes
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## Purpose
Order-048의 B1/B2/I1/I2/I3가 Order-049 Plan 1.1에서 실제 해결됐는지 독립 Delta Recheck한다. 전체 Safe Parallel을 처음부터 다시 검토하지 않는다.

집중 검증:
1. B1 Independent Concurrency Observation
2. B2 UNKNOWN Validation
3. I1 Windows Path Conservative Policy
4. I2 Per-task Evidence Linkage
5. I3 Scenario Manifest
6. Test 2 Ownership 계약 재사용 의미
7. Failure Isolation Derivation
8. M9~M13 및 기존 M1~M8 보존
9. Regression 96/96
10. Plan1.0/Evidence 보존

Claude는 READ-ONLY Reviewer다. Beta 원본 수정, Beta 내 새 Run/Evidence, MVP PASS/Freeze 확정, Phase2, Architecture/Terminology 변경, Git/GitHub 작업, 새 Scheduler/Agent pool/DB/lock/Plugin/Adapter를 금지한다. Mutation/Regression은 Beta 밖 격리 복사본에서만 수행한다.

## Candidate Baseline
- `MVP-TEST-3 / Safe Parallel`
- Version `1.1`
- reason `Order-049`
- Run `RUN-9a00bb3c-522b-46c7-ba35-01dd5568d407`
- Plan SHA `CEA57629C511F423846099CBA547F05BADE231E88B9246BE87D2B11215DE349A`
- Executor SHA `EF9954A8AAEA92BAE90C2F5ED5D66FAAB63DD1CB3D4D398086C95C888268D4D0`
- Validator SHA `8C707D7DED0AA2BB9CD23BD1A0E48C4244BC0AC171F1053F12503D85420EF355`
- Evidence `EVD-77ba1c95-4ec4-4b9d-9565-380f72a9c2cd`
- Evidence SHA `746E07D1300514F2BF7137557529E03FB457CC5495ADFA357A79C84C49086F81`
- Scenario `SCN-af3e3f74-ad03-4a02-8d53-6c9f63dfdf38`
- Execution PASS / Validation PASS / Gate PROCEED
- Manifest 71 / actual 71 / mismatch0
- Regression claimed 96/96

모두 검증 대상이다.

## D1 — Independent Concurrency / Trust Boundary
최우선 검증.

worker별 JSONL observation이 runtime summary와 실제로 독립된 관측 경로인지 코드 수준에서 추적한다.

확인:
- worker가 직접 observation 기록
- worker identity/barrier arrival-release/start-completion
- observation path/SHA
- runtime summary와 observation의 생성 주체/경로
- Validator 교차검증
- 실제 overlap

M9-A: 실제 순차 + runtime만 fake concurrency → FAIL/BLOCK.

M9-B: 실제 순차 + runtime과 observation을 모두 일관되게 fake parallel로 변조.
Validator가 worker 직접 append-only event, filesystem marker ordering, 독립 thread lifecycle 등 별도 신뢰 가능한 사실과 대조해 잡는지 확인한다.

runtime과 observation이 동일 trust boundary에서 자유롭게 함께 위조되어 PASS하면 BLOCKER.

정상 A/H는 실제 overlap과 독립 Task Evidence가 있어야 한다.

## D2 — UNKNOWN Validation
실제 classify/recompute에 각각:
- routing_to=None
- actual_actor=None
- routing empty
- functional_domain=None/""
- requested_scope=[]
- approved_scope invalid/empty
- owner empty
- task_id empty
- write_set missing/uninterpretable
- shared_resources missing
- independent_validation missing/false
- unresolved external dependency

Expected:
- PARALLEL_ALLOWED 0
- 안전한 순차 가능 → SEQUENTIAL_REQUIRED
- identity/permission/dependency 판단 불가 → HOLD

UNKNOWN을 INDEPENDENCE_PROVEN으로 만들면 BLOCKER.

## D3 — Windows Path Policy
classify와 Validator 양쪽에서:
same file, `..`, case-insensitive, slash/backslash, parent-child, trailing dot/space, `\\?\` prefix, relative/absolute, UNC/local alias, ADS, 8.3/unknown, ambiguous device/relative path를 확인.

Expected:
- conflict proven → SEQUENTIAL_REQUIRED
- identity uncertain → SEQUENTIAL_REQUIRED/HOLD
- unsafe PARALLEL_ALLOWED 0

실제 filesystem 확인 없이 8.3 등을 억지 확정하지 않는다.

## D4 — Per-task Evidence Linkage
Scenario A/H:
`Task Contract → unique Run → Output → Validation → Evidence`

확인:
- unique task_id/run_id
- Task↔Run
- Run↔Output
- actual output SHA = Evidence.output_sha256
- output status ↔ Validation 의미
- Validation↔Evidence
- Evidence task_id/run_id
- Batch가 per-task 사실을 덮어쓰지 않음

M12:
same run_id, output_sha 위조, output status/Validation 모순, Evidence task/run 변조+SHA 재계산 → 모두 FAIL/BLOCK.

## D5 — Scenario Manifest
Official Evidence/Validation output의 A~H 전체 manifest:
- scenario_id
- relative_path
- sha256

실제 tree를 독립 재계산. Expected 71/71, missing0, nonexistent0, mismatch0, unlinked0.

M13: 내용 변조/미등록 추가/등록 삭제/manifest hash 위조 중 3종 이상 → FAIL/BLOCK.

## D6 — Ownership Reuse
Test2 승인 Ownership 계약과 Plan1.1 owner validation을 비교:
- One Task One Owner 의미 동일
- multiple writer 차단
- owner normalization/case 정책 충돌 없음

Scenario Runner 전체 재사용 여부가 아니라 검증된 계약 의미 재사용 여부가 핵심.

## D7 — Failure Isolation Derivation
H1 PASS / H2 FAIL → PARTIAL_FAILURE / recovery H2 only / H1 rerun0.

batch_result/recovery_candidates가 per-task Validation에서 도출되거나 Validator가 독립 재계산하는지 확인.

H1/H2 결과 뒤집기, recovery를 PASS Task로 변경, batch PASS 위조 → FAIL/BLOCK.

## Existing Contract Preservation
실제 정상 병렬, dependency conflict, cycle HOLD, 기본 path conflict, ownership/shared resource, scope/routing/unknown, deterministic fallback, failure isolation, M1~M8이 계속 PASS해야 한다.

## M1~M13
모두 독립 재현. 특히 M9는 실제 순차 실행 + 일관된 가짜 병렬 기록까지 포함한다. 의도한 이유로 FAIL/BLOCK해야 한다.

## Validator Independence
독립 재계산:
contract validity/UNKNOWN, dependency/cycle/resolution, ownership, canonical/unknown path, domain/shared resource, scope/routing, independent concurrency observation, runtime summary, sequential order, per-task Run/Output/Validation/Evidence, batch/failure isolation, scenario manifest.

검사 불능 → ERROR.

## Evidence Integrity
실제 파일에서 Plan/Executor/Validator/Evidence SHA, Run/Event/Validation/Gate linkage, Scenario ID, Manifest 71, per-task Evidence links, unlinked/mismatch를 재계산. Plan1.0/Evidence도 보존 확인.

## Regression
Beta 밖 격리:
- 기존 91
- 신규 5
- TOTAL 96
- PASS 96
- FAIL0
- ERROR0

기존 Test 삭제/완화 및 Blind Retry 금지.

## Preservation
Test1/2/4/5/6/7 OFFICIAL PASS, Phase1, Common Harness/Core, Architecture/Terminology, Reference, Test3 Plan1.0/Evidence, 기존 Run/Event/Evidence 보존. Architecture Delta NONE.

## GitHub Boundary
git init/add/commit/push 없음. GitHub coordination/lock/queue/SSOT 사용 없음.

## Severity
BLOCKER:
- 실제 순차 + 일관 fake concurrency가 PASS
- UNKNOWN을 PARALLEL_ALLOWED
- unsafe path 병렬
- per-task Evidence identity/linkage 위조 허용
- Manifest 무결성 실패
- dependency/ownership/scope/routing conflict 실행
- failure isolation 파괴

IMPORTANT:
- concurrency observation이 executor와 동일 trust boundary
- Windows unknown path를 안전하다고 단정
- Ownership 의미가 Test2와 불일치
- batch/recovery가 하드코딩이고 독립 도출 없음
- Preservation/Regression 불충분

MINOR: 의미를 바꾸지 않는 보고/명명 문제.

## Final Decision
PASS 조건:
- D1~D7 PASS
- Existing Contract Preservation PASS
- M1~M13 PASS
- Validator Independence PASS
- Evidence Integrity PASS
- Regression 96/96 PASS
- Preservation PASS
- BLOCKER0 / IMPORTANT0
- Beta original changes by review0

PASS이면 Test3 Plan1.1 Independent Review PASS, Test3 OFFICIAL PASS candidate, Safe Parallel Review/Fix Loop closure candidate, MVP 7 Gates 전체 OFFICIAL PASS 후보 상태를 제안한다. Claude는 상태 파일을 수정하지 않는다.

REVISION REQUIRED이면 Test3 OFFICIAL PASS/MVP 전체 PASS/Freeze 금지, 재현/영향/최소 수정 Scope 보고.

## Required Output
1. Final Verdict
2. Beta Files Changed by Review
3. D1~D7
4. Actual Concurrency / Trust Boundary
5. UNKNOWN Validation
6. Windows Path Policy
7. Per-task Evidence
8. Scenario Manifest
9. M1~M13
10. BLOCKER / IMPORTANT / MINOR
11. Validator Independence
12. Evidence Integrity
13. Regression
14. Preservation / Architecture Delta
15. GitHub Boundary
16. MVP 7 Gates Status
17. Done / Now / Next
18. User Approval Required

## End State
- Writer Order-049: Codex
- Reviewer Order-050: Claude Code
- Mode: READ-ONLY
- Test3 Plan1.0: REVISION REQUIRED
- Test3 Plan1.1: PASS candidate
- Test3 OFFICIAL PASS: NOT YET
- Tests1/2/4/5/6/7: OFFICIAL PASS
- MVP overall PASS: NOT YET
- MVP Freeze: NOT YET
- GitHub Beta: OUT OF SCOPE
- User approval required: NO

=== ORDER END ===
