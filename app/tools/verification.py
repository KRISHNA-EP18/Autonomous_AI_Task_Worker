from app.models.schemas import VerificationResult
from sandbox.database import get_connection


class InvoiceVerifier:

    def verify_ap_invoice(
        self,
        invoice_number: str,
        expected_vendor: str,
        expected_amount: float,
        expected_currency: str,
        expected_due_date: str,
    ) -> VerificationResult:

        connection = get_connection()

        row = connection.execute(
            """
            SELECT *
            FROM ap_records
            WHERE invoice_number = ?
            """,
            (invoice_number,),
        ).fetchone()

        connection.close()

        # -----------------------------------------
        # Record does not exist
        # -----------------------------------------

        if row is None:
            return VerificationResult(
                verified=False,
                checks={
                    "exists": False,
                },
                evidence=[],
                message="AP invoice was not found.",
            )

        record = dict(row)

        # -----------------------------------------
        # Independent checks
        # -----------------------------------------

        checks = {
            "exists": True,
            "vendor_matches": (
                record["vendor"] == expected_vendor
            ),
            "amount_matches": (
                float(record["amount"]) == float(expected_amount)
            ),
            "currency_matches": (
                record["currency"] == expected_currency
            ),
            "due_date_matches": (
                record["due_date"] == expected_due_date
            ),
            "status_is_pending": (
                record["status"] == "pending"
            ),
        }

        verified = all(checks.values())

        evidence = [
            f"AP record exists: {record['invoice_number']}",
            f"Vendor: {record['vendor']}",
            f"Amount: {record['amount']}",
            f"Currency: {record['currency']}",
            f"Due date: {record['due_date']}",
            f"Status: {record['status']}",
        ]

        if verified:
            message = "AP invoice independently verified."
        else:
            message = "AP invoice exists but verification failed."

        return VerificationResult(
            verified=verified,
            checks=checks,
            evidence=evidence,
            message=message,
        )