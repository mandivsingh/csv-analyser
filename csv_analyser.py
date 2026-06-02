"""
CSV Analyser - Week 1, Day 2
Loads a CSV, sends df.describe() to Claude API, returns top insights + recommended analyses.
"""

import anthropic
import pandas as pd
import sys

# ── CONFIG ──────────────────────────────────────────────────────────────────
import os
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL    = "claude-sonnet-4-6"
CSV_PATH = r"D:\Projects\CSV_ANALYSER\events.csv"   # Hardcoded — change filename if needed
# ────────────────────────────────────────────────────────────────────────────


def load_csv(filepath: str) -> pd.DataFrame:
    """Load CSV and return a DataFrame."""
    try:
        df = pd.read_csv(filepath)
        print(f"✓ Loaded: {filepath}")
        print(f"  Shape : {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"  Cols  : {list(df.columns)}\n")
        return df
    except FileNotFoundError:
        print(f"✗ File not found: {filepath}")
        sys.exit(1)


def build_prompt(df: pd.DataFrame) -> str:
    """Build the prompt payload to send to Claude."""
    stats       = df.describe(include="all").to_string()
    dtypes      = df.dtypes.to_string()
    null_counts = df.isnull().sum().to_string()
    sample      = df.head(3).to_string()

    prompt = f"""You are a senior data analyst reviewing a dataset. Here is the metadata:

## Column Data Types
{dtypes}

## Null Counts Per Column
{null_counts}

## Summary Statistics (df.describe)
{stats}

## First 3 Rows (Sample)
{sample}

Based on this, provide:

1. TOP 3 INSIGHTS — specific, business-relevant observations from the data as-is.
   Do not hedge. State what you see clearly.

2. TOP 3 RECOMMENDED ANALYSES — concrete next-step analyses worth running.
   Each recommendation should name the method, the columns involved, and why it matters.

3. DATA QUALITY FLAGS — anything suspicious: skewed distributions, high nulls,
   unexpected value ranges, potential duplicates.

Be concise. Analyst tone. No filler sentences."""

    return prompt


def analyse(filepath: str) -> None:
    """Main function: load CSV → call Claude → print results."""
    df     = load_csv(filepath)
    prompt = build_prompt(df)

    client = anthropic.Anthropic(api_key=API_KEY)

    print("Sending to Claude API...\n")
    print("=" * 60)

    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system="You are a senior data analyst. Be direct, specific, and concise.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    print(message.content[0].text)
    print("=" * 60)


# ── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Use hardcoded CSV_PATH — no command line argument needed
    analyse(CSV_PATH)