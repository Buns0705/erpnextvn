"""FPT eInvoice provider.

Official portal: https://einvoice.fpt.com.vn

OAuth2 client-credentials flow with ``client_id`` + ``client_secret``
stored in API Key / API Secret settings fields.
"""

from __future__ import annotations

from typing import Any

import requests

from .base_provider import (
    BaseEInvoiceProvider,
    EInvoiceAuthError,
    EInvoiceSendError,
)


class FPTProvider(BaseEInvoiceProvider):
    """FPT eInvoice REST integration."""

    provider_name = "FPT"
    production_url = "https://api-invoice.fpt.com.vn"
    sandbox_url = "https://sandbox-api-invoice.fpt.com.vn"

    def authenticate(self) -> str:
        url = f"{self.api_url}/oauth2/token"
        try:
            response = requests.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.settings.api_key,
                    "client_secret": self.settings.get_password("api_secret")
                    if self.settings.api_secret
                    else "",
                    "scope": "invoice",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceAuthError(f"FPT auth failed: {exc}") from exc

        token = data.get("access_token")
        if not token:
            raise EInvoiceAuthError(f"FPT auth missing token: {data}")
        self._token = token
        return token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_draft(self, invoice_data: dict) -> dict:
        url = f"{self.api_url}/api/v1/invoices"
        payload = self._build_payload(invoice_data)
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"FPT create failed: {exc}") from exc

        return {
            "draft_id": data.get("id") or data.get("invoiceId", ""),
            "status": "Draft",
            "raw": data,
        }

    def sign_and_send(self, draft_id: str) -> dict:
        url = f"{self.api_url}/api/v1/invoices/{draft_id}/issue"
        try:
            response = requests.post(url, headers=self._headers(), timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"FPT issue failed: {exc}") from exc
        return {
            "invoice_number": data.get("invoiceNo") or draft_id,
            "lookup_code": data.get("lookupCode") or draft_id,
            "invoice_date": data.get("invoiceDate", ""),
            "transaction_id": draft_id,
        }

    def get_status(self, transaction_id: str) -> dict:
        url = f"{self.api_url}/api/v1/invoices/{transaction_id}"
        try:
            response = requests.get(url, headers=self._headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return {"status": "pending", "message": str(exc)}
        status = (data.get("status") or "").lower()
        return {
            "status": "accepted" if status in ("issued", "approved") else status or "pending",
            "message": data.get("message", ""),
        }

    def cancel(self, invoice_number: str, reason: str) -> dict:
        url = f"{self.api_url}/api/v1/invoices/{invoice_number}/cancel"
        try:
            response = requests.post(
                url, json={"reason": reason}, headers=self._headers(), timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"FPT cancel failed: {exc}") from exc
        return {"status": "cancelled", "cancel_date": ""}

    def replace(self, old_invoice_number: str, new_invoice_data: dict) -> dict:
        url = f"{self.api_url}/api/v1/invoices/{old_invoice_number}/replace"
        payload = self._build_payload(new_invoice_data)
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"FPT replace failed: {exc}") from exc

    def get_pdf(self, invoice_number: str) -> bytes:
        url = f"{self.api_url}/api/v1/invoices/{invoice_number}/pdf"
        try:
            response = requests.get(url, headers=self._headers(), timeout=60)
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"FPT PDF download failed: {exc}") from exc

    def _build_payload(self, invoice_data: dict) -> dict[str, Any]:
        seller = invoice_data["seller"]
        buyer = invoice_data["buyer"]
        inv = invoice_data["invoice"]
        return {
            "templateCode": self.settings.template_code or "01GTKT0/001",
            "invoiceSeries": self.settings.series_symbol or "K24TAA",
            "invoiceDate": inv["date"],
            "currencyCode": inv["currency"],
            "exchangeRate": inv["exchange_rate"],
            "seller": {
                "taxCode": seller["tax_code"],
                "name": seller["name"],
                "address": seller["address"],
                "email": seller.get("email", ""),
            },
            "buyer": {
                "taxCode": buyer["tax_code"],
                "name": buyer["name"],
                "address": buyer["address"],
                "email": buyer.get("email", ""),
            },
            "items": [
                {
                    "lineNumber": i + 1,
                    "itemName": it["item_name"],
                    "unit": it["uom"],
                    "quantity": it["qty"],
                    "unitPrice": it["rate"],
                    "amount": it["amount"],
                    "taxRate": it["tax_rate"],
                    "taxAmount": it["tax_amount"],
                }
                for i, it in enumerate(inv["items"])
            ],
            "totalAmountWithoutTax": inv["total_before_tax"],
            "totalTaxAmount": inv["total_tax"],
            "totalAmount": inv["grand_total"],
        }
