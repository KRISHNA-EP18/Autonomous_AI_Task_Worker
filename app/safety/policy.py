from typing import Literal

from app.models.schemas import ActionProposal


PolicyDecision = Literal["ALLOW", "ASK", "DENY"]


class PolicyEngine:

    def evaluate(
        self,
        action: ActionProposal,
    ) -> PolicyDecision:

        if action.tool != "browser":
            return "DENY"

        # Explicit submission action.
        if action.action == "submit":
            return "ASK"

        # Browser click actions.
        if action.action == "click":

            selector = action.arguments.get(
                "selector",
                "",
            )

            # Clicking a submit button changes company data.
            if "submit" in selector.lower():
                return "ASK"

            return "ALLOW"

        # Safe browser operations.
        if action.action in {
            "open",
            "observe",
            "fill",
            "screenshot",
        }:
            return "ALLOW"

        return "DENY"