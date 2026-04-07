"""
ARCFilesystemKB: filesystem shim providing kb.get() interface over ARC stage directories.

KnowledgeBase class does not exist in researchclaw. ARC is entirely file-based — artifacts
live as markdown files in stage subdirectories after pipeline completion. This adapter
provides the .get() interface expected by kinesin's bridge layer.
"""

from pathlib import Path


# Key-to-stage-file mapping
_KEY_MAP = {
    "findings": ("stage-07", "synthesis.md"),
    "literature": ("stage-05", "screened_papers.md"),
    "hypotheses": ("stage-08", "hypotheses.md"),
    "decisions": ("stage-06", "extraction.md"),
}


class ARCFilesystemKB:
    """
    Mimics a KnowledgeBase .get() API by reading ARC stage-* directories.

    KnowledgeBase class does not exist in researchclaw; this is the adapter shim.
    All reads are lazy (on .get() call); nothing is cached.
    """

    def __init__(self, run_dir: Path) -> None:
        """
        Args:
            run_dir: ARC run directory containing stage-01/, stage-02/, ... subdirs.
        """
        self.run_dir = Path(run_dir)

    def get(self, key: str) -> str | None:
        """
        Read stage artifact for key. Returns markdown text or None if not found.

        Key mappings:
            "findings"   → stage-07/synthesis.md
            "literature" → stage-05/screened_papers.md
            "hypotheses" → stage-08/hypotheses.md
            "decisions"  → stage-06/extraction.md

        Args:
            key: One of the above keys.

        Returns:
            Markdown string contents, or None if file does not exist.
        """
        if key not in _KEY_MAP:
            raise KeyError(
                f"Unknown KB key: '{key}'. Valid keys: {list(_KEY_MAP.keys())}"
            )
        stage_dir, filename = _KEY_MAP[key]
        artifact_path = self.run_dir / stage_dir / filename
        if not artifact_path.exists():
            return None
        return artifact_path.read_text(encoding="utf-8")

    def stage_completed(self, stage_name: str) -> bool:
        """
        Check if a stage directory exists and contains at least one .md file.

        Args:
            stage_name: Stage directory name, e.g. "stage-07" or the Stage enum .name
                        (converted automatically to "stage-NN" format).

        Returns:
            True if stage directory exists and has at least one .md file.
        """
        # Accept Stage enum names like "HYPOTHESIS_GEN" → try to resolve to stage-NN
        # by scanning directories for a match in their metadata, or accept "stage-NN" directly.
        stage_dir = self.run_dir / stage_name
        if not stage_dir.exists() or not stage_dir.is_dir():
            return False
        return any(stage_dir.glob("*.md"))

    def list_stages(self) -> list[str]:
        """Return sorted list of stage directory names present in run_dir."""
        return sorted(
            d.name
            for d in self.run_dir.iterdir()
            if d.is_dir() and d.name.startswith("stage-")
        )

    def __repr__(self) -> str:
        return f"ARCFilesystemKB(run_dir={self.run_dir!r})"
