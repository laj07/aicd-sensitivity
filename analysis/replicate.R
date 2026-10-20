# Independent replication of the AICD/Mandala three-method estimate in base R.
# Reads data/inputs.csv (the same file the Python model uses) and re-computes the methods
# and the regression interval, so the Python and R results can be checked against each other.
# Run from the repo root:  Rscript analysis/replicate.R

inp <- read.csv("data/inputs.csv", stringsAsFactors = FALSE)
p <- setNames(as.list(inp$value), inp$id)

cx_keys <- c("cx_notional", "cx_structural", "cx_penalty",
             "cx_defined", "cx_instruments", "cx_interconnect")

run_model <- function(p, os_hours = p$os_hours) {
  base_proj <- p$gdp_share_2013 * p$gdp_2024
  vol_mult  <- p$pages_2024 / p$pages_2013
  cx_mult   <- 1 + mean(unlist(p[cx_keys]))
  cpi_mult  <- 1 + p$cpi_2013_24
  role_mult <- p$roles_2024 / p$roles_2013
  oh <- p$oh_mult - 1

  m1 <- base_proj * vol_mult * cx_mult
  m2 <- p$base_2013 * cpi_mult * role_mult

  cw_labour <- p$cw_workers * p$fte * p$cw_salary / 1e9
  il <- p$il_workers * p$fte * p$il_salary * p$il_share / 1e9
  ia <- p$ia_workers * p$fte * p$ia_salary * p$ia_share / 1e9
  os_labour <- (os_hours * p$os_workers - p$os_excl) * p$os_wage / 1e9
  items <- c(
    cw_labour, cw_labour * oh, il, ia, (il + ia) * oh,
    os_labour, os_labour * oh,
    p$it_spend * p$it_share,
    p$el_workers * p$fte * p$el_rev * p$el_share / 1e9,
    p$ea_fees / p$ea_div * p$ea_share
  )
  m3 <- sum(items) - p$state_share_gsp * p$gsp_total
  c(m1 = m1, m2 = m2, m3 = m3, headline = (m1 + m2 + m3) / 3)
}

base <- run_model(p)
cat("Recomputed from printed inputs (AUD bn):\n")
print(round(base, 1))

cat("\nPrinted by the report: M1 190, M2 150, M3 ~130, headline 159\n")

cat("\nOther-staff hours at 60 instead of 87:\n")
print(round(run_model(p, os_hours = 60), 1))

# Regression: back the standard error out of the printed p-value (two-sided, normal approximation)
z  <- qnorm(1 - p$reg_p / 2)
se <- abs(p$reg_coef) / z
ci <- p$reg_coef + c(-1, 1) * 1.96 * se
cat(sprintf("\nRegression: coef %.1f, p = %.2f -> implied SE %.1f, 95%% CI [%.1f, %.1f]\n",
            p$reg_coef, p$reg_p, se, ci[1], ci[2]))
cat(sprintf("Interval includes zero: %s\n", ci[1] < 0 && ci[2] > 0))
