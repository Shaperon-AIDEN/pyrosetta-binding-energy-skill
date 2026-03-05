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

## Quick Start

```bash
python compute_binding_dg.py \
  --clone-id hmsame3_0234 \
  --species human \
  --clone-dir /path/to/structures \
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
