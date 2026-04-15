"""VN E Invoice Log DocType."""

from __future__ import annotations

from frappe.model.document import Document


class VNEInvoiceLog(Document):
    """Audit record for each e-invoice transaction with a VN provider.

    One log entry is created per API round-trip (create/publish, cancel,
    replace) so that the user can trace exactly what was sent.
    """

    pass
