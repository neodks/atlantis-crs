#!/bin/bash
# test_all_languages.sh - 모든 언어에 대한 SAST 도구 통합 테스트

set -ex

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_PROJECT="$PROJECT_ROOT/test-project"
RESULTS_DIR="$PROJECT_ROOT/test-results"

echo "========================================="
echo "SAST CLI 통합 테스트"
echo "========================================="
echo ""

# 결과 디렉토리 정리
rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

# 테스트 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
FAILED_TEST_NAMES=""

# 테스트 함수
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_files="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "----------------------------------------"
    echo "테스트 #$TOTAL_TESTS: $test_name"
    echo "명령어: $command"
    echo ""
    
    # 명령어 실행
    if eval "$command"; then
        echo "✓ 명령어 실행 성공"
        
        # 디버깅을 위해 결과 디렉토리 내용 출력
        echo "결과 디렉토리 내용:"
        ls -l "$(dirname "${expected_files%% *}")"
        sleep 1
        
        # 결과 파일 확인
        local all_files_exist=true
        for file in $expected_files; do
            if [ -f "$file" ]; then
                echo "  ✓ 파일 생성 확인: $file"
            else
                echo "  ✗ 파일 없음: $file"
                all_files_exist=false
            fi
        done
        
        if [ "$all_files_exist" = true ]; then
            echo "✓ 테스트 통과"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo "✗ 테스트 실패 (파일 누락)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            FAILED_TEST_NAMES="${FAILED_TEST_NAMES}  - ${test_name}\n"
        fi
    else
        echo "✗ 명령어 실행 실패"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_TEST_NAMES="${FAILED_TEST_NAMES}  - ${test_name}\n"
    fi
    
    echo ""
}

# 테스트 실행 전 new-crs-sarif 디렉토리로 이동
cd "$PROJECT_ROOT"

# 테스트 1: 기본 SAST 분석 (LLM 없이)
run_test \
    "기본 SAST 분석 (모든 언어)" \
    "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT -o $RESULTS_DIR/test1-basic" \
    "$RESULTS_DIR/test1-basic/vulnerable.c.sarif $RESULTS_DIR/test1-basic/vulnerable.cpp.sarif $RESULTS_DIR/test1-basic/Vulnerable.java.sarif"

# 테스트 2: LLM 검증 포함 (Ollama 필요)
if command -v ollama &> /dev/null && curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "Ollama 감지됨. LLM 테스트 실행..."
    
    run_test \
        "LLM 검증 포함" \
        "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT -o $RESULTS_DIR/test2-llm --enable-llm --llm-url http://localhost:11434" \
        "$RESULTS_DIR/test2-llm/vulnerable.c.sarif $RESULTS_DIR/test2-llm/Vulnerable.java.sarif"
else
    echo "⚠️  Ollama가 실행 중이지 않아 LLM 테스트를 건너뜁니다."
    echo "   LLM 테스트를 실행하려면 Ollama를 시작하세요: ollama serve"
    echo ""
fi

# 테스트 3: Aux 분석 포함
run_test \
    "Aux 분석 포함" \
    "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT -o $RESULTS_DIR/test3-aux --enable-aux" \
    "$RESULTS_DIR/test3-aux/vulnerable.c.sarif"

# 테스트 4: LLM + Aux 통합
if command -v ollama &> /dev/null && curl -s http://localhost:11434/api/tags &> /dev/null; then
    run_test \
        "LLM + Aux 통합" \
        "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT -o $RESULTS_DIR/test4-full --enable-llm --enable-aux --llm-url http://localhost:11434" \
        "$RESULTS_DIR/test4-full/vulnerable.c.sarif"
fi

# 언어별 개별 테스트
echo "========================================="
echo "언어별 개별 테스트"
echo "========================================="
echo ""

# C 테스트
run_test \
    "C 언어 분석" \
    "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT/c -o $RESULTS_DIR/test-c" \
    "$RESULTS_DIR/test-c/vulnerable.c.sarif"

# C++ 테스트
run_test \
    "C++ 언어 분석" \
    "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT/cpp -o $RESULTS_DIR/test-cpp" \
    "$RESULTS_DIR/test-cpp/vulnerable.cpp.sarif"

# Java 테스트
run_test \
    "Java 언어 분석" \
    "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT/java -o $RESULTS_DIR/test-java" \
    "$RESULTS_DIR/test-java/Vulnerable.java.sarif"

# Python 테스트
run_test \
    "Python 언어 분석" \
    "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT/python -o $RESULTS_DIR/test-python" \
    "$RESULTS_DIR/test-python/vulnerable.py.sarif"

# JavaScript 테스트
run_test \
    "JavaScript 언어 분석" \
    "uv run python3 -m sarif_cli.cli -i $TEST_PROJECT/js -o $RESULTS_DIR/test-js" \
    "$RESULTS_DIR/test-js/vulnerable.js.sarif"

# 최종 결과
echo "========================================="
echo "테스트 결과 요약"
echo "========================================="
echo "총 테스트: $TOTAL_TESTS"
echo "통과: $PASSED_TESTS"
echo "실패: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "✓ 모든 테스트 통과!"
    exit 0
else
    echo "✗ 일부 테스트 실패"
    if [ -n "$FAILED_TEST_NAMES" ]; then
        echo ""
        echo "실패한 테스트:"
        echo -e "$FAILED_TEST_NAMES"
    fi
    exit 1
fi
