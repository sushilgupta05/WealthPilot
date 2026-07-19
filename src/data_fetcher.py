"""
Finassist — MFapi.in Data Fetcher
Fetches real mutual fund data (NAV, metadata, history) from the free MFapi.in API.
No authentication or API key required.
"""
import time
import requests
from datetime import datetime, timedelta
from typing import Optional
from src.config import (
    MFAPI_SEARCH_URL,
    MFAPI_SCHEME_URL,
    MFAPI_REQUEST_DELAY,
)


class MFApiClient:
    """Client for the MFapi.in free mutual fund data API."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Finassist/1.0 (Educational Project)",
        })
        self._last_request_time = 0

    def _rate_limit(self):
        """Ensure minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < MFAPI_REQUEST_DELAY:
            time.sleep(MFAPI_REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def search_fund(self, query: str) -> list[dict]:
        """
        Search for mutual fund schemes by name.
        Returns list of {schemeCode, schemeName} dicts.
        """
        self._rate_limit()
        try:
            resp = self.session.get(MFAPI_SEARCH_URL, params={"q": query}, timeout=15)
            resp.raise_for_status()
            results = resp.json()
            if isinstance(results, list):
                return results
            return []
        except Exception as e:
            print(f"[MFApi] Search error for '{query}': {e}")
            return []

    def get_scheme_data(self, scheme_code: int) -> Optional[dict]:
        """
        Get full scheme data including metadata and historical NAVs.
        Returns dict with 'meta' and 'data' keys.
        """
        self._rate_limit()
        try:
            url = f"{MFAPI_SCHEME_URL}/{scheme_code}"
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "SUCCESS":
                return data
            return None
        except Exception as e:
            print(f"[MFApi] Scheme data error for code {scheme_code}: {e}")
            return None

    def get_latest_nav(self, scheme_code: int) -> Optional[dict]:
        """Get only the latest NAV for a scheme."""
        self._rate_limit()
        try:
            url = f"{MFAPI_SCHEME_URL}/{scheme_code}/latest"
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "SUCCESS":
                return data
            return None
        except Exception as e:
            print(f"[MFApi] Latest NAV error for code {scheme_code}: {e}")
            return None


def calculate_returns(nav_data: list[dict]) -> dict:
    """
    Calculate 1-year, 3-year, and 5-year returns from NAV history.
    nav_data is a list of {date, nav} dicts sorted newest-first.
    """
    if not nav_data or len(nav_data) < 2:
        return {}

    def parse_nav_date(date_str: str) -> datetime:
        for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def find_nav_near_date(target_date: datetime, navs: list) -> Optional[float]:
        """Find the NAV closest to the target date (within 10 days)."""
        best = None
        best_diff = timedelta(days=10)
        for entry in navs:
            d = parse_nav_date(entry["date"])
            if d is None:
                continue
            diff = abs(d - target_date)
            if diff < best_diff:
                best_diff = diff
                best = float(entry["nav"])
        return best

    returns = {}
    latest_nav = float(nav_data[0]["nav"])
    latest_date = parse_nav_date(nav_data[0]["date"])
    if latest_date is None:
        return {}

    periods = {
        "1_year": 365,
        "3_year": 365 * 3,
        "5_year": 365 * 5,
    }

    for period_name, days in periods.items():
        target = latest_date - timedelta(days=days)
        old_nav = find_nav_near_date(target, nav_data)
        if old_nav and old_nav > 0:
            total_return = ((latest_nav - old_nav) / old_nav) * 100
            if "year" in period_name:
                years = days / 365
                if years > 1:
                    cagr = ((latest_nav / old_nav) ** (1 / years) - 1) * 100
                    returns[period_name] = round(cagr, 2)
                else:
                    returns[period_name] = round(total_return, 2)

    return returns


def search_and_get_best_match(client: MFApiClient, fund_name: str) -> Optional[dict]:
    """
    Search for a fund by name and return the best Direct-Growth match scheme data.
    Prefers Direct Plan Growth options.
    """
    # Clean up the fund name for search
    search_terms = fund_name.replace("Fund", "").replace("Limited", "").strip()
    # Take key words
    words = search_terms.split()
    if len(words) > 4:
        search_query = " ".join(words[:4])
    else:
        search_query = search_terms

    results = client.search_fund(search_query)
    if not results:
        # Try with fewer words
        if len(words) > 2:
            search_query = " ".join(words[:2])
            results = client.search_fund(search_query)

    if not results:
        print(f"[MFApi] No results for '{fund_name}'")
        return None

    # Prioritize: Direct Plan + Growth
    direct_growth = [
        r for r in results
        if "direct" in r.get("schemeName", "").lower()
        and "growth" in r.get("schemeName", "").lower()
    ]

    if direct_growth:
        chosen = direct_growth[0]
    else:
        # Fallback: any growth plan
        growth = [r for r in results if "growth" in r.get("schemeName", "").lower()]
        chosen = growth[0] if growth else results[0]

    print(f"[MFApi] Matched '{fund_name}' → {chosen.get('schemeName')} (Code: {chosen.get('schemeCode')})")

    # Fetch full data
    scheme_data = client.get_scheme_data(int(chosen["schemeCode"]))
    return scheme_data


# ── Predefined scheme codes for popular funds (faster than searching) ───
KNOWN_SCHEME_CODES = {
    "SBI Bluechip Fund": 120503,
    "ICICI Prudential Technology Fund": 120594,
    "Axis Midcap Fund": 120505,
    "HDFC Sensex Index Fund": 140369,
    "Motilal Oswal Multicap Fund": 145076,
    "HDFC Low Duration Fund": 119093,
    "SBI Savings Fund": 105756,
    "Aditya Birla Sun Life Savings Fund": 107068,
    "ICICI Prudential Liquid Fund": 120585,
    "UTI Nifty 50 Index Fund": 120716,
    "Parag Parikh Flexi Cap Fund": 122639,
    "HDFC Top 100 Fund": 100179,
    "ICICI Prudential Bluechip Fund": 120586,
    "Axis Bluechip Fund": 120503,
    "HDFC Balanced Advantage Fund": 100140,
    "SBI Balanced Advantage Fund": 119773,
    "HDFC ELSS Tax Saver Fund": 100182,
    "Axis ELSS Tax Saver Fund": 120503,
}


if __name__ == "__main__":
    client = MFApiClient()

    # Test search
    print("=== Testing MFapi.in ===")
    results = client.search_fund("SBI Bluechip")
    print(f"Search results: {len(results)} found")
    if results:
        print(f"  First: {results[0]}")
        # Get data
        code = int(results[0]["schemeCode"])
        data = client.get_scheme_data(code)
        if data:
            meta = data.get("meta", {})
            print(f"\n  Fund House: {meta.get('fund_house')}")
            print(f"  Scheme: {meta.get('scheme_name')}")
            print(f"  Category: {meta.get('scheme_category')}")
            nav_history = data.get("data", [])
            print(f"  NAV points: {len(nav_history)}")
            if nav_history:
                print(f"  Latest NAV: {nav_history[0]['nav']} ({nav_history[0]['date']})")
                returns = calculate_returns(nav_history)
                print(f"  Returns: {returns}")
