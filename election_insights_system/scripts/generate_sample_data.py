"""
Generate synthetic but realistic election datasets.

Outputs (CSV + JSON) under data/sample_data/:
  - constituencies
  - candidates
  - voting_data            (>= 5000 rows)
  - party_performance
  - social_sentiment

Run:
    python scripts/generate_sample_data.py
"""
from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "sample_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATES = {
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Trichy"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Noida"],
    "West Bengal": ["Kolkata", "Howrah", "Siliguri", "Durgapur"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
}

PARTIES = ["INC", "BJP", "AAP", "TMC", "SP", "DMK", "Independent", "NCP", "BSP"]
EDUCATION = ["10th", "12th", "Graduate", "Post Graduate", "Doctorate"]
TRENDING_TOPICS = [
    "economy", "unemployment", "inflation", "farmers", "healthcare",
    "education", "women_safety", "infrastructure", "corruption", "minority_rights",
]
ELECTION_YEARS = [2014, 2019, 2024]


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------
def gen_constituencies(n_per_district: int = 4) -> pd.DataFrame:
    rows = []
    cid = 1
    for state, districts in STATES.items():
        for d in districts:
            for i in range(n_per_district):
                total = int(np.random.normal(1_500_000, 350_000))
                total = max(400_000, total)
                male_pct = np.random.uniform(0.48, 0.53)
                male = int(total * male_pct)
                female = total - male
                urban = round(np.random.uniform(20, 95), 2)
                rural = round(100 - urban, 2)
                rows.append({
                    "constituency_id": f"C{cid:04d}",
                    "constituency_name": f"{d}-{i + 1}",
                    "state": state,
                    "district": d,
                    "total_voters": total,
                    "male_voters": male,
                    "female_voters": female,
                    "urban_percentage": urban,
                    "rural_percentage": rural,
                })
                cid += 1
    return pd.DataFrame(rows)


def gen_candidates(constituencies: pd.DataFrame, per_constituency: int = 5) -> pd.DataFrame:
    rows = []
    cid = 1
    first_names = ["Arjun", "Rohan", "Priya", "Sneha", "Amit", "Vikram", "Anjali",
                   "Sunita", "Rahul", "Kiran", "Manoj", "Pooja", "Ravi", "Asha", "Deepak"]
    last_names = ["Sharma", "Patel", "Kumar", "Reddy", "Iyer", "Singh", "Nair",
                  "Das", "Gupta", "Joshi", "Mehta", "Rao", "Banerjee", "Chowdhury"]
    for _, c in constituencies.iterrows():
        # Use a subset of parties per constituency (more realistic)
        parties_here = random.sample(PARTIES, per_constituency)
        for p in parties_here:
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            age = int(np.clip(np.random.normal(52, 11), 25, 85))
            cases = int(np.random.choice([0, 0, 0, 1, 2, 3, 5, 8], p=[0.45, 0.15, 0.1, 0.1, 0.08, 0.05, 0.04, 0.03]))
            # Assets in INR (log-normal-ish): 1L to 100Cr
            assets = int(np.clip(np.random.lognormal(mean=15.5, sigma=1.3), 1e5, 1e9))
            rows.append({
                "candidate_id": f"K{cid:05d}",
                "candidate_name": name,
                "party": p,
                "constituency": c["constituency_name"],
                "age": age,
                "education": random.choices(EDUCATION, weights=[5, 10, 45, 30, 10])[0],
                "criminal_cases": cases,
                "assets": assets,
                "incumbency": bool(random.random() < 0.18),
            })
            cid += 1
    return pd.DataFrame(rows)


def gen_voting_data(constituencies: pd.DataFrame, booths_per_constituency: int = 30) -> pd.DataFrame:
    rows = []
    base_ts = datetime(2024, 5, 13, 7, 0, 0)
    for _, c in constituencies.iterrows():
        # baseline turnout per constituency (rural slightly higher)
        rural_bias = (c["rural_percentage"] - 50) * 0.05
        base_turnout = float(np.clip(np.random.normal(62 + rural_bias, 6), 35, 92))
        for b in range(booths_per_constituency):
            # Most booths cluster around base; some spikes/dips for anomalies
            spike = np.random.choice([0, 0, 0, 0, 8, -10, 15], p=[0.6, 0.1, 0.05, 0.05, 0.08, 0.06, 0.06])
            turnout = float(np.clip(np.random.normal(base_turnout + spike, 4), 10, 99))
            booth_voters = int(np.random.normal(1100, 220))
            booth_voters = max(300, booth_voters)
            votes_cast = int(booth_voters * turnout / 100)
            nota = int(votes_cast * np.random.uniform(0.005, 0.06))
            ts = base_ts + timedelta(minutes=int(np.random.uniform(0, 11 * 60)))
            rows.append({
                "constituency": c["constituency_name"],
                "polling_booth": f"{c['constituency_id']}-B{b + 1:03d}",
                "votes_cast": votes_cast,
                "turnout_percentage": round(turnout, 2),
                "NOTA_votes": nota,
                "timestamp": ts.isoformat(),
            })
    return pd.DataFrame(rows)


def gen_party_performance() -> pd.DataFrame:
    rows = []
    for year in ELECTION_YEARS:
        for state in STATES:
            # distribute seats among parties for that state/year
            seats_total = random.randint(20, 80)
            shares = np.random.dirichlet(np.ones(len(PARTIES)) * 1.2)
            seat_dist = (shares * seats_total).astype(int)
            # Fix rounding so it sums right
            diff = seats_total - seat_dist.sum()
            seat_dist[0] += diff
            vote_shares = (shares * 100).round(2)
            for party, seats, vs in zip(PARTIES, seat_dist, vote_shares):
                rows.append({
                    "party": party,
                    "seats_won": int(seats),
                    "vote_share": float(vs),
                    "state": state,
                    "election_year": year,
                })
    return pd.DataFrame(rows)


def gen_social_sentiment(days: int = 60) -> pd.DataFrame:
    rows = []
    start = datetime(2024, 3, 1)
    for d in range(days):
        date = start + timedelta(days=d)
        for p in PARTIES:
            base = np.random.randint(200, 2000)
            pos = int(base * np.random.uniform(0.3, 0.6))
            neg = int(base * np.random.uniform(0.2, 0.5))
            neu = max(50, base - pos - neg)
            topics = random.sample(TRENDING_TOPICS, k=random.randint(2, 4))
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "party": p,
                "positive_mentions": pos,
                "negative_mentions": neg,
                "neutral_mentions": neu,
                "trending_topics": ",".join(topics),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------
def save(df: pd.DataFrame, name: str) -> None:
    csv_path = OUT_DIR / f"{name}.csv"
    json_path = OUT_DIR / f"{name}.json"
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)
    print(f"  {name:22s} rows={len(df):>6}  -> {csv_path.name}, {json_path.name}")


def main() -> None:
    print(f"Writing sample data to: {OUT_DIR}")

    constituencies = gen_constituencies(n_per_district=4)
    save(constituencies, "constituencies")

    candidates = gen_candidates(constituencies, per_constituency=5)
    save(candidates, "candidates")

    voting = gen_voting_data(constituencies, booths_per_constituency=35)
    save(voting, "voting_data")

    party_perf = gen_party_performance()
    save(party_perf, "party_performance")

    sentiment = gen_social_sentiment(days=60)
    save(sentiment, "social_sentiment")

    # Manifest for easy inspection
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "counts": {
            "constituencies": len(constituencies),
            "candidates": len(candidates),
            "voting_data": len(voting),
            "party_performance": len(party_perf),
            "social_sentiment": len(sentiment),
        },
    }
    with open(OUT_DIR / "_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("Done.")


if __name__ == "__main__":
    main()
