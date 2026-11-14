"""Creates a 10,000-row customer table with typical data quality problems
(missing values, duplicates, invalid emails, impossible ages, mixed date/number formats)."""

import os
import numpy as np
import pandas as pd

RNG = np.random.default_rng(99)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

N = 10000
CITIES = ["Lefkoşa", "Girne", "Gazimağusa", "Güzelyurt", "İskele", "lefkosa", "GIRNE", " Girne "]
FIRST = ["Ayşe", "Mehmet", "Fatma", "Ali", "Zeynep", "Mustafa", "Elif", "Can", "Deniz", "Burak"]
LAST = ["Yılmaz", "Demir", "Kaya", "Çelik", "Şahin", "Arslan", "Doğan", "Koç"]
TO_ASCII = str.maketrans("ışçöüğ", "iscoug")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    rows = []
    for i in range(N):
        name = f"{RNG.choice(FIRST)} {RNG.choice(LAST)}"
        email = f"{name.lower().replace(' ', '.').translate(TO_ASCII)}{RNG.integers(1, 999)}@example.com"

        y, m, d = int(RNG.integers(2021, 2026)), int(RNG.integers(1, 13)), int(RNG.integers(1, 28))
        date_fmt = RNG.choice(["iso", "slash", "dot"])
        if date_fmt == "iso":
            signup = f"{y:04d}-{m:02d}-{d:02d}"
        elif date_fmt == "slash":
            signup = f"{d:02d}/{m:02d}/{y:04d}"
        else:
            signup = f"{d:02d}.{m:02d}.{y:04d}"

        spend = f"{float(RNG.uniform(0, 5000)):.2f}"
        spend_fmt = RNG.choice(["plain", "comma", "tl"])
        if spend_fmt == "comma":
            spend = spend.replace(".", ",")
        elif spend_fmt == "tl":
            spend = f"{spend} TL"

        rows.append({
            "customer_id": 1000 + i,
            "full_name": name,
            "email": email,
            "city": RNG.choice(CITIES),
            "signup_date": signup,
            "total_spend": spend,
            "age": int(RNG.integers(18, 80)),
        })
    df = pd.DataFrame(rows)

    for col in ["email", "city", "signup_date", "total_spend"]:
        idx = RNG.choice(df.index, size=int(N * 0.025), replace=False)
        df.loc[idx, col] = np.nan

    idx = RNG.choice(df.index, size=40, replace=False)
    df.loc[idx, "age"] = RNG.choice([-5, 0, 150, 999, 220], size=40)

    dup = df.sample(n=int(N * 0.012), random_state=1)
    df = pd.concat([df, dup], ignore_index=True)

    idx = RNG.choice(df.index, size=120, replace=False)
    df.loc[idx, "email"] = "not-an-email"

    df = df.sample(frac=1, random_state=3).reset_index(drop=True)
    df.to_csv(os.path.join(DATA_DIR, "customers_raw.csv"), index=False)
    print(f"{len(df):,} rows written")


if __name__ == "__main__":
    main()
