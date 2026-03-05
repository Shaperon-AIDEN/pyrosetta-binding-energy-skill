#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="pyrosetta-binding-energy"
DEST_DIR="${HOME}/.claude/skills/${SKILL_NAME}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "${DEST_DIR}"
cp "${SRC_DIR}/SKILL.md" "${DEST_DIR}/SKILL.md"
cp "${SRC_DIR}/compute_binding_dg.py" "${DEST_DIR}/compute_binding_dg.py"
cp "${SRC_DIR}/requirements.txt" "${DEST_DIR}/requirements.txt"

chmod +x "${DEST_DIR}/compute_binding_dg.py"

echo "Installed agent skill to: ${DEST_DIR}"
echo "Next: run scripts/install_dependencies.sh to ensure runtime dependencies."
