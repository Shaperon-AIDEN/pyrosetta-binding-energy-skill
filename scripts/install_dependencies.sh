#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
PYROSETTA_WHEEL_URL="${PYROSETTA_WHEEL_URL:-}"
PYROSETTA_FIND_LINKS_WEST="${PYROSETTA_FIND_LINKS_WEST:-https://west.rosettacommons.org/pyrosetta/quarterly/release}"
PYROSETTA_FIND_LINKS_EAST="${PYROSETTA_FIND_LINKS_EAST:-https://graylab.jhu.edu/download/PyRosetta4/archive/release-quarterly/release}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/4] Installing Python dependencies from requirements.txt"
"${PYTHON_BIN}" -m pip install -r "${ROOT_DIR}/requirements.txt"

echo "[2/4] Checking PyRosetta availability"
if "${PYTHON_BIN}" -c "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec('pyrosetta') else 1)"; then
  echo "PyRosetta already available."
  exit 0
fi

if [[ -n "${PYROSETTA_WHEEL_URL}" ]]; then
  echo "[3/4] Installing PyRosetta from PYROSETTA_WHEEL_URL"
  "${PYTHON_BIN}" -m pip install "${PYROSETTA_WHEEL_URL}"
else
  PY_VER="$(${PYTHON_BIN} -c 'import sys; print(f"cp{sys.version_info.major}{sys.version_info.minor}")')"
  PLATFORM_TAG="$(${PYTHON_BIN} -c 'import platform; print(f"{platform.system().lower()}_{platform.machine().lower()}")')"

  echo "[3/4] Installing PyRosetta package via pip --find-links (official quarterly mirrors)"
  echo "Detected runtime: platform=${PLATFORM_TAG}, python=${PY_VER}"

  if ! "${PYTHON_BIN}" -m pip install pyrosetta --find-links "${PYROSETTA_FIND_LINKS_WEST}"; then
    echo "West mirror failed, retrying with East mirror..."
    "${PYTHON_BIN}" -m pip install pyrosetta --find-links "${PYROSETTA_FIND_LINKS_EAST}"
  fi
fi

echo "[4/4] Verifying PyRosetta import"
"${PYTHON_BIN}" -c "import pyrosetta; print(f'PyRosetta import OK: {pyrosetta.__file__}')"

echo "Dependency installation completed."
