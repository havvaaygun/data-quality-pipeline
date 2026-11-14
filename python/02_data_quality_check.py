"""Profiles customers_raw.csv, writes customers_clean.csv and a data quality report."""

import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
REPORTS = os.path.join(ROOT, "reports")
CHARTS = os.path.join(REPORTS, "charts")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
AGE_MIN, AGE_MAX = 18, 100

CITIES = ["Lefkoşa", "Girne", "Gazimağusa", "Güzelyurt", "İskele"]
TO_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def city_key(v):
    return str(v).strip().translate(TO_ASCII).lower()


CITY_MAP = {city_key(c): c for c in CITIES}


def parse_date(v):
    if pd.isna(v):
        return pd.NaT
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return pd.to_datetime(str(v).strip(), format=fmt)
        except ValueError:
            pass
    return pd.NaT


def parse_spend(v):
    if pd.isna(v):
        return np.nan
    s = str(v).upper().replace("TL", "").strip().replace(",", ".")
    try:
        return round(float(s), 2)
    except ValueError:
        return np.nan


def clean_city(v):
    if pd.isna(v):
        return np.nan
    return CITY_MAP.get(city_key(v), str(v).strip())


def is_email(v):
    return pd.notna(v) and bool(EMAIL_RE.match(str(v)))


def find_issues(raw):
    n = len(raw)
    issues = []
    for col, cnt in raw.isna().sum().items():
        if cnt:
            issues.append(("Missing values", col, int(cnt), f"{100 * cnt / n:.1f}% of rows null"))

    dups = int(raw.duplicated().sum())
    if dups:
        issues.append(("Duplicate rows", "all columns", dups, "exact duplicate records"))

    bad_email = int((raw["email"].notna() & ~raw["email"].apply(is_email)).sum())
    if bad_email:
        issues.append(("Invalid format", "email", bad_email, "does not match email pattern"))

    bad_age = int(((raw["age"] < AGE_MIN) | (raw["age"] > AGE_MAX)).sum())
    if bad_age:
        issues.append(("Out of range", "age", bad_age, f"age outside [{AGE_MIN}, {AGE_MAX}]"))

    non_iso = int((~raw["signup_date"].dropna().astype(str).str.match(ISO_DATE_RE)).sum())
    if non_iso:
        issues.append(("Inconsistent format", "signup_date", non_iso, "non-ISO date format"))

    spend = raw["total_spend"].dropna().astype(str)
    messy_spend = int((spend.str.contains(",") | spend.str.upper().str.contains("TL")).sum())
    if messy_spend:
        issues.append(("Inconsistent format", "total_spend", messy_spend, "comma decimal / currency suffix"))

    report = pd.DataFrame(issues, columns=["issue_type", "column", "records_affected", "description"])
    return report.sort_values("records_affected", ascending=False)


def clean(raw):
    df = raw.drop_duplicates().copy()
    df["signup_date"] = df["signup_date"].apply(parse_date).dt.date
    df["total_spend"] = df["total_spend"].apply(parse_spend)
    df["city"] = df["city"].apply(clean_city)
    df.loc[(df["age"] < AGE_MIN) | (df["age"] > AGE_MAX), "age"] = np.nan
    df.loc[~df["email"].apply(is_email), "email"] = np.nan
    return df


def main():
    os.makedirs(CHARTS, exist_ok=True)
    raw = pd.read_csv(os.path.join(DATA_DIR, "customers_raw.csv"))
    report = find_issues(raw)
    cleaned = clean(raw)

    cleaned.to_csv(os.path.join(DATA_DIR, "customers_clean.csv"), index=False)
    report.to_csv(os.path.join(REPORTS, "data_quality_report.csv"), index=False)

    missing = raw.isna().sum()
    missing = missing[missing > 0].sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(missing.index, missing.values, color="#C0392B")
    ax.set_title("Kolon Bazında Eksik Değer Sayısı (ham veri)", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "missing_values.png"), dpi=130)
    plt.close(fig)

    completeness = 100 * (1 - raw.isna().sum().sum() / raw.size)
    print(f"raw rows {len(raw):,} | clean rows {len(cleaned):,} | completeness {completeness:.1f}%")
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
