#!/bin/bash
# install_spotbugs.sh

# SpotBugs 버전 설정
SPOTBUGS_VERSION="4.8.6"
INSTALL_DIR="$HOME/spotbugs-${SPOTBUGS_VERSION}"
DOWNLOAD_URL="https://github.com/spotbugs/spotbugs/releases/download/${SPOTBUGS_VERSION}/spotbugs-${SPOTBUGS_VERSION}.tgz"

# 설치 디렉토리가 이미 있는지 확인
if [ -d "$INSTALL_DIR" ]; then
    echo "SpotBugs is already installed at $INSTALL_DIR"
    export PATH="$PATH:${INSTALL_DIR}/bin"
    exit 0
fi

echo "Downloading SpotBugs ${SPOTBUGS_VERSION}..."
# 임시 디렉토리에 다운로드
TEMP_DIR=$(mktemp -d)
wget -q -O "${TEMP_DIR}/spotbugs.tgz" "$DOWNLOAD_URL"

# 다운로드 성공 여부 확인
if [ $? -ne 0 ]; then
    echo "Failed to download SpotBugs. Please check the URL and your network connection."
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Installing SpotBugs to $INSTALL_DIR..."
# 설치 디렉토리 생성
mkdir -p "$HOME"
# 압축 해제
tar -xzf "${TEMP_DIR}/spotbugs.tgz" -C "$HOME"

# 실행 권한 부여
echo "Setting execute permissions..."
chmod +x "${INSTALL_DIR}/bin/spotbugs"

# PATH에 추가 (사용자가 직접 쉘 설정 파일에 추가하도록 안내)
echo "Installation complete."
echo "Please add the following line to your ~/.bashrc, ~/.zshrc, or other shell profile:"
echo "export PATH=\$PATH:${INSTALL_DIR}/bin"

# Ensure the PATH is exported for the current session
export PATH="$PATH:${INSTALL_DIR}/bin"

# 임시 파일 삭제
rm -rf "$TEMP_DIR"
