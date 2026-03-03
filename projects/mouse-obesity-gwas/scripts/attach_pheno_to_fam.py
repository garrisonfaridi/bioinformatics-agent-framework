"""
attach_pheno_to_fam.py — Replace column 6 in a PLINK .fam file with
phenotype values, joining by IID (not positional).

Usage: python attach_pheno_to_fam.py input.fam pheno.txt output.fam

pheno.txt format (tab-separated, no header): IID<tab>value
FAM samples not found in pheno.txt get -9999 (GEMMA missing sentinel).
Handles post-QC FAM with fewer rows than the full phenotype file.
"""

import sys


def main() -> None:
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} input.fam pheno.txt output.fam", file=sys.stderr)
        sys.exit(1)

    fam_in    = sys.argv[1]
    pheno_in  = sys.argv[2]
    fam_out   = sys.argv[3]

    # Build IID → phenotype value lookup
    pheno_map: dict[str, str] = {}
    with open(pheno_in) as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                iid, val = str(parts[0]), parts[1]
                pheno_map[iid] = val

    with open(fam_in) as fh:
        fam_lines = fh.readlines()

    n_matched = n_missing = 0
    out_lines = []
    for fam_line in fam_lines:
        parts = fam_line.rstrip("\n").split()
        iid = str(parts[1])
        if iid in pheno_map:
            parts[5] = pheno_map[iid]
            n_matched += 1
        else:
            parts[5] = "-9999"
            n_missing += 1
        out_lines.append(" ".join(parts) + "\n")

    with open(fam_out, "w") as fh:
        fh.writelines(out_lines)

    print(f"FAM written: {len(out_lines)} samples | matched={n_matched} | missing_pheno={n_missing}")
    if n_missing > 0:
        print(f"  {n_missing} samples set to -9999 (not in phenotype file)")


if __name__ == "__main__":
    main()
