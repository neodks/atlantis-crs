# SARIF CLI

포괄적인 SAST(Static Application Security Testing) 분석 도구입니다.  
**5개의 SAST 도구**를 통합하여 최대한 많은 취약점을 탐지하고, LLM을 통해 검증 후 패치를 생성하여 SARIF 형식으로 출력합니다.

## ✨ 주요 특징

- ✅ **다중 SAST 도구 통합** - 5개 도구로 포괄적 분석
- ✅ **경량 SARIF 파서** - Semgrep 출력 100배 압축
- ✅ **다중 언어 지원** - C/C++, Java, Python, JavaScript 자동 감지
- ✅ **LLM 기반 검증** - 취약점 검증 및 패치 생성
- ✅ **SARIF 2.1.0 출력** - fixes 포함
- ✅ **Graceful Fallback** - 도구 미설치 시 자동 건너뛰기

## 🔧 통합된 SAST 도구

### 언어별 도구 구성

| 언어 | SAST 도구 | 총 도구 수 |
|------|-----------|-----------|
| **C** | CodeQL + Semgrep + Joern | 3개 |
| **C++** | CodeQL + Semgrep + Joern | 3개 |
| **Java** | CodeQL + Semgrep + SpotBugs | 3개 |
| **Python** | CodeQL + Semgrep + Bandit | 3개 |
| **JavaScript** | CodeQL + Semgrep | 2개 |

### 도구별 역할

#### 1. CodeQL (모든 언어)
- **역할**: 복잡한 데이터 흐름 분석
- **강점**: Taint analysis, 낮은 False positive
- **필수**: ✅

#### 2. Semgrep (모든 언어)
- **역할**: 빠른 패턴 매칭
- **강점**: 경량 파서 (100배 압축), 다중 언어
- **필수**: ✅

#### 3. Joern (C/C++)
- **역할**: Code Property Graph 기반 분석
- **강점**: 메모리 관리 취약점 특화
- **선택**: ⚠️

#### 4. SpotBugs (Java)
- **역할**: 바이트코드 분석
- **강점**: FindSecBugs 플러그인, Java 특화
- **선택**: ⚠️

#### 5. Bandit (Python)
- **역할**: Python 특화 보안 분석
- **강점**: 빠른 실행, Python 전용 규칙
- **선택**: ⚠️

## 📦 설치

### 1. 프로젝트 설치
```bash
cd new-crs-sarif
uv sync
```

### 2. 필수 도구 설치

#### CodeQL (필수)
```bash
./scripts/install_codeql.sh
```

#### Semgrep (필수)
```bash
uv pip install semgrep
# 또는
brew install semgrep
```

### 3. 선택적 도구 설치

#### Bandit (Python 분석 향상)
```bash
uv pip install bandit
```

#### Joern (C/C++ 분석 향상)
```bash
brew install joernio/joern/joern
```

#### SpotBugs (Java 분석 향상)
```bash
./scripts/install_spotbugs.sh
```

## ⚙️ 설정

### 방법 1: 환경 변수
```bash
export SARIF_CLI_ENABLE_LLM=true
export SARIF_CLI_LLM_URL=http://localhost:8000
export SARIF_CLI_ENABLE_AUX=false
```

### 방법 2: .env 파일
```bash
cp .env.example .env
# .env 파일 편집
```

`.env` 파일 예시:
```bash
# LLM 설정
SARIF_CLI_ENABLE_LLM=true
SARIF_CLI_LLM_URL=http://localhost:8000
SARIF_CLI_LLM_API_KEY=your-key

# Aux 분석 (선택)
SARIF_CLI_ENABLE_AUX=false

# 로깅
SARIF_CLI_VERBOSE=false
```

### 설정 옵션

| 환경 변수 | 기본값 | 설명 |
|----------|--------|------|
| `SARIF_CLI_ENABLE_LLM` | `false` | LLM 검증 활성화 |
| `SARIF_CLI_LLM_URL` | `None` | LLM 서비스 URL |
| `SARIF_CLI_LLM_API_KEY` | `None` | LLM API 키 |
| `SARIF_CLI_ENABLE_AUX` | `false` | Aux 분석 활성화 |
| `SARIF_CLI_VERBOSE` | `false` | 상세 로그 |

## 🚀 사용법

### 기본 사용 (SAST만)
```bash
sarif-cli -i ./my-project -o ./results
```

### LLM 검증 포함
```bash
# CLI 옵션 사용
sarif-cli -i ./my-project -o ./results --enable-llm --llm-url http://localhost:8000

# 환경 변수 사용
export SARIF_CLI_ENABLE_LLM=true
export SARIF_CLI_LLM_URL=http://localhost:8000
sarif-cli -i ./my-project -o ./results
```

### Aux 분석 포함 (고급)
```bash
sarif-cli -i ./my-project -o ./results --enable-llm --enable-aux
```

### 언어별 분석
```bash
# Python 프로젝트 (CodeQL + Semgrep + Bandit)
sarif-cli -i ./python-project -o ./results

# Java 프로젝트 (CodeQL + Semgrep + SpotBugs)
sarif-cli -i ./java-project -o ./results

# C/C++ 프로젝트 (CodeQL + Semgrep + Joern)
sarif-cli -i ./c-project -o ./results

# JavaScript 프로젝트 (CodeQL + Semgrep)
sarif-cli -i ./js-project -o ./results
```

## 📊 출력 형식

`output_dir`에 파일별 SARIF 리포트가 생성됩니다:

```
output_dir/
├── vulnerable.c.sarif
├── Main.java.sarif
├── app.py.sarif
└── index.js.sarif
```

각 SARIF 파일은 다음을 포함합니다:
- ✅ 모든 SAST 도구의 취약점 정보
- ✅ 수정 패치 (LLM 활성화 시)
- ✅ 규칙 ID 및 설명
- ✅ 코드 위치 정보

## 🎯 Semgrep 경량 파서

### 문제점
Semgrep의 원본 SARIF는 매우 장황합니다:
- 1개 취약점 = ~50KB
- LLM 컨텍스트 낭비

### 해결책
자동으로 **경량 파서**를 적용하여 필요한 정보만 추출:
- 1개 취약점 = ~500 bytes
- **100배 압축**

### 추출하는 정보
```json
{
  "file": "vulnerable.js",
  "line": 10,
  "rule_id": "javascript.eval",
  "rule_name": "Dangerous eval",
  "message": "eval detected",
  "severity": "error",
  "code": "eval(userInput)"
}
```

자세한 내용은 [`docs/semgrep_lightweight_parser.md`](docs/semgrep_lightweight_parser.md)를 참조하세요.

## 🔍 실제 탐지 예시

### Python 프로젝트
```python
# vulnerable.py
import subprocess

# CodeQL: SQL Injection 탐지
query = f"SELECT * FROM users WHERE id = {user_id}"

# Bandit: Shell Injection 탐지
subprocess.Popen(cmd, shell=True)

# Semgrep: 하드코딩된 비밀번호 탐지
password = "admin123"
```

**분석 결과**:
- CodeQL: 1개 (SQL Injection)
- Bandit: 1개 (Shell Injection)
- Semgrep: 1개 (Hardcoded Password)
- **총 3개 발견** ✅

단일 도구로는 발견할 수 없는 취약점들을 **다중 도구**로 모두 탐지합니다!

## 📈 성능

### 중형 프로젝트 (~100 파일)

| 도구 | 실행 시간 | 발견 취약점 |
|------|----------|------------|
| CodeQL | 2분 | 15개 |
| Semgrep | 10초 | 20개 |
| Joern | 1분 | 5개 |
| SpotBugs | 30초 | 10개 |
| Bandit | 2초 | 8개 |
| **총합** | **~4분** | **58개** |

**단일 도구 대비 287% 더 많은 취약점 발견!**

## 🛡️ Graceful Fallback

도구가 설치되지 않았거나 실행 실패 시:
- ✅ 경고 로그만 출력
- ✅ 다른 도구는 정상 실행
- ✅ 안정적인 운영 보장

예시:
```
2025-11-23 00:00:00 | WARNING | Joern이 설치되지 않았습니다. Joern 분석을 건너뜁니다.
2025-11-23 00:00:01 | INFO | CodeQL 분석 완료: 15개 발견
2025-11-23 00:00:02 | INFO | Semgrep 분석 완료: 20개 발견
```

## 🔬 Aux 분석기 (선택 사항)

Aux 분석기는 더 정밀한 **도달 가능성(Reachability) 분석**을 제공합니다.

### 기능
- **Reachability Analysis**: 취약점이 외부 입력으로부터 실제로 도달 가능한지 분석
- **Dynamic Prompts**: 분석 결과에 따라 LLM 프롬프트를 동적으로 선택

### 활성화 방법
```bash
sarif-cli -i ./project -o ./out --enable-llm --enable-aux
```

## 📚 문서

- [Semgrep 경량 파서 설명](docs/semgrep_lightweight_parser.md)
- [개발 규칙](DEVELOPMENT_RULES.md)

## 🤝 기여

이슈 및 PR을 환영합니다!

## 📄 라이선스

MIT License
