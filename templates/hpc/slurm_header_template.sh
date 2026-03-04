#!/usr/bin/env bash
#SBATCH --job-name=JOBNAME
#SBATCH --output=logs/JOBNAME_%j.out
#SBATCH --error=logs/JOBNAME_%j.err
#SBATCH --time=WALLTIME            # e.g. 24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=NCORES     # e.g. 8
#SBATCH --mem=MEMORY               # e.g. 64G
#SBATCH --partition=PARTITION      # e.g. standard, highmem, gpu
#SBATCH --account=ACCOUNT          # your HPC allocation code

# --- Environment setup ---
module load anaconda3              # or module load singularity, etc.
conda activate bioinfo-base

# --- Ensure logs directory exists ---
mkdir -p logs

# --- Working directory ---
cd "$SLURM_SUBMIT_DIR"

# --- Main command (replace below) ---
COMMAND
