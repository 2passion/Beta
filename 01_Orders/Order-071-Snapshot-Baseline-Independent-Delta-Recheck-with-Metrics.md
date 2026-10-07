# Order-071 — Snapshot/Baseline Independent Delta Recheck + Metrics

## Metadata
- Order ID: Order-071
- Project: Beta
- Status: APPROVED
- Type: READ-ONLY INDEPENDENT DELTA RECHECK + METRICS
- Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer: Codex
- Reviewer / To: Claude Code
- Action: REVIEW_ONLY
- Trigger: Order-070 PASS candidate
- MVP: PASS / FROZEN
- Phase2: NOT STARTED
- Production Runtime/Authorization: NOT AUTHORIZED
- Beta Git Write: NOT AUTHORIZED
- Metrics: REQUIRED / OBSERVATION ONLY

## Routing
```text
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Claude Code
action: REVIEW_ONLY
order: Order-071
project: Beta
mismatch -> HOLD / no Beta write / no runtime / no git write
```

## Purpose
Order-070을 좁게 독립 재검증:
1. Snapshot final identity / verified bytes
2. Python -I -c shadowing 방어
3. Snapshot directory/Evidence/NO_CHANGE
4. Core *.py baseline completeness
5. 신규12 Regression 품질
6. 178 Regression 보존
7. Metrics 연속 측정

전체 Runtime 재설계 금지. Beta 원본 READ-ONLY.

## D1 Snapshot Final Identity
Executor/Validator의 source bytes→SHA→exclusive snapshot→snapshot SHA→subprocess 직전 final SHA/identity→실제 실행 bytes 연결 확인.
final SHA 직후 snapshot replace/truncate/append/symlink 가능한 공격.
Expected malicious process0/marker0.

## D2 Verified Bytes Execution
`python -I -c <verified snapshot bytes>`가 실제 검증 bytes를 실행하는지 Executor/Validator 모두 확인. snapshot 파일이 final check 뒤 바뀌어도 실행 bytes가 바뀌지 않아야 함.

## D3 Module Shadowing
snapshot dir에 json.py/hashlib.py/pathlib.py/sitecustomize.py/usercustomize.py 등을 실제 투입.
PYTHONPATH/user-site 영향도 확인.
Expected marker0; sibling은 BLOCK되거나 -I/-c에서 import되지 않음.

## D4 Snapshot Directory
caller path 불가, run-local exact location, exclusive create, unexpected entry 차단, 허용 파일 목록, lifecycle/residue 확인.

## D5 Snapshot Evidence
정상 격리 Run에서 executor/validator snapshot identity/SHA/lifecycle/isolated mode가 body/index/event에 연결되는지 확인.

## D6 NO_CHANGE Snapshot
executor/validator snapshot 변조/삭제, sibling 추가, snapshot SHA Evidence/Event 변조, 가능한 body/index rehash 공격.
Expected NO_CHANGE 금지/HOLD. Genuine PASS만 NO_CHANGE.

## D7 Baseline Complete Core Set
`02_Core/beta_core/*.py` 전체 deterministic manifest 확인.
model.py/event_store.py/__init__.py 포함.
기존 Core 변경, 신규 py 추가, py 삭제/rename/case alias 가능한 공격.
Expected baseline 변화→authorization 무효/Run0.

## D8 Baseline Exclusions
__pycache__, tests/fixtures 제외. runtime_policy.json 별도 검증 유지. Production Core py 누락 경로가 없는지 확인.

## D9 KL-4
OPEN/CANDIDATE 유지. Baseline이 malicious Local Writer까지 해결한다고 주장하지 않음.

## D10 Previous Protections
표본 재검증: atomic auth, copy/pickle, original TOCTOU, concurrent request, Request/Baseline binding, READ-ONLY, forged packet/Git alone Run0.

## D11 Regression Quality
신규12가 실제 snapshot tamper/shadowing/model/event_store/__init__/new py/Evidence/NO_CHANGE/lifecycle/sibling 공격인지 확인. 핵심 mock 대체 금지.

## D12 Regression
격리 178/178, FAIL0/ERROR0, 가능하면 stability ×2.
공격과 Regression 병렬 실행 금지.

## D13 Preservation
Reviewer artifact 없음, 예상 밖 Beta 변경0, MVP FROZEN, Phase2 NOT STARTED, Production auth/run/evidence0, Git write0.

## D14 Closure Readiness
PASS일 때만 Implementation Closure candidate. KL-4 별도 User Acceptance Gate 필요. actual Runtime 금지.

# Metrics
순차 timing:
preflight→code review→attack preparation→attacks→regression#1→regression#2→preservation→report.
stage start/end/elapsed + total. Heavy stage 병렬 금지.

Token/Cost:
MEASURED/ESTIMATED/NOT_AVAILABLE. 실제 usage/가격/환율 근거 없으면 NOT_AVAILABLE.

Size:
Core/test/document files, lines, bytes; Order-071 lines/bytes; review Beta delta0; 가능하면 Order-058~071 cumulative delta.

Efficiency:
retry_count, blind_retry_count, blocker/important/minor, unexpected_exception_count, review_side_effect_count, recovery_action_count, user_gate_count.
이번 Review side effect 목표=0.

필수 Views:
3-Minute Summary + Stage Metrics Table + Detailed Metrics + Bottleneck Observation.
성능 Rule 자동 생성 금지.

## Severity
BLOCKER: snapshot tamper/shadowing 악성 실행, baseline mismatch 실행, actual Production Runtime, Reviewer Beta side effect 미복구.
IMPORTANT: snapshot Evidence/NO_CHANGE 불완전, baseline Core 누락, Regression 핵심 공격 미재현, 허위 Metrics.
MINOR: fail-closed 보고/명명, token/cost unavailable, 기존 KL hardening.

## Final Decision
PASS 조건:
D1~D14 PASS, marker0, baseline complete, NO_CHANGE tamper 차단, Regression178/178, BLOCKER0/IMPORTANT0, Beta changed0.
PASS → Implementation Closure candidate only.
REVISION REQUIRED → 최소 Fix.
HOLD → 검증 불가.

## Required Output
1 Final Verdict
2 Beta Files Changed
3 D1~D14
4 Snapshot Final Identity
5 Verified Bytes Execution
6 Module Shadowing
7 Snapshot Directory
8 Snapshot Evidence
9 NO_CHANGE
10 Baseline Completeness
11 Baseline Exclusions
12 KL-4
13 Previous Protections
14 Regression Quality
15 Regression
16 Preservation
17 Closure Readiness
18 BLOCKER/IMPORTANT/MINOR
19 Metrics 3-Minute Summary
20 Stage Metrics Table
21 Detailed Timing
22 Token/Cost
23 Code/Document Size
24 Validation Metrics
25 Efficiency/Recovery
26 Bottleneck Observation
27 Done/Now/Next
28 User Approval Required

## End State
- READ-ONLY review
- Metrics continues
- MVP FROZEN
- KL-4 OPEN candidate
- Production Runtime NOT RUN
- Phase2 NOT STARTED
- Beta Git write NO
- PASS → Closure candidate only

=== ORDER END ===
