from app.models.schemas import TaskSpec
from app.agent.state import AgentState


def test_agent_state_creation():

    task = TaskSpec(
        task_id="invoice_001",
        goal="Process the latest invoice from Acme Components",
        required_data=[
            "invoice_id",
            "amount",
            "due_date",
        ],
        allowed_tools=[
            "browser",
            "invoice_api",
            "erp_api",
        ],
        approval_required=[
            "create_ap_record",
        ],
        postconditions=[
            "invoice_exists_in_erp",
            "amount_matches",
            "due_date_matches",
        ],
    )

    state = AgentState(
        task=task,
        current_goal=task.goal,
    )

    assert state.status == "initialized"
    assert state.current_step == 0
    assert state.retry_count == 0
    assert state.task.goal == task.goal