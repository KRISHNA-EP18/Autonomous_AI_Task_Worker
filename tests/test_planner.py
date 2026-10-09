from app.agent.planner import Planner


def test_planner_returns_action():

    planner = Planner()

    observation = {
        "url": "http://127.0.0.1:8000/invoices",
        "title": "Invoice Portal",
        "text": """
        Company Invoice Portal

        INV-1043
        INV-1042
        INV-1041
        """,
        "links": [
            "INV-1043",
            "INV-1042",
            "INV-1041",
        ],
        "buttons": [
            "Search",
        ],
        "inputs": [
            {
                "type": "text",
                "name": "vendor",
                "id": "vendor",
            }
        ],
    }

    action = planner.propose_action(
        task="Find invoice INV-1042.",
        observation=observation,
    )

    assert action.tool == "browser"
    assert action.action in {
        "open",
        "observe",
        "click",
        "fill",
        "screenshot",
    }