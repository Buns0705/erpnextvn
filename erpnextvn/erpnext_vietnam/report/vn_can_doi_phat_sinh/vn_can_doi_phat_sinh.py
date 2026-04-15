"""VN Cân Đối Phát Sinh — Vietnamese Trial Balance.

Classic Vietnamese accounting trial-balance layout: for each non-group
account, shows opening balance (Nợ/Có), period movement (Nợ/Có), and
closing balance (Nợ/Có).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}
    company = filters.get("company")
    if not company:
        frappe.throw(_("Vui lòng chọn công ty"))

    columns = [
        {"label": _("Số TK"), "fieldname": "account_number", "fieldtype": "Data", "width": 100},
        {"label": _("Tên tài khoản"), "fieldname": "account_name", "fieldtype": "Data", "width": 260},
        {"label": _("Dư đầu Nợ"), "fieldname": "opening_debit", "fieldtype": "Currency", "width": 130},
        {"label": _("Dư đầu Có"), "fieldname": "opening_credit", "fieldtype": "Currency", "width": 130},
        {"label": _("Phát sinh Nợ"), "fieldname": "period_debit", "fieldtype": "Currency", "width": 140},
        {"label": _("Phát sinh Có"), "fieldname": "period_credit", "fieldtype": "Currency", "width": 140},
        {"label": _("Dư cuối Nợ"), "fieldname": "closing_debit", "fieldtype": "Currency", "width": 130},
        {"label": _("Dư cuối Có"), "fieldname": "closing_credit", "fieldtype": "Currency", "width": 130},
    ]

    accounts = frappe.get_all(
        "Account",
        filters={"company": company, "is_group": 0, "disabled": 0},
        fields=["name", "account_name", "account_number"],
        order_by="account_number",
    )

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    data: list[dict] = []
    for acc in accounts:
        params: dict[str, Any] = {"account": acc.name, "company": company}

        # Opening
        opening_bal = 0.0
        if from_date:
            opening = frappe.db.sql(
                """
                SELECT COALESCE(SUM(debit - credit), 0)
                FROM `tabGL Entry`
                WHERE is_cancelled = 0 AND account = %(account)s
                  AND company = %(company)s AND posting_date < %(from_date)s
                """,
                {**params, "from_date": from_date},
            )
            opening_bal = float(opening[0][0]) if opening else 0.0

        # Period
        period_params = dict(params)
        period_conds = ["is_cancelled = 0", "account = %(account)s", "company = %(company)s"]
        if from_date:
            period_conds.append("posting_date >= %(from_date)s")
            period_params["from_date"] = from_date
        if to_date:
            period_conds.append("posting_date <= %(to_date)s")
            period_params["to_date"] = to_date

        period = frappe.db.sql(
            f"""
            SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
            FROM `tabGL Entry`
            WHERE {' AND '.join(period_conds)}
            """,
            period_params,
        )
        period_debit, period_credit = (float(period[0][0]), float(period[0][1])) if period else (0.0, 0.0)

        closing_bal = opening_bal + period_debit - period_credit

        # Skip accounts with no activity and zero balances
        if opening_bal == 0 and period_debit == 0 and period_credit == 0 and closing_bal == 0:
            continue

        data.append({
            "account_number": acc.account_number or "",
            "account_name": acc.account_name,
            "opening_debit": opening_bal if opening_bal > 0 else 0,
            "opening_credit": -opening_bal if opening_bal < 0 else 0,
            "period_debit": period_debit,
            "period_credit": period_credit,
            "closing_debit": closing_bal if closing_bal > 0 else 0,
            "closing_credit": -closing_bal if closing_bal < 0 else 0,
        })

    return columns, data
