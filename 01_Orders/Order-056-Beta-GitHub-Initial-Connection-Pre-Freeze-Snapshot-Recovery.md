# Order-056 — Beta GitHub Initial Connection + Pre-Freeze Snapshot Recovery

## Metadata
- Order ID: Order-056
- Project: Beta
- Status: APPROVED
- Type: WRITE + VALIDATE + INITIAL GIT CONNECTION + PUSH
- Local SSOT Root: `C:\Obsidian\Beta`
- Generator: ChatGPT
- Writer / To: Codex
- Reviewer: Claude Code
- Action: WRITE_AND_PUSH
- Trigger: Order-055 HOLD + user-provided GitHub repository evidence
- GitHub Repository: `https://github.com/2passion/Beta.git`
- Expected Remote Name: `origin`
- Expected Branch: `main`
- GitHub Role: REMOTE BACKUP / VERSION HISTORY, NOT SSOT
- MVP Overall PASS: NOT YET
- MVP Freeze: NOT YET

## Execution Routing
```text
=== EXECUTION ROUTING ===
generator: ChatGPT
writer: Codex
reviewer: Claude Code
from: ChatGPT
to: Codex
action: WRITE_AND_PUSH
order: Order-056
project: Beta
mismatch_policy:
- recipient mismatch -> HOLD
- no Beta write / no git initialization / no push
- report ROUTING_MISMATCH
=== ROUTING END ===
```

## User Approval and New Evidence
사용자는 다음을 승인했다.
- GPT 권장 Pre-Freeze Snapshot 방식
- 현재 상태 파일 갱신/동기화
- GitHub commit/push
- GitHub는 SSOT가 아니라 원격 백업/버전 이력
- MVP Overall PASS/Freeze는 별도 최종 User Gate에서 결정

Order-055는 로컬 `.git`과 remote 부재 때문에 HOLD했다.

그 후 사용자가 GitHub 화면을 제공해 다음 repository를 명시적으로 확인했다.

```text
Owner: 2passion
Repository: Beta
HTTPS: https://github.com/2passion/Beta.git
Expected branch: main
UI state: empty repository quick-setup screen
```

이 Order는 위 repository만 허용한다.
다른 remote URL을 사용하지 않는다.

## Purpose
Order-055의 HOLD 원인이었던 “기존 local Git repository 없음”을 새 승인 근거로 해결한다.

수행:
1. Local/GitHub preflight
2. Order-054 상태 Sync
3. 민감정보/불필요 파일 검사
4. `C:\Obsidian\Beta`에서 최초 Git repository 초기화
5. branch `main`
6. remote `origin`을 정확히 `https://github.com/2passion/Beta.git`로 연결
7. remote가 실제 empty 또는 initial push 가능한 상태인지 확인
8. 필요한 Beta 파일만 stage
9. Pre-Freeze Snapshot commit
10. `origin/main` push
11. local/remote commit SHA 일치 검증
12. Snapshot 상태 기록

## SSOT Boundary
계속:
```text
C:\Obsidian\Beta = Local Architecture / Project SSOT
GitHub Beta       = Remote Snapshot / Backup / Version History
```

GitHub를 Architecture SSOT로 승격하지 않는다.

## Preflight — Local State
확인:
- `C:\Obsidian\Beta` 존재
- MVP 7 Gates = 7/7 OFFICIAL PASS
- Order-054 = PASS FOR USER GATE
- Known Limitations KL-1~KL-3 OPEN
- MVP Overall PASS = NOT YET
- MVP Freeze = NOT YET
- Architecture/Terminology FROZEN
- Phase2 NOT STARTED
- Active Rule 무단 승격 없음

불일치 시 HOLD.

## Preflight — Sensitive / Unwanted Files
Git init/stage 전에 전체 Local Beta를 검사한다.

최소 제외/위험 후보:
- API key
- access token
- private key
- password/credential 파일
- `.env`
- `__pycache__`
- `.pyc`
- `.tmp`
- editor/OS junk
- unrelated external files
- 과도한 binary/archive
- 개인 식별/비밀 정보

민감정보 후보가 있으면 자동 stage/push 금지 → HOLD.

필요한 `.gitignore`가 없으면 최소 `.gitignore` 생성 가능.
단, 실제 제외 이유와 내용을 결과에 보고한다.

## Preflight — Remote Verification
GitHub 화면만 믿고 destructive action하지 않는다.

가능한 read-only remote 조회로:
- repository 접근 가능 여부
- default/expected branch
- remote refs 존재 여부
- repository가 실제 empty인지
를 확인한다.

### Remote Empty
remote refs가 없고 initial push 가능한 상태면 진행.

### Remote Non-empty
예상과 달리 commit/ref가 존재하면:
- 자동 pull/merge/rebase 금지
- force push 금지
- local history와 합치지 않음
- HOLD 후 remote 상태 보고

### Authentication
read는 가능하지만 push auth가 없으면:
- commit까지 생성하기 전에 가능한 한 인증 가능성 확인
- push 단계 auth failure 시 HOLD
- credential/token을 파일에 저장하거나 출력하지 않음

## State Sync — Recover Order-055
Git 초기화 전에 또는 commit 전에 Order-054 결과를 기존 상태 View/History에 반영한다.

필수 상태:
```text
MVP 7 Gates = 7/7 OFFICIAL PASS
Overall Evidence Review = PASS FOR USER GATE
BLOCKER = 0
IMPORTANT = 0
Known Limitations = 3 OPEN
MVP Overall PASS = NOT YET
MVP Freeze = NOT YET
Next = Final User Gate
```

Order-055 = HOLD 이력은 보존한다.
Order-056이 그 HOLD의 recovery임을 기록한다.

## Known Limitations
OPEN 유지:
- KL-1 Safe Parallel concurrency trust boundary
- KL-2 Windows path edge
- KL-3 External dependency completion

CLOSED/RESOLVED/Active Rule로 바꾸지 않는다.

## Validation Before Git Initialization
State Sync 후:
- Architecture/Terminology/Core hash 불변
- Evidence tree 불변
- 기존 Run/Event/Validation/Evidence rewrite 없음
- 7 Gate 상태 일치
- Known Limitations OPEN
- Overall PASS NOT YET
- Freeze NOT YET

불일치 시 Git 초기화/commit/push 중단.

## Initial Git Connection
Remote가 empty이고 Local validation이 PASS일 때만:

```text
cd C:\Obsidian\Beta
git init
git branch -M main
git remote add origin https://github.com/2passion/Beta.git
```

실제 환경에 따라 `git init -b main` 등 동등 명령 사용 가능.

검증:
- `.git` 생성
- branch = main
- origin URL exact match
- 다른 unexpected remote 없음

## Stage Policy
무조건 `git add .`부터 실행하지 않는다.

먼저:
- `git status --short`
- 전체 untracked/modified 파일 목록
- ignore 결과
를 확인한다.

Local Beta 프로젝트 기준선에 포함할 파일만 stage한다.

금지:
- credential
- temp/cache
- unrelated files
- 의도하지 않은 대용량 binary
- Git 내부 파일을 별도 stage 대상으로 취급

Stage 후:
- `git diff --cached --name-status`
- `git diff --cached --stat`
검사.

예상 밖 파일이 있으면 commit 금지 → HOLD.

## Commit
Pre-Freeze임을 명확히 한다.

Commit message:
`chore(beta): pre-freeze snapshot after 7/7 MVP gates`

Commit metadata/내용에서 다음 상태가 추적 가능해야 한다.
- 7/7 OFFICIAL PASS
- Overall Evidence Review PASS FOR USER GATE
- Known Limitations OPEN
- MVP Overall PASS NOT YET
- MVP Freeze NOT YET

Commit 후 local HEAD SHA 기록.

## Push
허용:
```text
git push -u origin main
```
또는 동등한 일반 initial push.

금지:
- `--force`
- `--force-with-lease`
- remote 변경
- history rewrite
- merge/rebase
- 다른 branch push

## Post-Push Verification
push 성공 후 read-only로 확인:
- local HEAD SHA
- `origin/main` SHA
- 가능하면 remote repository ref SHA

완료 조건:
```text
local HEAD == origin/main == remote main
```

다르면 HOLD.

## Snapshot Evidence / State
push 성공 후 기존 History/State에 최소 기록:
- Order-056 PASS
- GitHub Initial Connection
- Pre-Freeze Snapshot
- remote name `origin`
- branch `main`
- commit SHA
- push PASS
- local/remote SHA match
- GitHub role = backup/version history
- Overall PASS NOT YET
- Freeze NOT YET

credential/secret는 기록하지 않는다.

## Important Atomicity Note
State Sync 후 Git 단계에서 HOLD가 발생할 수 있다.

그 경우:
- 이미 수행된 Local State Sync를 rollback하지 않는다.
- Git init만 성공하고 push가 실패했다면 사실대로 PARTIAL/HOLD 기록
- remote에 push되지 않았으면 Snapshot 완료로 표시하지 않는다.
- 재시도는 실패 원인 해결 Evidence가 있을 때만 한다.

## Idempotency
재수신 시:
- `.git`이 이미 생성돼 있고
- origin exact match
- main branch
- 동일 snapshot commit이 remote에 존재
- 상태 Sync 완료
이면 새 init/commit/push 없이 `NO_CHANGE`.

예상 밖 remote/history가 있으면 HOLD.

## Prohibited
- MVP Overall PASS 확정
- MVP Freeze
- Known Limitation 종료
- Phase2
- Architecture/Terminology 변경
- Rule/Prevention 승격
- Test/Regression 재실행
- 새 Runtime Evidence
- 다른 GitHub repository 사용
- force push
- merge/rebase
- credential 저장/출력

## Result Format
A. Routing
B. Local State Preflight
C. Sensitive/Unwanted File Check
D. Remote Read-only Verification
E. State Sync Recovery
F. Validation Before Git
G. Git Initialization
H. Remote Configuration
I. Files Staged
J. Commit
K. Push
L. Local/Remote SHA Verification
M. Snapshot State
N. Preservation
O. Files Changed
P. Done / Now / Next
Q. User Approval Required

## Completion Gate
PASS:
- Local preflight PASS
- sensitive risk 0
- remote verified expected repository
- remote empty/initial-push safe
- State Sync complete
- Local validation PASS
- git init/main/origin exact
- stage expected files only
- commit PASS
- push PASS
- local/remote SHA match
- Known Limitations OPEN
- Overall PASS NOT YET
- Freeze NOT YET
- Architecture/Core/Evidence preserved

HOLD:
- remote non-empty/unexpected
- sensitive risk
- auth failure
- stage unexpected
- SHA mismatch
- validation mismatch
- any destructive resolution required

## End State
성공 후:
- `C:\Obsidian\Beta` = Local SSOT
- Git initialized locally
- origin = `https://github.com/2passion/Beta.git`
- branch = main
- GitHub Pre-Freeze Snapshot = PASS
- local/remote SHA match
- MVP 7 Gates = 7/7 OFFICIAL PASS
- Overall Evidence Review = PASS FOR USER GATE
- Known Limitations = 3 OPEN
- MVP Overall PASS = NOT YET
- MVP Freeze = NOT YET
- Next = Final User Gate
- After user approval only: MVP Overall PASS & Freeze Closure

=== ORDER END ===
