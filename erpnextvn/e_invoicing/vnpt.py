"""VNPT eInvoice provider.

Official portal: https://einvoice.vnpt.vn

Uses the VNPT PublishService REST endpoints (``BusinessService.svc`` family).
Basic HTTP auth with Account/Password; invoices are submitted as XML
payloads, but here we use the VNPT JSON-API variant for simplicity.
"""

from __future__ import annotations

from typing import Any

import requests

from .base_provider import (
    BaseEInvoiceProvider,
    EInvoiceAuthError,
    EInvoiceSendError,
)


class VNPTProvider(BaseEInvoiceProvider):
    """VNPT eInvoice REST integration."""

    provider_name = "VNPT"
    production_url = "https://einvoice.vnpt.vn"
    sandbox_url = "https://demo-ehoadon.vnpt.vn"

    def authenticate(self) -> str:
        # VNPT uses Basic Auth per-request; no separate token step.
        if not self.settings.api_username:
            raise EInvoiceAuthError("VNPT: API username missing")
        self._token = self.settings.api_username
        return self._token

    def _auth(self) -> tuple[str, str]:
        return (
            self.settings.api_username or "",
            self.settings.get_password("api_password") if self.settings.api_password else "",
        )

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json", "Accept": "application/json"}

    def create_draft(self, invoice_data: dict) -> dict:
        url = f"{self.api_url}/PublishService.asmx/ImportAndPublishInv"
        payload = self._build_payload(invoice_data)
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._headers(),
                auth=self._auth(),
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"VNPT import failed: {exc}") from exc
        return {"draft_id": data.get("Fkey") or data.get("fkey", ""), "status": "Draft"}

    def sign_and_send(self, draft_id: str) -> dict:
        # VNPT ImportAndPublishInv publishes in one call.
        return {
            "invoice_number": draft_id,
            "lookup_code": draft_id,
            "invoice_date": "",
            "transaction_id": draft_id,
        }

    def get_status(self, transaction_id: str) -> dict:
        url = f"{self.api_url}/BusinessService.asmx/GetInvStatusByFkey"
        try:
            response = requests.post(
                url,
                json={"fkey": transaction_id},
                headers=self._headers(),
                auth=self._auth(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return {"status": "pending", "message": str(exc)}
        status = (data.get("status") or "").lower()
        return {"status": "accepted" if status == "published" else "pending", "message": ""}

    def cancel(self, invoice_number: str, reason: str) -> dict:
        url = f"{self.api_url}/BusinessService.asmx/CancelInv"
        try:
            response = requests.post(
                url,
                json={"fkey": invoice_number, "reason": reason},
                headers=self._headers(),
                auth=self._auth(),
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"VNPT cancel failed: {exc}") from exc
        return {"status": "cancelled", "cancel_date": ""}

    def replace(self, old_invoice_number: str, new_invoice_data: dict) -> dict:
        url = f"{self.api_url}/PublishService.asmx/ReplaceInv"
        payload = self._build_payload(new_invoice_data)
        payload["originalFkey"] = old_invoice_number
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._headers(),
                auth=self._auth(),
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"VNPT replace failed: {exc}") from exc

    def get_pdf(self, invoice_number: str) -> bytes:
        url = f"{self.api_url}/PortalService.asmx/downloadInvPDF"
        try:
            response = requests.post(
                url,
                json={"fkey": invoice_number},
                headers=self._headers(),
                auth=self._auth(),
                timeout=60,
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"VNPT PDF download failed: {exc}") from exc

    def _build_payload(self, invoice_data: dict) -> dict[str, Any]:
        seller = invoice_data["seller"]
        buyer = invoice_data["buyer"]
        inv = invoice_data["invoice"]

        return {
            "Inv": {
                "key": invoice_data["erp_reference"]["sales_invoice"],
                "Invoice": {
                    "CusCode": buyer.get("tax_code", ""),
                    "CusName": buyer["name"],
                    "CusAddress": buyer["address"],
                    "CusEmail": buyer.get("email", ""),
                    "CusTaxCode": buyer["tax_code"],
                    "PaymentMethod": inv.get("payment_method", "TM/CK"),
                    "KindOfService": "",
                    "Products": [
                        {
                            "ProdName": it["item_name"],
                            "ProdUnit": it["uom"],
                            "ProdQuantity": it["qty"],
                            "ProdPrice": it["rate"],
                            "Total": it["amount"],
                            "VATRate": it["tax_rate"],
                            "VATAmount": it["tax_amount"],
                            "Amount": it["amount"] + it["tax_amount"],
                        }
                        for it in inv["items"]
                    ],
                    "Total": inv["total_before_tax"],
                    "VATAmount": inv["total_tax"],
                    "Amount": inv["grand_total"],
                    "DiscountAmount": 0,
                },
            },
            "Pattern": self.settings.template_code or "01GTKT0/001",
            "Serial": self.settings.series_symbol or "AA/24E",
        }
