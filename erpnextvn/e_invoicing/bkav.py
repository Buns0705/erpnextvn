"""BKAV eHoadon provider.

Official portal: https://van-ban.ebh.vn / https://www.ehoadon.bkav.com

Authenticates with username/password and accepts invoice payloads as
JSON (``/api/Invoices/ImportAndIssue``). Uses a token header for
subsequent calls.
"""

from __future__ import annotations

from typing import Any

import requests

from .base_provider import (
    BaseEInvoiceProvider,
    EInvoiceAuthError,
    EInvoiceSendError,
)


class BKAVProvider(BaseEInvoiceProvider):
    """BKAV eHoadon REST integration."""

    provider_name = "BKAV"
    production_url = "https://api-ehoadon.bkav.com"
    sandbox_url = "https://demo-ehoadon.bkav.com"

    def authenticate(self) -> str:
        url = f"{self.api_url}/api/Users/Login"
        try:
            response = requests.post(
                url,
                json={
                    "Username": self.settings.api_username,
                    "Password": self.settings.get_password("api_password")
                    if self.settings.api_password
                    else "",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceAuthError(f"BKAV auth failed: {exc}") from exc

        token = data.get("Token") or data.get("token") or data.get("access_token")
        if not token:
            raise EInvoiceAuthError(f"BKAV auth missing token: {data}")
        self._token = token
        return token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_draft(self, invoice_data: dict) -> dict:
        url = f"{self.api_url}/api/Invoices/ImportAndIssue"
        payload = self._build_payload(invoice_data)
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"BKAV import failed: {exc}") from exc
        return {
            "draft_id": data.get("InvoiceGUID") or data.get("InvoiceNo", ""),
            "status": "Draft",
            "raw": data,
        }

    def sign_and_send(self, draft_id: str) -> dict:
        # ImportAndIssue publishes atomically.
        return {
            "invoice_number": draft_id,
            "lookup_code": draft_id,
            "invoice_date": "",
            "transaction_id": draft_id,
        }

    def get_status(self, transaction_id: str) -> dict:
        url = f"{self.api_url}/api/Invoices/GetStatus"
        try:
            response = requests.post(
                url,
                json={"InvoiceGUID": transaction_id},
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return {"status": "pending", "message": str(exc)}
        state = (data.get("Status") or "").lower()
        if state in ("issued", "published"):
            return {"status": "accepted", "message": ""}
        if state == "rejected":
            return {"status": "rejected", "message": data.get("Message", "")}
        return {"status": "pending", "message": data.get("Message", "")}

    def cancel(self, invoice_number: str, reason: str) -> dict:
        url = f"{self.api_url}/api/Invoices/Cancel"
        try:
            response = requests.post(
                url,
                json={"InvoiceGUID": invoice_number, "Reason": reason},
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"BKAV cancel failed: {exc}") from exc
        return {"status": "cancelled", "cancel_date": ""}

    def replace(self, old_invoice_number: str, new_invoice_data: dict) -> dict:
        url = f"{self.api_url}/api/Invoices/Replace"
        payload = self._build_payload(new_invoice_data)
        payload["OriginalInvoiceGUID"] = old_invoice_number
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"BKAV replace failed: {exc}") from exc

    def get_pdf(self, invoice_number: str) -> bytes:
        url = f"{self.api_url}/api/Invoices/DownloadPDF/{invoice_number}"
        try:
            response = requests.get(url, headers=self._headers(), timeout=60)
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"BKAV PDF download failed: {exc}") from exc

    def _build_payload(self, invoice_data: dict) -> dict[str, Any]:
        seller = invoice_data["seller"]
        buyer = invoice_data["buyer"]
        inv = invoice_data["invoice"]
        return {
            "InvoiceForm": self.settings.template_code or "1/001",
            "InvoiceSerial": self.settings.series_symbol or "K24TAA",
            "InvoiceDate": inv["date"],
            "BuyerName": buyer["name"],
            "BuyerTaxCode": buyer["tax_code"],
            "BuyerAddress": buyer["address"],
            "BuyerEmail": buyer.get("email", ""),
            "SellerName": seller["name"],
            "SellerTaxCode": seller["tax_code"],
            "SellerAddress": seller["address"],
            "Details": [
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
