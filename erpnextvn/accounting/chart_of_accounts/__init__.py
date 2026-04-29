"""Chart of Accounts for Vietnam — TT99, TT200, TT133.

Provides ``get_charts_for_country`` which ERPNext calls via the
``regional_overrides`` hook to populate the CoA dropdown in Setup Wizard
and Chart of Accounts Importer.
"""

from __future__ import annotations

import json
import os
from typing import Optional

_COA_DIR = os.path.dirname(__file__)

_CHARTS = {
    "Vietnam - Hệ thống tài khoản TT99/2025": "vn_tt99.json",
    "Vietnam - Hệ thống tài khoản TT200/2014": "vn_tt200.json",
    "Vietnam - Hệ thống tài khoản TT133/2016 (SME)": "vn_tt133.json",
}


def get_charts_for_country(country: str, charts: Optional[list] = None) -> list[str]:
    """Return chart names for Vietnam.

    Called by ERPNext via ``regional_overrides`` when the user selects
    Vietnam as the country in Company creation or Setup Wizard.

    Args:
        country: Country name (e.g. "Vietnam").
        charts: Existing list of chart names to extend.

    Returns:
        List of chart names available for this country.
    """
    if charts is None:
        charts = []

    if country == "Vietnam":
        charts.extend(list(_CHARTS.keys()))

    return charts


def get_account_tree(chart_name: str) -> dict:
    """Load and return the account tree for a given chart name.

    Args:
        chart_name: One of the keys from ``_CHARTS``.

    Returns:
        The parsed JSON dict with ``name``, ``country_code``, and ``tree``.
    """
    filename = _CHARTS.get(chart_name)
    if not filename:
        return {}

    filepath = os.path.join(_COA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
