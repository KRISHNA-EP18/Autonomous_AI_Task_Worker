from app.models.schemas import ActionProposal
from app.safety.policy import PolicyEngine


def test_safe_browser_action_is_allowed():

    policy = PolicyEngine()

    action = ActionProposal(
        tool="browser",
        action="open",
        arguments={
            "url": "http://127.0.0.1:8000/invoices"
        },
    )

    assert policy.evaluate(action) == "ALLOW"


def test_submit_requires_approval():

    policy = PolicyEngine()

    action = ActionProposal(
        tool="browser",
        action="submit",
        arguments={
            "invoice_number": "INV-1042"
        },
    )

    assert policy.evaluate(action) == "ASK"


def test_unknown_action_is_denied():

    policy = PolicyEngine()

    action = ActionProposal(
        tool="shell",
        action="delete_database",
        arguments={},
    )

    assert policy.evaluate(action) == "DENY"