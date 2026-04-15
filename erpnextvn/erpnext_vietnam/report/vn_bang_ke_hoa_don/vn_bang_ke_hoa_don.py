"""VN Bảng Kê Hóa Đơn — Invoice Register.

Lists Sales Invoices (or Purchase Invoices) for a period with VAT
breakdown. Supports the ``invoice_type`` filter to switch between
Sales ("Bán ra") and Purchase ("Mua vào").
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple[list[dict], list[dict]]:
    filters = filters or {}
    columns = [
        {"label": _("STT"), "fieldname": "idx", "fieldtype": "Int", "width": 60},
        {"label": _("Ngày HĐ"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Số HĐ"), "fieldname": "invoice_no", "fieldtype": "Data", "width": 160},
        {"label": _("Ký hiệu"), "fieldname": "series_symbol", "fieldtype": "Data", "width": 100},
        {"label": _("Khách hàng / NCC"), "fieldname": "party", "fieldtype": "Data", "width": 220},
        {"label": _("MST"), "fieldname": "tax_id", "fieldtype": "Data", "width": 120},
        {"label": _("Giá trị trước thuế"), "fieldname": "net_total", "fieldtype": "Currency", "width": 140},
        {"label": _("Thuế suất"), "fieldname": "tax_rate", "fieldtype": "Percent", "width": 90},
        {"label": _("Tiền thuế"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Tổng tiền"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 140},
    ]

    invoice_type = filters.get("invoice_type", "Sales")
    doctype = "Sales Invoice" if invoice_type == "Sales" else "Purchase Invoice"
    party_field = "customer_name" if invoice_type == "Sales" else "supplier_name"

    conditions = ["inv.docstatus = 1"]
    params: dict[str, Any] = {}
    if filters.get("company"):
        conditions.append("inv.company = %(company)s")
        params["company"] = filters["company"]
    if filters.get("from_date"):
        conditions.append("inv.posting_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("inv.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]

    where = " AND ".join(conditions)
    rows = frappe.db.sql(
        f"""
        SELECT inv.name, inv.posting_date, inv.{party_field} AS party,
               inv.tax_id, inv.net_total, inv.grand_total,
               inv.total_taxes_and_charges AS tax_amount
               {', inv.vn_einvoice_number AS einvoice_number' if invoice_type == 'Sales' else ''}
        FROM `tab{doctype}` inv
        WHERE {where}
        ORDER BY inv.posting_date, inv.name
        """,
        params,
        as_dict=True,
    )

    data: list[dict] = []
    for i, r in enumerate(rows, start=1):
        tax_rate = 0
        if r.net_total:
            tax_rate = round((r.tax_amount or 0) / r.net_total * 100, 2)
        data.append({
            "idx": i,
            "posting_date": r.posting_date,
            "invoice_no": r.get("einvoice_number") or r.name,
            "series_symbol": "",
            "party": r.party or "",
            "tax_id": r.tax_id or "",
            "net_total": r.net_total or 0,
            "tax_rate": tax_rate,
            "tax_amount": r.tax_amount or 0,
            "grand_total": r.grand_total or 0,
        })
    return columns, data
