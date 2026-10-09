from app.agent.controller import AgentController
from app.agent.executor import ActionExecutor
from app.agent.state import AgentState
from app.models.schemas import ActionProposal, TaskSpec
from app.safety.policy import PolicyEngine
from app.tools.browser import BrowserTool
from app.tools.verification import InvoiceVerifier


BASE_URL = "http://127.0.0.1:8000"


def test_controller_executes_action():

    browser = BrowserTool(headless=True)
    browser.start()

    try:
        executor = ActionExecutor(
            browser=browser,
            policy=PolicyEngine(),
        )

        controller = AgentController(
            executor=executor,
            verifier=InvoiceVerifier(),
        )

        task = TaskSpec(
            task_id="test-001",
            goal="Open the invoice portal.",
        )

        state = AgentState(task=task)

        action = ActionProposal(
            tool="browser",
            action="open",
            arguments={
                "url": f"{BASE_URL}/invoices"
            },
        )

        state = controller.execute_action(
            state,
            action,
        )

        assert state.status == "waiting_for_next_action"
        assert state.last_observation is not None
        assert state.last_observation.success is True
        assert len(state.history) == 1

    finally:
        browser.stop()
def test_controller_respects_approval_gate():

    browser = BrowserTool(headless=True)
    browser.start()

    try:
        executor = ActionExecutor(
            browser=browser,
            policy=PolicyEngine(),
        )

        controller = AgentController(
            executor=executor,
            verifier=InvoiceVerifier(),
        )

        task = TaskSpec(
            task_id="test-002",
            goal="Submit an AP invoice.",
        )

        state = AgentState(task=task)

        action = ActionProposal(
            tool="browser",
            action="submit",
            arguments={},
        )

        state = controller.execute_action(
            state,
            action,
            approval_granted=False,
        )

        assert state.status == "error"
        assert state.error == "APPROVAL_REQUIRED"

    finally:
        browser.stop()