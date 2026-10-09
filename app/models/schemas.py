from typing import Any, Literal
from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    task_id: str
    goal: str

    constraints: list[str] = Field(default_factory=list)

    required_data: list[str] = Field(default_factory=list)

    allowed_tools: list[str] = Field(default_factory=list)

    approval_required: list[str] = Field(default_factory=list)

    postconditions: list[str] = Field(default_factory=list)

    # Structured business data extracted from the task.
    parameters: dict[str, Any] = Field(default_factory=dict)


class ActionProposal(BaseModel):
    tool: str = Field(
        description="The tool to use. Must be exactly 'browser'."
    )

    action: str = Field(
        description=(
            "The browser action to perform. "
            "Must be one of: open, observe, click, fill, screenshot."
        )
    )

    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Arguments required by the browser action. "
            "For click, use {'selector': '<actual Playwright selector>'}. "
            "For fill, use {'selector': '<actual selector>', 'value': '<value>'}. "
            "For open, use {'url': '<actual URL>'}."
        ),
    )

    reason: str = Field(
        default="",
        description="Why this action is the best next action."
    )

    requires_approval: bool = Field(
        default=False,
        description="Whether human approval is required before this action."
    )


class Observation(BaseModel):
    """
    Result of executing an action.
    """

    success: bool

    source: str

    message: str = ""

    data: dict[str, Any] = Field(default_factory=dict)

    error: str | None = None


class ExecutionStep(BaseModel):
    """
    One complete action/observation cycle.
    """

    step_number: int

    action: ActionProposal

    observation: Observation


class VerificationResult(BaseModel):
    """
    Independent verification of the requested outcome.
    """

    verified: bool

    checks: dict[str, bool] = Field(default_factory=dict)

    evidence: list[str] = Field(default_factory=list)

    message: str = ""