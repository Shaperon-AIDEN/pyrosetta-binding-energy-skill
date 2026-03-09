# PyRosetta Binding Energy Skill

PyRosetta skill for binding energy calculation with mandatory workflow:

1. Relax (`FastRelax`)
2. Interface binding energy (`dG_interface`)

The skill supports:
- Auto-selection of largest-cluster representative structure per clone/species
- Direct input structure scoring (`--input-cif`)

## Repository Contents

- `SKILL.md`: skill definition for agent loading
- `compute_binding_dg.py`: main calculator
- `requirements.txt`: Python dependencies
- `scripts/install_dependencies.sh`: runtime dependency installer
- `scripts/install_skill_agent.sh`: one-step agent skill installer

## Dependencies

Required Python packages:
- `numpy`
- `biopython`
- `pyrosettacolabsetup`
- `pyrosetta` (installed via wheel URL in `install_dependencies.sh`)

Create and activate a conda environment first:

```bash
conda create -n pyrosetta-skill python=3.10 -y
conda activate pyrosetta-skill
```

Install all dependencies inside the activated conda environment:

```bash
chmod +x scripts/install_dependencies.sh
./scripts/install_dependencies.sh
```

If auto PyRosetta install is unavailable for your platform/Python, set `PYROSETTA_WHEEL_URL` and re-run:

```bash
PYROSETTA_WHEEL_URL="https://.../pyrosetta-....whl" PYTHON_BIN=python ./scripts/install_dependencies.sh
```

Default PyRosetta install now follows the official quarterly pip flow:

```bash
python -m pip install pyrosetta --find-links https://west.rosettacommons.org/pyrosetta/quarterly/release
```

The script retries with the East mirror automatically if the West mirror fails.

## Installation - Agent (recommended)

This installs the skill into `~/.claude/skills/pyrosetta-binding-energy`.

Use the same conda environment for installation and runtime:

```bash
conda activate pyrosetta-skill
chmod +x scripts/install_skill_agent.sh
./scripts/install_skill_agent.sh
```

`install_skill_agent.sh` now installs both skill files and runtime dependencies (including PyRosetta when auto-install is supported).

After installation, the agent can load/use `pyrosetta-binding-energy` skill.

## Installation - Manual

1. Create skill folder:

```bash
mkdir -p ~/.claude/skills/pyrosetta-binding-energy
```

2. Copy files:

```bash
cp SKILL.md ~/.claude/skills/pyrosetta-binding-energy/SKILL.md
cp compute_binding_dg.py ~/.claude/skills/pyrosetta-binding-energy/compute_binding_dg.py
cp requirements.txt ~/.claude/skills/pyrosetta-binding-energy/requirements.txt
chmod +x ~/.claude/skills/pyrosetta-binding-energy/compute_binding_dg.py
```

3. Install dependencies:

```bash
conda activate pyrosetta-skill
./scripts/install_dependencies.sh
```

If auto PyRosetta install is unavailable, provide a wheel URL explicitly:

```bash
PYROSETTA_WHEEL_URL="https://.../pyrosetta-....whl" PYTHON_BIN=python ./scripts/install_dependencies.sh
```

Optional mirror overrides:

```bash
PYROSETTA_FIND_LINKS_WEST="https://west.rosettacommons.org/pyrosetta/quarterly/release" \
PYROSETTA_FIND_LINKS_EAST="https://graylab.jhu.edu/download/PyRosetta4/archive/release-quarterly/release" \
PYTHON_BIN=python ./scripts/install_dependencies.sh
```

4. Run all commands with the same conda environment activated.

## Usage

### 1) Auto representative selection mode

```bash
conda activate pyrosetta-skill
python compute_binding_dg.py \
  --clone-id hmsame3_0234 \
  --species human \
  --clone-dir /path/to/structure_prediction_designedNMb_aligned \
  --chain-a A \
  --chain-b B \
  --cluster-cutoff 0.2 \
  --cpu-threads 8 \
  --relax-cycles 5 \
  --scorefxn ref2015 \
  --output-json /path/to/output/hmsame3_0234_human.json
```

### 2) Direct input structure mode

```bash
conda activate pyrosetta-skill
python compute_binding_dg.py \
  --input-cif /path/to/model.cif \
  --chain-a A \
  --chain-b B \
  --cpu-threads 8 \
  --relax-cycles 5 \
  --scorefxn ref2015 \
  --output-json /path/to/output/model_energy.json
```

### 3) Selection-only mode (no PyRosetta run)

```bash
conda activate pyrosetta-skill
python compute_binding_dg.py \
  --clone-id hmsame3_0234 \
  --species mouse \
  --clone-dir /path/to/structure_prediction_designedNMb_aligned \
  --select-only \
  --output-json /path/to/output/mouse_selected.json
```

## Output Schema

Output JSON includes:
- `input_cif`
- `selection` (largest-cluster metadata)
- `energies`:
  - `relaxed_total_score`
  - `dG_interface`
  - `dG_crossterm`
  - `packstat`
  - `complexed_sasa`

## Notes

- Default interface is `A_B`; change `--chain-a/--chain-b` when chain IDs differ.
- Use `--cpu-threads N` to limit CPU thread usage (sets `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`).
- For long batch runs, consider running under `tmux`/`screen`.
- Keep runtime environment consistent when comparing clone rankings.
- Always run with the same conda environment used during dependency installation.
