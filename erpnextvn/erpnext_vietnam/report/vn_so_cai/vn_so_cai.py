"""VN Sổ Cái — Vietnamese-format General Ledger.

Renders GL Entries for a specific account with opening balance,
period activity, and running balance columns formatted per the
Vietnamese "Sổ cái" convention.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}

    columns = [
        {"label": _("Ngày"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Chứng từ"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
        {"label": _("Diễn giải"), "fieldname": "remarks", "fieldtype": "Data", "width": 260},
        {"label": _("TK đối ứng"), "fieldname": "against_account", "fieldtype": "Data", "width": 160},
        {"label": _("Nợ"), "fieldname": "debit", "fieldtype": "Currency", "width": 130},
        {"label": _("Có"), "fieldname": "credit", "fieldtype": "Currency", "width": 130},
        {"label": _("Số dư"), "fieldname": "balance", "fieldtype": "Currency", "width": 140},
        {"label": _("Loại CT"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
    ]

    account = filters.get("account")
    if not account:
        frappe.throw(_("Vui lòng chọn tài khoản"))

    conditions = ["is_cancelled = 0", "account = %(account)s"]
    params: dict[str, Any] = {"account": account}

    if filters.get("company"):
        conditions.append("company = %(company)s")
        params["company"] = filters["company"]

    # Opening balance: entries before the from_date
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    opening_balance = 0.0
    if from_date:
        opening = frappe.db.sql(
            """
            SELECT COALESCE(SUM(debit - credit), 0) AS bal
            FROM `tabGL Entry`
            WHERE is_cancelled = 0 AND account = %(account)s
              AND posting_date < %(from_date)s
              AND company = %(company)s
            """,
            {"account": account, "from_date": from_date, "company": params.get("company")},
        )
        opening_balance = float(opening[0][0]) if opening else 0.0

    if from_date:
        conditions.append("posting_date >= %(from_date)s")
        params["from_date"] = from_date
    if to_date:
        conditions.append("posting_date <= %(to_date)s")
        params["to_date"] = to_date

    where = " AND ".join(conditions)
    entries = frappe.db.sql(
        f"""
        SELECT posting_date, voucher_type, voucher_no, against, remarks,
               debit, credit
        FROM `tabGL Entry`
        WHERE {where}
        ORDER BY posting_date, creation
        """,
        params,
        as_dict=True,
    )

    data: list[dict] = [{
        "posting_date": from_date,
        "voucher_no": "",
        "remarks": _("Số dư đầu kỳ"),
        "against_account": "",
        "debit": opening_balance if opening_balance > 0 else 0,
        "credit": -opening_balance if opening_balance < 0 else 0,
        "balance": opening_balance,
        "voucher_type": "",
    }]

    balance = opening_balance
    for e in entries:
        balance += (e.debit or 0) - (e.credit or 0)
        data.append({
            "posting_date": e.posting_date,
            "voucher_type": e.voucher_type,
            "voucher_no": e.voucher_no,
            "remarks": e.remarks or "",
            "against_account": e.against or "",
            "debit": e.debit or 0,
            "credit": e.credit or 0,
            "balance": balance,
        })

    return columns, data
