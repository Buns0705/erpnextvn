"""Viettel S-Invoice provider.

Official portal: https://sinvoice.viettel.vn

API endpoints (REST, JSON):

- ``POST /InvoiceAPI/InvoiceUtilsWS/getToken`` — authenticate
- ``POST /InvoiceAPI/InvoiceWS/createInvoice/{taxCode}`` — create + publish
- ``POST /InvoiceAPI/InvoiceWS/getInvoiceNo`` — query invoice status
- ``POST /InvoiceAPI/InvoiceWS/cancelTransactionInvoice/{taxCode}`` — cancel
- ``POST /InvoiceAPI/InvoiceWS/replaceInvoice/{taxCode}`` — replace
- ``GET /InvoiceAPI/InvoiceUtilsWS/getRepresentationFileCtc`` — PDF

All endpoints accept/return JSON and use Basic authentication or the
bearer token obtained from ``getToken``.
"""

from __future__ import annotations

import base64
from typing import Any

import requests

from .base_provider import (
    BaseEInvoiceProvider,
    EInvoiceAuthError,
    EInvoiceSendError,
)


class ViettelProvider(BaseEInvoiceProvider):
    """Viettel S-Invoice REST integration."""

    provider_name = "Viettel"
    production_url = "https://api-sinvoice.viettel.vn"
    sandbox_url = "https://demo-sinvoice.viettel.vn"

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> str:
        url = f"{self.api_url}/auth/Login"
        try:
            response = requests.post(
                url,
                json={
                    "username": self.settings.api_username,
                    "password": self.settings.get_password("api_password")
                    if self.settings.api_password
                    else "",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceAuthError(f"Viettel auth failed: {exc}") from exc

        token = data.get("access_token") or data.get("token")
        if not token:
            raise EInvoiceAuthError(
                f"Viettel auth response missing token: {data}"
            )
        self._token = token
        return token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Invoice lifecycle
    # ------------------------------------------------------------------

    def create_draft(self, invoice_data: dict) -> dict:
        """Build the Viettel-specific payload and POST to ``createInvoice``."""
        tax_code = invoice_data["seller"]["tax_code"]
        payload = self._build_payload(invoice_data)

        url = f"{self.api_url}/InvoiceAPI/InvoiceWS/createInvoice/{tax_code}"
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
            response.raise_for_status()
            body = response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"Viettel createInvoice failed: {exc}") from exc

        # Viettel's createInvoice publishes immediately; treat response as draft+result.
        return {
            "draft_id": body.get("result", {}).get("invoiceNo", "") or body.get("invoiceNo", ""),
            "status": "Draft",
            "raw": body,
        }

    def sign_and_send(self, draft_id: str) -> dict:
        """Viettel publishes during ``createInvoice`` — this step is a no-op.

        For API parity we echo the draft result with the canonical keys.
        """
        return {
            "invoice_number": draft_id,
            "lookup_code": draft_id,
            "invoice_date": "",
            "transaction_id": draft_id,
        }

    def get_status(self, transaction_id: str) -> dict:
        url = f"{self.api_url}/InvoiceAPI/InvoiceWS/getInvoiceNo"
        try:
            response = requests.post(
                url,
                json={"invoiceNo": transaction_id},
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return {"status": "pending", "message": str(exc)}

        state = (data.get("state") or "").lower()
        if state == "approved":
            return {"status": "accepted", "message": ""}
        if state == "rejected":
            return {"status": "rejected", "message": data.get("description", "")}
        return {"status": "pending", "message": data.get("description", "")}

    def cancel(self, invoice_number: str, reason: str) -> dict:
        tax_code = self.settings.api_username  # tax code is often the login
        url = f"{self.api_url}/InvoiceAPI/InvoiceWS/cancelTransactionInvoice/{tax_code}"
        try:
            response = requests.post(
                url,
                json={
                    "supplierTaxCode": tax_code,
                    "transactionUuid": invoice_number,
                    "additionalReferenceDesc": reason,
                },
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"Viettel cancel failed: {exc}") from exc
        return {"status": "cancelled", "cancel_date": data.get("cancelDate", "")}

    def replace(self, old_invoice_number: str, new_invoice_data: dict) -> dict:
        tax_code = new_invoice_data["seller"]["tax_code"]
        url = f"{self.api_url}/InvoiceAPI/InvoiceWS/replaceInv/{tax_code}"
        payload = self._build_payload(new_invoice_data)
        payload["originalInvoiceId"] = old_invoice_number
        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"Viettel replace failed: {exc}") from exc

    def get_pdf(self, invoice_number: str) -> bytes:
        url = (
            f"{self.api_url}/InvoiceAPI/InvoiceUtilsWS/getRepresentationFileCtc"
            f"?invoiceNo={invoice_number}"
        )
        try:
            response = requests.get(url, headers=self._headers(), timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EInvoiceSendError(f"Viettel PDF download failed: {exc}") from exc
        # Response may be base64-encoded; try to decode.
        try:
            return base64.b64decode(response.text)
        except Exception:
            return response.content

    # ------------------------------------------------------------------
    # Payload builder
    # ------------------------------------------------------------------

    def _build_payload(self, invoice_data: dict) -> dict[str, Any]:
        """Translate the provider-neutral dict into Viettel's schema."""
        seller = invoice_data["seller"]
        buyer = invoice_data["buyer"]
        inv = invoice_data["invoice"]

        item_list = []
        for i, it in enumerate(inv["items"], start=1):
            item_list.append(
                {
                    "lineNumber": i,
                    "itemName": it["item_name"],
                    "unitName": it["uom"],
                    "unitPrice": it["rate"],
                    "quantity": it["qty"],
                    "itemTotalAmountWithoutTax": it["amount"],
                    "taxPercentage": it["tax_rate"],
                    "taxAmount": it["tax_amount"],
                }
            )

        return {
            "generalInvoiceInfo": {
                "invoiceType": "01GTKT",
                "templateCode": self.settings.template_code or "1/001",
                "invoiceSeries": self.settings.series_symbol or "K24TAA",
                "currencyCode": inv["currency"],
                "exchangeRate": inv["exchange_rate"],
                "invoiceIssuedDate": inv["date"],
                "paymentStatus": True,
                "paymentType": "TM/CK",
            },
            "buyerInfo": {
                "buyerName": buyer["name"],
                "buyerCode": buyer.get("tax_code", ""),
                "buyerTaxCode": buyer["tax_code"],
                "buyerAddressLine": buyer["address"],
                "buyerEmail": buyer.get("email", ""),
            },
            "sellerInfo": {
                "sellerLegalName": seller["name"],
                "sellerTaxCode": seller["tax_code"],
                "sellerAddressLine": seller["address"],
                "sellerPhoneNumber": seller.get("phone", ""),
                "sellerEmail": seller.get("email", ""),
            },
            "payments": [{"paymentMethodName": inv.get("payment_method", "TM/CK")}],
            "itemInfo": item_list,
            "summarizeInfo": {
                "sumOfTotalLineAmountWithoutTax": inv["total_before_tax"],
                "totalAmountWithoutTax": inv["total_before_tax"],
                "totalTaxAmount": inv["total_tax"],
                "totalAmountWithTax": inv["grand_total"],
            },
        }
