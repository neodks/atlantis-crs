#!/bin/bash
# Aux 분석 도구 설치 및 설정 스크립트

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STATIC_DIR="$PROJECT_ROOT/sarif_cli/static"

echo "🔧 Aux 분석 도구 설정을 시작합니다..."

# 1. 디렉토리 생성
echo "📂 static 디렉토리 생성: $STATIC_DIR"
mkdir -p "$STATIC_DIR"

# 2. SootUp (Java) 설정
echo "☕️ Java 분석 도구 (SootUp) 설정 확인..."
SOOTUP_JAR="$STATIC_DIR/sootup-reachability.jar"

if [ -f "$SOOTUP_JAR" ]; then
    echo "✅ SootUp JAR가 이미 존재합니다: $SOOTUP_JAR"
else
    echo "⚠️ SootUp JAR가 없습니다."
    echo "   crs-sarif 프로젝트에서 빌드하여 복사하거나 다운로드해야 합니다."
    # TODO: 실제 다운로드 URL이 있다면 추가
    # curl -L "https://example.com/sootup-reachability.jar" -o "$SOOTUP_JAR"
    
    # 임시로 더미 파일 생성 (테스트용)
    # echo "Creating dummy jar for testing..."
    # touch "$SOOTUP_JAR"
fi

# 3. SVF (C/C++) 설정
echo "🔍 C/C++ 분석 도구 (SVF) 설정 확인..."
# SVF는 보통 시스템에 설치되거나 바이너리로 제공됨
if command -v wpa &> /dev/null; then
    echo "✅ SVF (wpa)가 PATH에 있습니다."
else
    echo "⚠️ SVF (wpa)를 찾을 수 없습니다."
    echo "   SVF를 설치하고 PATH에 추가해주세요."
    echo "   참고: https://github.com/SVF-tools/SVF"
    
    # Ubuntu 예시
    # echo "   Ubuntu: sudo apt-get install svf-lib"
fi

echo ""
echo "🎉 설정 스크립트 완료!"
echo "Aux 분석을 사용하려면 다음을 실행하세요:"
echo "  export ENABLE_AUX_ANALYSIS=true"
echo "  sarif-cli ..."
