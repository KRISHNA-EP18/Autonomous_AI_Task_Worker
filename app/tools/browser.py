from playwright.sync_api import sync_playwright


class BrowserTool:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=self.headless
        )

        self.context = self.browser.new_context()

        self.page = self.context.new_page()

        return self
    def get_page_text(self):
        return self.page.locator("body").inner_text()
    def stop(self):
        if self.browser:
            self.browser.close()

        if self.playwright:
            self.playwright.stop()

        self.browser = None
        self.playwright = None
        self.context = None
        self.page = None

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------

    def open(self, url: str):
        self.page.goto(url, wait_until="domcontentloaded")

        return self.observe()

    # --------------------------------------------------
    # Observation
    # --------------------------------------------------

    def observe(self):
        links = self.page.locator("a").all_inner_texts()
        buttons = self.page.locator("button").all_inner_texts()

        inputs = self.page.locator(
            "input, textarea, select"
        )

        input_data = []

        for i in range(inputs.count()):
            element = inputs.nth(i)

            input_data.append({
                "tag": element.evaluate(
                    "(el) => el.tagName.toLowerCase()"
                ),
                "type": element.get_attribute("type"),
                "name": element.get_attribute("name"),
                "id": element.get_attribute("id"),
                "placeholder": element.get_attribute("placeholder"),
            })

        return {
            "url": self.page.url,
            "title": self.page.title(),
            "text": self.page.locator("body").inner_text(),
            "links": links,
            "buttons": buttons,
            "inputs": input_data,
        }

    # --------------------------------------------------
    # Actions
    # --------------------------------------------------

    def click(self, selector: str):
        self.page.locator(selector).click(timeout=5000)

        self.page.wait_for_load_state(
            "domcontentloaded"
        )

        return self.observe()

    def fill(self, selector: str, value: str):
        self.page.locator(selector).fill(value)

        return self.observe()

    # --------------------------------------------------
    # Evidence
    # --------------------------------------------------

    def screenshot(self, path: str):
        self.page.screenshot(
            path=path,
            full_page=True,
        )

        return {
            "path": path,
            "url": self.page.url,
        }