"""MISA meInvoice provider.

Official portal: https://www.meinvoice.vn

Authentication uses an API key (``AppID``) and API secret passed as
headers. Endpoints return JSON.
"""

from __future__ import annotations

from typing import Any

import requests

from .base_provider import (
    BaseEInvoiceProvider,
    EInvoiceAuthError,
    EInvoiceSendError,
)


class MISAProvider(BaseEInvoiceProvider):
    """MISA meInvoice REST integration."""

    provider_name = "MISA"
    production_url = "https://api.meinvoice.vn/api"
    sandbox_url = "https://demoapi.meinvoice.vn/api"

    def authenticate(self) -> str:
        url = f"{self.api_url}/v1/auth/getToken"
        try:
            response = requests.post(
                url,
                json={
                    "AppID": self.settings.api_key,
                    "AppSecret": self.settings.get_password("api_secret")
                    if self.settings.api_secret
                    else "",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceAuthError(f"MISA auth failed: {exc}") from exc

        token = data.get("Data", {}).get("access_token") or data.get("access_token")
        if not token:
            raise EInvoiceAuthError(f"MISA auth missing token: {data}")
        self._token = token
        return token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_draft(self, invoice_data: dict) -> dict:
        url = f"{self.api_url}/v1/invoices/issue"
        payload = self._build_payload(invoice_data)
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"MISA issue failed: {exc}") from exc

        inv = data.get("Data", {}) or data
        return {
            "draft_id": inv.get("RefID") or inv.get("InvoiceNo") or "",
            "status": "Draft",
            "raw": inv,
        }

    def sign_and_send(self, draft_id: str) -> dict:
        # MISA 'issue' endpoint signs + publishes atomically.
        return {
            "invoice_number": draft_id,
            "lookup_code": draft_id,
            "invoice_date": "",
            "transaction_id": draft_id,
        }

    def get_status(self, transaction_id: str) -> dict:
        url = f"{self.api_url}/v1/invoices/status/{transaction_id}"
        try:
            response = requests.get(url, headers=self._headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return {"status": "pending", "message": str(exc)}
        status_code = data.get("Data", {}).get("Status")
        mapping = {0: "pending", 1: "accepted", 2: "rejected"}
        return {"status": mapping.get(status_code, "pending"), "message": ""}

    def cancel(self, invoice_number: str, reason: str) -> dict:
        url = f"{self.api_url}/v1/invoices/cancel"
        try:
            response = requests.post(
                url,
                json={"RefID": invoice_number, "Reason": reason},
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"MISA cancel failed: {exc}") from exc
        return {"status": "cancelled", "cancel_date": ""}

    def replace(self, old_invoice_number: str, new_invoice_data: dict) -> dict:
        url = f"{self.api_url}/v1/invoices/replace"
        payload = self._build_payload(new_invoice_data)
        payload["OriginalRefID"] = old_invoice_number
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"MISA replace failed: {exc}") from exc

    def get_pdf(self, invoice_number: str) -> bytes:
        url = f"{self.api_url}/v1/invoices/{invoice_number}/pdf"
        try:
            response = requests.get(url, headers=self._headers(), timeout=60)
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"MISA PDF download failed: {exc}") from exc

    def _build_payload(self, invoice_data: dict) -> dict[str, Any]:
        seller = invoice_data["seller"]
        buyer = invoice_data["buyer"]
        inv = invoice_data["invoice"]
        return {
            "InvoiceForm": self.settings.template_code or "1",
            "InvoiceSerial": self.settings.series_symbol or "K24TAA",
            "BuyerInfo": {
                "BuyerName": buyer["name"],
                "BuyerTaxCode": buyer["tax_code"],
                "BuyerAddress": buyer["address"],
                "BuyerEmail": buyer.get("email", ""),
            },
            "SellerInfo": {
                "SellerLegalName": seller["name"],
                "SellerTaxCode": seller["tax_code"],
                "SellerAddress": seller["address"],
            },
            "InvoiceDetails": [
                {
                    "LineNumber": i + 1,
                    "ItemName": it["item_name"],
                    "Unit": it["uom"],
                    "Quantity": it["qty"],
                    "UnitPrice": it["rate"],
                    "Amount": it["amount"],
                    "VATRate": it["tax_rate"],
                    "VATAmount": it["tax_amount"],
                }
                for i, it in enumerate(inv["items"])
            ],
            "TotalAmountWithoutVAT": inv["total_before_tax"],
            "TotalVATAmount": inv["total_tax"],
            "TotalAmount": inv["grand_total"],
        }
