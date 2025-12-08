#!/bin/bash

# ==============================================================================
# Setup ML Model Script
# ==============================================================================
# This script helps download the CatBoost model file using Git LFS
# and ensures it's properly set up for the API to use.
#
# Usage: ./setup_model.sh
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODEL_FILE="api/model/catboost_model.cbm"
MIN_MODEL_SIZE=1000000  # 1MB - models should be at least this size
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ML Model Setup Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Change to repo root
cd "$REPO_ROOT"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if file is a Git LFS pointer
is_lfs_pointer() {
    local file="$1"
    if [ ! -f "$file" ]; then
        return 1
    fi
    # Check if file is small and contains LFS pointer text
    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
    if [ "$size" -lt 1000 ]; then
        if grep -q "version https://git-lfs.github.com/spec/v1" "$file" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Step 1: Check if model already exists and is valid
MODEL_PATH="$REPO_ROOT/$MODEL_FILE"
if [ -f "$MODEL_PATH" ]; then
    FILE_SIZE=$(stat -f%z "$MODEL_PATH" 2>/dev/null || stat -c%s "$MODEL_PATH" 2>/dev/null || echo "0")
    if [ "$FILE_SIZE" -ge "$MIN_MODEL_SIZE" ] && ! is_lfs_pointer "$MODEL_PATH"; then
        FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1024 / 1024" | bc 2>/dev/null || echo "0")
        echo -e "${GREEN}✅ Model file already exists and is valid (${FILE_SIZE_MB} MB)${NC}"
        echo -e "${GREEN}✅ No setup needed - model is ready to use!${NC}"
        echo ""
        exit 0
    fi
fi

# Step 1: Check if Git LFS is installed
echo -e "${YELLOW}[1/5] Checking Git LFS installation...${NC}"
if ! command_exists git-lfs; then
    echo -e "${RED}❌ Git LFS is not installed.${NC}"
    echo ""
    echo "Please install Git LFS:"
    echo ""
    echo "  macOS:"
    echo "    brew install git-lfs"
    echo ""
    echo "  Linux (Ubuntu/Debian):"
    echo "    sudo apt-get update && sudo apt-get install git-lfs"
    echo ""
    echo "  Or download from: https://git-lfs.github.com/"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ Git LFS is installed${NC}"
echo ""

# Step 2: Initialize Git LFS
echo -e "${YELLOW}[2/5] Initializing Git LFS...${NC}"
if ! git lfs version >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Git LFS not initialized in this repository${NC}"
    git lfs install
    echo -e "${GREEN}✅ Git LFS initialized${NC}"
else
    echo -e "${GREEN}✅ Git LFS already initialized${NC}"
fi
echo ""

# Step 3: Check if we're in a git repository
echo -e "${YELLOW}[3/5] Checking Git repository...${NC}"
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Not in a Git repository${NC}"
    echo "Please run this script from the root of your Git repository."
    exit 1
fi
echo -e "${GREEN}✅ In Git repository${NC}"
echo ""

# Step 4: Pull LFS files
echo -e "${YELLOW}[4/5] Pulling Git LFS files (this may take a moment)...${NC}"
if git lfs pull >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Git LFS pull completed${NC}"
else
    echo -e "${YELLOW}⚠️  Git LFS pull had issues, but continuing...${NC}"
fi
echo ""

# Step 5: Verify model file
echo -e "${YELLOW}[5/5] Verifying model file...${NC}"

if [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}❌ Model file not found at: $MODEL_PATH${NC}"
    echo ""
    echo "Please ensure:"
    echo "  1. You're in the correct repository"
    echo "  2. The model file exists in the repository"
    echo "  3. Git LFS is properly configured"
    echo ""
    exit 1
fi

# Check file size
FILE_SIZE=$(stat -f%z "$MODEL_PATH" 2>/dev/null || stat -c%s "$MODEL_PATH" 2>/dev/null || echo "0")
FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1024 / 1024" | bc 2>/dev/null || echo "0")

# Check if it's a pointer file
if is_lfs_pointer "$MODEL_PATH"; then
    echo -e "${RED}❌ Model file is still a Git LFS pointer (not the actual file)${NC}"
    echo ""
    echo "The file size is only ${FILE_SIZE} bytes, which indicates it's a pointer."
    echo ""
    echo "Try the following:"
    echo "  1. Ensure you have Git LFS installed: git lfs version"
    echo "  2. Re-pull LFS files: git lfs pull"
    echo "  3. Check LFS status: git lfs ls-files"
    echo "  4. If needed, fetch from remote: git fetch && git lfs pull"
    echo ""
    exit 1
fi

if [ "$FILE_SIZE" -lt "$MIN_MODEL_SIZE" ]; then
    echo -e "${YELLOW}⚠️  Warning: Model file seems small (${FILE_SIZE_MB} MB)${NC}"
    echo "Expected at least 1 MB. The model might be corrupted."
    echo ""
else
    echo -e "${GREEN}✅ Model file found and verified${NC}"
    echo "   Location: $MODEL_PATH"
    echo "   Size: ${FILE_SIZE_MB} MB"
    echo ""
fi

# Final summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Setup Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "The model file is ready to use."
echo ""
echo "To test the API:"
echo "  1. Start Docker: docker-compose up -d"
echo "  2. Check API health: curl http://localhost:8008/health"
echo "  3. Test prediction: curl 'http://localhost:8008/predict-price?product_name=Cappuccino&location=Kentron&venue_type=restaurant&portion_size=medium&age_group=25-34'"
echo ""

