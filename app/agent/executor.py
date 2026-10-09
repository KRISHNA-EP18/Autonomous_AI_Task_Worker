from typing import Any

from app.models.schemas import ActionProposal, Observation
from app.safety.policy import PolicyEngine
from app.tools.browser import BrowserTool


class ActionExecutor:
    def __init__(
        self,
        browser: BrowserTool,
        policy: PolicyEngine,
    ):
        self.browser = browser
        self.policy = policy

    def execute(
        self,
        action: ActionProposal,
        approval_granted: bool = False,
    ) -> Observation:

        decision = self.policy.evaluate(action)

        # -----------------------------------------
        # DENY
        # -----------------------------------------

        if decision == "DENY":
            return Observation(
                success=False,
                source="policy",
                message="Action denied by policy.",
                error="POLICY_DENIED",
            )

        # -----------------------------------------
        # ASK
        # -----------------------------------------

        if decision == "ASK" and not approval_granted:
            return Observation(
                success=False,
                source="policy",
                message="Human approval required.",
                error="APPROVAL_REQUIRED",
            )

        # -----------------------------------------
        # Execute browser action
        # -----------------------------------------

        if action.tool != "browser":
            return Observation(
                success=False,
                source="executor",
                message="Unsupported tool.",
                error="UNSUPPORTED_TOOL",
            )

        try:

            if action.action == "open":

                result = self.browser.open(
                    action.arguments["url"]
                )

            elif action.action == "observe":

                result = self.browser.observe()

            elif action.action == "click":

                result = self.browser.click(
                    action.arguments["selector"]
                )

            elif action.action == "fill":

                result = self.browser.fill(
                    action.arguments["selector"],
                    action.arguments["value"],
                )

            elif action.action == "screenshot":

                result = self.browser.screenshot(
                    action.arguments["path"]
                )

            else:

                return Observation(
                    success=False,
                    source="executor",
                    message="Unknown browser action.",
                    error="UNKNOWN_BROWSER_ACTION",
                )

            return Observation(
                success=True,
                source="browser",
                message=f"Browser action '{action.action}' executed.",
                data=result,
            )

        except Exception as exc:

            return Observation(
                success=False,
                source="browser",
                message="Browser action failed.",
                error=str(exc),
            )