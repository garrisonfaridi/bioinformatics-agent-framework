#!/usr/bin/env Rscript
# genotype_qc_report.R
# Reads PLINK2 QC output files and produces diagnostic plots + summary.
#
# Snakemake inputs:  results/02_qc/cfw_qc.vmiss, .smiss, .afreq
# Snakemake outputs: results/02_qc/maf_histogram.png
#                    results/02_qc/qc_summary.txt

log_file <- snakemake@log[[1]]
log_con  <- file(log_file, open = "wt")
sink(log_con, type = "message")
sink(log_con, type = "output")

suppressPackageStartupMessages(library(data.table))

vmiss_file  <- snakemake@input$vmiss
smiss_file  <- snakemake@input$smiss
afreq_file  <- snakemake@input$afreq
bim_file    <- snakemake@input$bim
fam_qc_file <- snakemake@input$fam_qc
fam_in_file <- snakemake@input$fam_in
out_maf     <- snakemake@output$maf_plot
out_summary <- snakemake@output$summary

# ---------------------------------------------------------------------------
# Load QC files
# ---------------------------------------------------------------------------
message("Loading variant missingness: ", vmiss_file)
vmiss <- tryCatch(fread(vmiss_file), error = function(e) {
  message("WARNING: could not read vmiss file: ", e$message)
  data.table(F_MISS = numeric(0))
})

message("Loading sample missingness: ", smiss_file)
smiss <- tryCatch(fread(smiss_file), error = function(e) {
  message("WARNING: could not read smiss file: ", e$message)
  data.table(F_MISS = numeric(0))
})

message("Loading allele frequencies: ", afreq_file)
afreq <- tryCatch(fread(afreq_file), error = function(e) {
  message("WARNING: could not read afreq file: ", e$message)
  data.table(ALT_FREQS = numeric(0))
})

# ---------------------------------------------------------------------------
# Compute minor allele frequency (take minor side)
# ---------------------------------------------------------------------------
if ("ALT_FREQS" %in% colnames(afreq)) {
  maf <- pmin(afreq$ALT_FREQS, 1 - afreq$ALT_FREQS)
} else {
  maf <- numeric(0)
}

# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
png(out_maf, width = 1200, height = 500, res = 120)
par(mfrow = c(1, 3))

# MAF histogram
if (length(maf) > 0) {
  hist(maf, breaks = 50, main = "MAF distribution (post-QC)",
       xlab = "Minor allele frequency", col = "steelblue", border = "white")
  abline(v = 0.05, col = "red", lty = 2, lwd = 2)
  legend("topright", legend = "MAF = 0.05 threshold", col = "red", lty = 2)
} else {
  plot.new(); title("MAF (no data)")
}

# Variant missingness histogram
if (nrow(vmiss) > 0 && "F_MISS" %in% colnames(vmiss)) {
  hist(vmiss$F_MISS, breaks = 50, main = "Variant missingness (post-QC)",
       xlab = "Missing genotype rate", col = "darkorange", border = "white")
  abline(v = 0.05, col = "red", lty = 2, lwd = 2)
} else {
  plot.new(); title("Variant missingness (no data)")
}

# Sample missingness histogram
if (nrow(smiss) > 0 && "F_MISS" %in% colnames(smiss)) {
  hist(smiss$F_MISS, breaks = 30, main = "Sample missingness (post-QC)",
       xlab = "Missing genotype rate per sample", col = "forestgreen", border = "white")
  abline(v = 0.10, col = "red", lty = 2, lwd = 2)
} else {
  plot.new(); title("Sample missingness (no data)")
}

dev.off()
message("QC plot saved: ", out_maf)

# ---------------------------------------------------------------------------
# Summary — true counts from BIM/FAM (the actual filtered outputs)
# ---------------------------------------------------------------------------

# True final SNP count (from the BED/BIM that PLINK2 actually produced)
n_retained_snps <- tryCatch({
  bim_dt <- fread(bim_file, header = FALSE, sep = "\t",
                  col.names = c("chr", "snp", "cm", "bp", "a1", "a2"))
  nrow(bim_dt)
}, error = function(e) {
  message("WARNING: could not read BIM file: ", e$message)
  NA_integer_
})
message("True retained SNPs (from BIM): ", n_retained_snps)

# Input and retained sample counts (from FAM files)
n_samples_in <- tryCatch({
  fam_in <- fread(fam_in_file, header = FALSE)
  nrow(fam_in)
}, error = function(e) { NA_integer_ })

fam_qc <- tryCatch({
  fread(fam_qc_file, header = FALSE,
        col.names = c("fid", "iid", "pat", "mat", "sex", "pheno"))
}, error = function(e) { NULL })

n_samples_qc      <- if (!is.null(fam_qc)) nrow(fam_qc) else NA_integer_
n_samples_removed <- if (!is.na(n_samples_in) && !is.na(n_samples_qc))
                       n_samples_in - n_samples_qc else NA_integer_

# Sex composition from QC FAM column 5 (1=male, 2=female, 0=unknown)
sex_summary <- if (!is.null(fam_qc) && "sex" %in% colnames(fam_qc)) {
  sx <- table(fam_qc$sex)
  sprintf("%s male, %s female, %s unknown",
          ifelse("1" %in% names(sx), sx["1"], 0),
          ifelse("2" %in% names(sx), sx["2"], 0),
          ifelse("0" %in% names(sx), sx["0"], 0))
} else { "unknown" }
message("Cohort sex composition: ", sex_summary)

# Pre-filter counts (afreq/vmiss are computed on all variants before maf/geno filters)
n_input_snps <- if (nrow(afreq) > 0) nrow(afreq) else NA

summary_lines <- c(
  sprintf("Total input SNPs (before variant QC) : %s",
          ifelse(is.na(n_input_snps), "unknown", n_input_snps)),
  sprintf("  SNPs passing MAF > 0.05             : %s (from pre-filter set)",
          if (length(maf) > 0) sum(maf >= 0.05) else "N/A"),
  sprintf("  SNPs passing geno <= 5%%             : %s (from pre-filter set)",
          if (nrow(vmiss) > 0 && "F_MISS" %in% colnames(vmiss))
            sum(vmiss$F_MISS <= 0.05) else "N/A"),
  sprintf("Final retained SNPs (MAF+geno combined): %s",
          ifelse(is.na(n_retained_snps), "unknown", n_retained_snps)),
  "",
  sprintf("Total input samples                   : %s",
          ifelse(is.na(n_samples_in), "unknown", n_samples_in)),
  sprintf("Samples removed (mind > 30%%)           : %s",
          ifelse(is.na(n_samples_removed), "unknown", n_samples_removed)),
  sprintf("Final retained samples                 : %s",
          ifelse(is.na(n_samples_qc), "unknown", n_samples_qc)),
  sprintf("Cohort sex composition                 : %s", sex_summary)
)
writeLines(summary_lines, out_summary)
message("QC summary written: ", out_summary)
cat(paste(summary_lines, collapse = "\n"), "\n")

sink(type = "message")
sink(type = "output")
close(log_con)
