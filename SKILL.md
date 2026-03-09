---
name: pyrosetta-binding-energy
description: >
  Calculate protein complex binding energy (dG) using PyRosetta with mandatory
  Relax -> Interface dG workflow. Supports auto-selecting largest-cluster
  representative structures per clone/species.
---

# PyRosetta Binding Energy Skill

This skill computes binding energy for protein complexes in two steps:

1. Run `FastRelax`
2. Run interface energy analysis to get `dG_interface`

## Environment Setup (conda)

Use a dedicated conda environment for install and execution:

```bash
conda create -n pyrosetta-skill python=3.10 -y
conda activate pyrosetta-skill
chmod +x scripts/install_skill_agent.sh
./scripts/install_skill_agent.sh
```

`install_skill_agent.sh` installs skill files and then runs dependency installation (including PyRosetta auto-install when supported).

PyRosetta install uses official quarterly pip mirrors (`pip install pyrosetta --find-links ...`) with West mirror first, then East mirror fallback.

If your platform is not supported for auto PyRosetta install, run with an explicit wheel URL:

```bash
PYROSETTA_WHEEL_URL="https://.../pyrosetta-....whl" PYTHON_BIN=python ./scripts/install_dependencies.sh
```

Optional mirror overrides:

```bash
PYROSETTA_FIND_LINKS_WEST="https://west.rosettacommons.org/pyrosetta/quarterly/release" \
PYROSETTA_FIND_LINKS_EAST="https://graylab.jhu.edu/download/PyRosetta4/archive/release-quarterly/release" \
PYTHON_BIN=python ./scripts/install_dependencies.sh
```

If you only want dependency setup without skill file copy:

```bash
chmod +x scripts/install_dependencies.sh
./scripts/install_dependencies.sh
```

## Quick Start

```bash
conda activate pyrosetta-skill
python compute_binding_dg.py \
  --clone-id hmsame3_0234 \
  --species human \
  --clone-dir /path/to/structures \
  --cpu-threads 8 \
  --output-json /path/to/out/hmsame3_0234_human.json
```

## Input Modes

1. **Auto representative selection**
   - `--clone-id`, `--species`, `--clone-dir`
   - Selects the largest-cluster medoid from species-specific models.

2. **Direct structure mode**
   - `--input-cif /path/to/model.cif`

## Output

JSON includes:
- Selected input CIF
- Selection metadata (cluster size/fraction, representative index)
- `relaxed_total_score`
- `dG_interface`
- Additional interface metrics (`packstat`, `complexed_sasa`)
