#!/usr/bin/env bash
set -e

echo "=== Kinesin one-time setup ==="

# ---------------------------------------------------------------------------
# Step 1: Install ScienceClaw (directory-based, not pip-installable)
# ---------------------------------------------------------------------------
echo "[1/5] Installing ScienceClaw..."
SC_DIR="$HOME/scienceclaw"

if [ -d "$SC_DIR/.git" ]; then
    echo "  Found existing clone at $SC_DIR — pulling latest..."
    git -C "$SC_DIR" pull --quiet
else
    echo "  Cloning scienceclaw to $SC_DIR..."
    git clone --quiet https://github.com/lamm-mit/scienceclaw.git "$SC_DIR"
fi

# Install scienceclaw's own deps (core only, quiet)
pip install -r "$SC_DIR/requirements.txt" --quiet

# Wire up 'import scienceclaw' by adding $HOME to site-packages via .pth file
SITE_PKGS=$(python3 -c "import site; print(site.getsitepackages()[0])")
PTH_FILE="$SITE_PKGS/scienceclaw_home.pth"
if [ ! -f "$PTH_FILE" ] || ! grep -q "$SC_DIR" "$PTH_FILE" 2>/dev/null; then
    printf "%s\n%s\n" "$HOME" "$SC_DIR" > "$PTH_FILE"
    echo "  Created $PTH_FILE -> $HOME and $SC_DIR"
fi

# ---------------------------------------------------------------------------
# Step 2: Verify ScienceClaw import
# ---------------------------------------------------------------------------
echo "[2/5] Verifying ScienceClaw import..."
python3 -c "from scienceclaw.autonomous.deep_investigation import run_deep_investigation; print('ScienceClaw OK')"

# ---------------------------------------------------------------------------
# Step 3: ScienceClaw agent initialization (biology profile)
# ---------------------------------------------------------------------------
echo "[3/5] Running ScienceClaw initialization (biology profile)..."
cd "$SC_DIR"
python3 setup.py --quick --profile biology --name "KinesinAgent" || {
    echo "  WARNING: scienceclaw.setup --quick failed (non-fatal — import check passed)."
    echo "  If needed, run manually: cd ~/scienceclaw && python3 setup.py --quick --profile biology"
}
cd - > /dev/null

# ---------------------------------------------------------------------------
# Step 4: Verify researchclaw import
# ---------------------------------------------------------------------------
echo "[4/5] Verifying researchclaw import..."
python3 -c "import researchclaw; print('researchclaw OK:', researchclaw.__version__)"

# ---------------------------------------------------------------------------
# Step 5: Verify omicsclaw and install spatial/singlecell extras
# ---------------------------------------------------------------------------
echo "[5/5] Verifying omicsclaw import and installing spatial/singlecell extras..."
python3 -c "import omicsclaw; print('omicsclaw OK')"
pip install "omicsclaw[spatial,singlecell]" --quiet || {
    echo "  WARNING: omicsclaw[spatial,singlecell] extras not defined — installing base only."
    pip install omicsclaw --quiet
}

echo ""
echo "Setup complete."
echo "For spatial-domains DL support (SpaGCN/STAGATE/torch): pip install omicsclaw[spatial-domains]"
echo "For full OmicsClaw extras: pip install omicsclaw[all]"
