import re
from typing import Any


class InvoiceExtractor:

    def extract(self, observation: dict) -> dict[str, Any]:
        text = observation.get("text", "")

        invoice = {}

        # -----------------------------------------
        # Invoice number
        # -----------------------------------------

        match = re.search(
            r"Invoice Number:\s*([A-Z0-9-]+)",
            text,
            re.IGNORECASE,
        )

        if match:
            invoice["invoice_number"] = match.group(1).strip()

        # -----------------------------------------
        # Vendor
        # -----------------------------------------

        match = re.search(
            r"Vendor:\s*(.+)",
            text,
            re.IGNORECASE,
        )

        if match:
            invoice["vendor"] = match.group(1).strip()

        # -----------------------------------------
        # Amount
        # -----------------------------------------

        match = re.search(
            r"Amount:\s*[A-Z]*\s*([\d,.]+)",
            text,
            re.IGNORECASE,
        )

        if match:
            invoice["amount"] = float(
                match.group(1).replace(",", "")
            )

        # -----------------------------------------
        # Currency
        # -----------------------------------------

        match = re.search(
            r"Amount:\s*([A-Z]{3})",
            text,
            re.IGNORECASE,
        )

        if match:
            invoice["currency"] = (
                match.group(1).upper()
            )

        # -----------------------------------------
        # Due date
        # -----------------------------------------

        match = re.search(
            r"Due Date:\s*(\d{4}-\d{2}-\d{2})",
            text,
            re.IGNORECASE,
        )

        if match:
            invoice["due_date"] = match.group(1)

        return invoice