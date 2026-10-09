from app.agent.executor import ActionExecutor
from app.models.schemas import ActionProposal
from app.safety.policy import PolicyEngine
from app.tools.browser import BrowserTool


BASE_URL = "http://127.0.0.1:8000"


def test_executor_allows_navigation():

    browser = BrowserTool(headless=True)
    browser.start()

    try:
        executor = ActionExecutor(
            browser=browser,
            policy=PolicyEngine(),
        )

        action = ActionProposal(
            tool="browser",
            action="open",
            arguments={
                "url": f"{BASE_URL}/invoices"
            },
        )

        result = executor.execute(action)

        assert result.success is True
        assert result.source == "browser"
        assert "/invoices" in result.data["url"]

    finally:
        browser.stop()


def test_executor_blocks_submit_without_approval():

    browser = BrowserTool(headless=True)
    browser.start()

    try:
        executor = ActionExecutor(
            browser=browser,
            policy=PolicyEngine(),
        )

        action = ActionProposal(
            tool="browser",
            action="submit",
            arguments={},
        )

        result = executor.execute(action)

        assert result.success is False
        assert result.error == "APPROVAL_REQUIRED"

    finally:
        browser.stop()


def test_executor_denies_unknown_tool():

    browser = BrowserTool(headless=True)
    browser.start()

    try:
        executor = ActionExecutor(
            browser=browser,
            policy=PolicyEngine(),
        )

        action = ActionProposal(
            tool="shell",
            action="delete_database",
            arguments={},
        )

        result = executor.execute(action)

        assert result.success is False
        assert result.error == "POLICY_DENIED"

    finally:
        browser.stop()