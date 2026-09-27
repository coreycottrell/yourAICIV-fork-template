#!/bin/bash
# template_substitute.sh - Broad template variable substitution for forked AiCIVs
# Called by birth_orchestrator.sh Phase 2 after identity files are written.
# Replaces template variables across all .md, .py, .sh, .json files.
#
# Usage: template_substitute.sh <birth_dir> <civ_name> <human_name> [human_email]

set -euo pipefail

BIRTH_DIR="$1"
CIV_NAME="$2"
HUMAN_NAME="$3"
HUMAN_EMAIL="${4:-}"

if [ -z "$BIRTH_DIR" ] || [ -z "$CIV_NAME" ] || [ -z "$HUMAN_NAME" ]; then
    echo "Usage: template_substitute.sh <birth_dir> <civ_name> <human_name> [human_email]"
    exit 1
fi

CIV_NAME_LOWER=$(echo "$CIV_NAME" | tr "[:upper:]" "[:lower:]")
CIV_HANDLE="$CIV_NAME_LOWER"
CIV_EMAIL="${CIV_NAME_LOWER}@aiciv.ai"
HUMAN_NAME_LOWER=$(echo "$HUMAN_NAME" | tr "[:upper:]" "[:lower:]")
PARENT_CIV="Witness"
CIV_ROOT="/home/aiciv"

echo "[template_substitute] CIV_NAME=$CIV_NAME, HUMAN_NAME=$HUMAN_NAME"

cd "$BIRTH_DIR" || exit 1

# Build sed script - printf keeps left side literal, substitutes right side
SEDSCRIPT=$(mktemp /tmp/sed_subst.XXXXXX)
{
    printf 's|${CIV_NAME}|%s|g\n' "$CIV_NAME"
    printf 's|${CIV_NAME_LOWER}|%s|g\n' "$CIV_NAME_LOWER"
    printf 's|${CIV_ROOT}|%s|g\n' "$CIV_ROOT"
    printf 's|${CIV_HANDLE}|%s|g\n' "$CIV_HANDLE"
    printf 's|${CIV_EMAIL}|%s|g\n' "$CIV_EMAIL"
    printf 's|${HUMAN_NAME}|%s|g\n' "$HUMAN_NAME"
    printf 's|${HUMAN_NAME_LOWER}|%s|g\n' "$HUMAN_NAME_LOWER"
    printf 's|${HUMAN_EMAIL}|%s|g\n' "$HUMAN_EMAIL"
    printf 's|${PARENT_CIV}|%s|g\n' "$PARENT_CIV"
} > "$SEDSCRIPT"

echo "[template_substitute] Sed script:"
cat "$SEDSCRIPT"

# Apply substitutions to all eligible files
find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.sh" -o -name "*.json" \) \
    ! -path "./.git/*" ! -path "*/acgee-wisdom/*" ! -path "*/lineage/*" \
    -print0 | xargs -0 sed -i -f "$SEDSCRIPT" 2>/dev/null || true

rm -f "$SEDSCRIPT"
echo "[template_substitute] Complete."
