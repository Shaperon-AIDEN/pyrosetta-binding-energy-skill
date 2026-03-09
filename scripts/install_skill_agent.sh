#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="pyrosetta-binding-energy"
DEST_DIR="${HOME}/.claude/skills/${SKILL_NAME}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

echo "[1/2] Installing skill files"
mkdir -p "${DEST_DIR}"
cp "${SRC_DIR}/SKILL.md" "${DEST_DIR}/SKILL.md"
cp "${SRC_DIR}/compute_binding_dg.py" "${DEST_DIR}/compute_binding_dg.py"
cp "${SRC_DIR}/requirements.txt" "${DEST_DIR}/requirements.txt"

chmod +x "${DEST_DIR}/compute_binding_dg.py"

echo "Skill files installed to: ${DEST_DIR}"

echo "[2/2] Installing runtime dependencies (including PyRosetta when supported)"
PYTHON_BIN="${PYTHON_BIN}" "${SRC_DIR}/scripts/install_dependencies.sh"

echo "Installed agent skill to: ${DEST_DIR}"
echo "Skill installation complete."
