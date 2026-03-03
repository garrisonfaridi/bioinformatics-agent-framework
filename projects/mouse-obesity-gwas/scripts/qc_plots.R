#!/usr/bin/env Rscript
# qc_plots.R — QQ plot, Manhattan plot, per-chromosome SNP density.
# Always runs regardless of significance branch.
#
# Snakemake inputs:  results/03_lmm/output/cfw_qc.assoc.txt
#                    results/03_lmm/significance_check.json
# Snakemake outputs: results/06_qc_plots/qq_plot.png
#                    results/06_qc_plots/manhattan_plot.png
#                    results/06_qc_plots/snp_density.png
#                    results/06_qc_plots/lambda.txt

log_file <- snakemake@log[[1]]
log_con  <- file(log_file, open = "wt")
sink(log_con, type = "message")
sink(log_con, type = "output")

suppressPackageStartupMessages({
  library(qqman)
  library(data.table)
  library(jsonlite)
})

assoc_file    <- snakemake@input$assoc
sig_json_file <- snakemake@input$sig
out_qq        <- snakemake@output$qq
out_man       <- snakemake@output$manhattan
out_density   <- snakemake@output$density
out_lambda    <- snakemake@output$lambda_txt
lambda_warn   <- snakemake@params$lambda_warn

# ---------------------------------------------------------------------------
# 1. Load association results
# ---------------------------------------------------------------------------
message("Loading assoc file: ", assoc_file)
assoc <- tryCatch(
  fread(assoc_file),
  error = function(e) {
    message("ERROR loading assoc file: ", e$message)
    NULL
  }
)

if (is.null(assoc) || nrow(assoc) == 0) {
  message("WARNING: empty assoc file — creating placeholder plots")
  for (f in c(out_qq, out_man, out_density)) {
    png(f); plot.new(); title("No GWAS results"); dev.off()
  }
  writeLines("lambda = NA (no data)", out_lambda)
  sink(type = "message"); sink(type = "output"); close(log_con)
  quit(status = 0)
}

colnames(assoc) <- tolower(colnames(assoc))
message(sprintf("Loaded %d SNPs. Columns: %s", nrow(assoc), paste(colnames(assoc), collapse = ", ")))

# Map GEMMA columns to qqman expected: SNP, CHR, BP, P
# GEMMA output: chr, rs, ps, n_mis, n_obs, af, beta, se, logl_H1, l_remle, p_wald, p_lrt, p_score
snp_col   <- intersect(c("rs", "snp"), colnames(assoc))[1]
chr_col   <- "chr"
pos_col   <- intersect(c("ps", "bp", "pos"), colnames(assoc))[1]
pval_col  <- intersect(c("p_wald", "p_lrt", "p", "pval"), colnames(assoc))[1]

if (any(is.na(c(snp_col, chr_col, pos_col, pval_col)))) {
  stop(sprintf("Could not identify required columns. Found: %s",
               paste(colnames(assoc), collapse = ", ")))
}

# Build standardized data.table
gwas <- data.table(
  SNP = assoc[[snp_col]],
  CHR = as.integer(assoc[[chr_col]]),
  BP  = as.integer(assoc[[pos_col]]),
  P   = as.numeric(assoc[[pval_col]])
)

# Remove NA, zero, or non-finite p-values
gwas <- gwas[!is.na(P) & P > 0 & is.finite(P) & !is.na(CHR) & CHR > 0]
message(sprintf("Valid SNPs for plotting: %d", nrow(gwas)))

# Load thresholds from significance_check.json
sig_data       <- fromJSON(sig_json_file)
bonf_threshold <- sig_data$threshold_bonferroni
sugg_threshold <- sig_data$threshold_suggestive
n_snps         <- sig_data$n_snps_post_qc

# ---------------------------------------------------------------------------
# 2. Genomic inflation factor λ
# ---------------------------------------------------------------------------
chisq_obs    <- qchisq(1 - gwas$P, df = 1)
lambda_gc    <- median(chisq_obs, na.rm = TRUE) / qchisq(0.5, df = 1)
message(sprintf("Genomic inflation factor λ = %.4f", lambda_gc))

lambda_lines <- c(
  sprintf("lambda_GC    = %.4f", lambda_gc),
  sprintf("n_snps       = %d", n_snps),
  sprintf("warning      = %s", if (lambda_gc > lambda_warn) "YES — inflation detected" else "NO")
)
writeLines(lambda_lines, out_lambda)

if (lambda_gc > lambda_warn) {
  message(sprintf("WARNING: λ = %.3f exceeds threshold %.2f — investigate confounding",
                  lambda_gc, lambda_warn))
}

# ---------------------------------------------------------------------------
# 3. QQ plot
# ---------------------------------------------------------------------------
message("Producing QQ plot")
png(out_qq, width = 800, height = 700, res = 120)
qq(gwas$P,
   main = sprintf("QQ Plot — Mouse BW GWAS (CFW)\nλ = %.4f (n = %d SNPs)", lambda_gc, nrow(gwas)),
   col  = "steelblue",
   cex  = 0.5,
   las  = 1)
if (lambda_gc > lambda_warn) {
  legend("topleft", legend = sprintf("WARNING: λ = %.3f > %.2f", lambda_gc, lambda_warn),
         col = "red", pch = NA, lty = 1, lwd = 2, bty = "n", text.col = "red")
}
dev.off()
message("QQ plot saved: ", out_qq)

# ---------------------------------------------------------------------------
# 4. Manhattan plot
# ---------------------------------------------------------------------------
message("Producing Manhattan plot")
png(out_man, width = 1400, height = 600, res = 120)

tryCatch({
  manhattan(
    gwas,
    chr    = "CHR",
    bp     = "BP",
    snp    = "SNP",
    p      = "P",
    main   = sprintf("Manhattan Plot — CFW Mouse Body Weight GWAS (n=%d SNPs)", nrow(gwas)),
    suggestiveline = -log10(sugg_threshold),
    genomewideline = -log10(bonf_threshold),
    col    = c("steelblue", "navy"),
    cex    = 0.4,
    las    = 1
  )
  legend("topright", bty = "n",
         legend = c(sprintf("Bonferroni (p < %.2e)", bonf_threshold),
                    sprintf("Suggestive (p < %.2e)", sugg_threshold)),
         col = c("red", "blue"), lty = c(1, 2), lwd = 2)
}, error = function(e) {
  plot.new()
  title(sprintf("Manhattan plot error: %s", e$message))
  message("Manhattan plot error: ", e$message)
})

dev.off()
message("Manhattan plot saved: ", out_man)

# ---------------------------------------------------------------------------
# 5. Per-chromosome SNP density
# ---------------------------------------------------------------------------
message("Producing per-chromosome SNP density plot")
snp_counts <- gwas[, .N, by = CHR][order(CHR)]

png(out_density, width = 1000, height = 400, res = 120)
barplot(
  snp_counts$N,
  names.arg = snp_counts$CHR,
  main      = "SNP count per chromosome (post-QC)",
  xlab      = "Chromosome",
  ylab      = "Number of SNPs",
  col       = "steelblue",
  border    = "white",
  las       = 2
)
dev.off()
message("SNP density plot saved: ", out_density)

message(sprintf("λ = %.4f | %d SNPs | Bonferroni = %.3e | Suggestive = %.3e",
                lambda_gc, nrow(gwas), bonf_threshold, sugg_threshold))
message("qc_plots complete.")

sink(type = "message"); sink(type = "output"); close(log_con)
