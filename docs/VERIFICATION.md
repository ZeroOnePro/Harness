# 저장소 검증

실행 위치: 저장소 루트. 작성 환경: zsh, Python 3 (`python` 명령). 이 저장소에는 제품 빌드·기능 테스트·CI 설정이 없다. 문서와 스킬 변경은 원본 보존·참조 경로·스킬 형식을 확인한다.

## 재실행할 검사

공백 오류와 메일 첨부 원본 9개의 존재·크기·SHA-256을 확인한다. 해시 기준은 `attachments-manifest.json`이며 새 내용에 맞춰 덮어쓰지 않는다.

```sh
git diff --check
python - <<'PY'
import hashlib
import json
from pathlib import Path

manifest = json.loads(Path('attachments-manifest.json').read_text())
assert manifest['attachment_count'] == len(manifest['files']) == 9
for item in manifest['files']:
    data = Path(item['path']).read_bytes()
    assert len(data) == item['bytes'], item['path']
    assert hashlib.sha256(data).hexdigest() == item['sha256'], item['path']
print('PASS: 9 original attachments')
PY
```

활성 문서·스킬의 로컬 Markdown 링크 대상이 존재하는지 확인한다. 보관된 원문은 편집 대상에서 제외한다. 아래 검사는 외부 URL의 유효성이나 절 번호의 의미를 검증하지 않는다.

```sh
python - <<'PY'
import re
from pathlib import Path
from urllib.parse import unquote

files = [Path('README.md'), Path('AGENTS.md')]
files += list(Path('docs').rglob('*.md'))
files += list(Path('.agents/skills').rglob('SKILL.md'))
count = 0
for path in files:
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        target = unquote(target.split('#', 1)[0])
        assert (path.parent / target).exists(), (str(path), target)
        count += 1
print(f'PASS: {count} local links in {len(files)} files')
PY
```

스킬 형식은 작성 환경의 `skill-creator/scripts/quick_validate.py`로 각 폴더를 검사한다. 해당 스크립트는 이 저장소에 포함되지 않는다. 이번 환경에서는 기본 `python`에 `PyYAML`이 없어 최초 검사가 실패했다. 이미 `PyYAML 6.0.1`이 있는 `/usr/bin/python3`로 실행한다. 다른 환경에서는 이 의존성이 있는 Python과 실제 스킬 경로를 사용한다.

```sh
/usr/bin/python3 /home/sungminyou/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/harness-architect
/usr/bin/python3 /home/sungminyou/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/harness-simplify
```

표시용 메타데이터와 폴더·스킬 이름이 일치하고 자동 선택을 막는 설정이 없는지 확인한다.

```sh
/usr/bin/python3 - <<'PY'
from pathlib import Path
import yaml

for skill in sorted(Path('.agents/skills').iterdir()):
    body = (skill / 'SKILL.md').read_text()
    front = yaml.safe_load(body.split('---', 2)[1])
    assert front['name'] == skill.name
    config = yaml.safe_load((skill / 'agents/openai.yaml').read_text())
    ui = config['interface']
    assert 25 <= len(ui['short_description']) <= 64
    assert '$' + skill.name in ui['default_prompt']
    assert config.get('policy', {}).get('allow_implicit_invocation', True)
    print(f'PASS: {skill.name} UI metadata')
PY
```

## 2026-10-30 적용 검증 기록

| 항목 | 결과·증거 |
| --- | --- |
| 기준 상태 | `b67e17270aa17df6c392a50c720efb2c839aa445`에서 시작, 기존 작업 트리 변경 없음 |
| 첨부 원본 | 위 명령으로 9개 파일의 크기·SHA-256 확인 |
| 문서 연결 | 로컬 링크 28개 / 활성 파일 6개 확인. 새 시작 지침에서 두 스킬과 적용·검증 문서에 연결 |
| 스킬 형식 | 두 폴더에 `quick_validate.py` 실행. 이름·설명·미완성 표식 검사 |
| UI 메타데이터 | 각 `agents/openai.yaml`의 표시 이름·설명과 실제 스킬 이름을 가리키는 기본 요청 확인 |
| 설계 검토 적용 | 원본 변경·전체 도입·선택형 추가 대안을 비교해 선택 이유를 적용 기록에 남김 |
| 중복 검토 적용 | 기존 질문·명세·검증 규칙을 재사용하고 별도 중복 스킬을 추가하지 않음 |
| diff | `git diff --check`와 원본·해시 목록의 변경 여부 확인 |
| 자동 발견·새 세션 행동 평가 | 미실행. 파일 배치·형식 검사와 구분 |
| 코드 컴포넌트 검토·실행 | 제품 코드가 없어 해당 없음. 실제 제품 프로젝트 검증은 미실행 |
| 적용/미적용 품질·토큰·시간 비교 | 미실행·미측정. 후속 사례는 [스킬 적용 기록](SKILL_ADOPTION.md)에 있음 |

위 기록은 이 저장소의 문서·형식 검증 범위다. 다른 프로젝트로의 적용 완료나 성능 개선을 뜻하지 않는다.
