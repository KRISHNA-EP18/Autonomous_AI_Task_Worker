from app.tools.browser import BrowserTool


def test_invoice_portal():
    browser = BrowserTool(headless=True)

    try:
        browser.start()

        result = browser.open(
            "http://127.0.0.1:8000/invoices"
        )

        assert "Invoice Portal" in result["title"]

        text = browser.get_page_text()

        assert "INV-1042" in text
        assert "Acme Components" in text

    finally:
        browser.stop()