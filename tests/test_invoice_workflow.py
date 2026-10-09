from app.tools.browser import BrowserTool
import uuid

BASE_URL = "http://127.0.0.1:8000"


def test_invoice_to_ap_workflow():
    browser = BrowserTool(headless=True)
    test_invoice_number = f"INV-AUTO-{uuid.uuid4().hex[:8].upper()}"

    try:
        browser.start()

        # -----------------------------------------
        # 1. Open Invoice Portal
        # -----------------------------------------

        observation = browser.open(
            f"{BASE_URL}/invoices"
        )

        assert "INV-1042" in observation["text"]

        # -----------------------------------------
        # 2. Open invoice INV-1042
        # -----------------------------------------

        observation = browser.click(
            "a:has-text('INV-1042')"
        )

        assert observation["url"].endswith(
            "/invoices/INV-1042"
        )

        assert "Acme Components" in observation["text"]
        assert "18450" in observation["text"]

        # -----------------------------------------
        # 3. Open AP creation form
        # -----------------------------------------

        observation = browser.open(
            f"{BASE_URL}/ap/new"
        )

        assert observation["title"] == "Create AP Invoice"

        # -----------------------------------------
        # 4. Fill invoice data
        # -----------------------------------------

        browser.fill(
            "#invoice_number",
            test_invoice_number
        )

        browser.fill(
            "#vendor",
            "Acme Components"
        )

        browser.fill(
            "#amount",
            "18450"
        )

        browser.fill(
            "#currency",
            "INR"
        )

        browser.fill(
            "#due_date",
            "2026-10-31"
        )

        # -----------------------------------------
        # 5. Submit
        # -----------------------------------------

        observation = browser.click(
            "button[type='submit']"
        )

        # -----------------------------------------
        # 6. Verify browser result
        # -----------------------------------------

        assert "Successfully" in observation["text"]

        assert test_invoice_number in observation["text"]

    finally:
        browser.stop()