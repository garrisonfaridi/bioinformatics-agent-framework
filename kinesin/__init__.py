"""
Kinesin — BioResearch End-to-End Autonomous Research System.

Integrates AutoResearchClaw (literature + paper writing), ScienceClaw (multi-agent debate),
and OmicsClaw (spatial + single-cell skills) on top of the existing bioinformatics framework.

Layers:
    1. literature/   — ARC literature bridge (Stages 1-8)
    2. coordination/ — ScienceClaw hypothesis debate
    3. [external]    — Existing framework (scripts/, peer_review/)
    4. writing/      — ARC paper writing bridge (Stages 16-23)
    5. metaclaw/     — Cross-run learning (optional, default off)
"""

__version__ = "0.1.0"
__author__ = "Garrison Faridi"
