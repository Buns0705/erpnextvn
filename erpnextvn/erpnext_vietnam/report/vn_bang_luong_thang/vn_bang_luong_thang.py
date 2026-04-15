"""VN Bảng Lương Tháng — Monthly Payroll Report.

Aggregates submitted Salary Slips for a company/month and renders the
Vietnamese-format monthly payroll summary with insurance and PIT
columns.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Report entry point.

    Args:
        filters: ``company``, ``month`` (1..12), ``year``, optional ``department``.

    Returns:
        ``(columns, data)`` — a list of column definitions and list of row dicts.
    """
    filters = filters or {}
    columns = _columns()
    data = _get_data(filters)
    return columns, data


def _columns() -> list[dict]:
    return [
        {"label": _("Mã NV"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": _("Họ tên"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("Phòng ban"), "fieldname": "department", "fieldtype": "Data", "width": 140},
        {"label": _("Ngày công"), "fieldname": "payment_days", "fieldtype": "Float", "width": 90},
        {"label": _("Lương CB"), "fieldname": "base", "fieldtype": "Currency", "width": 120},
        {"label": _("Phụ cấp"), "fieldname": "allowances", "fieldtype": "Currency", "width": 120},
        {"label": _("Tổng thu nhập"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 130},
        {"label": _("BHXH NLĐ"), "fieldname": "bhxh", "fieldtype": "Currency", "width": 110},
        {"label": _("BHYT NLĐ"), "fieldname": "bhyt", "fieldtype": "Currency", "width": 110},
        {"label": _("BHTN NLĐ"), "fieldname": "bhtn", "fieldtype": "Currency", "width": 110},
        {"label": _("TN tính thuế"), "fieldname": "taxable_income", "fieldtype": "Currency", "width": 120},
        {"label": _("Thuế TNCN"), "fieldname": "pit", "fieldtype": "Currency", "width": 110},
        {"label": _("Thực lĩnh"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 130},
    ]


def _get_data(filters: dict[str, Any]) -> list[dict]:
    conditions = ["ss.docstatus = 1"]
    params: dict[str, Any] = {}

    if filters.get("company"):
        conditions.append("ss.company = %(company)s")
        params["company"] = filters["company"]

    if filters.get("month") and filters.get("year"):
        conditions.append("MONTH(ss.start_date) = %(month)s")
        conditions.append("YEAR(ss.start_date) = %(year)s")
        params["month"] = filters["month"]
        params["year"] = filters["year"]

    if filters.get("department"):
        conditions.append("ss.department = %(department)s")
        params["department"] = filters["department"]

    where = " AND ".join(conditions)
    rows = frappe.db.sql(
        f"""
        SELECT
            ss.employee, ss.employee_name, ss.department, ss.payment_days,
            ss.base, ss.gross_pay, ss.net_pay, ss.total_deduction,
            ss.vn_insurance_employee, ss.vn_pit_amount, ss.vn_taxable_income
        FROM `tabSalary Slip` ss
        WHERE {where}
        ORDER BY ss.department, ss.employee_name
        """,
        params,
        as_dict=True,
    )

    data: list[dict] = []
    for r in rows:
        bhxh = _component_total(r.employee, r.name if "name" in r else None, "BHXH (NLĐ 8%)")
        bhyt = _component_total(r.employee, r.name if "name" in r else None, "BHYT (NLĐ 1.5%)")
        bhtn = _component_total(r.employee, r.name if "name" in r else None, "BHTN (NLĐ 1%)")

        data.append(
            {
                "employee": r.employee,
                "employee_name": r.employee_name,
                "department": r.department or "",
                "payment_days": r.payment_days or 0,
                "base": r.base or 0,
                "allowances": max(0, (r.gross_pay or 0) - (r.base or 0)),
                "gross_pay": r.gross_pay or 0,
                "bhxh": bhxh,
                "bhyt": bhyt,
                "bhtn": bhtn,
                "taxable_income": r.vn_taxable_income or 0,
                "pit": r.vn_pit_amount or 0,
                "net_pay": r.net_pay or 0,
            }
        )

    return data


def _component_total(employee: str, slip_name: str | None, component: str) -> float:
    """Return the amount of a specific salary component on the latest slip."""
    if not slip_name:
        return 0
    value = frappe.db.get_value(
        "Salary Detail",
        {"parent": slip_name, "salary_component": component},
        "amount",
    )
    return value or 0
