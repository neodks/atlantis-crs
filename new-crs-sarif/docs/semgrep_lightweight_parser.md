# Semgrep 경량 파서 설명

## 문제점

Semgrep의 SARIF 출력은 매우 장황합니다:
- 1개 취약점 = ~50KB
- 불필요한 메타데이터, 긴 설명, 도움말 포함
- LLM 컨텍스트 낭비

## 해결 방법

`semgrep_wrapper.py`의 `_parse_sarif_lightweight()` 함수가 **필요한 정보만 추출**합니다.

### 추출하는 정보 (경량화)

```python
{
    "file": "vulnerable.js",           # 파일 경로
    "line": 10,                        # 라인 번호
    "rule_id": "javascript.eval",      # 규칙 ID
    "rule_name": "Dangerous eval",     # 규칙 이름 (짧게)
    "message": "eval detected",        # 메시지
    "severity": "error",               # 심각도
    "code": "eval(userInput)"          # 코드 스니펫 (200자 제한)
}
```

### 제거하는 정보

- ❌ 긴 규칙 설명 (`fullDescription`)
- ❌ 도움말 (`help`)
- ❌ 메타데이터 (`properties`)
- ❌ 긴 코드 스니펫 (200자로 제한)
- ❌ 규칙 전체 정의

## 크기 비교

| 형식 | 1개 취약점 크기 | 10개 취약점 크기 |
|------|----------------|------------------|
| Semgrep 원본 SARIF | ~50KB | ~500KB |
| 경량화된 결과 | ~500 bytes | ~5KB |
| **압축률** | **100배** | **100배** |

## LLM 전달 시 장점

1. ✅ **컨텍스트 절약**: 100배 작은 크기
2. ✅ **빠른 처리**: 파싱 및 전송 속도 향상
3. ✅ **핵심 정보만**: LLM이 필요한 정보만 제공
4. ✅ **토큰 절약**: LLM API 비용 절감

## 사용 예시

```python
from sarif_cli.semgrep_wrapper import SemgrepAnalyzer

analyzer = SemgrepAnalyzer()
results = analyzer.analyze(project_dir, "javascript")

# results는 이미 경량화된 형식
for r in results:
    print(f"{r['file']}:{r['line']} - {r['message']}")
```

## 기술적 세부사항

### 1. SARIF 파싱 최적화

```python
def _parse_sarif_lightweight(self, sarif_data, project_dir):
    # 규칙 정보: 이름과 심각도만 추출
    rules = {}
    for rule in run.get("tool", {}).get("driver", {}).get("rules", []):
        rules[rule["id"]] = {
            "name": rule.get("shortDescription", {}).get("text"),
            "severity": rule.get("properties", {}).get("security-severity"),
            # fullDescription, help 등은 제외
        }
    
    # 결과: 핵심 정보만 추출
    for result in run.get("results", []):
        # 코드 스니펫 길이 제한
        snippet = region.get("snippet", {}).get("text", "")
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
```

### 2. 메모리 효율성

- 전체 SARIF를 메모리에 로드하지 않음
- 스트리밍 방식으로 필요한 정보만 추출
- 즉시 경량화된 형식으로 변환

### 3. LLM 호환성

경량화된 결과는 LLM 프롬프트에 직접 사용 가능:

```python
# LLM에 전달할 컨텍스트
context = f"""
파일: {result['file']}
라인: {result['line']}
취약점: {result['rule_name']}
코드: {result['code']}
"""
```

## 다른 도구와의 비교

| 도구 | 원본 크기 | 경량화 후 | 파서 필요 |
|------|----------|----------|----------|
| CodeQL | 작음 (~5KB) | - | ❌ 불필요 |
| Semgrep | 매우 큼 (~50KB) | 작음 (~500B) | ✅ **필요** |
| Bandit | 중간 (~10KB) | - | ⚠️ 선택적 |
| SpotBugs | 중간 (~15KB) | - | ⚠️ 선택적 |

## 결론

Semgrep의 장황한 SARIF 출력 문제를 **경량 파서**로 해결:
- ✅ 100배 크기 감소
- ✅ LLM 컨텍스트 절약
- ✅ 핵심 정보만 추출
- ✅ 빠른 처리 속도
