"""VN E Invoice Settings — Single DocType."""

from __future__ import annotations

from frappe.model.document import Document


class VNEInvoiceSettings(Document):
    """Global settings for the Vietnamese e-invoicing integration.

    Selects one of the five supported providers and stores API /
    certificate credentials plus invoice-template metadata.
    """

    pass
