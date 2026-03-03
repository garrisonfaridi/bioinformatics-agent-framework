#!/usr/bin/env Rscript
# phenotype_prep.R
# Reads pheno.csv, applies inverse-normal transformation, writes GEMMA-compatible phenotype.
#
# Snakemake inputs:  data/pheno.csv, data/cfw.fam
# Snakemake outputs: results/01_phenotype/pheno_int.txt
#                    results/01_phenotype/pheno_dist.png
#                    results/01_phenotype/step_summary.txt

log_file <- snakemake@log[[1]]
log_con  <- file(log_file, open = "wt")
sink(log_con, type = "message")
sink(log_con, type = "output")

suppressPackageStartupMessages({
  library(data.table)
  library(jsonlite)
})

pheno_file  <- snakemake@input$pheno
fam_file    <- snakemake@input$fam
out_pheno   <- snakemake@output$pheno_int
out_plot    <- snakemake@output$dist_plot
out_summary <- snakemake@output$summary

bw_col    <- snakemake@params$column
transform <- snakemake@params$transform

# ---------------------------------------------------------------------------
# 1. Load phenotype table
# ---------------------------------------------------------------------------
message("Reading phenotype file: ", pheno_file)
pheno <- fread(pheno_file)
message("Columns in pheno.csv: ", paste(colnames(pheno), collapse = ", "))

if (!bw_col %in% colnames(pheno)) {
  stop(sprintf(
    "Column '%s' not found in pheno.csv. Available columns: %s",
    bw_col, paste(colnames(pheno), collapse = ", ")
  ))
}

# ---------------------------------------------------------------------------
# 2. Load FAM file to get sample order
# ---------------------------------------------------------------------------
message("Reading FAM file: ", fam_file)
fam <- fread(fam_file, header = FALSE,
             col.names = c("FID", "IID", "PAT", "MAT", "SEX", "PHENO"))

# Attempt to join on IID; fallback to positional if IID not in pheno
id_col <- intersect(c("IID", "id", "sample", "mouse_id", "ID"), colnames(pheno))[1]
if (!is.na(id_col)) {
  message("Joining phenotype on column: ", id_col)
  # Cast both join keys to character to avoid integer/character type mismatch
  fam[, IID := as.character(IID)]
  pheno[, (id_col) := as.character(get(id_col))]
  merged <- merge(fam[, .(FID, IID)], pheno[, .SD, .SDcols = c(id_col, bw_col)],
                  by.x = "IID", by.y = id_col, all.x = TRUE, sort = FALSE)
  bw_vals <- merged[[bw_col]]
} else {
  message("No ID column found; assuming phenotype rows match FAM order")
  if (nrow(pheno) != nrow(fam)) {
    stop("pheno.csv row count does not match FAM row count and no ID column found")
  }
  bw_vals <- pheno[[bw_col]]
}

n_total   <- length(bw_vals)
n_missing <- sum(is.na(bw_vals))
message(sprintf("Samples: %d total, %d missing phenotype", n_total, n_missing))

# ---------------------------------------------------------------------------
# 3. Diagnostic plot (raw distribution)
# ---------------------------------------------------------------------------
png(out_plot, width = 900, height = 600, res = 120)
par(mfrow = c(1, 2))

hist(bw_vals, breaks = 30, main = "Raw body weight (g)", xlab = "BW (g)",
     col = "steelblue", border = "white")

if (transform == "inverse_normal") {
  # Inverse-normal transformation (rank-based)
  ranks    <- rank(bw_vals, na.last = "keep", ties.method = "average")
  n_valid  <- sum(!is.na(bw_vals))
  bw_int   <- qnorm((ranks - 0.5) / n_valid)
  bw_int[is.na(bw_vals)] <- NA
} else if (transform == "log") {
  bw_int <- log(bw_vals)
} else {
  bw_int <- bw_vals
}

hist(bw_int, breaks = 30,
     main = sprintf("%s-transformed BW", transform),
     xlab = "Transformed BW", col = "darkorange", border = "white")
dev.off()
message("Distribution plot saved: ", out_plot)

# ---------------------------------------------------------------------------
# 4. Write phenotype file with IID for ID-based join (tab-separated: IID\tvalue)
# attach_pheno_to_fam.py joins by IID so post-QC sample drops are handled correctly
# ---------------------------------------------------------------------------
bw_out <- ifelse(is.na(bw_int), -9999, round(bw_int, 6))
pheno_out_dt <- data.table(IID = fam$IID, pheno = bw_out)
fwrite(pheno_out_dt, out_pheno, sep = "\t", col.names = FALSE)
message("Phenotype file written (IID + value): ", out_pheno)

# ---------------------------------------------------------------------------
# 5. Step summary
# ---------------------------------------------------------------------------
summary_lines <- c(
  paste0("Phenotype column  : ", bw_col),
  paste0("Transform applied : ", transform),
  paste0("N samples (FAM)   : ", n_total),
  paste0("N missing pheno   : ", n_missing),
  paste0("N valid pheno     : ", n_total - n_missing),
  sprintf("Raw BW mean±SD    : %.2f ± %.2f g", mean(bw_vals, na.rm = TRUE),
          sd(bw_vals, na.rm = TRUE)),
  sprintf("Raw BW range      : %.2f – %.2f g", min(bw_vals, na.rm = TRUE),
          max(bw_vals, na.rm = TRUE)),
  sprintf("INT BW mean±SD    : %.4f ± %.4f", mean(bw_int, na.rm = TRUE),
          sd(bw_int, na.rm = TRUE))
)
writeLines(summary_lines, out_summary)
message("Step summary written: ", out_summary)
cat(paste(summary_lines, collapse = "\n"), "\n")

sink(type = "message")
sink(type = "output")
close(log_con)
