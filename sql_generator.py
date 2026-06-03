"""
SQL Generator - Week 1, Day 4
Pass a plain-English business question + table schema to Claude, get back a SQL query.
"""

import anthropic
import os

# ── CONFIG ───────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL   = "claude-sonnet-4-6"
# ─────────────────────────────────────────────────────────────────────────────

# ── SCHEMA ───────────────────────────────────────────────────────────────────
# Define your table schema here — update this when you switch datasets
SCHEMA = """
Table: events
Columns:
  - event_time     (TIMESTAMP)  : when the event occurred
  - event_type     (VARCHAR)    : one of 'view', 'cart', 'purchase'
  - product_id     (BIGINT)     : unique product identifier
  - category_id    (BIGINT)     : category identifier
  - category_code  (VARCHAR)    : human-readable category (e.g. electronics.video.tv)
  - brand          (VARCHAR)    : product brand (e.g. samsung, lg, apple)
  - price          (FLOAT)      : product price in USD
  - user_id        (BIGINT)     : unique user identifier
  - user_session   (VARCHAR)    : session identifier per user visit
"""
# ─────────────────────────────────────────────────────────────────────────────


def build_prompt(question: str) -> str:
    """Build the prompt to send to Claude."""
    prompt = f"""You are a senior data analyst and SQL expert. Given a table schema and a business question, write a clean, optimized SQL query.

## Table Schema
{SCHEMA}

## Business Question
{question}

## Instructions
- Write a single SQL query that answers the question completely - use a subquery and with clause if needed - return the output in a clean format.
- Do not suggest follow-up analyses or add unrequested sections
- Use NULLIF to avoid division by zero in any rate calculations
- Include all relevant funnel stages (view, cart, purchase) where applicable
- Add brief inline comments for any non-obvious logic
- Format the SQL cleanly with consistent indentation
- Give the best appropriate query which makes the most sense. 
- For all conversion rate calculations, deduplicate at user_session level using COUNT(DISTINCT user_session). Do not switch to user_id or user-product deduplication unless explicitly asked.
- After the query, write 2 sentences max explaining what the query returns and any assumptions made
- If a categorical column like brand, category_code is null, then mark it as 'unknown' and include it in analysis

Return the SQL query first, then the explanation. Nothing else."""

    return prompt


def generate_sql(question: str) -> None:
    """Send question to Claude and print the SQL query."""
    client = anthropic.Anthropic(api_key=API_KEY)
    prompt = build_prompt(question)

    print(f"\nQuestion: {question}")
    print("=" * 60)

    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system="You are a senior data analyst and SQL expert. Be precise and concise.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    print(message.content[0].text)
    print("=" * 60)


# ── QUESTIONS ────────────────────────────────────────────────────────────────
# Add or edit questions here — run the script to generate SQL for all of them
QUESTIONS = [
    "What is the full funnel conversion rate (view to cart to purchase) by brand?",
    "Which top 10 products have the highest view count but zero purchases?",
    "What is the average session length (number of events) by event type?",
]
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    for question in QUESTIONS:
        generate_sql(question)