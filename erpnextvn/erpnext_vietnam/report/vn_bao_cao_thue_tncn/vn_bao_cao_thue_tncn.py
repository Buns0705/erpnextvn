"""VN Báo Cáo Thuế TNCN — Personal Income Tax Report.

Summarizes monthly PIT per employee for a given date range.
Used to support form 05/KK-TNCN periodic declarations.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}
    columns = [
        {"label": _("Mã NV"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": _("Họ tên"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("MST cá nhân"), "fieldname": "tax_code", "fieldtype": "Data", "width": 140},
        {"label": _("Tổng thu nhập"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 140},
        {"label": _("Giảm trừ"), "fieldname": "deductions", "fieldtype": "Currency", "width": 140},
        {"label": _("TN tính thuế"), "fieldname": "taxable_income", "fieldtype": "Currency", "width": 140},
        {"label": _("Thuế TNCN"), "fieldname": "pit", "fieldtype": "Currency", "width": 140},
    ]

    conditions = ["ss.docstatus = 1"]
    params: dict[str, Any] = {}
    if filters.get("company"):
        conditions.append("ss.company = %(company)s")
        params["company"] = filters["company"]
    if filters.get("from_date"):
        conditions.append("ss.start_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("ss.end_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]

    where = " AND ".join(conditions)
    rows = frappe.db.sql(
        f"""
        SELECT
            ss.employee, ss.employee_name,
            SUM(ss.gross_pay) AS gross_pay,
            SUM(ss.total_deduction) AS deductions,
            SUM(ss.vn_taxable_income) AS taxable_income,
            SUM(ss.vn_pit_amount) AS pit
        FROM `tabSalary Slip` ss
        WHERE {where}
        GROUP BY ss.employee, ss.employee_name
        ORDER BY ss.employee_name
        """,
        params,
        as_dict=True,
    )

    data: list[dict] = []
    for r in rows:
        tax_code = frappe.db.get_value("Employee", r.employee, "vn_tax_code") or ""
        data.append({
            "employee": r.employee,
            "employee_name": r.employee_name,
            "tax_code": tax_code,
            "gross_pay": r.gross_pay or 0,
            "deductions": r.deductions or 0,
            "taxable_income": r.taxable_income or 0,
            "pit": r.pit or 0,
        })
    return columns, data
