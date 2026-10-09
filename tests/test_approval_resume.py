from app.agent.controller import AgentController
from app.agent.state import AgentState
from app.models.schemas import TaskSpec, ActionProposal
from app.tools.verification import InvoiceVerifier


class FakeExecutor:
    def __init__(self):
        self.executed = []

    def execute(self, action, approval_granted=False):
        self.executed.append((action, approval_granted))

        if action.action == "submit" and not approval_granted:
            from app.models.schemas import Observation

            return Observation(
                success=False,
                source="policy",
                message="Human approval required.",
                error="APPROVAL_REQUIRED",
            )

        from app.models.schemas import Observation

        return Observation(
            success=True,
            source="fake",
            message="Action executed.",
            data={"url": "/success"},
        )


def test_approval_state():
    task = TaskSpec(
        task_id="test-approval",
        goal="Submit invoice",
    )

    state = AgentState(task=task)

    action = ActionProposal(
        tool="browser",
        action="submit",
        arguments={"selector": "button[type='submit']"},
        reason="Submit the AP form",
        requires_approval=True,
    )

    executor = FakeExecutor()
    controller = AgentController(
        executor=executor,
        verifier=InvoiceVerifier(),
    )

    state = controller.execute_action(
        state,
        action,
        approval_granted=False,
    )

    assert state.last_observation.error == "APPROVAL_REQUIRED"

    state = controller.request_approval(
        state,
        action,
    )

    assert state.status == "waiting_for_approval"
    assert state.approval_requested is True
    assert state.approval_action == action

    state = controller.approve(state)

    assert state.approval_granted is True
    assert state.approval_requested is False
    assert state.status == "resuming"