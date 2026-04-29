"""Chart of Accounts for Vietnam — TT99, TT200, TT133.

Overrides ERPNext's ``get_charts_for_country`` via
``override_whitelisted_methods`` hook so that the Vietnamese charts
appear in the "Chart Of Accounts Template" dropdown when creating a
Company with country = Vietnam.

Also monkey-patches ``get_chart`` at import time so ERPNext can load
the account tree from our JSON files.
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


@frappe.whitelist()
def get_charts_for_country(country, with_standard=False):
    """Return chart names — includes both ERPNext standard + our VN charts.

    This completely replaces ERPNext's ``get_charts_for_country`` via the
    ``override_whitelisted_methods`` hook. It first calls the original
    ERPNext logic (scanning its own ``verified/`` folder) then appends
    our Vietnamese charts.
    """
    from erpnext.accounts.doctype.account.chart_of_accounts import (
        chart_of_accounts as _orig_module,
    )

    charts = []

    # --- Original ERPNext logic (scan verified/ folder) ---
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
    """If chart_template is one of ours, return the tree dict."""
    filename = _CHARTS.get(chart_template)
    if not filename:
        return None
    filepath = os.path.join(_COA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tree")


def _patch_get_chart():
    """Monkey-patch ERPNext's ``get_chart`` so it can load our JSON files.

    Called once at module import time. Wraps the original ``get_chart``
    to first check if the template is one of ours.
    """
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


# Apply patch on import
_patch_get_chart()
