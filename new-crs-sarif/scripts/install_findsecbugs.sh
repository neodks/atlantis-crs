#!/bin/bash
set -e

PLUGIN_VERSION="1.13.0"
INSTALL_DIR="$HOME/bin/spotbugs/plugin"
JAR_FILE="findsecbugs-plugin-${PLUGIN_VERSION}.jar"
DOWNLOAD_URL="https://github.com/find-sec-bugs/find-sec-bugs/releases/download/version-${PLUGIN_VERSION}/${JAR_FILE}"

echo "Installing FindSecBugs plugin ${PLUGIN_VERSION}..."

# Create plugin directory
mkdir -p "$INSTALL_DIR"

# Download
if [ ! -f "$INSTALL_DIR/$JAR_FILE" ]; then
    echo "Downloading FindSecBugs from $DOWNLOAD_URL..."
    curl -L -o "$INSTALL_DIR/$JAR_FILE" "$DOWNLOAD_URL"
else
    echo "FindSecBugs plugin already exists."
fi

echo "FindSecBugs plugin installed at $INSTALL_DIR/$JAR_FILE"
