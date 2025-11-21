# SAST CLI 테스트 및 개발 규칙

## 테스트 결과 폴더

**규칙**: 모든 테스트 결과는 `test-results/` 폴더에 저장해야 합니다.

### 이유
- `.gitignore`에 `test-results/` 폴더가 등록되어 있어 Git에서 자동으로 제외됩니다.
- 테스트 결과물이 저장소에 커밋되는 것을 방지합니다.
- 일관된 테스트 결과 관리를 위함입니다.

### 사용 예시

```bash
# ✅ 올바른 사용
export PATH=$HOME/bin/joern/joern-cli:$HOME/bin/spotbugs:$PATH
export OLLAMA_MODEL="qwen3:4b-thinking-2507-q4_K_M"
uv run sarif-cli -i ./test-project -o ./test-results/basic --enable-llm --llm-url http://localhost:11434

# ❌ 잘못된 사용 (results* 폴더는 gitignore 되지만 명시적이지 않음)
uv run sarif-cli -i ./test-project -o ./results-test
```

## 규칙 기반 패치 시스템

### 위치
`sarif_cli/llm_verifier.py`의 `generate_simple_patch()` 함수

### 목적
LLM이 없거나 오류 발생 시 기본적인 보안 패치를 자동으로 생성하는 폴백(fallback) 시스템

### 현재 구현된 규칙

#### 1. Buffer Overflow (CWE-119)
**Rule ID**: `CWE-119`, `buffer` (case-insensitive)

**패턴**:
- `strcpy` → `strncpy` + TODO 주석
- `gets` → `fgets` + TODO 주석

**예시**:
```c
// Before
strcpy(dest, src);

// After (Rule-based patch)
strncpy(dest, src);  // TODO: Add size parameter for strncpy
```

#### 2. SQL Injection (CWE-89)
**Rule ID**: `CWE-89`, `SQL`

**패턴**:
- SQL 문자열 조합 감지 → PreparedStatement 사용 권장

**예시**:
```java
// Patch comment
// Use PreparedStatement instead of string concatenation
```

#### 3. Null Pointer Dereference
**Rule ID**: `NP_ALWAYS_NULL`, `null` (case-insensitive)

**패턴**:
- Null 역참조 감지 → null check 추가 권장

**예시**:
```java
// Patch comment
// Add null check before dereferencing
```

#### 4. 기타 규칙
알려지지 않은 취약점의 경우:
```
// TODO: Manual review required for {rule_id}
```

### 규칙 확장 방법

새로운 CWE 규칙을 추가하려면 `generate_simple_patch()` 함수에 다음과 같이 추가:

```python
elif "CWE-XXX" in vulnerability.rule_id or "pattern" in vulnerability.rule_id.lower():
    if "unsafe_function" in original_line:
        patched_line = original_line.replace("unsafe_function", "safe_function")
        return patched_line + "  // TODO: Additional parameters needed"
    return "// Recommended fix for CWE-XXX"
```

### 제한사항
- 간단한 문자열 치환만 지원
- 복잡한 로직 변경은 불가능
- LLM 검증이 훨씬 정확하므로 가능한 LLM 사용 권장

## LLM 설정

### 로컬 LLM (Ollama) 사용

```bash
# 환경 변수 설정
export OLLAMA_MODEL="qwen3:4b-thinking-2507-q4_K_M"

# CLI 실행
uv run sarif-cli -i ./test-project \\
  -o ./test-results/llm-test \\
  --enable-llm \\
  --llm-url http://localhost:11434
```

### 지원되는 LLM
- Ollama (OpenAI compatible API)
- 기타 OpenAI compatible API 서버

### LLM 없이 실행
LLM을 사용하지 않으면 규칙 기반 패치만 생성됩니다:
```bash
uv run sarif-cli -i ./test-project -o ./test-results/no-llm
```

## 개발 워크플로우

1. **코드 수정** → `new-crs-sarif/` 폴더에서만 작업
2. **테스트 실행** → 결과는 `test-results/` 폴더에 저장
3. **결과 확인** → SARIF 파일 검토
4. **정리** → `git status`로 test-results가 트래킹되지 않는지 확인

## 주의사항

⚠️ **절대 하지 말아야 할 것**:
- `crs-sarif/` 폴더의 파일 수정 (읽기 전용)
- 테스트 결과를 프로젝트 루트에 직접 저장
- SARIF 파일을 Git에 커밋
