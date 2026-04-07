# cost.py — Cost calculations and savings dashboard
#
# HOW DO WE MEASURE SAVINGS?
# We compare what we actually spent vs. what we WOULD have spent
# if every single prompt had gone to GPT-4o.
#
# Example:
#   20 simple prompts via Phi-3   = $0.00
#   15 medium prompts via Llama3  = $0.00
#   7  complex prompts via GPT-4o = $0.07
#   Total actual cost             = $0.07
#
#   If all 42 went to GPT-4o at ~$0.003 each = $0.126
#   Money saved = $0.126 - $0.07 = $0.056 (44% savings!)

from app.database import get_stats

# Average cost per GPT-4o request (based on ~200 input + 300 output tokens)
GPT4O_COST_PER_REQUEST = 0.003   # $0.003 = about 0.3 cents per request


def get_dashboard() -> dict:
    """
    Calculate cost savings and return a summary for the dashboard.
    """
    stats = get_stats()

    total_requests = stats["total_requests"]
    actual_cost    = stats["actual_cost"]

    # What would it have cost if every request went to GPT-4o?
    cost_if_all_gpt4o = round(total_requests * GPT4O_COST_PER_REQUEST, 6)

    # How much did we save?
    money_saved = round(cost_if_all_gpt4o - actual_cost, 6)

    # Savings as a percentage
    if cost_if_all_gpt4o > 0:
        savings_percent = round((money_saved / cost_if_all_gpt4o) * 100, 1)
    else:
        savings_percent = 0.0

    return {
        "total_requests":     total_requests,
        "by_tier":            stats["by_tier"],
        "actual_cost_usd":    actual_cost,
        "cost_if_all_gpt4o":  cost_if_all_gpt4o,
        "money_saved_usd":    money_saved,
        "savings_percent":    savings_percent,
    }
