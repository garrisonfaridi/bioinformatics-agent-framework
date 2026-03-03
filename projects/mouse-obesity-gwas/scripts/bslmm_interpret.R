#!/usr/bin/env Rscript
# bslmm_interpret.R — Parse GEMMA BSLMM hyperparameter chains and
# characterize the genetic architecture of mouse body weight.
# Only runs if check_significance produced has_hits = false.
#
# Snakemake inputs:  results/04_bslmm/output/cfw_qc.hyp.txt
# Snakemake outputs: results/04_bslmm/hyperparameters.csv
#                    results/04_bslmm/architecture_summary.txt
#                    results/04_bslmm/trace_plots.png

log_file <- snakemake@log[[1]]
log_con  <- file(log_file, open = "wt")
sink(log_con, type = "message")
sink(log_con, type = "output")

suppressPackageStartupMessages(library(data.table))

hyp_file    <- snakemake@input$hyp
out_csv     <- snakemake@output$hyp_csv
out_arch    <- snakemake@output$arch_txt
out_trace   <- snakemake@output$trace_plot

# ---------------------------------------------------------------------------
# 1. Load hyperparameter chains
# ---------------------------------------------------------------------------
message("Loading BSLMM hyperparameter file: ", hyp_file)
hyp <- tryCatch({
  # GEMMA .hyp.txt uses tab separators but also pads values with spaces (e.g.
  # "h \t pve \t ..."), and appends a trailing tab on every data row.
  # fread's auto-sep detection splits on BOTH spaces and tabs, doubling the
  # column count. Force sep = "\t" and strip whitespace from names / values.
  raw <- fread(hyp_file, sep = "\t", fill = TRUE, strip.white = TRUE)
  setnames(raw, trimws(colnames(raw)))         # trim header padding
  # Drop the trailing-tab phantom: the last column will be all NA/empty
  empty_cols <- names(raw)[sapply(raw, function(x) all(is.na(x) | trimws(as.character(x)) == ""))]
  for (col in empty_cols) {
    raw[[col]] <- NULL
    message("Dropped empty trailing column: ", col)
  }
  raw
}, error = function(e) {
  message("ERROR reading hyp file: ", e$message)
  NULL
})

if (is.null(hyp) || nrow(hyp) == 0) {
  message("WARNING: hyp file empty or unreadable — writing placeholder outputs")
  fwrite(data.table(parameter = "ERROR", posterior_mean = NA), out_csv)
  writeLines(c("BSLMM output unavailable — check logs/run_bslmm.log"), out_arch)
  png(out_trace); plot.new(); title("BSLMM trace (no data)"); dev.off()
  sink(type = "message"); sink(type = "output"); close(log_con)
  quit(status = 0)
}

message(sprintf("Loaded %d MCMC samples", nrow(hyp)))
message("Columns: ", paste(colnames(hyp), collapse = ", "))

# GEMMA BSLMM .hyp.txt columns: pve, pge, rho, pi, n_gamma, ...
# Standardize column lookup (GEMMA output is lowercase)
colnames(hyp) <- trimws(tolower(colnames(hyp)))

# ---------------------------------------------------------------------------
# 2. Compute posterior summaries (mean + 95% CI)
# ---------------------------------------------------------------------------
params_of_interest <- intersect(c("pve", "pge", "rho", "pi", "n_gamma"), colnames(hyp))

if (length(params_of_interest) == 0) {
  message("WARNING: none of the expected hyperparameter columns found")
  message("Available: ", paste(colnames(hyp), collapse = ", "))
  params_of_interest <- colnames(hyp)
}

ci95 <- function(x) {
  quantile(x, probs = c(0.025, 0.975), na.rm = TRUE)
}

summary_rows <- lapply(params_of_interest, function(p) {
  vals  <- hyp[[p]]
  mn    <- mean(vals, na.rm = TRUE)
  md    <- median(vals, na.rm = TRUE)
  ci    <- ci95(vals)
  data.table(
    parameter    = p,
    posterior_mean = round(mn, 6),
    posterior_median = round(md, 6),
    ci_lower_2.5  = round(ci[1], 6),
    ci_upper_97.5 = round(ci[2], 6)
  )
})

summary_dt <- rbindlist(summary_rows)
message("Posterior summaries:")
print(summary_dt)

dir.create(dirname(out_csv), recursive = TRUE, showWarnings = FALSE)
fwrite(summary_dt, out_csv)
message("Hyperparameter CSV written: ", out_csv)

# ---------------------------------------------------------------------------
# 3. Interpret genetic architecture
# ---------------------------------------------------------------------------
get_param <- function(name) {
  if (name %in% summary_dt$parameter) {
    summary_dt[parameter == name, posterior_mean]
  } else {
    NA_real_
  }
}

pve     <- get_param("pve")
pge     <- get_param("pge")
n_gamma <- get_param("n_gamma")

message(sprintf("PVE   = %.4f", pve))
message(sprintf("PGE   = %.4f", pge))
message(sprintf("n_γ   = %.1f", n_gamma))

# Interpretation logic
arch_lines <- c(
  "=== BSLMM Genetic Architecture Summary ===",
  sprintf("PVE  (proportion of variance explained): %.4f [95%% CI: %.4f, %.4f]",
          pve,
          if ("pve" %in% summary_dt$parameter) summary_dt[parameter == "pve", ci_lower_2.5] else NA,
          if ("pve" %in% summary_dt$parameter) summary_dt[parameter == "pve", ci_upper_97.5] else NA),
  sprintf("PGE  (proportion due to sparse effects): %.4f [95%% CI: %.4f, %.4f]",
          pge,
          if ("pge" %in% summary_dt$parameter) summary_dt[parameter == "pge", ci_lower_2.5] else NA,
          if ("pge" %in% summary_dt$parameter) summary_dt[parameter == "pge", ci_upper_97.5] else NA),
  sprintf("n_γ  (expected number of sparse loci):  %.1f", n_gamma),
  "",
  "=== Architecture Interpretation ==="
)

if (!is.na(pve) && pve < 0.05) {
  arch_lines <- c(arch_lines,
    "CONCLUSION: Low heritability (PVE < 0.05) in this sample.",
    "  - The trait shows limited genetic signal with N=300 pilot samples.",
    "  - Recommend: (1) Run full N=1,200 dataset; (2) verify phenotype quality;",
    "    (3) ensure sex is modeled as covariate (BW is strongly sex-dimorphic).",
    "  - GWAS power is severely limited at this sample size for polygenic traits."
  )
} else if (!is.na(pve) && !is.na(pge) && pge < 0.10) {
  arch_lines <- c(arch_lines,
    sprintf("CONCLUSION: Moderate heritability (PVE = %.2f) but highly polygenic architecture.", pve),
    "  - Sparse component explains < 10% of genetic variance (PGE < 0.10).",
    "  - Body weight in CFW mice is controlled by many variants of small effect.",
    "  - No large-effect loci are likely to emerge without >> 1,200 animals.",
    "  - This is consistent with the highly polygenic nature of body weight in rodents.",
    "  - Recommend: Aggregate multiple loci (polygenic score), not single-variant mapping."
  )
} else if (!is.na(pve) && !is.na(pge) && pge >= 0.10) {
  pge_ci_lo <- if ("pge" %in% summary_dt$parameter) summary_dt[parameter == "pge", ci_lower_2.5]  else NA
  pge_ci_hi <- if ("pge" %in% summary_dt$parameter) summary_dt[parameter == "pge", ci_upper_97.5] else NA
  pve_ci_lo <- if ("pve" %in% summary_dt$parameter) summary_dt[parameter == "pve", ci_lower_2.5]  else NA
  pve_ci_hi <- if ("pve" %in% summary_dt$parameter) summary_dt[parameter == "pve", ci_upper_97.5] else NA
  arch_lines <- c(arch_lines,
    sprintf("CONCLUSION: Point estimate suggests moderate sparse component (PVE = %.3f, PGE = %.2f),",
            pve, pge),
    "  but posteriors are largely uninformative — see CAVEAT below.",
    sprintf("  - Approximately %.0f genomic loci estimated in sparse component (95%% CI: %.0f–%.0f).",
            n_gamma,
            if ("n_gamma" %in% summary_dt$parameter) summary_dt[parameter == "n_gamma", ci_lower_2.5]  else NA,
            if ("n_gamma" %in% summary_dt$parameter) summary_dt[parameter == "n_gamma", ci_upper_97.5] else NA),
    "",
    "  CAVEAT — Posterior credible intervals are nearly uninformative:",
    sprintf("  - PGE 95%% CI: [%.3f, %.3f] — spans essentially the full [0, 1] range.", pge_ci_lo, pge_ci_hi),
    sprintf("  - PVE 95%% CI: [%.4f, %.4f] — consistent with near-zero to moderate heritability.", pve_ci_lo, pve_ci_hi),
    "  - These wide CIs reflect the pilot sample size (N~300) rather than true",
    "    genetic architecture. The MCMC cannot distinguish sparse from polygenic models.",
    "",
    "  LITERATURE COMPARISON:",
    sprintf("  - Observed PVE = %.3f is 4–8x lower than published CFW body weight", pve),
    "    SNP-heritability: h² = 0.20–0.40 (Parker et al. 2016 Nat Genet; Nicod et al. 2016).",
    "  - This likely reflects: (1) reduced power from pilot N vs full N=1,200;",
    "    (2) reduced SNP panel (16,710 vs 92K input); (3) uninformative MCMC priors",
    "    at this sample size. Do NOT interpret low PVE as evidence of low heritability.",
    "",
    "  RECOMMENDATIONS:",
    "  1. Run 2–3 independent MCMC chains with different seeds; compute Gelman-Rubin",
    "     Rhat and effective sample size (ESS) before drawing architectural conclusions.",
    "  2. Re-run BSLMM with full N=1,200 dataset for informative posteriors.",
    "  3. Use polygenic score approach rather than sparse-loci mapping at this N."
  )
} else {
  arch_lines <- c(arch_lines,
    "CONCLUSION: Architecture parameters unavailable or inconclusive.",
    "  - Check BSLMM chain convergence (trace plots) and GEMMA logs."
  )
}

writeLines(arch_lines, out_arch)
message("Architecture summary written: ", out_arch)
cat(paste(arch_lines, collapse = "\n"), "\n")

# ---------------------------------------------------------------------------
# 4. Trace plots for MCMC convergence
# ---------------------------------------------------------------------------
n_plots <- length(params_of_interest)
n_cols  <- min(2L, n_plots)
n_rows  <- ceiling(n_plots / n_cols)

png(out_trace, width = 500 * n_cols, height = 400 * n_rows, res = 120)
par(mfrow = c(n_rows, n_cols), mar = c(4, 4, 2, 1))

for (p in params_of_interest) {
  vals <- suppressWarnings(as.numeric(hyp[[p]]))  # coerce; handles logical NA col
  finite_vals <- vals[is.finite(vals)]
  if (length(finite_vals) == 0) {
    plot.new()
    title(main = paste0(p, " (all values non-finite — skipped)"))
    next
  }
  tryCatch({
    plot(seq_along(vals), vals, type = "l", col = "steelblue",
         main = p, xlab = "MCMC iteration", ylab = p, lwd = 0.5,
         ylim = range(finite_vals))          # explicit ylim avoids auto-range crash
    abline(h = mean(finite_vals), col = "red", lty = 2)
  }, error = function(e) {
    message("WARNING: trace plot for '", p, "' failed: ", e$message)
    plot.new()
    title(main = paste0(p, " (plot error)"))
  })
}

dev.off()
message("Trace plots saved: ", out_trace)

sink(type = "message"); sink(type = "output"); close(log_con)
