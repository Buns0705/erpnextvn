"""Chart of Accounts for Vietnam — TT99, TT200, TT133.

Mechanism:

1. ``override_whitelisted_methods`` redirects the RPC call
   ``get_charts_for_country`` to ours so the dropdown is populated
   when creating a Company with country = Vietnam.

2. A monkey-patch on ERPNext's ``get_chart`` lets ``create_charts``
   load our JSON files. Because ``create_charts`` imports
   ``get_chart`` directly (not via RPC), we cannot use
   ``override_whitelisted_methods`` for it. The patch is applied:

   - Lazily when this module is first imported
   - Eagerly via the ``boot_session`` hook
"""

from __future__ import annotations

import json
import os

import frappe

_COA_DIR = os.path.dirname(__file__)

_CHARTS = {
    "Vietnam - Hệ thống tài khoản TT99/2025": "vn_tt99.json",
    "Vietnam - Hệ thống tài khoản TT200/2014": "vn_tt200.json",
    "Vietnam - Hệ thống tài khoản TT133/2016 (SME)": "vn_tt133.json",
}

_PATCHED = False


@frappe.whitelist()
def get_charts_for_country(country, with_standard=False):
    """Return chart names — includes both ERPNext standard + our VN charts.

    Replaces ERPNext's ``get_charts_for_country`` via the
    ``override_whitelisted_methods`` hook.
    """
    # Ensure get_chart is patched before anyone tries to load a chart
    ensure_patched()

    from erpnext.accounts.doctype.account.chart_of_accounts import (
        chart_of_accounts as _orig_module,
    )

    charts = []

    # --- Original ERPNext logic (scan its own verified/ folder) ---
    def _get_chart_name(content):
        if content:
            content = json.loads(content)
            if (
                content and content.get("disabled", "No") == "No"
            ) or frappe.local.flags.allow_unverified_charts:
                charts.append(content["name"])

    country_code = frappe.get_cached_value("Country", country, "code")
    if country_code:
        folders = ("verified",)
        if frappe.local.flags.allow_unverified_charts:
            folders = ("verified", "unverified")

        for folder in folders:
            path = os.path.join(os.path.dirname(_orig_module.__file__), folder)
            if not os.path.exists(path):
                continue
            for fname in os.listdir(path):
                fname = frappe.as_unicode(fname)
                if (
                    fname.startswith(country_code) or fname.startswith(country)
                ) and fname.endswith(".json"):
                    with open(os.path.join(path, fname)) as f:
                        _get_chart_name(f.read())

    # --- Add our Vietnamese charts ---
    if country == "Vietnam":
        for chart_name in _CHARTS:
            if chart_name not in charts:
                charts.append(chart_name)

    if len(charts) != 1 or with_standard:
        charts += ["Standard", "Standard with Numbers"]

    return charts


def _get_chart_vn(chart_template):
    """Return the tree dict if chart_template is one of ours, else None."""
    filename = _CHARTS.get(chart_template)
    if not filename:
        return None
    filepath = os.path.join(_COA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tree")


def ensure_patched(bootinfo=None):
    """Monkey-patch ERPNext's ``get_chart`` once per Python process.

    Called from:
    - ``boot_session`` hook (every login / page load)
    - ``get_charts_for_country`` (defensive)
    - module import time

    Idempotent — safe to call repeatedly.
    """
    global _PATCHED
    if _PATCHED:
        return

    try:
        from erpnext.accounts.doctype.account.chart_of_accounts import (
            chart_of_accounts as _mod,
        )
    except ImportError:
        return

    _original_get_chart = _mod.get_chart

    def _patched_get_chart(chart_template, existing_company=None):
        vn_tree = _get_chart_vn(chart_template)
        if vn_tree:
            return vn_tree
        return _original_get_chart(chart_template, existing_company)

    _mod.get_chart = _patched_get_chart
    _PATCHED = True


# Apply on import (lazy fallback)
ensure_patched()
