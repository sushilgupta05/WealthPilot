"""
Finassist — Fund Corpus Builder
Fetches real data from MFapi.in and generates structured fund fact sheet
documents for the RAG corpus. Each fact sheet is a text file with standardized
sections: overview, NAV, returns, holdings, risk, and investment suitability.
"""
import json
from pathlib import Path
from src.config import FUND_CORPUS_DIR, DEFAULT_USER
from src.data_fetcher import (
    MFApiClient,
    calculate_returns,
    search_and_get_best_match,
    KNOWN_SCHEME_CODES,
)
from src.user_profile_loader import get_user_profile, get_holdings_flat


# ── Additional popular funds to enrich the corpus ────────────────────────
ADDITIONAL_FUNDS_FOR_CORPUS = [
    "UTI Nifty 50 Index Fund",
    "Parag Parikh Flexi Cap Fund",
    "Nippon India Small Cap Fund",
    "Mirae Asset Large Cap Fund",
    "Kotak Equity Opportunities Fund",
    "SBI Small Cap Fund",
    "HDFC Flexi Cap Fund",
    "ICICI Prudential Value Discovery Fund",
]

# Risk classification based on category keywords
RISK_MAP = {
    "large cap": "Moderately Low",
    "index": "Low",
    "flexi cap": "Moderate",
    "multi cap": "Moderate",
    "mid cap": "Moderately High",
    "small cap": "High",
    "sector": "High",
    "technology": "High",
    "liquid": "Very Low",
    "low duration": "Low",
    "short duration": "Low",
    "savings": "Very Low",
    "balanced": "Moderate",
    "hybrid": "Moderate",
    "elss": "Moderate to High",
    "debt": "Low",
    "bond": "Low to Moderate",
    "conservative": "Low",
    "dynamic": "Moderate",
    "value": "Moderate to High",
}


def classify_risk(category: str, scheme_name: str) -> str:
    """Classify fund risk based on category and scheme name keywords."""
    combined = (category + " " + scheme_name).lower()
    for keyword, risk in RISK_MAP.items():
        if keyword in combined:
            return risk
    return "Moderate"


def build_fact_sheet_text(
    meta: dict,
    nav_history: list,
    returns: dict,
    holding_info: dict = None,
) -> str:
    """
    Generate a structured fund fact sheet as plain text.
    This will be chunked and embedded for RAG retrieval.
    """
    fund_house = meta.get("fund_house", "N/A")
    scheme_name = meta.get("scheme_name", "N/A")
    scheme_category = meta.get("scheme_category", "N/A")
    scheme_type = meta.get("scheme_type", "N/A")
    scheme_code = meta.get("scheme_code", "N/A")
    isin = meta.get("isin_growth", "N/A")

    # Latest NAV
    latest_nav = nav_history[0]["nav"] if nav_history else "N/A"
    latest_date = nav_history[0]["date"] if nav_history else "N/A"

    # Risk
    risk_level = classify_risk(scheme_category, scheme_name)

    # Expense ratio and top holdings from user profile data if available
    expense_ratio = "N/A"
    top_holdings_str = "N/A"
    expected_return_str = "N/A"
    allocation_pct = "N/A"
    amount_invested = "N/A"

    if holding_info:
        expense_ratio = holding_info.get("expense_ratio", "N/A")
        if expense_ratio != "N/A":
            expense_ratio = f"{expense_ratio}%"
        top_holdings = holding_info.get("topHoldings", [])
        if top_holdings:
            top_holdings_str = ", ".join(str(h) for h in top_holdings)
        expected_return_str = holding_info.get("expected_return", "N/A")
        allocation_pct = holding_info.get("allocation_pct", "N/A")
        amount_val = holding_info.get("amount", None)
        if amount_val:
            amount_invested = f"INR {amount_val:,.0f}"

    # Returns formatting
    return_1y = f"{returns.get('1_year', 'N/A')}%" if '1_year' in returns else "N/A"
    return_3y = f"{returns.get('3_year', 'N/A')}% CAGR" if '3_year' in returns else "N/A"
    return_5y = f"{returns.get('5_year', 'N/A')}% CAGR" if '5_year' in returns else "N/A"

    # Determine if this is a low-cost fund
    low_cost_tag = ""
    if holding_info and holding_info.get("expense_ratio"):
        er = holding_info["expense_ratio"]
        if isinstance(er, (int, float)) and er < 0.5:
            low_cost_tag = " [LOW-COST FUND]"

    # Build the fact sheet
    fact_sheet = f"""
================================================================================
FUND FACT SHEET: {scheme_name}{low_cost_tag}
================================================================================

OVERVIEW
--------
Fund Name:        {scheme_name}
Fund House:       {fund_house}
Scheme Category:  {scheme_category}
Scheme Type:      {scheme_type}
AMFI Code:        {scheme_code}
ISIN:             {isin}
Risk Level:       {risk_level}

NAV INFORMATION
---------------
Latest NAV:       ₹{latest_nav} (as of {latest_date})

HISTORICAL RETURNS (Calculated from NAV data)
----------------------------------------------
1-Year Return:    {return_1y}
3-Year Return:    {return_3y}
5-Year Return:    {return_5y}

Note: Past performance is not indicative of future results. Returns are
calculated based on historical NAV data and may differ from officially
published returns due to data availability and calculation methodology.

EXPENSE RATIO
-------------
Total Expense Ratio (TER): {expense_ratio}

{"LOW-COST FUND INDICATOR: This fund has an expense ratio below 0.5%, making it one of the most cost-efficient options in its category. Lower expense ratios mean more of your investment returns stay with you over the long term." if low_cost_tag else ""}

TOP HOLDINGS
------------
{top_holdings_str}

EXPECTED RETURN RANGE
---------------------
Expected Annual Return: {expected_return_str}

INVESTMENT IN PORTFOLIO
-----------------------
Amount Invested:    {amount_invested}
Portfolio Weight:   {allocation_pct}%

RISK CLASSIFICATION
-------------------
Risk Level: {risk_level}
{"This fund carries HIGH RISK and is suitable for investors with a high risk appetite and long investment horizon (7+ years)." if risk_level in ("High", "Moderately High") else ""}
{"This fund carries MODERATE RISK and is suitable for investors with a balanced approach to risk and a medium to long investment horizon (5+ years)." if risk_level == "Moderate" else ""}
{"This fund carries LOW RISK and is suitable for conservative investors seeking capital preservation with modest returns." if risk_level in ("Low", "Very Low", "Moderately Low") else ""}

INVESTMENT SUITABILITY
----------------------
{"Suitable for aggressive investors looking for high growth potential. Best paired with a long investment horizon of 7+ years." if risk_level in ("High", "Moderately High") else ""}
{"Suitable for balanced investors seeking steady growth with moderate volatility. Recommended holding period: 5+ years." if risk_level in ("Moderate", "Moderate to High") else ""}
{"Suitable for conservative investors prioritizing capital safety. Can be used for short to medium-term goals (1-3 years)." if risk_level in ("Low", "Very Low", "Moderately Low", "Low to Moderate") else ""}

DISCLAIMER
----------
This fact sheet is generated from publicly available data (MFapi.in and AMFI)
for educational purposes only. It does not constitute investment advice.
Past performance does not guarantee future results. Always consult a licensed
financial advisor before making investment decisions.
================================================================================
""".strip()

    return fact_sheet


def build_user_portfolio_document(user_name: str) -> str:
    """
    Build a comprehensive portfolio overview document for RAG context.
    This helps the assistant understand the user's complete financial picture.
    """
    profile = get_user_profile(user_name)
    if not profile:
        return ""

    doc = f"""
================================================================================
USER PORTFOLIO OVERVIEW: {profile['name']}
================================================================================

INVESTOR PROFILE
----------------
Name:              {profile['name']}
Age:               {profile['age']}
Occupation:        {profile['occupation']}
Risk Profile:      {profile['riskProfile']}
Total Portfolio:   {profile['currency']} {profile['totalPortfolioValue']:,.0f}

INVESTMENT GOALS
----------------
"""
    for i, goal in enumerate(profile.get("goals", []), 1):
        doc += f"{i}. {goal}\n"

    doc += """
PORTFOLIO ALLOCATION
--------------------
"""
    for key, alloc in profile.get("allocation", {}).items():
        doc += f"- {key}: {alloc['percentage']}% (₹{alloc['value']:,.0f}) — {alloc['description']}\n"

    # Financial metrics
    metrics = profile.get("yearlyFinancialMetrics", {})
    if metrics:
        doc += f"""
FINANCIAL METRICS
-----------------
Expected Annual Return:  {metrics.get('expectedAnnualReturn', 'N/A')}
Expected Volatility:     {metrics.get('expectedVolatility', 'N/A')}
Sharpe Ratio:            {metrics.get('sharpeRatio', 'N/A')}
Projected Value (5yr):   ₹{metrics.get('projectedValue_5yr', 0):,.0f}
Projected Value (10yr):  ₹{metrics.get('projectedValue_10yr', 0):,.0f}
Projected Value (20yr):  ₹{metrics.get('projectedValue_20yr', 0):,.0f}
"""

    doc += f"""
REBALANCING
-----------
Strategy:                {profile.get('rebalancingStrategy', 'N/A')}
Last Rebalanced:         {profile.get('lastRebalanced', 'N/A')}
Next Recommended:        {profile.get('nextRebalanceDateRecommended', 'N/A')}

DISCLAIMER
----------
This portfolio overview is for educational/informational purposes only.
It does not constitute investment advice.
================================================================================
"""
    return doc.strip()


def build_corpus(user_name: str = DEFAULT_USER):
    """
    Main function to build the entire fund fact sheet corpus.
    Fetches data from MFapi.in for all user holdings + additional popular funds.
    """
    print(f"\n{'='*60}")
    print(f"  Finassist — Building Fund Corpus for {user_name}")
    print(f"{'='*60}\n")

    client = MFApiClient()
    holdings = get_holdings_flat(user_name)

    # Build a map of fund_name → holding_info for enrichment
    holding_map = {}
    for h in holdings:
        name = h.get("name", "")
        if name:
            holding_map[name] = h

    # Combine user holdings (fund names) + additional popular funds
    all_fund_names = list(set(
        [h.get("name", "") for h in holdings if "Fund" in h.get("name", "")]
        + ADDITIONAL_FUNDS_FOR_CORPUS
    ))

    print(f"📊 Total funds to fetch: {len(all_fund_names)}")
    corpus_count = 0
    failed = []

    for i, fund_name in enumerate(all_fund_names, 1):
        print(f"\n[{i}/{len(all_fund_names)}] Fetching: {fund_name}")

        # Try known scheme code first, then search
        scheme_code = KNOWN_SCHEME_CODES.get(fund_name)
        scheme_data = None

        if scheme_code:
            scheme_data = client.get_scheme_data(scheme_code)

        if not scheme_data:
            scheme_data = search_and_get_best_match(client, fund_name)

        if not scheme_data:
            print(f"  ❌ Failed to fetch data for: {fund_name}")
            failed.append(fund_name)
            continue

        meta = scheme_data.get("meta", {})
        nav_history = scheme_data.get("data", [])

        # Calculate returns
        returns = calculate_returns(nav_history) if nav_history else {}

        # Get holding info if this fund is in user's portfolio
        holding_info = holding_map.get(fund_name, None)

        # Generate fact sheet
        fact_sheet = build_fact_sheet_text(meta, nav_history, returns, holding_info)

        # Save to file
        safe_name = (
            meta.get("scheme_name", fund_name)
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "")
            .replace("(", "")
            .replace(")", "")
            [:80]
        )
        file_path = FUND_CORPUS_DIR / f"{safe_name}.txt"
        file_path.write_text(fact_sheet, encoding="utf-8")
        corpus_count += 1
        print(f"  ✅ Saved: {file_path.name} ({len(nav_history)} NAV points, returns: {returns})")

    # Also save the user portfolio document
    portfolio_doc = build_user_portfolio_document(user_name)
    if portfolio_doc:
        portfolio_path = FUND_CORPUS_DIR / f"PORTFOLIO_{user_name.upper()}.txt"
        portfolio_path.write_text(portfolio_doc, encoding="utf-8")
        corpus_count += 1
        print(f"\n  ✅ Saved portfolio overview: {portfolio_path.name}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Corpus Build Complete!")
    print(f"  ✅ Successfully generated: {corpus_count} documents")
    print(f"  ❌ Failed: {len(failed)} funds")
    if failed:
        print(f"  Failed funds: {', '.join(failed)}")
    print(f"  📁 Corpus directory: {FUND_CORPUS_DIR}")
    print(f"{'='*60}\n")

    return corpus_count


if __name__ == "__main__":
    build_corpus()
