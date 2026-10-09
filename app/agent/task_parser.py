import re

from app.models.schemas import TaskSpec


class TaskParser:

    def parse(self, task_text: str) -> TaskSpec:

        invoice_match = re.search(
            r"\b(?:INV|NOV|VT)-\d+\b",
            task_text,
            re.IGNORECASE,
        )

        invoice_number = (
            invoice_match.group(0).upper()
            if invoice_match
            else None
        )

        parameters = {}

        if invoice_number:
            parameters["invoice_number"] = invoice_number

        return TaskSpec(
            task_id="task-001",
            goal=task_text,
            required_data=[
                "invoice_number",
                "vendor",
                "amount",
                "currency",
                "due_date",
            ],
            allowed_tools=[
                "browser",
            ],
            approval_required=[
                "submit_ap_invoice",
            ],
            postconditions=[
                "AP invoice exists",
                "vendor matches source invoice",
                "amount matches source invoice",
                "currency matches source invoice",
                "due date matches source invoice",
            ],
            parameters=parameters,
        )