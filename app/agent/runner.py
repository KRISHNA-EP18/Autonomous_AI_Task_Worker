from app.agent.controller import AgentController
from app.agent.planner import Planner
from app.agent.state import AgentState


class AgentRunner:

    def __init__(
        self,
        controller: AgentController,
        planner: Planner,
        max_steps: int = 12,
    ):
        self.controller = controller
        self.planner = planner
        self.max_steps = max_steps

    # ========================================================
    # MAIN RUN LOOP
    # ========================================================

    def run(
        self,
        state: AgentState,
        initial_observation: dict,
    ):

        observation = initial_observation

        for _ in range(self.max_steps):

            # ------------------------------------------------
            # Terminal states
            # ------------------------------------------------

            if state.status in {
                "error",
                "completed",
                "verification_failed",
                "cancelled",
            }:
                break

            # ------------------------------------------------
            # Human approval pauses execution
            # ------------------------------------------------

            if state.status == "waiting_for_approval":
                break

            # ------------------------------------------------
            # Build planner context
            # ------------------------------------------------

            planner_observation = dict(
                observation
            )

            planner_observation[
                "agent_context"
            ] = {

                "current_step": state.current_step,

                "retry_count": state.retry_count,

                "last_action": (
                    {
                        "tool": state.last_action.tool,
                        "action": state.last_action.action,
                        "arguments": (
                            state.last_action.arguments
                        ),
                    }
                    if state.last_action
                    else None
                ),

                "task_parameters": (
                    state.task.parameters
                ),

                "completed_actions": [
                    {
                        "action": (
                            step.action.action
                        ),

                        "arguments": (
                            step.action.arguments
                        ),

                        "success": (
                            step.observation.success
                        ),
                    }

                    for step in state.history
                ],
            }

            # ------------------------------------------------
            # Ask planner for exactly one action
            # ------------------------------------------------

            action = self.planner.propose_action(
                task=state.task.goal,
                observation=planner_observation,
            )

            # ------------------------------------------------
            # Prevent endless observation loops
            # ------------------------------------------------

            if action.action == "observe":

                consecutive_observes = 0

                for step in reversed(
                    state.history
                ):

                    if (
                        step.action.action
                        == "observe"
                    ):
                        consecutive_observes += 1

                    else:
                        break

                if consecutive_observes >= 2:

                    # Take one fresh browser observation
                    # instead of allowing the planner to
                    # consume all remaining steps.

                    try:

                        fresh_observation = (
                            self.controller
                            .executor
                            .browser
                            .observe()
                        )

                        observation = (
                            fresh_observation
                        )

                        state.retry_count += 1

                        if state.retry_count > 2:

                            state.status = "error"

                            state.error = (
                                "PLANNER_STALLED_ON_OBSERVATION"
                            )

                            break

                        continue

                    except Exception as exc:

                        state.status = "error"

                        state.error = (
                            "OBSERVATION_FAILED: "
                            f"{exc}"
                        )

                        break

            # ------------------------------------------------
            # Execute action
            # ------------------------------------------------

            state = self.controller.execute_action(
                state=state,
                action=action,
                approval_granted=(
                    state.approval_granted
                ),
            )

            # ------------------------------------------------
            # Approval required
            # ------------------------------------------------

            if (
                state.last_observation
                and
                state.last_observation.error
                == "APPROVAL_REQUIRED"
            ):

                state = (
                    self.controller.request_approval(
                        state,
                        action,
                    )
                )

                break

            # ------------------------------------------------
            # Action failed
            # ------------------------------------------------

            if (
                state.last_observation is None
                or
                not state.last_observation.success
            ):

                state, observation = (
                    self.handle_failure(
                        state
                    )
                )

                if state.status == "error":
                    break

                continue

            # ------------------------------------------------
            # Successful action
            # ------------------------------------------------

            state.retry_count = 0

            observation = (
                state.last_observation.data
            )

            # ------------------------------------------------
            # Extract invoice information
            # ------------------------------------------------

            url = observation.get(
                "url",
                "",
            )

            if "/invoices/" in url:

                state = (
                    self.controller
                    .extract_invoice_data(
                        state
                    )
                )

                # Refresh planner observation with
                # the newly extracted parameters.

                observation = (
                    state.last_observation.data
                    if state.last_observation
                    else observation
                )

            # ------------------------------------------------
            # Check whether browser indicates submission
            # succeeded.
            # ------------------------------------------------

            if self.controller.should_verify(
                state
            ):

                parameters = (
                    state.task.parameters
                )

                required = [
                    "invoice_number",
                    "vendor",
                    "amount",
                    "currency",
                    "due_date",
                ]

                missing = [
                    key
                    for key in required
                    if key not in parameters
                ]

                if missing:

                    state.status = (
                        "verification_failed"
                    )

                    state.error = (
                        "Missing verification parameters: "
                        + ", ".join(missing)
                    )

                    break

                state = (
                    self.controller.verify_invoice(
                        state,
                        invoice_number=(
                            parameters[
                                "invoice_number"
                            ]
                        ),
                        expected_vendor=(
                            parameters[
                                "vendor"
                            ]
                        ),
                        expected_amount=float(
                            parameters[
                                "amount"
                            ]
                        ),
                        expected_currency=(
                            parameters[
                                "currency"
                            ]
                        ),
                        expected_due_date=(
                            parameters[
                                "due_date"
                            ]
                        ),
                    )
                )

                break

        # ====================================================
        # MAX STEPS
        # ====================================================

        if state.status not in {
            "completed",
            "waiting_for_approval",
            "verification_failed",
            "cancelled",
            "error",
        }:

            state.status = "error"

            state.error = (
                "MAX_STEPS_EXCEEDED"
            )

        return state

    # ========================================================
    # RESUME AFTER HUMAN APPROVAL
    # ========================================================

    def resume(self, state: AgentState):

        if state.status != "waiting_for_approval":
            return state

        # ========================================================
        # IMPORTANT STREAMLIT / PLAYWRIGHT FIX
        # ========================================================
        #
        # Streamlit reruns the script after the Approve button.
        # The previous sync Playwright browser belongs to the
        # previous Streamlit execution thread.
        #
        # Therefore we MUST create a fresh browser here instead
        # of reusing the old BrowserTool.
        # ========================================================

        from app.tools.browser import BrowserTool
        from app.agent.executor import ActionExecutor
        from app.safety.policy import PolicyEngine

        try:

            # ----------------------------------------------------
            # Create a fresh browser in the CURRENT Streamlit
            # thread.
            # ----------------------------------------------------

            new_browser = BrowserTool(
                headless=False
            )

            new_browser.start()

            # ----------------------------------------------------
            # Replace the old browser inside the executor.
            # ----------------------------------------------------

            self.controller.executor.browser = new_browser

            # ----------------------------------------------------
            # Grant approval.
            # ----------------------------------------------------

            state = self.controller.approve(state)

            # ----------------------------------------------------
            # Recover the invoice information from agent memory.
            # ----------------------------------------------------

            parameters = state.task.parameters

            required = [
                "invoice_number",
                "vendor",
                "amount",
                "currency",
                "due_date",
            ]

            missing = [
                key
                for key in required
                if key not in parameters
            ]

            if missing:

                state.status = "verification_failed"

                state.error = (
                    "Missing parameters after approval: "
                    + ", ".join(missing)
                )

                new_browser.stop()

                return state

            # ----------------------------------------------------
            # Reconstruct the AP creation page.
            # ----------------------------------------------------

            observation = new_browser.open(
                "http://127.0.0.1:8000/ap/new"
            )

            # ----------------------------------------------------
            # Re-fill the form from verified agent memory.
            #
            # These are deterministic actions. We do NOT ask the
            # LLM to reconstruct them.
            # ----------------------------------------------------

            fields = [
                (
                    "#invoice_number",
                    str(parameters["invoice_number"]),
                ),
                (
                    "#vendor",
                    str(parameters["vendor"]),
                ),
                (
                    "#amount",
                    str(parameters["amount"]),
                ),
                (
                    "#currency",
                    str(parameters["currency"]),
                ),
                (
                    "#due_date",
                    str(parameters["due_date"]),
                ),
            ]

            for selector, value in fields:

                result = new_browser.fill(
                    selector,
                    value,
                )

                if not result:

                    state.status = "error"

                    state.error = (
                        f"Failed to refill AP field: "
                        f"{selector}"
                    )

                    new_browser.stop()

                    return state

            # ----------------------------------------------------
            # Execute the previously approved submission.
            # ----------------------------------------------------

            approved_action = state.last_action

            # We deliberately use a deterministic selector.
            #
            # Human approval was already granted above.
            # ----------------------------------------------------

            from app.models.schemas import ActionProposal

            submit_action = ActionProposal(
                tool="browser",
                action="click",
                arguments={
                    "selector": (
                        "button:has-text('Submit Invoice')"
                    )
                },
                reason=(
                    "Submit the AP invoice after explicit "
                    "human approval."
                ),
                requires_approval=True,
            )

            state = self.controller.execute_action(
                state=state,
                action=submit_action,
                approval_granted=True,
            )

            # ----------------------------------------------------
            # Check execution result.
            # ----------------------------------------------------

            if (
                state.last_observation is None
                or not state.last_observation.success
            ):

                state.status = "error"

                state.error = (
                    state.last_observation.error
                    if state.last_observation
                    else "SUBMISSION_FAILED"
                )

                new_browser.stop()

                return state

            # ----------------------------------------------------
            # Independent verification.
            # ----------------------------------------------------

            state = self.controller.verify_invoice(
                state,
                invoice_number=(
                    parameters["invoice_number"]
                ),
                expected_vendor=(
                    parameters["vendor"]
                ),
                expected_amount=float(
                    parameters["amount"]
                ),
                expected_currency=(
                    parameters["currency"]
                ),
                expected_due_date=(
                    parameters["due_date"]
                ),
            )

            # ----------------------------------------------------
            # Keep browser alive long enough for Streamlit to
            # display the final state.
            #
            # Do not call stop() here.
            # ----------------------------------------------------

            return state

        except Exception as exc:

            state.status = "error"

            state.error = (
                f"APPROVAL_RESUME_FAILED: {exc}"
            )

            return state

    # ========================================================
    # FAILURE RECOVERY
    # ========================================================

    def handle_failure(
        self,
        state: AgentState,
    ):

        state.retry_count += 1

        # ----------------------------------------------------
        # Retry limit
        # ----------------------------------------------------

        if (
            state.retry_count
            > state.max_retries
        ):

            state.status = "error"

            state.error = (
                "MAX_RETRIES_EXCEEDED"
            )

            return state, {}

        # ----------------------------------------------------
        # Re-observe browser after failure
        # ----------------------------------------------------

        try:

            recovery_observation = (
                self.controller
                .executor
                .browser
                .observe()
            )

            failed_action = (
                state.last_action
            )

            failed_action_data = (

                {
                    "tool": failed_action.tool,
                    "action": failed_action.action,
                    "arguments": (
                        failed_action.arguments
                    ),
                }

                if failed_action
                else None
            )

            failure_reason = (

                state.last_observation.error

                if state.last_observation

                else "Unknown failure"
            )

            recovery_observation[
                "recovery_context"
            ] = {

                "previous_action_failed": True,

                "failed_action": (
                    failed_action_data
                ),

                "failure_reason": (
                    failure_reason
                ),

                "instruction": (
                    "DO NOT repeat the failed action. "
                    "Re-examine the current page and "
                    "choose a different valid action "
                    "based only on the observed UI."
                ),
            }

            state.status = "recovering"

            return (
                state,
                recovery_observation,
            )

        except Exception as exc:

            state.status = "error"

            state.error = (
                "RECOVERY_OBSERVATION_FAILED: "
                f"{exc}"
            )

            return state, {}