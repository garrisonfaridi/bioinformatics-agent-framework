"""
Know-how version consistency checker.

Parses version pins from knowhow/*.md files (YAML frontmatter preferred,
inline mentions as fallback) and compares against the active conda environment
or base-env.yml.

Usage
-----
    python scripts/check_knowhow_versions.py
    python scripts/check_knowhow_versions.py --knowhow-dir knowhow/ --strict
    python scripts/check_knowhow_versions.py --env-file base-env.yml

Output
------
    knowhow_version_report.txt  (also printed to stdout)
    Exit code 0 = all MATCH or NOT_FOUND
    Exit code 1 = at least one MISMATCH (use with CI)
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract tool_versions dict from YAML frontmatter block (--- ... ---)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    fm_block = match.group(1)
    # Find tool_versions: section
    tv_match = re.search(r"tool_versions:\s*\n((?:\s+\S.*\n?)*)", fm_block)
    if not tv_match:
        return {}
    versions: dict[str, str] = {}
    for line in tv_match.group(1).splitlines():
        # Match "  toolname: "1.2.3""
        m = re.match(r'\s+(\S+):\s+"?([^\s#"]+)"?', line)
        if m:
            versions[m.group(1).lower()] = m.group(2)
    return versions


# ---------------------------------------------------------------------------
# Inline version mention extraction (fallback)
# ---------------------------------------------------------------------------

# Patterns to match tool version mentions in prose / tables
_INLINE_PATTERNS = [
    # "GATK 4.4.0.0", "GATK4 4.3.x", "STAR 2.7.11a"
    r"\b([\w\-]+)\s+v?(\d+\.\d+[\.\w]*)",
    # backtick-pinned conda: "gatk==4.4.0.0", "star=2.7.11a"
    r"`([\w\-]+)[=:]+v?(\d+\.\d+[\.\w]*)`",
    # table row: "| GATK4 | ... | 4.4.0.0 |"
    r"\|\s*([\w\-]+)\s+\|(?:[^|]+\|){1,3}\s*v?(\d+\.\d+[\.\w]*)\s*\|",
]


def extract_inline_versions(text: str) -> dict[str, str]:
    """Best-effort extraction of tool versions from prose text."""
    versions: dict[str, str] = {}
    for pat in _INLINE_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            tool = m.group(1).lower().replace("-", "").replace("_", "")
            ver = m.group(2)
            # Skip very common words that match the pattern
            if tool in {"version", "release", "update", "tag", "use", "the",
                        "a", "an", "with", "for", "in", "at", "of"}:
                continue
            if tool not in versions:
                versions[tool] = ver
    return versions


# ---------------------------------------------------------------------------
# Conda / env-file version resolution
# ---------------------------------------------------------------------------

def get_conda_versions() -> dict[str, str]:
    """Run `conda list` and return name→version dict."""
    try:
        result = subprocess.run(
            ["conda", "list", "--export"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}

    versions: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if line.startswith("#") or "=" not in line:
            continue
        parts = line.split("=")
        if len(parts) >= 2:
            name = parts[0].lower().replace("-", "").replace("_", "")
            versions[name] = parts[1]
    return versions


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse a conda env YAML for version pins."""
    versions: dict[str, str] = {}
    if not env_path.exists():
        return versions
    with env_path.open() as fh:
        content = fh.read()
    # Match "  - toolname=1.2.3" or "  - toolname>=1.2.3"
    for m in re.finditer(r"^\s+-\s+([\w\-]+)[=<>!]+v?(\d+\.\d+[\.\w]*)", content,
                         re.MULTILINE):
        name = m.group(1).lower().replace("-", "").replace("_", "")
        versions[name] = m.group(2)
    return versions


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def normalize(name: str) -> str:
    return name.lower().replace("-", "").replace("_", "")


def _versions_match(doc_ver: str, env_ver: str) -> bool:
    """Compare major.minor of two version strings; ignore patch differences."""
    def split_ver(v: str) -> list[str]:
        return re.split(r"[.\-]", normalize(v))

    dparts = split_ver(doc_ver)
    eparts = split_ver(env_ver)
    # Compare up to major.minor (first 2 numeric parts); must both be present
    cmp_len = min(2, len(dparts), len(eparts))
    return dparts[:cmp_len] == eparts[:cmp_len]


def check_versions(knowhow_dir: Path, env_versions: dict[str, str],
                   strict: bool = False) -> list[dict]:
    rows: list[dict] = []
    for md_file in sorted(knowhow_dir.glob("*.md")):
        text = md_file.read_text()
        fm_versions = parse_frontmatter(text)
        # Prefer frontmatter; fall back to inline
        doc_versions = fm_versions if fm_versions else extract_inline_versions(text)

        for tool, doc_ver in doc_versions.items():
            norm = normalize(tool)
            env_ver = env_versions.get(norm)
            if env_ver is None:
                status = "NOT_FOUND"
            elif _versions_match(doc_ver, env_ver):
                status = "MATCH"
            else:
                status = "MISMATCH"
            rows.append({
                "doc": md_file.name,
                "tool": tool,
                "doc_version": doc_ver,
                "env_version": env_ver or "—",
                "status": status,
                "source": "frontmatter" if fm_versions else "inline",
            })
    return rows


def format_report(rows: list[dict]) -> str:
    lines = ["Know-How Version Consistency Report", "=" * 60, ""]
    if not rows:
        return "\n".join(lines) + "No version pins found in knowhow docs.\n"

    mismatches = [r for r in rows if r["status"] == "MISMATCH"]
    matches    = [r for r in rows if r["status"] == "MATCH"]
    not_found  = [r for r in rows if r["status"] == "NOT_FOUND"]

    lines += [f"Total pins checked: {len(rows)}",
              f"  MATCH:     {len(matches)}",
              f"  MISMATCH:  {len(mismatches)}",
              f"  NOT_FOUND: {len(not_found)}", ""]

    if mismatches:
        lines.append("MISMATCHES (require attention):")
        for r in mismatches:
            lines.append(
                f"  [{r['doc']}] {r['tool']}: doc={r['doc_version']} env={r['env_version']}"
            )
        lines.append("")

    lines.append("Full table:")
    header = f"  {'Status':<12} {'Doc':<30} {'Tool':<20} {'Doc ver':<15} {'Env ver':<15} Source"
    lines.append(header)
    lines.append("  " + "-" * 100)
    for r in sorted(rows, key=lambda x: (x["status"], x["doc"], x["tool"])):
        lines.append(
            f"  {r['status']:<12} {r['doc']:<30} {r['tool']:<20} "
            f"{r['doc_version']:<15} {r['env_version']:<15} {r['source']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check knowhow doc versions vs. conda env")
    parser.add_argument("--knowhow-dir", default="knowhow",
                        help="Path to knowhow docs directory (default: knowhow/)")
    parser.add_argument("--env-file", default="base-env.yml",
                        help="Conda env YAML to parse (used if conda list fails)")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 on any MISMATCH (CI mode)")
    parser.add_argument("--output", default=None,
                        help="Output report path (default: knowhow_version_report.txt in repo root)")
    args = parser.parse_args()

    knowhow_dir = Path(args.knowhow_dir)
    if not knowhow_dir.exists():
        print(f"ERROR: knowhow dir not found: {knowhow_dir}", file=sys.stderr)
        sys.exit(1)

    # Try live conda env first; fall back to env file
    env_versions = get_conda_versions()
    if not env_versions:
        print("[check_knowhow_versions] conda list unavailable; parsing env file instead",
              file=sys.stderr)
        env_versions = parse_env_file(Path(args.env_file))

    rows = check_versions(knowhow_dir, env_versions, strict=args.strict)
    report = format_report(rows)

    out_path = Path(args.output) if args.output else Path(__file__).parent.parent / "knowhow_version_report.txt"
    out_path.write_text(report)
    print(report)
    print(f"[check_knowhow_versions] Report written to {out_path}")

    mismatches = [r for r in rows if r["status"] == "MISMATCH"]
    if mismatches and args.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
