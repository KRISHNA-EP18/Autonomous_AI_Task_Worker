from app.agent.state import AgentState
from app.agent.executor import ActionExecutor
from app.models.schemas import (
    ActionProposal,
    ExecutionStep,
)
from app.tools.verification import InvoiceVerifier
from app.agent.invoice_extractor import InvoiceExtractor
class AgentController:

    def __init__(
        self,
        executor: ActionExecutor,
        verifier: InvoiceVerifier,
    ):
        self.executor = executor
        self.verifier = verifier
        self.invoice_extractor = InvoiceExtractor()
    def execute_action(
        self,
        state: AgentState,
        action: ActionProposal,
        approval_granted: bool = False,
    ) -> AgentState:

        state.status = "executing"
        state.current_step += 1
        state.last_action = action

        observation = self.executor.execute(
            action,
            approval_granted=approval_granted,
        )

        state.last_observation = observation
        state.observations.append(observation)

        state.history.append(
            ExecutionStep(
                step_number=state.current_step,
                action=action,
                observation=observation,
            )
        )

        if observation.success:
            state.status = "waiting_for_next_action"
            state.retry_count = 0

        else:
            state.status = "error"
            state.error = observation.error

        return state

    def verify_invoice(
        self,
        state,
        invoice_number,
        expected_vendor,
        expected_amount,
        expected_currency,
        expected_due_date,
    ):
        state.status = "verifying"

        result = self.verifier.verify_ap_invoice(
            invoice_number=invoice_number,
            expected_vendor=expected_vendor,
            expected_amount=expected_amount,
            expected_currency=expected_currency,
            expected_due_date=expected_due_date,
        )

        state.verification = result

        if result.verified:
            state.status = "completed"
            state.error = None
        else:
            state.status = "verification_failed"
            state.error = result.message

        return state
    def should_verify(self, state: AgentState) -> bool:

     if not state.last_observation:
        return False

     if not state.last_observation.success:
        return False

     text = state.last_observation.data.get(
        "text",
        ""
     )

     return (
        "Invoice Submitted Successfully" in text
        or "Invoice submitted successfully" in text
    )
    def extract_invoice_data(
    self,
    state: AgentState,
) -> AgentState:

        if not state.last_observation:
            return state

        observation = state.last_observation.data

        invoice = self.invoice_extractor.extract(
            observation
        )

        if not invoice:
            state.error = "Could not extract invoice data."
            return state

        state.memory["invoice"] = invoice

        # Put the extracted source data into the task
        # parameters so the verifier can use it later.
        state.task.parameters.update(invoice)

        return state
    def request_approval(self, state, action):
        state.status = "waiting_for_approval"
        state.approval_requested = True
        state.approval_action = action
        state.approval_message = (
            f"Approval required before executing "
            f"{action.tool}.{action.action}"
        )
        return state
    def approve(self, state):
        state.approval_granted = True
        state.approval_requested = False
        state.approval_action = None
        state.status = "resuming"

        return state
    def reject(self, state):
        state.approval_granted = False
        state.approval_requested = False
        state.approval_message = "Human approval was rejected."
        state.status = "cancelled"
        state.error = "ACTION_REJECTED_BY_HUMAN"
        return state