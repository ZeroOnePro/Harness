# AI Coding Agent Token Efficiency Guide

이 문서는 공유 대화의 상세 가이드를 바탕으로 정리한 참고 문서입니다. Codex, Claude Code 등 AI 코딩 에이전트가 불필요한 컨텍스트와 Tool Call을 줄이기 위한 공통 원칙을 담았습니다.

## 사용 방법
- AGENTS.md: Codex 프로젝트 루트에 배치할 짧은 실행 지침.
- CLAUDE.md: Claude Code 프로젝트 루트에 배치할 짧은 실행 지침.
- 이 상세 가이드: 필요할 때만 읽는 별도 참고 문서.
- 기존 지침 파일이 있다면 내용을 검토해 필요한 규칙만 합칩니다.
- 상세 가이드 전체를 상시 지침에 중복 삽입하면 지침 자체의 컨텍스트 비용이 커질 수 있습니다.

## Core Principle
항상 필요한 정보만 읽고, 필요한 코드만 수정하고, 필요한 설명만 출력합니다.
토큰 절약보다 정확성이 우선이며, 충분한 정보가 있다면 추가 탐색을 하지 않습니다.

## 1. Minimize Context
작업에 직접 관련된 파일만 읽습니다.
- 프로젝트 전체를 무작정 탐색하지 않습니다.
- 파일명이나 심볼을 알고 있다면 해당 위치부터 확인합니다.
- 큰 파일은 필요한 함수, 클래스, 컴포넌트 주변만 읽습니다.
- 이미 읽은 내용을 이유 없이 다시 읽지 않습니다.
- 관련 없는 디렉터리는 탐색하지 않습니다.

권장 흐름: search → relevant section → edit.
피할 흐름: scan entire repository → read many files → decide.

## 2. Prefer Search Over Full File Reads
함수명, 변수명, 컴포넌트명, 에러 메시지처럼 식별 가능한 정보가 있다면 먼저 검색합니다.
예: handleSubmit, useAuth, LoginForm, "Failed to fetch".
검색 결과로 파일과 위치를 좁힌 뒤 해당 부분을 확인합니다.
전체 파일은 파일 구조 전체, 여러 함수 간 상호작용을 이해해야 하거나 부분 읽기만으로 안전한 수정이 불가능할 때 읽습니다.

## 3. Make the Smallest Possible Change
문제 해결에 필요한 최소 변경을 우선합니다.
관련 없는 리팩터링, 파일명 변경, 포맷 변경, 의존성 변경을 하지 않습니다.
필요하지 않은 추상화나 helper 함수를 추가하지 않고 기존 코드 스타일을 유지합니다.
전체 파일 재작성보다 작은 diff를 사용합니다.

## 4. Do Not Rewrite Unchanged Code
수정하지 않는 코드를 다시 생성하거나 출력하지 않습니다.
함수 하나를 수정한다면 해당 함수만 수정합니다.
대형 React 컴포넌트, JSON, YAML, lockfile, 생성 파일, 설정 파일의 전체 재작성에 특히 주의합니다.

## 5. Avoid Unnecessary Tool Calls
Tool Call 전에 현재 정보만으로 작업할 수 있는지 판단합니다.
검색 → 파일 읽기 → 같은 파일 다시 읽기 → 프로젝트 재검색 같은 반복을 피합니다.
권장 흐름은 검색 → 관련 코드 확인 → 수정 → 검증입니다.

## 6. Stop Exploring When Enough Information Exists
원인과 수정 지점이 명확하면 탐색을 종료하고 구현합니다.
더 좋은 방법이 있을지도 모른다는 이유만으로 프로젝트 전체를 추가 조사하지 않습니다.
추가 탐색은 다른 코드에 대한 영향, API·타입 정의, 필요한 기존 패턴, 불분명한 테스트 실패를 확인할 때 수행합니다.

## 7. Keep Responses Concise
작업 중 설명과 최종 응답을 짧게 유지합니다.
보고할 내용:
1. 무엇을 수정했는지
2. 중요한 이유
3. 테스트 또는 검증 결과
4. 남은 문제

변경하지 않은 코드 설명, 당연한 동작 설명, 동일 내용 반복, 긴 과정 회고, 불필요한 요약을 피합니다.

## 8. Avoid Repeating User Requirements
사용자가 제공한 요구사항을 답변에서 길게 반복하지 않습니다.
필요한 핵심 제약만 짧게 유지합니다.
예: Constraint: modify Login.tsx only.

## 9. Limit Scope
요청받은 범위를 넘지 않습니다.
버그 수정 중 요청하지 않은 UI 개선, 스타일 변경, 구조 변경, 성능 최적화, 새 테스트 프레임워크 도입을 임의로 하지 않습니다.
현재 작업에 필요하지 않은 개선점은 수정하지 않습니다.

## 10. Use Existing Project Patterns
새 구조를 만들기 전에 가까운 기존 구현을 참고합니다.
보통 인접 파일 1~2개로 충분하며, 패턴을 찾으려고 프로젝트 전체를 검색하지 않습니다.

## 11. Reduce Test Scope
변경과 가장 관련 있는 의미 있는 검증부터 수행합니다.
targeted test → relevant package test → type check → build → full test suite.
작은 수정마다 전체 스위트를 실행하지 않되, 저장소 정책에서 요구하거나 영향 범위상 필요한 검증은 생략하지 않습니다.

## 12. Reduce Command Output
긴 터미널 로그 전체를 컨텍스트에 넣지 않습니다.
가능하면 필요한 에러 부분이나 마지막 출력만 확인합니다.
예: command 2>&1 | tail -50
이 예시는 해당 명령을 지원하는 셸 기준이며 다른 셸에서는 동등한 방법을 사용합니다.
설치, 빌드, 전체 테스트, 상세 컴파일러 출력, Docker 로그, 서버 로그에 주의합니다.
성공 로그 전체를 읽을 필요는 없지만 잘린 출력 때문에 중요한 실패를 놓치지 않아야 합니다.

## 13. Ignore Large or Irrelevant Files
직접 관련되지 않는 한 다음 항목을 읽지 않습니다.

```text
node_modules/
dist/
build/
coverage/
.git/
.cache/
.next/
vendor/
tmp/
logs/
*.log
*.min.js
*.map
package-lock.json
yarn.lock
pnpm-lock.yaml
```

Lockfile은 실제 문제와 관련된 경우에 확인합니다.

## 14. Preserve Existing Files
부분 수정으로 해결할 수 있다면 전체 파일을 다시 생성하지 않습니다.
formatter나 자동 재작성으로 무관한 diff가 생기지 않도록 하며, 변경 diff는 작고 명확하게 유지합니다.

## 15. Avoid Premature Refactoring
더 깔끔하거나 현대적으로 보인다는 이유만으로 리팩터링하지 않습니다.
현재 정상 동작하고 요청과 관계없는 코드는 유지합니다.

## 16. Avoid Unnecessary Comments
코드 자체로 명확한 로직에는 주석을 추가하지 않습니다.
예: count += 1 앞에 "Increment count by one"을 설명할 필요는 없습니다.
주석은 복잡한 의도, 제약, 비직관적 로직을 설명할 때 추가합니다.

## 17. Do Not Over-Engineer
간단한 문제에는 간단한 해결책을 사용합니다.
추상화, wrapper, utility, factory, custom hook, dependency, configuration layer, state management layer, design pattern은 실제 필요성이 있을 때만 추가합니다.
10줄 수정으로 해결할 일을 불필요한 다섯 파일 구조로 만들지 않습니다.

## 18. Use Short Planning
긴 계획을 출력하지 않습니다.
복잡한 작업도 다음 정도로 충분합니다.
1. Locate implementation
2. Identify cause
3. Apply minimal fix
4. Run targeted verification

간단한 수정은 별도의 긴 계획 없이 진행합니다.

## 19. Summarize Long Sessions
긴 세션은 핵심 상태만 요약합니다.
- Goal
- Changed files
- Important decisions
- Current issue
- Remaining work

오래된 탐색 과정, 실패한 가설, 불필요한 대화 기록은 반복하지 않습니다.
권장 요약 길이는 약 300~500 tokens이며, 정확한 작업 재개에 필요한 내용은 보존합니다.

## 20. Prefer Implementation Over Discussion
요구사항이 명확하면 장시간 설명하거나 대안을 나열하기보다 구현합니다.
understand → inspect → implement → verify.
대안 비교는 실제 구현 결정을 위해 필요할 때만 수행합니다.

## Agent Behavior Rules
- Be token-efficient.
- Inspect only files relevant to the task.
- Prefer targeted search over reading entire files.
- Do not repeatedly read the same files unless the content may have changed.
- Make the smallest possible change.
- Do not refactor unrelated code.
- Do not rewrite entire files when a small patch is sufficient.
- Do not modify unrelated formatting.
- Do not add abstractions, dependencies, comments, or helper functions unless necessary.
- Avoid unnecessary tool calls.
- Stop exploring once enough information exists to safely implement the change.
- Use existing project patterns where practical, but do not search the entire repository merely to find them.
- Run the smallest relevant validation first.
- Avoid putting large command outputs into context.
- Do not repeat requirements or previously established information.
- Keep explanations concise.
- Do not explain unchanged code.
- If enough information is available, implement instead of continuing analysis.

## Recommended Workflow
1. Understand the exact requested change
2. Identify likely file or symbol
3. Search only relevant code
4. Read minimum required context
5. Make minimal patch
6. Run targeted validation
7. Report concise result

버그 수정: error → locate → inspect → identify cause → minimal fix → targeted test.
기능 추가: requirement → locate nearest existing pattern → implement smallest compatible change → targeted verification.

## Sub-agent 사용
공유 대화의 요약 원칙에 따라 불필요한 Sub-agent 사용도 줄입니다.
독립적이고 범위가 명확한 작업에 실질적 이점이 있으며 사용자 요청과 적용 지침이 허용할 때만 위임합니다.
같은 파일이나 문제를 여러 에이전트가 중복 조사하지 않도록 하고, 필요한 맥락과 짧은 결과만 주고받습니다.

## Priority
공유 가이드의 우선순위:
1. Correctness
2. Safety
3. User requirements
4. Existing project conventions
5. Minimal changes
6. Token efficiency

토큰 절약을 위해 정확성을 희생하지 않습니다.
정확성을 확보한 이후 불필요한 탐색, 출력, 수정, Tool Call을 최소화합니다.

## 출처
https://chatgpt.com/share/6aaaa4b7-2ee0-83ee-acd4-f257dcb7ad0c
