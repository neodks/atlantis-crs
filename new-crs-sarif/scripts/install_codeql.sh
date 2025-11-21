#!/bin/bash
# install_codeql.sh - CodeQL CLI 및 표준 쿼리 라이브러리 설치

set -e

CODEQL_VERSION="v2.19.4"
INSTALL_DIR="$HOME/codeql-cli"
QUERIES_DIR="$HOME/codeql-home"
DOWNLOAD_URL="https://github.com/github/codeql-cli-binaries/releases/download/${CODEQL_VERSION}/codeql-linux64.zip"

# OS 감지 (macOS의 경우 URL 변경)
if [[ "$(uname)" == "Darwin" ]]; then
    DOWNLOAD_URL="https://github.com/github/codeql-cli-binaries/releases/download/${CODEQL_VERSION}/codeql-osx64.zip"
fi

echo "=== CodeQL 설치 스크립트 ==="
echo "CodeQL 버전: ${CODEQL_VERSION}"
echo "설치 디렉토리: ${INSTALL_DIR}"
echo "쿼리 디렉토리: ${QUERIES_DIR}"
echo ""

# 1. CodeQL CLI 설치
if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/codeql/codeql" ]; then
    CURRENT_VERSION=$("$INSTALL_DIR/codeql/codeql" version 2>/dev/null | head -1 | awk '{print $NF}' || echo "unknown")
    echo "✓ CodeQL CLI가 이미 설치되어 있습니다: $INSTALL_DIR (버전: $CURRENT_VERSION)"
    
    # 버전이 다르면 업그레이드 제안
    if [[ "$CURRENT_VERSION" != "$CODEQL_VERSION" && "$CURRENT_VERSION" != "unknown" ]]; then
        echo "  현재 버전: $CURRENT_VERSION, 스크립트 버전: $CODEQL_VERSION"
        echo "  업그레이드하려면 $INSTALL_DIR를 삭제하고 다시 실행하세요."
    fi
else
    echo "CodeQL CLI ${CODEQL_VERSION} 다운로드 중..."
    TEMP_DIR=$(mktemp -d)
    
    # wget 또는 curl 사용
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "${TEMP_DIR}/codeql.zip" "$DOWNLOAD_URL"
    elif command -v curl &> /dev/null; then
        curl -L -o "${TEMP_DIR}/codeql.zip" "$DOWNLOAD_URL"
    else
        echo "오류: wget 또는 curl이 필요합니다."
        exit 1
    fi

    echo "CodeQL 압축 해제 중..."
    mkdir -p "$INSTALL_DIR"
    unzip -q "${TEMP_DIR}/codeql.zip" -d "$INSTALL_DIR"
    
    echo "✓ CodeQL CLI 설치 완료"
    
    # 임시 파일 삭제
    rm -rf "$TEMP_DIR"
fi

# 2. CodeQL 표준 쿼리 라이브러리 다운로드 (선택사항)
echo ""
echo "CodeQL 표준 쿼리 라이브러리 확인 중..."

mkdir -p "$QUERIES_DIR"

# codeql repo는 용량이 크므로 선택적으로만 clone
if [ -d "$QUERIES_DIR/codeql" ]; then
    echo "✓ CodeQL 쿼리가 이미 존재합니다: $QUERIES_DIR/codeql"
else
    echo "  (선택사항) Git repo를 clone하려면 다음 명령을 실행하세요:"
    echo "  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/github/codeql.git $QUERIES_DIR/codeql"
fi

# 3. CodeQL 쿼리 팩 다운로드 (필수)
echo ""
echo "CodeQL 쿼리 팩 다운로드 중..."

CODEQL_BIN="$INSTALL_DIR/codeql/codeql"

if [ -f "$CODEQL_BIN" ]; then
    echo "필수 쿼리 팩 다운로드 중..."
    
    # C/C++ 쿼리 팩
    echo "  - codeql/cpp-queries"
    "$CODEQL_BIN" pack download codeql/cpp-queries 2>/dev/null || echo "    (이미 설치됨 또는 다운로드 건너뜀)"
    
    # Java 쿼리 팩
    echo "  - codeql/java-queries"
    "$CODEQL_BIN" pack download codeql/java-queries 2>/dev/null || echo "    (이미 설치됨 또는 다운로드 건너뜀)"
    
    # 의존성 팩
    echo "  - codeql/suite-helpers"
    "$CODEQL_BIN" pack download codeql/suite-helpers 2>/dev/null || echo "    (이미 설치됨 또는 다운로드 건너뜀)"
    
    echo "  - codeql/util"
    "$CODEQL_BIN" pack download codeql/util 2>/dev/null || echo "    (이미 설치됨 또는 다운로드 건너뜀)"
    
    echo "✓ 쿼리 팩 다운로드 완료"
else
    echo "⚠ CodeQL 실행 파일을 찾을 수 없습니다. 쿼리 팩 다운로드를 건너뜁니다."
fi

# 4. 완료 메시지
echo ""
echo "========================================="
echo "CodeQL 설치가 완료되었습니다!"
echo "========================================="
echo ""
echo "다음 명령어를 실행하여 PATH에 추가하세요:"
echo ""
echo "  export PATH=\"\$PATH:$INSTALL_DIR/codeql\""
echo ""
echo "영구적으로 설정하려면 셸 프로파일에 추가하세요:"
echo "  echo 'export PATH=\"\$PATH:$INSTALL_DIR/codeql\"' >> ~/.zshrc  # zsh 사용 시"
echo "  echo 'export PATH=\"\$PATH:$INSTALL_DIR/codeql\"' >> ~/.bashrc  # bash 사용 시"
echo ""
echo "설치된 내용:"
echo "  - CodeQL CLI: $INSTALL_DIR/codeql"
echo "  - 쿼리 팩: ~/.codeql/packages/"
if [ -d "$QUERIES_DIR/codeql" ]; then
    echo "  - 쿼리 소스: $QUERIES_DIR/codeql"
fi
echo ""
