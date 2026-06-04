"""
Tool Use - Week 2, Day 1
Claude decides when to call a function, you execute it, Claude interprets the result.
Cost-optimised: truncated results, low max_tokens, single question at a time.
"""

import anthropic
import pandas as pd
import os
import time

# ── CONFIG ───────────────────────────────────────────────────────────────────
API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL    = "claude-sonnet-4-6"
CSV_PATH = r"D:\Projects\CSV_ANALYSER\events.csv"

# ── COST CONTROLS ─────────────────────────────────────────────────────────────
MAX_RESULT_LINES = 30   # Truncate tool results before sending back to Claude
MAX_TOKENS       = 800  # Keep responses short
# ─────────────────────────────────────────────────────────────────────────────

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
print("Loading dataset...")
df = pd.read_csv(CSV_PATH)
print(f"✓ Loaded {df.shape[0]:,} rows\n")
# ─────────────────────────────────────────────────────────────────────────────


# ── TOOL DEFINITION ──────────────────────────────────────────────────────────
tools = [
    {
        "name": "run_analysis",
        "description": (
            "Runs pandas code on the e-commerce events dataset and returns the result. "
            "The dataset is loaded as `df`. "
            "Available columns: event_time, event_type, product_id, category_id, "
            "category_code, brand, price, user_id, user_session."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Pandas code to run on `df`. Single expression returns directly. Multi-line code must assign final output to a variable called `result`."
                },
                "explanation": {
                    "type": "string",
                    "description": "One sentence explaining what this code computes."
                }
            },
            "required": ["code", "explanation"]
        }
    }
]
# ─────────────────────────────────────────────────────────────────────────────


# ── TOOL EXECUTOR ─────────────────────────────────────────────────────────────
def run_analysis(code: str) -> str:
    """Execute pandas code and return truncated result as string."""
    try:
        local_vars = {"df": df, "pd": pd, "result": None}
        try:
            result = eval(code, local_vars)
        except SyntaxError:
            exec(code, local_vars)
            result = local_vars.get("result")
        if isinstance(result, (pd.DataFrame, pd.Series)):
            full = result.to_string()
        else:
            full = str(result)
        # Truncate to MAX_RESULT_LINES to control token cost
        lines = full.split("\n")
        if len(lines) > MAX_RESULT_LINES:
            full = "\n".join(lines[:MAX_RESULT_LINES]) + f"\n... ({len(lines) - MAX_RESULT_LINES} more rows truncated)"
        return full
    except Exception as e:
        return f"Error: {str(e)}"
# ─────────────────────────────────────────────────────────────────────────────


# ── AGENT LOOP ────────────────────────────────────────────────────────────────
def ask(question: str) -> None:
    """Send a question to Claude, let it call tools, return final answer."""
    client = anthropic.Anthropic(api_key=API_KEY)

    print(f"Question: {question}")
    print("=" * 60)

    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=(
                "You are a senior data analyst. Use the run_analysis tool to answer questions. "
                "Be concise. Show key numbers only. No filler."
            ),
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"→ Running: {block.input.get('explanation', '')}")
                    result = run_analysis(block.input["code"])
                    print(f"→ Result:\n{result}\n")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"Answer:\n{block.text}")
            break

        else:
            print(f"Unexpected stop reason: {response.stop_reason}")
            break

    print("=" * 60)


# ── RUN ONE QUESTION AT A TIME ────────────────────────────────────────────────
# Comment/uncomment the question you want to run — don't run all at once
QUESTION = "Which brand has the highest cart to purchase conversion rate? Only include brands with more than 1000 view sessions."
# QUESTION = "What are the top 5 most viewed products that have never been purchased?"
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    ask(QUESTION)