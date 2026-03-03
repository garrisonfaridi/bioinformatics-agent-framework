"""
download_data.py — Download CFW GWAS dataset from Dryad and optionally
subset to pilot_n samples using PLINK2 --keep.

Dryad now requires authentication for programmatic downloads.

MANUAL DOWNLOAD INSTRUCTIONS (if this script fails):
  1. Go to: https://datadryad.org/stash/dataset/doi:10.5061/dryad.2rs41
  2. Log in with a free Dryad account
  3. Download: cfw.bed, cfw.bim, cfw.fam, pheno.csv
  4. Place them in: <project>/data/raw/
  5. Re-run snakemake — the script will detect them and proceed to subsetting

Snakemake inputs:  (none — uses config)
Snakemake outputs: data/cfw.bed, .bim, .fam, data/pheno.csv
"""

import hashlib
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Snakemake injected variables
# ---------------------------------------------------------------------------
PILOT_N = snakemake.params.pilot_n   # noqa: F821
DRYAD_DOI = snakemake.params.doi     # noqa: F821

OUT_BED   = snakemake.output.bed     # noqa: F821
OUT_BIM   = snakemake.output.bim     # noqa: F821
OUT_FAM   = snakemake.output.fam     # noqa: F821
OUT_PHENO = snakemake.output.pheno   # noqa: F821

LOG = open(snakemake.log[0], "w")    # noqa: F821


def log(msg: str) -> None:
    print(msg, file=LOG, flush=True)
    print(msg, flush=True)


# Dryad version ID for DOI 10.5061/dryad.2rs41
DRYAD_VERSION_ID = 769

# File IDs from Dryad API /api/v2/versions/769/files
DRYAD_FILE_IDS = {
    "cfw.bed":  4350,
    "cfw.bim":  4348,
    "cfw.fam":  4346,
    "pheno.csv": 4340,
}

TARGET_FILES = list(DRYAD_FILE_IDS.keys())


def md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def try_dryad_download(file_name: str, dest: str, session: requests.Session) -> bool:
    """
    Attempt to download a file from Dryad using multiple URL patterns.
    Returns True on success.
    """
    file_id = DRYAD_FILE_IDS[file_name]

    urls_to_try = [
        # API v2 file download (requires auth token)
        f"https://datadryad.org/api/v2/files/{file_id}/download",
        # Stash stream URL
        f"https://datadryad.org/stash/downloads/file_stream/{file_id}",
        f"https://datadryad.org/downloads/file_stream/{file_id}",
    ]

    for url in urls_to_try:
        log(f"  Trying: {url}")
        try:
            r = session.get(url, stream=True, timeout=120, allow_redirects=True)
            if r.status_code == 200 and int(r.headers.get("content-length", 1)) > 0:
                with open(dest, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
                size = Path(dest).stat().st_size
                if size > 1000:  # sanity check — not empty
                    log(f"  Downloaded {file_name}: {size:,} bytes")
                    return True
                else:
                    log(f"  Download produced suspiciously small file ({size} bytes), skipping")
                    Path(dest).unlink(missing_ok=True)
            else:
                log(f"  HTTP {r.status_code} — skipping")
        except Exception as exc:
            log(f"  Error: {exc}")

    return False


def subset_plink(input_prefix: str, output_prefix: str, n: int) -> None:
    """Randomly subset to n samples via PLINK2 --keep."""
    fam_path = f"{input_prefix}.fam"
    with open(fam_path) as fh:
        samples = [line.split()[:2] for line in fh if line.strip()]

    if n >= len(samples):
        log(f"pilot_n={n} >= total N={len(samples)}, using full dataset")
        for ext in ("bed", "bim", "fam"):
            src = f"{input_prefix}.{ext}"
            dst = f"{output_prefix}.{ext}"
            if src != dst:
                import shutil
                shutil.copy(src, dst)
        return

    chosen = random.sample(samples, n)
    log(f"Subsetting {len(samples)} → {n} samples for pilot run")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        for fid, iid in chosen:
            tmp.write(f"{fid}\t{iid}\n")
        keep_file = tmp.name

    cmd = [
        "plink2",
        "--bfile", input_prefix,
        "--keep", keep_file,
        "--make-bed",
        "--out", output_prefix,
        "--no-psam-pheno",
    ]
    log(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    os.unlink(keep_file)


def main() -> None:
    data_dir = Path(OUT_BED).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Check if raw files already exist (manual download path)
    # ------------------------------------------------------------------
    already_present = all((raw_dir / f).exists() and (raw_dir / f).stat().st_size > 1000
                          for f in TARGET_FILES)

    if already_present:
        log("All raw files found in data/raw/ — skipping download")
    else:
        # ------------------------------------------------------------------
        # 2. Attempt programmatic download from Dryad
        # ------------------------------------------------------------------
        log(f"Attempting Dryad download for DOI: {DRYAD_DOI}")
        session = requests.Session()
        session.headers["Accept"] = "application/json"

        missing = [f for f in TARGET_FILES
                   if not (raw_dir / f).exists() or (raw_dir / f).stat().st_size <= 1000]
        log(f"Files to download: {missing}")

        failed = []
        for file_name in missing:
            dest = str(raw_dir / file_name)
            log(f"Downloading {file_name}...")
            ok = try_dryad_download(file_name, dest, session)
            if not ok:
                failed.append(file_name)

        if failed:
            log("\n" + "=" * 60)
            log("ERROR: Dryad requires authentication for programmatic downloads.")
            log(f"Could not download: {failed}")
            log("")
            log("MANUAL DOWNLOAD REQUIRED:")
            log("  1. Go to: https://datadryad.org/stash/dataset/doi:10.5061/dryad.2rs41")
            log("  2. Log in (free Dryad account)")
            log("  3. Download these files:")
            for f in TARGET_FILES:
                log(f"       {f}")
            log(f"  4. Place them in: {raw_dir}/")
            log("  5. Re-run: snakemake --cores 4 --use-conda --configfile config.yaml")
            log("=" * 60)
            LOG.close()
            sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Subset to pilot_n samples
    # ------------------------------------------------------------------
    raw_prefix   = str(raw_dir / "cfw")
    pilot_prefix = str(data_dir / "cfw")

    subset_plink(raw_prefix, pilot_prefix, PILOT_N)

    import shutil
    raw_pheno = raw_dir / "pheno.csv"
    if raw_pheno.exists():
        shutil.copy(str(raw_pheno), OUT_PHENO)
        log(f"Copied pheno.csv → {OUT_PHENO}")

    # Verify outputs are non-empty
    for out_path in (OUT_BED, OUT_BIM, OUT_FAM, OUT_PHENO):
        size = Path(out_path).stat().st_size
        if size == 0:
            log(f"ERROR: Output file is empty: {out_path}")
            sys.exit(1)
        log(f"Output OK: {out_path} ({size:,} bytes)")

    log("download_data complete.")
    LOG.close()


if __name__ == "__main__":
    main()
