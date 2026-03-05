#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/3] Installing Python dependencies from requirements.txt"
"${PYTHON_BIN}" -m pip install -r "${ROOT_DIR}/requirements.txt"

echo "[2/3] Checking PyRosetta availability"
if "${PYTHON_BIN}" -c "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec('pyrosetta') else 1)"; then
  echo "PyRosetta already available."
  exit 0
fi

PY_VER="$(${PYTHON_BIN} -c 'import sys; print(f"cp{sys.version_info.major}{sys.version_info.minor}")')"
WHEEL_URL=""

if [[ "${PY_VER}" == "cp312" ]]; then
  WHEEL_URL="https://west.rosettacommons.org/pyrosetta/quarterly/release/pyrosetta-0-cp312-cp312-linux_x86_64.whl"
elif [[ "${PY_VER}" == "cp311" ]]; then
  WHEEL_URL="https://west.rosettacommons.org/pyrosetta/quarterly/release/pyrosetta-0-cp311-cp311-linux_x86_64.whl"
fi

if [[ -z "${WHEEL_URL}" ]]; then
  echo "Unsupported Python version for auto PyRosetta wheel install: ${PY_VER}"
  echo "Install a compatible PyRosetta wheel manually, then re-run this script."
  exit 1
fi

echo "[3/3] Installing PyRosetta wheel for ${PY_VER}"
"${PYTHON_BIN}" -m pip install "${WHEEL_URL}"

echo "Dependency installation completed."
