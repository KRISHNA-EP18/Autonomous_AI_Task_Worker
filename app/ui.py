import streamlit as st

from app.agent.controller import AgentController
from app.agent.planner import Planner
import streamlit as st

from app.agent.controller import AgentController
from app.agent.planner import Planner
from app.agent.runner import AgentRunner
from app.agent.state import AgentState
from app.agent.executor import ActionExecutor
from app.agent.task_parser import TaskParser

from app.safety.policy import PolicyEngine
from app.tools.browser import BrowserTool
from app.tools.verification import InvoiceVerifier


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="CentrAlign AI Worker",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🤖 CentrAlign AI Worker")

st.caption(
    "Autonomous enterprise task execution with "
    "planning, browser automation, human approval, "
    "failure recovery, and independent verification."
)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "agent_state" not in st.session_state:
    st.session_state.agent_state = None

if "browser" not in st.session_state:
    st.session_state.browser = None

if "runner" not in st.session_state:
    st.session_state.runner = None

if "task_text" not in st.session_state:
    st.session_state.task_text = ""


# ============================================================
# TASK INPUT
# ============================================================

st.subheader("Task")

task_text = st.text_input(
    "Describe the task",
    value="Find invoice INV-1042 and add it to AP.",
    placeholder="Example: Find invoice INV-1042 and add it to AP.",
)


# ============================================================
# START TASK
# ============================================================

if st.button("▶ Run Task", type="primary"):

    # Save task text
    st.session_state.task_text = task_text

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    st.info("🤖 Starting agent...")

    try:

        # ----------------------------------------------------
        # Browser
        # ----------------------------------------------------

        browser = BrowserTool(headless=True)

        browser.start()

        st.info("🌐 Browser started.")

        # ----------------------------------------------------
        # Policy
        # ----------------------------------------------------

        policy = PolicyEngine()

        # ----------------------------------------------------
        # Executor
        # ----------------------------------------------------

        executor = ActionExecutor(
            browser=browser,
            policy=policy,
        )

        # ----------------------------------------------------
        # Independent verifier
        # ----------------------------------------------------

        verifier = InvoiceVerifier()

        # ----------------------------------------------------
        # Controller
        # ----------------------------------------------------

        controller = AgentController(
            executor=executor,
            verifier=verifier,
        )

        # ----------------------------------------------------
        # Planner
        # ----------------------------------------------------

        planner = Planner()

        # ----------------------------------------------------
        # Runner
        # ----------------------------------------------------

        runner = AgentRunner(
            controller=controller,
            planner=planner,
            max_steps=10,
        )

        # ----------------------------------------------------
        # Task Parser
        # ----------------------------------------------------

        parser = TaskParser()

        task = parser.parse(task_text)

        # ----------------------------------------------------
        # Initial Agent State
        # ----------------------------------------------------

        state = AgentState(
            task=task,
        )

        # ----------------------------------------------------
        # Open Invoice Portal
        # ----------------------------------------------------

        initial_observation = browser.open(
            f"{BASE_URL}/invoices"
        )

        st.info(
            f"📄 Invoice portal opened: "
            f"{initial_observation.get('url', '')}"
        )

        # ----------------------------------------------------
        # Save objects BEFORE running the agent
        # ----------------------------------------------------

        st.session_state.browser = browser
        st.session_state.runner = runner
        st.session_state.agent_state = state

        # ----------------------------------------------------
        # Run Agent
        # ----------------------------------------------------

        st.info(
            "🧠 Agent is planning and executing..."
        )

        state = runner.run(
            state=state,
            initial_observation=initial_observation,
        )

        # ----------------------------------------------------
        # Save final state
        # ----------------------------------------------------

        st.session_state.agent_state = state

        st.rerun()

    except Exception as exc:

        st.error(
            f"❌ Agent failed to start or execute: {exc}"
        )

        st.exception(exc)


# ============================================================
# CURRENT AGENT STATE
# ============================================================

state = st.session_state.agent_state


if state:

    st.divider()

    # ========================================================
    # STATUS
    # ========================================================

    st.subheader("Agent Status")

    status = state.status

    if status == "completed":

        st.success(
            "✅ Task completed and independently verified."
        )

    elif status == "waiting_for_approval":

        st.warning(
            "⚠️ Human approval required before the "
            "next action can be executed."
        )

    elif status == "verification_failed":

        st.error(
            "❌ The task execution completed, but "
            "independent verification failed."
        )

    elif status == "error":

        st.error(
            f"❌ Agent error: {state.error}"
        )

    elif status == "cancelled":

        st.error(
            "🚫 Task cancelled by human."
        )

    elif status == "recovering":

        st.warning(
            "🔄 Agent is recovering from a failed action."
        )

    else:

        st.info(
            f"Agent status: `{status}`"
        )


    # ========================================================
    # TASK INFORMATION
    # ========================================================

    with st.expander("Task Information", expanded=False):

        st.write(
            f"**Goal:** {state.task.goal}"
        )

        if state.task.parameters:

            st.write("**Parameters:**")

            st.json(
                state.task.parameters
            )

        if state.task.postconditions:

            st.write("**Postconditions:**")

            for condition in state.task.postconditions:

                st.write(
                    f"• {condition}"
                )


    # ========================================================
    # HUMAN APPROVAL
    # ========================================================

    if state.status == "waiting_for_approval":

        st.divider()

        st.subheader("⚠️ Human Approval Required")

        if state.approval_message:

            st.write(
                state.approval_message
            )

        if state.approval_action:

            action = state.approval_action

            st.write(
                f"**Tool:** `{action.tool}`"
            )

            st.write(
                f"**Action:** `{action.action}`"
            )

            if action.reason:

                st.write(
                    f"**Reason:** {action.reason}"
                )

            if action.arguments:

                st.write(
                    "**Arguments:**"
                )

                st.json(
                    action.arguments
                )

        st.warning(
            "The agent will not execute this action "
            "until you approve it."
        )

        col1, col2 = st.columns(2)

        # ----------------------------------------------------
        # APPROVE
        # ----------------------------------------------------

        with col1:

            if st.button(
                "✅ Approve",
                type="primary",
                use_container_width=True,
            ):

                try:

                    st.session_state.agent_state = (
                        st.session_state.runner.resume(
                            state
                        )
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"❌ Resume failed: {exc}"
                    )

                    st.exception(exc)

        # ----------------------------------------------------
        # REJECT
        # ----------------------------------------------------

        with col2:

            if st.button(
                "❌ Reject",
                use_container_width=True,
            ):

                try:

                    state = (
                        st.session_state
                        .runner
                        .controller
                        .reject(state)
                    )

                    st.session_state.agent_state = state

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"❌ Could not reject action: {exc}"
                    )

                    st.exception(exc)


    # ========================================================
    # AGENT ACTIVITY
    # ========================================================

    st.divider()

    st.subheader("Agent Activity")

    if not state.history:

        st.info(
            "No actions have been executed yet."
        )

    else:

        for step in state.history:

            action = step.action
            observation = step.observation

            if observation.success:

                st.success(
                    f"Step {step.step_number} — "
                    f"`{action.tool}.{action.action}`"
                )

            else:

                st.error(
                    f"Step {step.step_number} — "
                    f"`{action.tool}.{action.action}` "
                    f"→ {observation.error}"
                )

            with st.expander(
                f"Details — Step {step.step_number}",
                expanded=False,
            ):

                st.write(
                    f"**Reason:** {action.reason}"
                )

                if action.arguments:

                    st.write("**Arguments:**")

                    st.json(
                        action.arguments
                    )

                st.write("**Observation:**")

                st.write(
                    observation.message
                )

                if observation.error:

                    st.write(
                        f"**Error:** {observation.error}"
                    )


    # ========================================================
    # RECOVERY INFORMATION
    # ========================================================

    if state.retry_count > 0:

        st.divider()

        st.subheader("🔄 Recovery")

        st.write(
            f"Retry attempts: "
            f"**{state.retry_count} / {state.max_retries}**"
        )


    # ========================================================
    # VERIFICATION
    # ========================================================

    if state.verification:

        st.divider()

        st.subheader(
            "🔍 Independent Verification"
        )

        verification = state.verification

        # ----------------------------------------------------
        # Verification status
        # ----------------------------------------------------

        if verification.verified:

            st.success(
                "✅ All verification checks passed."
            )

        else:

            st.error(
                "❌ Verification failed."
            )

        # ----------------------------------------------------
        # Individual checks
        # ----------------------------------------------------

        for check, passed in verification.checks.items():

            if passed:

                st.write(
                    f"✅ {check}"
                )

            else:

                st.write(
                    f"❌ {check}"
                )

        # ----------------------------------------------------
        # Verification message
        # ----------------------------------------------------

        if verification.message:

            st.write(
                f"**Result:** {verification.message}"
            )

        # ----------------------------------------------------
        # Evidence
        # ----------------------------------------------------

        if verification.evidence:

            st.subheader("Evidence")

            for evidence in verification.evidence:

                st.write(
                    f"• {evidence}"
                )


    # ========================================================
    # MEMORY
    # ========================================================

    if state.memory:

        st.divider()

        with st.expander(
            "Agent Memory",
            expanded=False,
        ):

            st.json(
                state.memory
            )