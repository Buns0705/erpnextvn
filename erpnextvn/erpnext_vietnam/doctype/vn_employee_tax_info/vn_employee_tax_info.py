"""VN Employee Tax Info DocType."""

from __future__ import annotations

from frappe.model.document import Document


class VNEmployeeTaxInfo(Document):
    """Per-employee Vietnamese tax and insurance configuration.

    Optional record storing personal income tax code, dependent count,
    insurance base salary, and wage region for each employee.
    """

    pass
