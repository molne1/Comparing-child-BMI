# calculate_r_bmi.R

# Calculates R-BMI (BMI at 18 years for a matched z-score) from a child dataset.
# Arguments:
#   df            : data.frame with at least sex, age, bmi columns
#   sex_column    : column name (string) where sex is coded as 1 (boy) or 2 (girl)
#   bmi_column    : column name (string) with BMI values
#   age_column    : column name (string) with age (months if age_in_months = TRUE; years otherwise)
#   age_in_months : logical, TRUE if age_column is in months, FALSE if in years
#
# Returns:
#   The same data.frame with a new column "R-BMI" containing the computed value or NA on failure.

calculate_r_bmi <- function(df, sex_column, bmi_column, age_column, age_in_months = TRUE) {

  # --- Load reference table from GitHub ---
  url <- "https://raw.githubusercontent.com/molne1/Comparing-child-BMI/refs/heads/main/assets/2024-05-14_RBMI_SD1SD2.csv"

  # Keep original column names (e.g., "SD-4", "SD0", "SD40")
  rbmi_ref <- tryCatch(
    read.csv(url, check.names = FALSE),
    error = function(e) {
      stop("Failed to read reference CSV from GitHub: ", conditionMessage(e))
    }
  )

  # Split by sex
  rbmi_boy_ref  <- subset(rbmi_ref, sex == 1)
  rbmi_girl_ref <- subset(rbmi_ref, sex == 2)

  # SD columns (z-score grid)
  sd_columns <- grep("^SD", names(rbmi_ref), value = TRUE)

  # Reference BMI at 18 years (216 months)
  SD_at_18_boy  <- rbmi_boy_ref[rbmi_boy_ref$age_months == 216, sd_columns, drop = FALSE]
  SD_at_18_girl <- rbmi_girl_ref[rbmi_girl_ref$age_months == 216, sd_columns, drop = FALSE]

  # Prepare result and issue tracking
  rbmi <- rep(NA_real_, nrow(df))
  rows_with_issues <- integer(0)

  # Helper: safe extraction & conversion
  get_numeric <- function(x) {
    val <- suppressWarnings(as.numeric(x))
    if (length(val) == 0 || is.na(val)) NA_real_ else val
  }
  get_integer <- function(x) {
    val <- suppressWarnings(as.integer(x))
    if (length(val) == 0 || is.na(val)) NA_integer_ else val
  }

  # Iterate rows
  for (i in seq_len(nrow(df))) {
    # Read inputs
    sex <- tryCatch(get_integer(df[i, sex_column]), error = function(e) NA_integer_)
    bmi <- tryCatch(get_numeric(df[i, bmi_column]), error = function(e) NA_real_)
    age_in <- tryCatch(df[i, age_column], error = function(e) NA_real_)

    if (is.na(sex)) {
      message("Row ", i, ": Missing/Unable to read column for sex")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }
    if (is.na(bmi)) {
      message("Row ", i, ": Missing/Unable to read column for BMI")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }

    if (isTRUE(age_in_months)) {
      age <- suppressWarnings(as.integer(age_in))
    } else {
      age <- suppressWarnings(as.integer(round(get_numeric(age_in) * 12)))
    }

    if (is.na(age)) {
      message("Row ", i, ": Missing/Unable to read column for age")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }
    if (age > 216L) {
      message("Row ", i, ": Individual is above 18 yrs of age")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }

    # Choose sex-specific reference
    ref <- NULL
    ref18 <- NULL
    if (sex == 1L) {
      ref <- rbmi_boy_ref
      ref18 <- SD_at_18_boy
    } else if (sex == 2L) {
      ref <- rbmi_girl_ref
      ref18 <- SD_at_18_girl
    } else {
      message("Row ", i, ": Invalid sex code (expected 1=boy or 2=girl)")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }

    # SD columns within this reference
    sd_cols <- grep("^SD", names(ref), value = TRUE)

    # Target z-score grid -4..40 (as in your Python code)
    sd_numbers <- seq(-4L, 40L, by = 1L)

    # If column count doesn't match, try to align by the suffix number
    if (length(sd_cols) != length(sd_numbers)) {
      parsed_nums <- suppressWarnings(as.integer(gsub("^SD", "", sd_cols)))
      ord <- order(parsed_nums)
      sd_cols <- sd_cols[ord]
      sd_numbers <- parsed_nums[ord]
    }

    # BMI values for the child's age across z-scores
    row_at_age <- ref[ref$age_months == age, sd_cols, drop = FALSE]
    if (nrow(row_at_age) < 1L) {
      message("Row ", i, ": No reference row for age_months = ", age)
      rows_with_issues <- c(rows_with_issues, i)
      next
    }
    bmi_values <- as.numeric(row_at_age[1, , drop = TRUE])

    # Remove NA pairs
    valid <- !is.na(bmi_values) & !is.na(sd_numbers)
    if (sum(valid) < 2L) {
      message("Row ", i, ": Not enough valid reference points to interpolate z-score")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }

    # Interpolate: BMI -> z-score (linear)
    # Note: rule = 1 returns NA outside range (mirrors Python error -> NA behavior)
    bmi_to_z <- tryCatch(approxfun(x = bmi_values[valid], y = sd_numbers[valid],
                                   method = "linear", rule = 1),
                         error = function(e) NULL)
    if (is.null(bmi_to_z)) {
      message("Row ", i, ": Failed to build BMI->z interpolation")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }

    z <- bmi_to_z(bmi)
    if (is.na(z)) {
      message("Row ", i, ": BMI outside reference range at age ", age)
      rows_with_issues <- c(rows_with_issues, i)
      next
    }
    z <- round(as.numeric(z), 2)

    # Interpolate: z-score -> BMI at 18 years
    bmi18_values <- as.numeric(ref18[1, sd_cols, drop = TRUE])
    valid2 <- !is.na(bmi18_values) & !is.na(sd_numbers)
    if (sum(valid2) < 2L) {
      message("Row ", i, ": Not enough valid 18y reference points to interpolate R-BMI")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }

    z_to_bmi18 <- tryCatch(approxfun(x = sd_numbers[valid2], y = bmi18_values[valid2],
                                     method = "linear", rule = 1),
                           error = function(e) NULL)
    if (is.null(z_to_bmi18)) {
      message("Row ", i, ": Failed to build z->BMI18 interpolation")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }

    rbmi_val <- z_to_bmi18(z)
    if (is.na(rbmi_val)) {
      message("Row ", i, ": z-score outside reference at 18 years")
      rows_with_issues <- c(rows_with_issues, i)
      next
    }

    rbmi[i] <- round(as.numeric(rbmi_val), 1)
  }

  df[["R-BMI"]] <- rbmi
  df
}
