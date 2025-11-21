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

### SpotBugs (Java)
- SpotBugs를 사용하여 Java 코드의 버그를 탐지합니다.
- 아래 스크립트를 실행하여 SpotBugs를 설치해야 합니다:
  ```bash
  ./install_spotbugs.sh
  ```
- 분석 시 자동으로 프로젝트 내의 Java 소스 코드를 컴파일합니다. (`javac` 필요)

### Fallback 모드
Joern이 설치되지 않았거나 실패 시 자동으로 fallback 모드로 전환됩니다.

## Aux 분석기 (선택 사항)

Aux 분석기는 더 정밀한 도달 가능성(Reachability) 분석을 제공하여 LLM 검증의 정확도를 높입니다.

### 기능
- **Reachability Analysis**: 취약점이 외부 입력으로부터 실제로 도달 가능한지 분석
- **Dynamic Prompts**: 분석 결과에 따라 LLM 프롬프트를 동적으로 선택 (`basic` vs `aux_enhanced`)

### 활성화 방법
CLI 옵션 `--enable-aux`를 사용하거나 환경 변수 `ENABLE_AUX_ANALYSIS=true`를 설정하세요.

```bash
sarif-cli -i ./project -o ./out --enable-llm --enable-aux
```
