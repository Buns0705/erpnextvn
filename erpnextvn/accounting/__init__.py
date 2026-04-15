"""Vietnam accounting helpers."""

from __future__ import annotations

import json
import os

COA_DIR = os.path.join(os.path.dirname(__file__), "chart_of_accounts")

#: Supported chart-of-accounts variants keyed by the Select option shown to
#: users on Company.vn_chart_of_accounts_type.
COA_FILES = {
    "Thông tư 99": "vn_tt99.json",
    "Thông tư 200": "vn_tt200.json",
    "Thông tư 133": "vn_tt133.json",
}

#: Default CoA for new Vietnamese companies created on or after 01/01/2026.
DEFAULT_COA = "Thông tư 99"


def load_coa(variant: str = DEFAULT_COA) -> dict:
    """Load the chart-of-accounts tree for a given variant.

    Args:
        variant: One of the keys in :data:`COA_FILES`. Defaults to TT99.

    Returns:
        The parsed JSON dict (name, country_code, tree).
    """
    filename = COA_FILES.get(variant, COA_FILES[DEFAULT_COA])
    with open(os.path.join(COA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)
