from app.agent.invoice_extractor import InvoiceExtractor


def test_invoice_extractor():

    observation = {
        "text": """
        Invoice Details

        Invoice Number: INV-1042
        Vendor: Acme Components
        Amount: INR 18450.00
        Invoice Date: 2026-10-01
        Due Date: 2026-10-31
        Status: unpaid
        """
    }

    extractor = InvoiceExtractor()

    invoice = extractor.extract(
        observation
    )

    assert invoice["invoice_number"] == "INV-1042"
    assert invoice["vendor"] == "Acme Components"
    assert invoice["amount"] == 18450.0
    assert invoice["currency"] == "INR"
    assert invoice["due_date"] == "2026-10-31"