# Beta Index

## 목차

1. 프로젝트
2. 현재 Architecture
3. Done
3.1 Known Limitations
3.2 GitHub Pre-Freeze Snapshot
3.3 MVP Freeze Baseline
4. Now
5. Next
6. 주요 위치
7. 문서 우선순위
8. Asset / Reference / Archive
9. 버전 관리
10. 다음 단계
11. 문서 종료


## 1. 프로젝트

Name: Beta

Purpose:
AI 기반 개발 시스템의 설계·검토·검증

File Root:
C:\Obsidian\Beta


## 2. 현재 Architecture

Document:
Harness-A-Architecture-v1.0.md

Version:
v1.0

Status:
FROZEN

Terminology:
Terminology.md

Terminology Status:
FROZEN


## 3. Done

- Beta 로컬 작업공간 초기화 완료
- 초기 Beta Reference 자료 이전 완료
- Harness-A-Architecture-v1.0.md DRAFT 최초 작성 완료
- Claude Code Cross Review 완료 — REVISION REQUIRED / Blocker 1
- Order-001 승인 수정사항 반영 완료
- Order-002 READ-ONLY Re-Review 완료 — PASS WITH MINOR REVISION
- Order-003 Architecture Minor Revision 반영 완료
- Terminology SSOT DRAFT 생성 완료
- Order-004 Final Delta Review 완료 — PASS WITH MINOR REVISION
- Order-005 Final Minor Revision 완료
- Order-006 Final READ-ONLY Delta Check 완료 — PASS / Blocker NONE
- Architecture v1.0 DRAFT 최종 검토 완료
- Architecture v1.0 REVIEW 상태 전환 완료
- Terminology REVIEW 상태 전환 완료
- Order-007 REVIEW State Transition PASS
- User Approval 완료
- Order-008 FROZEN State Transition 완료
- Architecture v1.0 FROZEN
- Terminology FROZEN
- Order-009 MVP Implementation Preflight 완료 — READY WITH DECISIONS
- D-MVP-001~005와 조건 A/B User Approval 완료
- Order-010 Local Core MVP Phase 1 Bootstrap 완료 — PASS
- Phase 1 unittest 10개 PASS
- Phase 1 합성 CLI Run PASS — Validation PASS / Gate PROCEED
- Order-011 Phase 1 Independent Review — PASS WITH IMPORTANT FIX
- Order-012 Phase 1 Important Fix 완료 — PASS
- Phase 1 전체 unittest 17개 PASS
- plan 1.2 New Run 재검증 — Validation PASS / Gate PROCEED
- Order-013 Important Fix Recheck — FAIL / Blocker NONE
- Order-013 Root Cause 확인 — Executor/Validator shared timeout
- Order-014 Timeout Separation Fix 완료 — PASS
- Timeout Stress Revalidation 완료 — 단독 20/20, 묶음 10/10, 전체 Suite 10/10
- plan 1.3 New Run 재검증 — Validation PASS / Gate PROCEED
- Order-015 Final Timeout Delta Recheck — PASS
- shared timeout Root Cause — RESOLVED
- Local Core MVP Phase 1 Review/Fix Loop — CLOSED
- Order-016 MVP Test Implementation Sequence Review — READY
- Order-017 Common MVP Test Harness + MVP Test 2 Ownership 완료 — PASS
- MVP Test 2 Ownership Plan 1.0 Runtime Evidence — Validation PASS / Gate PROCEED
- Order-018 MVP Test 2 Independent Review — PASS WITH IMPORTANT FIX
- Order-019 Common MVP Test Harness Important Fix 완료 — PASS
- MVP Test 2 Ownership Plan 1.1 Revalidation — Validation PASS / Gate PROCEED
- Order-020 Common MVP Test Harness Delta Recheck — PASS
- Common MVP Test Harness Review/Fix Loop — CLOSED
- MVP Test 2 Ownership — OFFICIAL PASS
- Order-021 MVP Test 1 Reuse 구현 완료 — PASS
- MVP Test 1 Reuse Plan 1.0 Runtime Evidence — Validation PASS / Gate PROCEED
- Order-022 MVP Test 1 Reuse Independent Review — PASS WITH IMPORTANT FIX
- Order-023 Reuse Validator Important Fix 완료 — PASS
- MVP Test 1 Reuse Plan 1.1 Revalidation — Validation PASS / Gate PROCEED
- Order-024 Reuse Validator Delta Recheck — PASS
- MVP Test 1 Reuse — OFFICIAL PASS
- Order-025 MVP Test 4 Bottleneck 구현 완료 — PASS
- MVP Test 4 Bottleneck Plan 1.0 Runtime Evidence — Validation PASS / Gate PROCEED
- Order-026 MVP Test 4 Independent Review — REVISION REQUIRED / Blocker 1
- Order-026 Root Cause — Retry Limit 자기보고 count 및 실행 제어·Run/EVD 직접 검증 부족
- Order-027 Bottleneck Retry Enforcement Fix 완료 — PASS
- MVP Test 4 Bottleneck Plan 1.1 Revalidation — Validation PASS / Gate PROCEED
- Order-028 Bottleneck Retry Delta Recheck — FAIL
- Order-028 Root Cause — Scenario B Decision이 run_task 호출 조건에 연결되지 않음
- Order-029 Scenario B Decision Enforcement Fix 완료 — PASS
- MVP Test 4 Bottleneck Plan 1.2 Revalidation — Validation PASS / Gate PROCEED
- Order-030 Scenario B Final Delta Recheck — PASS
- MVP Test 4 Bottleneck — OFFICIAL PASS
- Bottleneck Review/Fix Loop — CLOSED
- Order-031 MVP Test 5 Prevention 구현 완료 — PASS
- MVP Test 5 Prevention Plan 1.0 Runtime Evidence — Validation PASS / Gate PROCEED
- Order-032 MVP Test 5 Prevention Independent Review — REVISION REQUIRED / Blocker 1 / Important 3
- Order-032 Blocker — 선언된 Fix Signature만 비교하고 Target Plan 실제 Fix를 검증하지 않음
- Order-032 Important — Source Eligibility·Search 실행 제어·Root Cause Evidence 연결 부족
- Order-033 Prevention Enforcement Fix 완료 — PASS
- MVP Test 5 Prevention Plan 1.1 Revalidation — Validation PASS / Gate PROCEED
- Order-034 Prevention Enforcement Delta Recheck — PASS / Check 1~13 PASS / New Blocker NONE
- Order-032 B1/I1/I2/I3 — RESOLVED
- MVP Test 5 Prevention — OFFICIAL PASS
- Prevention Review/Fix Loop — CLOSED
- Order-035 Test 5 Closure Sync + Execution Routing Contract + MVP Test 6 User Gate — PASS
- Order-035 Execution Routing Contract — PASS / mismatch fixture HOLD / Side Effect 0
- MVP Test 6 User Gate Plan 1.0 Runtime Evidence — Validation PASS / Gate PROCEED
- Order-036 MVP Test 6 User Gate Independent Review — REVISION REQUIRED / B1·B2·I1·I2·I3·I4
- Order-037 MVP Test 6 User Gate Enforcement Fix — PASS
- MVP Test 6 User Gate Plan 1.1 Runtime Evidence — Validation PASS / Gate PROCEED
- Order-038 MVP Test 6 Plan 1.1 Independent Delta Recheck — REVISION REQUIRED / Decision-to-Execution Blocker 1
- Order-039 MVP Test 6 Decision-to-Execution Enforcement Fix — PASS
- MVP Test 6 User Gate Plan 1.2 Runtime Evidence — Validation PASS / Gate PROCEED
- Order-040 MVP Test 6 Plan 1.2 Independent Delta Recheck — PASS
- MVP Test 6 User Gate — OFFICIAL PASS / Official Version 1.2
- User Gate Review/Fix Loop — CLOSED
- Order-041 MVP Test 6 Official Closure Sync — SYNCED
- Order-042 MVP Test 7 Resume 구현 완료 — PASS candidate
- MVP Test 7 Resume Plan 1.0 Runtime Evidence — Validation PASS / Gate PROCEED
- MVP Test 7 전체 Regression 77개 PASS / Mutation M1~M6 PASS
- Order-043 MVP Test 7 Resume Independent Review — REVISION REQUIRED / I1·I2·I3·I4
- MVP Test 7 Resume Plan 1.0 — REVISION REQUIRED 이력 보존
- Order-044 MVP Test 7 Resume Evidence Enforcement Fix — PASS candidate
- MVP Test 7 Resume Plan 1.1 Runtime Evidence — Validation PASS / Gate PROCEED
- MVP Test 7 전체 Regression 82개 PASS / Mutation M1~M11 PASS
- Order-045 MVP Test 7 Plan 1.1 Independent Delta Recheck — PASS / Blocker 0 / Important 0
- MVP Test 7 Resume — OFFICIAL PASS / Official Version 1.1
- Resume Review/Fix Loop — CLOSED
- Order-046 MVP Test 7 Official Closure Sync — SYNCED
- Order-047 MVP Test 3 Safe Parallel 구현 완료 — PASS candidate
- MVP Test 3 Safe Parallel Plan 1.0 Runtime Evidence — Validation PASS / Gate PROCEED
- MVP Test 3 전체 Regression 91개 PASS / Mutation M1~M8 PASS
- Order-048 MVP Test 3 Plan 1.0 Independent Review — REVISION REQUIRED / B1·B2·I1·I2·I3
- MVP Test 3 Safe Parallel Plan 1.0 — REVISION REQUIRED 이력 보존
- Order-049 Safe Parallel Enforcement Fix 완료 — PASS candidate
- MVP Test 3 Safe Parallel Plan 1.1 Runtime Evidence — Validation PASS / Gate PROCEED
- MVP Test 3 전체 Regression 96개 PASS / Mutation M1~M13 PASS
- Order-050 MVP Test 3 Plan 1.1 Independent Delta Recheck — REVISION REQUIRED / B1·B3·I1·I2
- MVP Test 3 Safe Parallel Plan 1.1 — REVISION REQUIRED 이력 보존
- Order-051 Safe Parallel Final Enforcement Fix 완료 — PASS candidate
- MVP Test 3 Safe Parallel Plan 1.2 Runtime Evidence — Validation PASS / Gate PROCEED
- MVP Test 3 전체 Regression 100개 PASS / Mutation M1~M17 PASS
- Order-052 MVP Test 3 Plan 1.2 Independent Delta Recheck — PASS / Blocker 0 / Important 0 / Minor 3
- MVP Test 3 Safe Parallel Plan 1.2 — Independent Review PASS
- MVP Test 3 Safe Parallel — OFFICIAL PASS / Official Version 1.2
- Safe Parallel Review/Fix Loop — CLOSED
- MVP 7 Gates — 7/7 OFFICIAL PASS
- Order-053 MVP Test 3 Official Closure Sync — SYNCED
- Order-054 MVP 7 Gates Overall Evidence Review — PASS FOR USER GATE / Blocker 0 / Important 0 / Minor 3
- Order-055 Pre-Freeze Snapshot — HOLD / Local Git Repository 및 Remote 부재
- Order-056 GitHub Initial Connection + Pre-Freeze Snapshot Recovery — PASS
- Final User Gate — APPROVED
- Beta Local Core MVP — OVERALL PASS
- MVP Status — FROZEN
- ChatGPT Project Beta와 Obsidian의 역할 분리
- A와 B의 관계 정의
- Local Core 우선 방향 결정
- 초기 데이터 구조와 사용자 Workflow 검토
- 12개 논리 역할의 책임 경계 검토
- MVP Test 1~7 정의
- Markdown Architecture SSOT 방식 결정
- HTML Visual Guide 방식 결정
- 버전과 상태 분리 방식 결정
- Asset / Reference / Archive 구분 결정


## 3.1 Known Limitations

- KL-1 Concurrency trust boundary — M14-D 단일 thread의 file-order/runtime/observation 일관 위조 및 M14-E 순차 실행 후 filesystem mtime 조작은 OS/별도 process 수준 관측 없이는 완전 증명에 한계가 있음 — OPEN / ACCEPTED FOR MVP
- KL-2 Windows path edge — `NUL .txt`, `CONIN$`, `CONOUT$`가 현재 안전 판정될 수 있음 — OPEN / ACCEPTED FOR MVP
- KL-3 External dependency Evidence completion — `completed_dependencies` 선언을 실제 Run/Evidence 완료와 독립 대조하지 않음 — OPEN / ACCEPTED FOR MVP
- 상태: 3 OPEN / ACCEPTED FOR MVP / 해결됨으로 표시하지 않음 / Active Rule 또는 Prevention으로 승격하지 않음
- 수용 판단 Gate: Final User Gate — APPROVED


## 3.2 GitHub Pre-Freeze Snapshot

- 상태: PASS
- Snapshot Commit: `73b15556dcd3f88569b596e10bc975f7101aa4bd`
- Branch: `main`
- Remote: `origin` → `https://github.com/2passion/Beta.git`
- Push: PASS
- Snapshot 검증: local HEAD = origin/main = remote main
- 확인 시각: `2026-10-06T03:47:03+09:00`
- GitHub 역할: Backup / Version History
- Local SSOT: `C:\Obsidian\Beta`
- MVP Overall PASS: NOT YET
- MVP Freeze: NOT YET


## 3.3 MVP Freeze Baseline

- Architecture SSOT: `00_Architecture/Harness-A-Architecture-v1.0.md` / v1.0 / FROZEN
- Terminology SSOT: `00_Architecture/Terminology.md` / FROZEN
- Official Gate Versions: Test 1 v1.1 / Test 2 v1.1 / Test 3 v1.2 / Test 4 v1.2 / Test 5 v1.1 / Test 6 v1.2 / Test 7 v1.1
- Overall Evidence Review: Order-054 / PASS FOR USER GATE
- Pre-Freeze Snapshot: Order-056 / PASS
- Final User Gate: APPROVED
- Known Limitations: 3 OPEN / ACCEPTED FOR MVP
- Freeze Commit: push 후 SHA 기록 예정
- Branch: `main`
- Remote: `origin` → `https://github.com/2passion/Beta.git`
- GitHub 역할: Freeze Snapshot / Backup / Version History
- Local SSOT: `C:\Obsidian\Beta`
- Architecture Delta: NONE
- Phase2: NOT STARTED


## 4. Now

Architecture v1.0 FROZEN
Terminology FROZEN
Local Core MVP Phase 1 CLOSED
MVP Test 1 Reuse OFFICIAL PASS
MVP Test 2 Ownership OFFICIAL PASS
MVP Test 3 Safe Parallel OFFICIAL PASS / Official Version 1.2
Safe Parallel Review/Fix Loop CLOSED
MVP Test 4 Bottleneck OFFICIAL PASS
MVP Test 5 Prevention OFFICIAL PASS
Prevention Review/Fix Loop CLOSED
MVP Test 6 User Gate OFFICIAL PASS / Official Version 1.2
User Gate Review/Fix Loop CLOSED
MVP Test 7 Resume OFFICIAL PASS / Official Version 1.1
Resume Review/Fix Loop CLOSED
MVP 7 Gates 7/7 OFFICIAL PASS
Overall Evidence Review PASS FOR USER GATE
BLOCKER 0 / IMPORTANT 0
Known Limitations 3 OPEN / ACCEPTED FOR MVP
Final User Gate APPROVED
MVP Overall PASS PASS
MVP Status FROZEN
Architecture Delta NONE
Phase2 NOT STARTED


## 5. Next

Runtime Operation / Evidence Collection
→ 범위 확장 전 운영 Evidence 축적
→ 모든 확장은 Evidence → Proposal → Review → User Approval 필요


## 6. 주요 위치

Architecture:
00_Architecture

Terminology:
00_Architecture/Terminology.md

Orders:
01_Orders

Core:
02_Core

Tests:
03_Tests

Evidence:
04_Evidence

Reference:
Reference

Archive:
Archive


## 7. 문서 우선순위

1. 최신 FROZEN Architecture SSOT
2. 승인된 Decision / Rule
3. 현재 Order / Task
4. 실제 Evidence
5. 승인된 Asset
6. Reference
7. Archive
8. 과거 Chat 및 새로운 AI 제안


## 8. Asset / Reference / Archive

Asset:
Beta에서 실제 실행·재사용하도록 승인된 자산.

Reference:
현재 설계·비교에 사용하는 참고자료.
자동으로 Asset으로 취급하지 않는다.

Archive:
현재 기준에서는 사용하지 않지만
추적·복구를 위해 보존하는 과거자료.


## 9. 버전 관리

버전과 상태를 분리한다.

최초 Architecture:

v1.0 DRAFT
→ v1.0 REVIEW
→ v1.0 FROZEN

FROZEN 이후 작은 변경:

v1.0
→ v1.1

큰 Architecture 변경:

v1.x
→ v2.0

상태 변경만으로 Version을 올리지 않는다.


## 10. 다음 단계

현재 Next는 5. Next를 따른다.


## 11. 문서 종료

이 문서는 Beta 프로젝트에서
현재 상태와 핵심 파일 위치를 찾기 위한 Index다.

=== DOCUMENT END ===
