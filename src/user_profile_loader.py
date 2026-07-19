"""
Finassist — User Profile Loader
Loads and parses user profiles from user_profiles.json.
"""
import json
from typing import Optional
from src.config import USER_PROFILES_PATH, format_inr


def load_all_profiles() -> dict:
    """Load the entire user profiles JSON file."""
    with open(USER_PROFILES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_user_profile(name: str) -> Optional[dict]:
    """Get a specific user's full profile by name."""
    data = load_all_profiles()
    for portfolio in data.get("portfolios", []):
        if portfolio.get("name", "").lower() == name.lower():
            return portfolio
    return None


def get_all_user_names() -> list[str]:
    """Get list of all user names."""
    data = load_all_profiles()
    return [p["name"] for p in data.get("portfolios", [])]


def get_portfolio_summary(name: str) -> str:
    """Generate a formatted portfolio summary string for a user."""
    profile = get_user_profile(name)
    if not profile:
        return f"User '{name}' not found."

    currency = profile.get("currency", "INR")
    total_value = profile.get("totalPortfolioValue", 0)

    summary_lines = [
        f"## Portfolio Summary — {profile['name']}",
        f"**Age:** {profile['age']} | **Occupation:** {profile['occupation']}",
        f"**Risk Profile:** {profile['riskProfile']}",
        f"**Total Portfolio Value:** {currency} {format_inr(total_value)}",
        "",
        "### Goals",
    ]
    for goal in profile.get("goals", []):
        summary_lines.append(f"- {goal}")

    summary_lines.append("")
    summary_lines.append("### Allocation")
    for key, alloc in profile.get("allocation", {}).items():
        pct = alloc.get("percentage", 0)
        val = alloc.get("value", 0)
        desc = alloc.get("description", "")
        summary_lines.append(f"- **{key}**: {pct}% (₹{format_inr(val)}) — {desc}")

    return "\n".join(summary_lines)


def get_holdings_flat(name: str) -> list[dict]:
    """Extract all holdings as a flat list with fund names and metadata."""
    profile = get_user_profile(name)
    if not profile:
        return []

    holdings = profile.get("holdings", {})
    flat = []
    for category, items in holdings.items():
        if isinstance(items, list):
            for item in items:
                item_copy = dict(item)
                item_copy["holding_category"] = category
                flat.append(item_copy)
    return flat


def get_fund_names_for_search(name: str) -> list[str]:
    """Get all fund/scheme names from a user's holdings for MFapi search."""
    holdings = get_holdings_flat(name)
    fund_names = []
    for h in holdings:
        fund_name = h.get("name", "")
        if fund_name and "Fund" in fund_name:
            fund_names.append(fund_name)
    return fund_names


if __name__ == "__main__":
    # Quick test
    print(get_portfolio_summary("Sushil"))
    print("\n--- Fund Names ---")
    for fn in get_fund_names_for_search("Sushil"):
        print(f"  {fn}")
