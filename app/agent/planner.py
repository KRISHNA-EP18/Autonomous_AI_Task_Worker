import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.llm import LLMClient
from app.models.schemas import ActionProposal


class Planner:

    def __init__(self):
        self.llm = LLMClient()

    # ========================================================
    # MAIN PLANNER
    # ========================================================

    def propose_action(
        self,
        task: str,
        observation: dict,
    ) -> ActionProposal:

        system_prompt = """
You are the planning component of an autonomous enterprise task worker.

Your job is to decide EXACTLY ONE safe next browser action.

You MUST return a complete ActionProposal containing:

- tool
- action
- arguments
- reason
- requires_approval


============================================================
TOOL
============================================================

The tool MUST always be:

"browser"


============================================================
AVAILABLE ACTIONS
============================================================

Only these actions are allowed:

- open
- observe
- click
- fill
- screenshot


============================================================
GENERAL RULES
============================================================

1. Return exactly ONE action.

2. Never omit any ActionProposal field.

3. ONLY use information present in the CURRENT OBSERVATION
   and AGENT CONTEXT.

4. The observed page is the source of truth.

5. NEVER invent buttons, links, input fields, URLs,
   selectors, or page contents.

6. Never access the database.

7. Never use shell commands.

8. Never claim that the task is complete.

9. The controller independently verifies completion.

10. If the next action is unclear, use "observe" instead
    of guessing.

11. NEVER repeatedly choose "observe" when the current page
    already contains enough information for the next action.


============================================================
CLICK ACTION
============================================================

For a visible link with text "INV-1042":

{
    "selector": "a:has-text('INV-1042')"
}

For a visible button with text "Submit Invoice":

{
    "selector": "button:has-text('Submit Invoice')"
}

The selector MUST correspond to an element visible in the
CURRENT OBSERVATION.

Never output placeholder selectors such as:

"selector"
"<selector>"
"YOUR_SELECTOR"
"your_selector"
"placeholder"


============================================================
FILL ACTION
============================================================

For example:

{
    "selector": "#invoice_number",
    "value": "INV-1042"
}

The selector must correspond to an actual observed input.


============================================================
OPEN ACTION
============================================================

Known pages in this simulated company environment are:

http://127.0.0.1:8000/invoices
http://127.0.0.1:8000/ap
http://127.0.0.1:8000/ap/new

Only navigate to these application pages.


============================================================
TASK PROGRESS
============================================================

Use the CURRENT URL and AGENT CONTEXT to understand what
has already been accomplished.

If the current URL is:

/invoices/<invoice_number>

then that invoice has already been opened.

DO NOT click the same invoice link again.

For:

"Find invoice INV-1042 and add it to AP"

the normal progression is:

1. Find/open the invoice.
2. Extract its information.
3. Navigate to AP creation.
4. Fill the AP form.
5. Request human approval.
6. Submit after approval.
7. Independently verify the result.

Never repeat an action that already succeeded unless the
current page requires it.


============================================================
SUBMISSION / APPROVAL
============================================================

Submitting an AP invoice is a high-impact action.

A click on:

button:has-text('Submit Invoice')

MUST have:

requires_approval = true

Never submit an AP invoice without human approval.


============================================================
RECOVERY
============================================================

If recovery_context is present and:

previous_action_failed = true

then:

1. DO NOT repeat the failed action.
2. Inspect the CURRENT page.
3. Use the current page's actual links, buttons and inputs.
4. Choose a DIFFERENT valid action.
5. If uncertain, use "observe".

Never blindly repeat a failed action.


============================================================
OBSERVATION
============================================================

Use "observe" when:

- the current page is unclear,
- a previous action failed,
- the available controls need to be re-examined.

Do NOT repeatedly choose "observe" if the current page
already contains enough information for the next meaningful
action.


============================================================
IMPORTANT
============================================================

Do not invent an "Add to AP" button.

Only use controls actually visible in the current observation.

The visible UI is authoritative.
"""

        user_prompt = f"""
TASK:

{task}


CURRENT OBSERVATION:

{observation}


Choose exactly ONE next browser action.

The current observation and agent context are authoritative.

Before choosing click or fill:

- Check actual observed links.
- Check actual observed buttons.
- Check actual observed inputs.
- Make sure the selector corresponds to a real element.

If the current URL already contains the invoice number,
do NOT click that invoice link again.

If recovery_context is present:

- The previous action failed.
- Do NOT repeat it.
- Choose a different action based on the current page.

If uncertain, use "observe" instead of guessing.
"""

        structured_model = self.llm.model.with_structured_output(
            ActionProposal,
            method="json_schema",
            strict=True,
        )

        response = structured_model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

        # ----------------------------------------------------
        # Deterministic repair
        # ----------------------------------------------------

        response = self._repair_action(
            response,
            task,
            observation,
        )

        # ----------------------------------------------------
        # Deterministic grounding
        # ----------------------------------------------------

        response = self._ground_action(
            response,
            observation,
        )

        # ----------------------------------------------------
        # Final validation
        # ----------------------------------------------------

        return self._validate_action(response)

    # ========================================================
    # REPAIR MALFORMED ACTIONS
    # ========================================================

    def _repair_action(
        self,
        action: ActionProposal,
        task: str,
        observation: dict,
    ) -> ActionProposal:

        # ====================================================
        # OPEN ACTION
        # ====================================================

        if action.action == "open":

            url = action.arguments.get("url")

            if url is not None:
                url = str(url).strip().strip("'\"")
                action.arguments["url"] = url

            allowed_urls = {
                "http://127.0.0.1:8000/invoices",
                "http://127.0.0.1:8000/ap",
                "http://127.0.0.1:8000/ap/new",
            }

            current_url = observation.get("url", "")

            # ------------------------------------------------
            # Already valid
            # ------------------------------------------------

            if url in allowed_urls:
                return action

            # ------------------------------------------------
            # Invoice detail page
            # ------------------------------------------------

            if "/invoices/" in current_url:

                action.arguments["url"] = (
                    "http://127.0.0.1:8000/ap/new"
                )

                action.reason = (
                    "The invoice has already been opened. "
                    "Navigate to the AP invoice creation form."
                )

                return action

            # ------------------------------------------------
            # Invoice portal → AP creation
            # ------------------------------------------------

            if (
                "/invoices" in current_url
                and "ap" in task.lower()
                and "add" in task.lower()
            ):

                action.arguments["url"] = (
                    "http://127.0.0.1:8000/ap/new"
                )

                action.reason = (
                    "Navigate from the invoice portal "
                    "to the AP invoice creation form."
                )

                return action

            # ------------------------------------------------
            # AP portal → AP creation
            # ------------------------------------------------

            if current_url.endswith("/ap"):

                action.arguments["url"] = (
                    "http://127.0.0.1:8000/ap/new"
                )

                action.reason = (
                    "Open the AP invoice creation form."
                )

                return action

            # ------------------------------------------------
            # Safe fallback
            # ------------------------------------------------

            return ActionProposal(
                tool="browser",
                action="observe",
                arguments={},
                reason=(
                    "The proposed URL is not an approved "
                    "application URL. Re-observe the page "
                    "before navigating."
                ),
                requires_approval=False,
            )

        # ====================================================
        # CLICK ACTION
        # ====================================================

        if action.action != "click":
            return action

        selector = action.arguments.get("selector")

        if selector is not None:
            selector = str(selector).strip().strip("'\"")

        invalid_selectors = {
            None,
            "",
            "selector",
            "<selector>",
            "YOUR_SELECTOR",
            "your_selector",
            "placeholder",
            "<your_selector>",
            "your selector",
        }

        if (
            selector is not None
            and selector.lower() in {
                str(value).lower()
                for value in invalid_selectors
            }
        ):
            selector = None

        # ----------------------------------------------------
        # Already valid
        # ----------------------------------------------------

        if selector is not None:
            action.arguments["selector"] = selector
            return action

        # ----------------------------------------------------
        # Extract invoice number
        # ----------------------------------------------------

        invoice_match = re.search(
            r"\b(?:INV|NOV|VT)-\d+(?:-[A-Z0-9]+)?\b",
            task,
            re.IGNORECASE,
        )

        invoice_number = None

        if invoice_match:
            invoice_number = invoice_match.group(0).upper()

        # ----------------------------------------------------
        # Repair from observed links
        # ----------------------------------------------------

        links = observation.get("links", [])

        if invoice_number:

            for link in links:

                link_text = str(link).strip()

                if invoice_number.lower() in link_text.lower():

                    action.arguments["selector"] = (
                        f"a:has-text('{link_text}')"
                    )

                    action.reason = (
                        f"Open the observed invoice link "
                        f"{link_text}."
                    )

                    return action

        # ----------------------------------------------------
        # Repair from observed buttons
        # ----------------------------------------------------

        buttons = observation.get("buttons", [])

        for button in buttons:

            button_text = str(button).strip()

            if not button_text:
                continue

            # Prefer submit button when it is visible.
            if "submit" in button_text.lower():

                action.arguments["selector"] = (
                    f"button:has-text('{button_text}')"
                )

                action.requires_approval = True

                action.reason = (
                    f"Submit the AP invoice using the "
                    f"observed '{button_text}' button."
                )

                return action

            if button_text.lower() in task.lower():

                action.arguments["selector"] = (
                    f"button:has-text('{button_text}')"
                )

                action.reason = (
                    f"Click the observed button "
                    f"{button_text}."
                )

                return action

        # ----------------------------------------------------
        # Safe fallback
        # ----------------------------------------------------

        return ActionProposal(
            tool="browser",
            action="observe",
            arguments={},
            reason=(
                "The proposed selector was invalid and could "
                "not be safely repaired. Re-observe the "
                "current page."
            ),
            requires_approval=False,
        )

    # ========================================================
    # GROUND ACTION AGAINST CURRENT OBSERVATION
    # ========================================================

    def _ground_action(
        self,
        action: ActionProposal,
        observation: dict,
    ) -> ActionProposal:

        current_url = observation.get("url", "")

        agent_context = observation.get(
            "agent_context",
            {},
        )

        task_parameters = agent_context.get(
            "task_parameters",
            {},
        )

        completed_actions = agent_context.get(
            "completed_actions",
            [],
        )

        # ====================================================
        # DETERMINISTIC AP FORM PROGRESSION
        # ====================================================

        if "/ap/new" in current_url:

            required_fields = [
                ("invoice_number", "#invoice_number"),
                ("vendor", "#vendor"),
                ("amount", "#amount"),
                ("currency", "#currency"),
                ("due_date", "#due_date"),
            ]

            observed_inputs = observation.get(
                "inputs",
                [],
            )

            observed_ids = {
                str(field.get("id"))
                for field in observed_inputs
                if field.get("id")
            }

            observed_names = {
                str(field.get("name"))
                for field in observed_inputs
                if field.get("name")
            }

            # ------------------------------------------------
            # Determine which fields have already been filled
            # successfully.
            # ------------------------------------------------

            filled_fields = set()

            for completed in completed_actions:

                if not completed.get("success"):
                    continue

                if completed.get("action") != "fill":
                    continue

                arguments = completed.get(
                    "arguments",
                    {},
                )

                selector = str(
                    arguments.get("selector", "")
                ).strip()

                for field_name, field_selector in required_fields:

                    if selector == field_selector:
                        filled_fields.add(field_name)

                    if selector == f"[name='{field_name}']":
                        filled_fields.add(field_name)

            # ------------------------------------------------
            # Fill the first missing required field.
            # ------------------------------------------------

            for field_name, field_selector in required_fields:

                if field_name in filled_fields:
                    continue

                value = task_parameters.get(field_name)

                if value is None:
                    continue

                if field_name not in observed_ids and \
                   field_name not in observed_names:
                    continue

                return ActionProposal(
                    tool="browser",
                    action="fill",
                    arguments={
                        "selector": field_selector,
                        "value": str(value),
                    },
                    reason=(
                        f"Fill the next required AP field: "
                        f"{field_name}."
                    ),
                    requires_approval=False,
                )

            # ------------------------------------------------
            # All required fields are filled.
            #
            # If the submit button is visible, select it
            # deterministically instead of allowing the LLM
            # to enter an observe loop.
            # ------------------------------------------------

            buttons = observation.get(
                "buttons",
                [],
            )

            for button in buttons:

                button_text = str(button).strip()

                if "submit" in button_text.lower():

                    return ActionProposal(
                        tool="browser",
                        action="click",
                        arguments={
                            "selector": (
                                f"button:has-text('{button_text}')"
                            )
                        },
                        reason=(
                            "All required AP invoice fields "
                            "have been filled. Human approval "
                            "is required before submission."
                        ),
                        requires_approval=True,
                    )

        # ====================================================
        # FILL ACTION GROUNDING
        # ====================================================

        if action.action == "fill":

            selector = str(
                action.arguments.get("selector", "")
            ).strip()

            value = action.arguments.get("value")

            inputs = observation.get(
                "inputs",
                [],
            )

            observed_selectors = set()

            for field in inputs:

                field_id = field.get("id")
                field_name = field.get("name")

                if field_id:
                    observed_selectors.add(
                        f"#{field_id}"
                    )

                if field_name:
                    observed_selectors.add(
                        f"[name='{field_name}']"
                    )

            # ------------------------------------------------
            # Already valid
            # ------------------------------------------------

            if selector in observed_selectors:
                return action

            # ------------------------------------------------
            # Match value against task parameters
            # ------------------------------------------------

            field_order = [
                "invoice_number",
                "vendor",
                "amount",
                "currency",
                "due_date",
            ]

            for field_name in field_order:

                expected_value = task_parameters.get(
                    field_name
                )

                if expected_value is None:
                    continue

                if value is None:
                    continue

                if (
                    str(value).strip()
                    == str(expected_value).strip()
                ):

                    if field_name in {
                        field.get("id")
                        for field in inputs
                    }:

                        action.arguments["selector"] = (
                            f"#{field_name}"
                        )

                        action.arguments["value"] = str(
                            expected_value
                        )

                        action.reason = (
                            f"Fill the observed "
                            f"{field_name} field with "
                            f"the task value."
                        )

                        return action

                    if field_name in {
                        field.get("name")
                        for field in inputs
                    }:

                        action.arguments["selector"] = (
                            f"[name='{field_name}']"
                        )

                        action.arguments["value"] = str(
                            expected_value
                        )

                        action.reason = (
                            f"Fill the observed "
                            f"{field_name} field with "
                            f"the task value."
                        )

                        return action

            # ------------------------------------------------
            # Match selector text to a known field
            # ------------------------------------------------

            selector_lower = selector.lower()

            field_aliases = {
                "invoice": "invoice_number",
                "invoice_number": "invoice_number",
                "vendor": "vendor",
                "amount": "amount",
                "currency": "currency",
                "due": "due_date",
                "due_date": "due_date",
            }

            for alias, field_name in field_aliases.items():

                if alias not in selector_lower:
                    continue

                if field_name in {
                    field.get("id")
                    for field in inputs
                }:

                    action.arguments["selector"] = (
                        f"#{field_name}"
                    )

                    return action

            # ------------------------------------------------
            # Could not safely ground fill
            # ------------------------------------------------

            return ActionProposal(
                tool="browser",
                action="observe",
                arguments={},
                reason=(
                    "The proposed fill selector was not "
                    "grounded to an observed input. "
                    "Re-observing the form."
                ),
                requires_approval=False,
            )

        # ====================================================
        # CLICK ACTION GROUNDING
        # ====================================================

        if action.action != "click":
            return action

        selector = action.arguments.get(
            "selector",
            "",
        )

        selector = str(selector).strip()

        links = [
            str(link).strip()
            for link in observation.get(
                "links",
                [],
            )
        ]

        buttons = [
            str(button).strip()
            for button in observation.get(
                "buttons",
                [],
            )
        ]

        # ----------------------------------------------------
        # Ground link selector
        # ----------------------------------------------------

        link_match = re.search(
            r"a:has-text\(['\"](.+?)['\"]\)",
            selector,
        )

        if link_match:

            requested_text = (
                link_match.group(1).strip()
            )

            exists = any(
                requested_text.lower() in link.lower()
                for link in links
            )

            if not exists:

                return ActionProposal(
                    tool="browser",
                    action="observe",
                    arguments={},
                    reason=(
                        f"The requested link "
                        f"'{requested_text}' is not present "
                        "on the current page. Re-observing."
                    ),
                    requires_approval=False,
                )

        # ----------------------------------------------------
        # Ground button selector
        # ----------------------------------------------------

        button_match = re.search(
            r"button:has-text\(['\"](.+?)['\"]\)",
            selector,
        )

        if button_match:

            requested_text = (
                button_match.group(1).strip()
            )

            exists = any(
                requested_text.lower() in button.lower()
                for button in buttons
            )

            if not exists:

                return ActionProposal(
                    tool="browser",
                    action="observe",
                    arguments={},
                    reason=(
                        f"The requested button "
                        f"'{requested_text}' is not present "
                        "on the current page. Re-observing."
                    ),
                    requires_approval=False,
                )

            if "submit" in requested_text.lower():
                action.requires_approval = True

        return action

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    def _validate_action(
        self,
        action: ActionProposal,
    ) -> ActionProposal:

        # ----------------------------------------------------
        # TOOL
        # ----------------------------------------------------

        if action.tool != "browser":

            raise ValueError(
                f"Invalid tool proposed: {action.tool}"
            )

        # ----------------------------------------------------
        # ACTION
        # ----------------------------------------------------

        allowed_actions = {
            "open",
            "observe",
            "click",
            "fill",
            "screenshot",
        }

        if action.action not in allowed_actions:

            raise ValueError(
                f"Invalid browser action: {action.action}"
            )

        # ----------------------------------------------------
        # CLICK
        # ----------------------------------------------------

        if action.action == "click":

            selector = action.arguments.get(
                "selector"
            )

            if not isinstance(selector, str):

                raise ValueError(
                    "Planner returned an invalid click selector."
                )

            if not selector.strip():

                raise ValueError(
                    "Planner returned an empty click selector."
                )

        # ----------------------------------------------------
        # FILL
        # ----------------------------------------------------

        if action.action == "fill":

            selector = action.arguments.get(
                "selector"
            )

            value = action.arguments.get(
                "value"
            )

            if not isinstance(selector, str):

                raise ValueError(
                    "Planner returned an invalid fill selector."
                )

            if not selector.strip():

                raise ValueError(
                    "Planner returned an empty fill selector."
                )

            if value is None:

                raise ValueError(
                    "Planner returned a fill action "
                    "without a value."
                )

        # ----------------------------------------------------
        # OPEN
        # ----------------------------------------------------

        if action.action == "open":

            url = action.arguments.get(
                "url"
            )

            if not isinstance(url, str):

                raise ValueError(
                    "Planner returned an invalid URL."
                )

            url = url.strip()

            allowed_urls = {
                "http://127.0.0.1:8000/invoices",
                "http://127.0.0.1:8000/ap",
                "http://127.0.0.1:8000/ap/new",
            }

            if url not in allowed_urls:

                raise ValueError(
                    f"Planner proposed an unapproved URL: {url}"
                )

        # ----------------------------------------------------
        # SUBMISSION APPROVAL
        # ----------------------------------------------------

        if action.action == "click":

            selector = str(
                action.arguments.get(
                    "selector",
                    "",
                )
            ).lower()

            if "submit" in selector:

                action.requires_approval = True

        return action