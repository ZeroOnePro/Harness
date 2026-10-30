# 공개 스킬 검토와 하네스 적용

확인일: 2026-10-30. 기준 하네스: `b67e17270aa17df6c392a50c720efb2c839aa445`.

현재 하네스에서 부족한 설계 경계 검토와 단순화 절차를 저장소 스킬 두 개로 추가했다. 요구사항 확인·재현·검증·세션 재개는 기존 지침을 재사용한다. 아래 판단은 이 하네스에 대한 적용 판단이며 프로젝트의 성능 순위가 아니다.

## 원문 확인 중 달라진 내용

- pstack의 현재 [unslop](https://github.com/backnotprop/pstack/blob/25abb38559ddbabec563646224d09eff9a250eca/skills/unslop/SKILL.md)은 글의 AI식 표현을 다듬는다. 코드 중복·추상화 정리와 같지 않으므로 새 스킬은 `harness-simplify`로 명명했다.
- pstack의 [architect](https://github.com/backnotprop/pstack/blob/25abb38559ddbabec563646224d09eff9a250eca/skills/architect/SKILL.md)는 다른 스킬과 다중 모델 실행을 연결한다. 여기서는 설계 스케치·대안 비교의 아이디어를 참고해 단일 에이전트로 수행할 수 있는 절차를 독립 작성했다.
- 기존 [GSD 저장소](https://github.com/gsd-build/get-shit-done)는 현재 [GSD Core](https://github.com/open-gsd/gsd-core)로 이전을 안내한다. 이전 저장소의 설치 안내를 그대로 적용하지 않았다.

## 후보별 판단

| 후보·확인 자료 | 이 하네스의 적용 판단 |
| --- | --- |
| [pstack](https://github.com/backnotprop/pstack) | 설계 스케치와 대안 비교를 `harness-architect`에 반영. 전체 스킬·다중 모델 실행은 추가하지 않음 |
| [Matt Pocock Skills](https://github.com/mattpocock/skills) | 질문·명세·버그 진단은 기존 운영 지침 4·11.2·12.1절과 겹침. 질문 인터뷰를 매 작업에 강제하지 않고 기존 규칙 유지 |
| [Superpowers](https://github.com/obra/superpowers) | 검증 증거·원인 분석은 운영 지침 5~6·11.2절과 겹침. 전체 개발 순서를 상시 적용하지 않음 |
| [gstack](https://github.com/garrytan/gstack) · [BMAD](https://github.com/bmad-code-org/BMAD-METHOD) | 제품·PM·QA 역할을 구성해야 하는 프로젝트에서 재검토. 현재 문서 저장소에 역할 체계 추가는 보류 |
| [GSD 이전 안내](https://github.com/gsd-build/get-shit-done) | 세션 재개는 적용 가이드 8.3절 활용. 현재 프로젝트에 별도 단계 관리 체계가 필요한 증거가 없음 |
| [Spec Kit](https://github.com/github/spec-kit) | 복잡한 변경은 운영 지침 12.1절의 최소 명세 활용. 공식 명세·작업 추적이 필요해지면 도입 검토 |
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | UI 구현이 있는 대상 프로젝트에서 선택. 현재 저장소에는 UI가 없음 |
| [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) | React·Next.js·Vercel 관련 대상 프로젝트에서 선택. 현재 저장소에 해당 구현 없음 |
| [Anthropic Skills](https://github.com/anthropics/skills) | 스킬 구조와 작성 방식 참고. 예제를 일괄 설치할 필요 없음 |
| Karpathy Guidelines | 제공된 이름만으로 특정 저장소를 확정하지 않음. 최소 변경·단순성은 기존 운영 지침 5·10절 유지 |

이 표의 보류는 해당 도구를 실행·평가해 효과가 없었다는 뜻이 아니다. README와 선택한 스킬 원문을 확인해 현재 필요성과 중복을 판단했다.

## 적용한 구성과 선택 이유

| 대안 | 변경 영향·유지보수 | 선택 |
| --- | --- | --- |
| 외부 프레임워크 일괄 설치 | 기존 질문·검증 규칙과 중복되고 별도 실행 환경·업데이트 관리가 추가됨 | 보류 |
| 루트 v2 가이드를 직접 개정 | 메일 원본 보존 경로와 개정본을 먼저 분리해야 함 | 이번에는 보류 |
| 짧은 시작 지침 + 선택형 스킬 + 적용 기록 | 원본을 유지하고 필요한 절차만 읽을 수 있음 | 적용 |

- [AGENTS.md](../AGENTS.md)는 공통 행동·원본 보존·문서와 스킬의 읽는 조건을 연결한다.
- [harness-architect](../.agents/skills/harness-architect/SKILL.md)는 현재 책임과 호출 경로를 확인한 뒤 설계 대안·변경 영향·검증 경로를 비교한다.
- [harness-simplify](../.agents/skills/harness-simplify/SKILL.md)는 같은 정책의 중복과 역할 없는 추상화를 찾고, 기존 계약·필수 제약을 보존하며 정리한다.

공통 질문·검증 절차를 별도 스킬로 또 복제하지 않았다. 두 스킬은 외부 스킬 호출이나 모델 설치에 의존하지 않는다. 문서 표현 정리용 `unslop`은 이번 코드·지침 유지보수 목적에서 별도로 설치하지 않았다.

## 사용과 다른 프로젝트로 전달

Codex의 저장소 스킬 위치는 `.agents/skills/`다. 메타데이터로 스킬을 고르고 필요한 본문만 읽는 방식은 [OpenAI 공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)를 기준으로 했다. 이 저장소에서 명시적으로 요청할 때는 다음처럼 사용한다.

```text
$harness-architect로 현재 구조의 책임과 변경 영향을 검토해줘.
$harness-simplify로 이번 변경의 중복과 불필요한 추상화를 정리해줘.
```

스킬이 목록에 나타나지 않으면 Codex를 재시작해 확인한다. 목록의 자동 발견과 새 세션의 행동 평가는 아직 별도로 실행하지 않았다. 현재 세션에서는 실제 파일을 읽고 절차를 적용할 수 있다.

다른 프로젝트에 하네스를 적용할 때는 기존 적용 가이드에 더해 필요한 스킬 폴더만 대상의 `.agents/skills/`로 복사하고, 기존 `AGENTS.md`에 사용 조건과 실제 경로를 합친다. 같은 이름의 스킬이 있으면 먼저 비교한다. 선택 기록도 전달한다면 이 문서의 상대 경로가 대상에 맞는지 확인한다. 이 저장소의 원본 보관 규칙·해시 목록은 일반 제품 프로젝트의 규칙으로 복사하지 않는다.

Claude Code 등 다른 도구에서는 해당 도구가 지원하는 스킬 경로와 호출 방식을 확인한 뒤 연결한다. 여기서 `.agents/skills/`에 배치한 사실을 다른 도구의 자동 발견·플러그인 설치 완료로 간주하지 않는다.

## 행동·비용 평가

아래 사례는 후속 비교용이다. 이번 문서·메타데이터 검사는 [검증 기록](VERIFICATION.md)에 있으며, 독립 행동 평가 통과를 뜻하지 않는다.

| 입력·상황 | 기대 행동 | 현재 상태 |
| --- | --- | --- |
| 오타 한 줄 수정 | 바로 수정·확인, 설계 대안과 인터뷰 생략 | 미실행 |
| 기존 문서에 목적·완료 기준이 있는 기능 요청 | 재질문 없이 기존 기준 사용, 필요할 때만 최소 명세 | 미실행 |
| 상태 소유자가 얽힌 컴포넌트 분리 | 실제 호출·상태 경로를 근거로 대안·호환성·검증 비교 | 미실행 |
| 비슷한 함수가 서로 다른 정책을 처리 | 겉모양만 보고 통합하지 않음 | 미실행 |
| 공개 API의 내부 참조가 없음 | 외부 계약 확인 없이 삭제하지 않음 | 미실행 |
| 하네스의 중복 문구 정리 | 출처·권한·검증·원본 바이트를 보존하고 참조 연결 | 미실행 |
| 검증 환경을 사용할 수 없음 | 검사 성공을 주장하지 않고 미검증 경로 명시 | 미실행 |

비교할 때 기준 커밋·모델·도구·입력·시작 상태를 맞추고 한 스킬씩 적용/미적용을 비교한다. 순서와 반복 횟수를 기록하고 원래 정상 사례도 포함한다. 매 실행에 요구사항 충족률, 관련 테스트 결과, 불필요한 질문·재작업 횟수, 완료 시간을 남긴다. 제공되는 사용량에서 입력·출력·캐시 읽기 토큰과 추가 모델 호출을 구분하고, 관측할 수 없는 값은 미측정으로 둔다.

품질이 유지·개선되는지 먼저 보고 비용과 시간을 비교한다. 실제 전후 실행 없이 스킬 생성, 문서 축약, 메타데이터 통과를 토큰 절감이나 행동 개선으로 보고하지 않는다.

추가 원문 기준: [Matt Pocock Skills README](https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/README.md), [Superpowers 완료 검증](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/verification-before-completion/SKILL.md). 각 저장소는 이후 변경될 수 있다. 새 스킬은 원문 파일을 복제한 배포본이 아니다.
