# SARIF CLI

간소화된 SAST(Static Application Security Testing) 분석 도구입니다. 
input 디렉토리의 소스 코드를 분석하여 취약점을 탐지하고, LLM을 통해 검증 후 패치를 생성하여 SARIF 형식으로 출력합니다.

## 특징
- ✅ 간단한 CLI 인터페이스 (input_dir → output_dir)
- ✅ 다중 언어 지원 (C/C++, Java 자동 감지)
- ✅ **실제 SAST 도구 통합** (Joern for C/C++)
- ✅ LLM 기반 취약점 검증 및 패치 생성
- ✅ SARIF 2.1.0 형식 출력 (fixes 포함)
- ✅ **환경 변수 및 .env 파일 지원**

## 설치

```bash
cd new-crs-sarif
uv sync
```

## 설정

### 방법 1: 환경 변수
```bash
export SARIF_CLI_ENABLE_LLM=true
export SARIF_CLI_LLM_URL=http://localhost:8000
export SARIF_CLI_ENABLE_JOERN=true
```

### 방법 2: .env 파일
```bash
cp .env.example .env
# .env 파일 편집
```

`.env` 파일 예시:
```bash
SARIF_CLI_ENABLE_LLM=true
SARIF_CLI_LLM_URL=http://localhost:8000
SARIF_CLI_LLM_API_KEY=your-key
SARIF_CLI_ENABLE_JOERN=true
```

### 설정 옵션
| 환경 변수 | 기본값 | 설명 |
|----------|--------|------|
| `SARIF_CLI_ENABLE_LLM` | `false` | LLM 검증 활성화 |
| `SARIF_CLI_LLM_URL` | `None` | LLM 서비스 URL |
| `SARIF_CLI_LLM_API_KEY` | `None` | LLM API 키 |
| `SARIF_CLI_ENABLE_JOERN` | `true` | Joern 분석 활성화 |
| `SARIF_CLI_VERBOSE` | `false` | 상세 로그 |

## 사용법

### 기본 사용 (SAST만)
```bash
sarif-cli -i ./my-project -o ./results
```

### LLM 검증 포함
```bash
# 방법 1: CLI 옵션
sarif-cli -i ./my-project -o ./results --enable-llm --llm-url http://localhost:8000

# 방법 2: 환경 변수
export SARIF_CLI_ENABLE_LLM=true
export SARIF_CLI_LLM_URL=http://localhost:8000
sarif-cli -i ./my-project -o ./results
```

### .env 파일 사용
```bash
# .env 파일에 설정 후
sarif-cli -i ./my-project -o ./results
```

## 출력 형식
`output_dir`에 파일별 SARIF 리포트가 생성됩니다:
```
output_dir/
├── file1.c.sarif
├── Main.java.sarif
└── utils.cpp.sarif
```

각 SARIF 파일은 취약점 정보와 수정 패치(LLM 활성화 시)를 포함합니다.

## SAST 도구

### Joern (C/C++)
- 실제 Joern 서버 사용
- CPG (Code Property Graph) 기반 분석
- Buffer Overflow, Use-After-Free, NULL Pointer Dereference 등 탐지

### Fallback 모드
Joern이 설치되지 않았거나 실패 시 자동으로 fallback 모드로 전환됩니다.
