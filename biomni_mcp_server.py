"""
Biomni MCP server wrapper for Claude Code.

Exposes bioinformatics-relevant biomni tool modules as MCP tools
accessible to Claude Code via the Model Context Protocol.

Register (one-time, then restart Claude Code):
    claude mcp add biomni -- python /Users/garrisonfaridi/agent/bioinformatics-freelance/biomni_mcp_server.py

Requires:
    ANTHROPIC_API_KEY set in environment
    biomni >= 0.0.8 installed in active Python env (miniforge3)

First run downloads ~11 GB biomni data lake — run once on a good connection.
"""

import os
from biomni.agent.a1 import A1

TOOL_MODULES = [
    # Core bioinformatics
    "biomni.tool.genomics",          # RNA-seq, WGS, alignment, variant calling
    "biomni.tool.genetics",          # GWAS, variant interpretation, population genetics
    "biomni.tool.cell_biology",      # scRNA-seq, cell type annotation, multi-omics
    "biomni.tool.molecular_biology", # ChIP-seq, ATAC-seq, epigenomics
    "biomni.tool.systems_biology",   # KEGG, GO enrichment, gene networks
    # Data and literature
    "biomni.tool.database",          # UniProt, NCBI, Ensembl, ClinVar, PDB, GWAS
    "biomni.tool.literature",        # PubMed mining, paper summarization
    "biomni.tool.protocols",         # Standard experimental protocols
    # Disease and clinical
    "biomni.tool.cancer_biology",    # Somatic variants, tumor microenvironment, TCGA
    "biomni.tool.immunology",        # Immune cell biology, TCR/BCR, cytokines
    "biomni.tool.pathology",         # Disease mechanisms, histopathology context
    # Drug and biochemistry
    "biomni.tool.pharmacology",      # Drug-gene interactions, ADMET, repurposing
    "biomni.tool.biochemistry",      # Metabolic pathways, enzyme activity
    # Additional domains
    "biomni.tool.bioimaging",        # Microscopy, spatial transcriptomics
    "biomni.tool.biophysics",        # Structural biology, protein dynamics
    "biomni.tool.physiology",        # Organ/tissue-level biology
    "biomni.tool.microbiology",      # Microbiome, host-pathogen
    "biomni.tool.bioengineering",    # Synthetic constructs, CRISPR design
    "biomni.tool.synthetic_biology", # Circuit design, metabolic engineering
    "biomni.tool.lab_automation",    # Liquid handling, plate-based assay context
]

DATA_PATH = os.path.expanduser("~/agent/bioinformatics-freelance/biomni_data")

if __name__ == "__main__":
    agent = A1(
        path=DATA_PATH,
        llm="claude-sonnet-4-5",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        expected_data_lake_files=[],
    )
    mcp = agent.create_mcp_server(tool_modules=TOOL_MODULES)
    mcp.run(transport="stdio")
