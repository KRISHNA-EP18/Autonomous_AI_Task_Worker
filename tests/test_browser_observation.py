from app.tools.browser import BrowserTool


def test_browser_observation():
    browser = BrowserTool(headless=True)

    try:
        browser.start()

        observation = browser.open(
            "http://127.0.0.1:8000/invoices"
        )

        assert observation["url"].endswith("/invoices")

        assert observation["title"] == "Invoice Portal"

        assert "INV-1042" in observation["text"]

        assert "INV-1042" in observation["links"]

        assert len(observation["inputs"]) >= 1

        vendor_input = next(
            item
            for item in observation["inputs"]
            if item["name"] == "vendor"
        )

        assert vendor_input["id"] == "vendor"

    finally:
        browser.stop()