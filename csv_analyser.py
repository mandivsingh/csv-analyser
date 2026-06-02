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
    # Sample to keep prompt size manageable
    df_sample = df.sample(n=10000, random_state=42)
    
    stats           = df_sample.describe().round(2).to_string()
    dtypes          = df.dtypes.to_string()
    null_counts     = df.isnull().sum().to_string()
    sample          = df.head(3).to_string()
    top_sessions    = df.groupby('user_session').size().sort_values(ascending=False).head(5).to_string()
    event_breakdown = df['event_type'].value_counts(normalize=True).mul(100).round(2).to_string()
    price_outliers  = df[['price', 'brand', 'category_code']].sort_values(by='price', ascending=False).head(5).to_string()

    prompt = f"""You are a senior data analyst reviewing an e-commerce event dataset. Here is the metadata:
 
## Column Data Types
{dtypes}
 
## Null Counts Per Column
{null_counts}
 
## Summary Statistics (df.describe)
{stats}
 
## First 3 Rows (Sample)
{sample}
 
## Event Type Breakdown (% of total events)
{event_breakdown}
 
## Top 5 Sessions by Event Count (bot/outlier check)
{top_sessions}
 
## Top 5 Most Expensive Items
{price_outliers}
 
Based on this, provide:
 
1. TOP 3 INSIGHTS — specific, business-relevant observations.
   For each insight: state what you see → benchmark it against e-commerce industry norms → explain why it matters → recommend one concrete action.
   Do not hedge. No filler.
 
2. TOP 3 RECOMMENDED ANALYSES — concrete next steps.
   For each: name the method, columns involved, and the business decision it would inform.
 
3. DATA QUALITY FLAGS — flag anything suspicious: high nulls, outlier sessions, unexpected value ranges, type issues.
   For each flag: state the issue → assess severity (low/medium/high) → recommend fix.
 
Analyst tone. Be specific. No generic observations."""

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
        max_tokens=2000,
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