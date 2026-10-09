from typing import Any
from pydantic import BaseModel, Field

from app.models.schemas import (
    TaskSpec,
    ActionProposal,
    Observation,
    ExecutionStep,
    VerificationResult,
)


class AgentState(BaseModel):
    task: TaskSpec
    status: str = "initialized"
    current_step: int = 0

    plan: list[str] = Field(default_factory=list)
    current_goal: str = ""

    memory: dict[str, Any] = Field(default_factory=dict)
    observations: list[Observation] = Field(default_factory=list)
    history: list[ExecutionStep] = Field(default_factory=list)

    last_action: ActionProposal | None = None
    last_observation: Observation | None = None
    verification: VerificationResult | None = None

    approval_granted: bool = False
    approval_requested: bool = False
    approval_action: ActionProposal | None = None
    approval_message: str = ""

    retry_count: int = 0
    max_retries: int = 3

    error: str | None = None