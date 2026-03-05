#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path

import numpy as np
from Bio.PDB.MMCIFParser import MMCIFParser
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]

CLONE_FILE_PATTERN = re.compile(
    r"^(?P<prefix>[hm])_(?P<clone>hmsame\d+_\d{4})_seed(?P<seed>\d+)_model_(?P<model>\d+)\.cif$"
)


def species_prefix(species: str) -> str:
    s = species.lower()
    if s == "human":
        return "h"
    if s == "mouse":
        return "m"
    raise ValueError(f"Unsupported species: {species}")


def load_chain_ca_map(cif_path: Path, chain_id: str) -> dict[tuple[str, int, str], FloatArray]:
    parser = MMCIFParser(QUIET=True)
    struct = parser.get_structure(cif_path.stem, str(cif_path))
    if struct is None:
        raise ValueError(f"Failed to parse structure from {cif_path}")
    model = next(struct.get_models())
    if chain_id not in model:
        raise ValueError(f"Chain '{chain_id}' not found in {cif_path}")

    chain = model[chain_id]
    ca_map: dict[tuple[str, int, str], FloatArray] = {}
    for res in chain.get_residues():
        hetflag, seq, icode = res.id
        if hetflag != " ":
            continue
        if "CA" not in res:
            continue
        key = (res.get_resname(), int(seq), str(icode).strip())
        ca_map[key] = np.asarray(res["CA"].coord, dtype=float)
    return ca_map


def kabsch_rmsd(ca_a: dict[tuple[str, int, str], FloatArray], ca_b: dict[tuple[str, int, str], FloatArray]) -> float:
    common = sorted(set(ca_a) & set(ca_b), key=lambda x: (x[1], x[0], x[2]))
    if len(common) < 3:
        return float("nan")

    a = np.stack([ca_a[k] for k in common], axis=0)
    b = np.stack([ca_b[k] for k in common], axis=0)

    a_cent = a.mean(axis=0)
    b_cent = b.mean(axis=0)
    a0 = a - a_cent
    b0 = b - b_cent

    h = b0.T @ a0
    u, _, vt = np.linalg.svd(h)
    d = np.sign(np.linalg.det(u @ vt))
    r = u @ np.diag([1.0, 1.0, d]) @ vt
    b_aligned = b0 @ r

    diff = a0 - b_aligned
    return float(np.sqrt(np.mean(np.sum(diff * diff, axis=1))))


def connected_components(dist: FloatArray, cutoff: float) -> list[list[int]]:
    n = dist.shape[0]
    seen = [False] * n
    comps: list[list[int]] = []
    for i in range(n):
        if seen[i]:
            continue
        stack = [i]
        seen[i] = True
        comp: list[int] = []
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for j in range(n):
                if seen[j]:
                    continue
                val = dist[cur, j]
                if not math.isnan(val) and val <= cutoff:
                    seen[j] = True
                    stack.append(j)
        comps.append(sorted(comp))
    comps.sort(key=len, reverse=True)
    return comps


def choose_medoid(member_indices: list[int], dist: FloatArray) -> int:
    best_idx = member_indices[0]
    best_mean = float("inf")
    for i in member_indices:
        vals = [dist[i, j] for j in member_indices if i != j and not math.isnan(dist[i, j])]
        mean_val = float(np.mean(vals)) if vals else 0.0
        if mean_val < best_mean:
            best_mean = mean_val
            best_idx = i
    return best_idx


def select_representative_from_clone(
    clone_dir: Path,
    clone_id: str,
    species: str,
    chain_for_clustering: str,
    cutoff: float,
) -> tuple[Path, Mapping[str, object]]:
    prefix = species_prefix(species)
    files: list[Path] = []
    for p in sorted(clone_dir.glob("*.cif")):
        m = CLONE_FILE_PATTERN.match(p.name)
        if not m:
            continue
        if m.group("clone") != clone_id:
            continue
        if m.group("prefix") != prefix:
            continue
        files.append(p)

    if not files:
        raise FileNotFoundError(f"No CIF files found for clone={clone_id}, species={species} in {clone_dir}")

    ca_maps = [load_chain_ca_map(p, chain_for_clustering) for p in files]
    n = len(files)
    dist = np.full((n, n), np.nan, dtype=float)
    for i in range(n):
        dist[i, i] = 0.0
        for j in range(i + 1, n):
            rmsd = kabsch_rmsd(ca_maps[i], ca_maps[j])
            dist[i, j] = rmsd
            dist[j, i] = rmsd

    comps = connected_components(dist, cutoff)
    largest = comps[0]
    medoid_idx = choose_medoid(largest, dist)
    rep = files[medoid_idx]
    meta = {
        "n_models_species": n,
        "cluster_cutoff_A": cutoff,
        "largest_cluster_size": len(largest),
        "largest_cluster_fraction": len(largest) / float(n),
        "largest_cluster_member_indices_0based": largest,
        "representative_index_0based": medoid_idx,
        "representative_file": str(rep),
    }
    return rep, meta


def run_pyrosetta_relax_and_dg(
    input_cif: Path,
    chain_a: str,
    chain_b: str,
    relax_cycles: int,
    scorefxn_name: str,
) -> dict[str, float]:
    try:
        pyrosetta = importlib.import_module("pyrosetta")
    except Exception as exc:
        raise RuntimeError(
            "PyRosetta import failed. Install PyRosetta in the execution environment first."
        ) from exc

    InterfaceAnalyzerMover = pyrosetta.rosetta.protocols.analysis.InterfaceAnalyzerMover
    FastRelax = pyrosetta.rosetta.protocols.relax.FastRelax

    pyrosetta.init(
        extra_options=" ".join(
            [
                "-ex1",
                "-ex2",
                "-use_input_sc",
                "-flip_HNQ",
                "-no_optH false",
                "-ignore_unrecognized_res true",
                "-relax:constrain_relax_to_start_coords",
            ]
        )
    )

    pose = pyrosetta.pose_from_file(str(input_cif))
    scorefxn = pyrosetta.create_score_function(scorefxn_name)

    mm = pyrosetta.MoveMap()
    mm.set_bb(True)
    mm.set_chi(True)
    mm.set_jump(True)

    relax = FastRelax(scorefxn, int(relax_cycles))
    relax.set_movemap(mm)
    relax.constrain_relax_to_start_coords(True)
    relax.apply(pose)

    relaxed_total_score = float(scorefxn(pose))

    scoring = pyrosetta.rosetta.core.scoring
    scorefxn_dg = scorefxn.clone()
    scorefxn_dg.set_weight(scoring.ScoreType.coordinate_constraint, 0.0)
    scorefxn_dg.set_weight(scoring.ScoreType.atom_pair_constraint, 0.0)
    scorefxn_dg.set_weight(scoring.ScoreType.angle_constraint, 0.0)
    scorefxn_dg.set_weight(scoring.ScoreType.dihedral_constraint, 0.0)

    interface = f"{chain_a}_{chain_b}"
    iam = InterfaceAnalyzerMover(interface)
    iam.set_scorefunction(scorefxn_dg)
    iam.set_compute_packstat(True)
    iam.apply(pose)

    return {
        "relaxed_total_score": relaxed_total_score,
        "dG_interface": float(iam.get_interface_dG()),
        "dG_crossterm": float(iam.get_crossterm_interface_energy()),
        "packstat": float(iam.get_interface_packstat()),
        "complexed_sasa": float(iam.get_complexed_sasa()),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Select largest-cluster representative and compute Relax->dG in PyRosetta")
    p.add_argument("--input-cif", type=Path, default=None, help="Direct input CIF path. If set, clone/species selection is skipped")
    p.add_argument("--clone-id", type=str, default=None, help="Clone ID, e.g. hmsame3_0234")
    p.add_argument("--species", type=str, choices=["human", "mouse"], default=None)
    p.add_argument("--clone-dir", type=Path, default=Path("."), help="Base directory containing per-clone CIF folders")
    p.add_argument("--chain-a", type=str, default="A", help="Target chain ID for interface string")
    p.add_argument("--chain-b", type=str, default="B", help="Binder chain ID for interface string")
    p.add_argument("--cluster-chain", type=str, default="B", help="Chain used for RMSD clustering")
    p.add_argument("--cluster-cutoff", type=float, default=0.2, help="RMSD cutoff in Angstrom for largest cluster")
    p.add_argument("--relax-cycles", type=int, default=5)
    p.add_argument("--scorefxn", type=str, default="ref2015")
    p.add_argument("--select-only", action="store_true", help="Only select representative structure, skip PyRosetta Relax/dG")
    p.add_argument("--output-json", type=Path, required=True)
    return p


def main() -> int:
    args = build_parser().parse_args()

    rep_meta: Mapping[str, object] = {}
    if args.input_cif is not None:
        input_cif = args.input_cif
        if not input_cif.exists():
            raise FileNotFoundError(f"Input CIF not found: {input_cif}")
    else:
        if not args.clone_id or not args.species:
            raise ValueError("When --input-cif is not given, both --clone-id and --species are required")
        clone_dir = args.clone_dir / args.clone_id
        if not clone_dir.exists():
            raise FileNotFoundError(f"Clone directory not found: {clone_dir}")
        input_cif, rep_meta = select_representative_from_clone(
            clone_dir=clone_dir,
            clone_id=args.clone_id,
            species=args.species,
            chain_for_clustering=args.cluster_chain,
            cutoff=args.cluster_cutoff,
        )

    energies: dict[str, float] | None = None
    if not args.select_only:
        energies = run_pyrosetta_relax_and_dg(
            input_cif=input_cif,
            chain_a=args.chain_a,
            chain_b=args.chain_b,
            relax_cycles=args.relax_cycles,
            scorefxn_name=args.scorefxn,
        )

    out = {
        "input_cif": str(input_cif),
        "chain_a": args.chain_a,
        "chain_b": args.chain_b,
        "scorefxn": args.scorefxn,
        "relax_cycles": args.relax_cycles,
        "selection": rep_meta,
        "energies": energies,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"input_cif={input_cif}")
    if rep_meta:
        print(f"largest_cluster_size={rep_meta['largest_cluster_size']}")
        print(f"largest_cluster_fraction={rep_meta['largest_cluster_fraction']:.6f}")
    if energies is not None:
        print(f"relaxed_total_score={energies['relaxed_total_score']:.6f}")
        print(f"dG_interface={energies['dG_interface']:.6f}")
    print(f"output_json={args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
