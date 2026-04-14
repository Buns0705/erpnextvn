"""VN Province DocType controller."""

from __future__ import annotations

from frappe.model.document import Document


class VNProvince(Document):
    """Vietnamese province / centrally-governed city.

    Stores the 63 provinces used for HR wage-region calculation and
    tax-authority reporting.
    """

    pass
