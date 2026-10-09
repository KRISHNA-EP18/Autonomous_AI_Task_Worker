from app.tools.verification import InvoiceVerifier
from sandbox.database import get_connection


def test_invoice_verification():

    invoice_number = "VERIFY-001"

    connection = get_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO ap_records (
            invoice_number,
            vendor,
            amount,
            currency,
            due_date,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            "Acme Components",
            15000.0,
            "INR",
            "2026-10-31",
            "pending",
            "2026-10-06T00:00:00+00:00",
        ),
    )

    connection.commit()
    connection.close()

    verifier = InvoiceVerifier()

    result = verifier.verify_ap_invoice(
        invoice_number=invoice_number,
        expected_vendor="Acme Components",
        expected_amount=15000.0,
        expected_currency="INR",
        expected_due_date="2026-10-31",
    )

    assert result.verified is True
    assert result.checks["exists"] is True
    assert result.checks["vendor_matches"] is True
    assert result.checks["amount_matches"] is True
    assert result.checks["currency_matches"] is True
    assert result.checks["due_date_matches"] is True
def test_verification_detects_wrong_amount():

    invoice_number = "VERIFY-002"

    connection = get_connection()

    connection.execute(
        """
        INSERT OR REPLACE INTO ap_records (
            invoice_number,
            vendor,
            amount,
            currency,
            due_date,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            "Acme Components",
            15000.0,
            "INR",
            "2026-10-31",
            "pending",
            "2026-10-06T00:00:00+00:00",
        ),
    )

    connection.commit()
    connection.close()

    verifier = InvoiceVerifier()

    result = verifier.verify_ap_invoice(
        invoice_number=invoice_number,
        expected_vendor="Acme Components",
        expected_amount=18000.0,
        expected_currency="INR",
        expected_due_date="2026-10-31",
    )

    assert result.verified is False
    assert result.checks["amount_matches"] is False