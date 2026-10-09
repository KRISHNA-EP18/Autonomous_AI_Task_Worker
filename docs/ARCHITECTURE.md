# Architecture — Autonomous AI Task Worker

## 1. Overview

The Autonomous AI Task Worker executes a bounded business workflow: finding an invoice and adding its details to an accounts-payable (AP) system.

The system combines language-model reasoning, browser automation, policy checks, human approval, and independent verification. The current implementation targets a simulated business environment rather than a production ERP system.

## 2. System Architecture

```text
                User
                 |
                 v
          Streamlit UI
                 |
                 v
        Task Parsing and State
                 |
                 v
        Agent Controller/Runner
                 |
           +-----+------+
           |            |
           v            v
      Groq LLM      Policy Checks
           |            |
           +-----+------+
                 |
                 v
         Browser Automation
             Playwright
                 |
                 v
       Simulated Invoice Portal
          FastAPI + SQLite
                 |
                 v
        Human Approval Checkpoint
                 |
                 v
         AP Record Submission
                 |
                 v
       Independent Verification
                 |
                 v
          Final Task Result
```

## 3. Main Components

### User Interface

The Streamlit interface accepts the task description, displays execution progress, provides the approval interaction, and presents the final verification results.

### Task Parsing and State

The system extracts relevant task information, including the invoice identifier, and maintains execution state, observations, action history, and errors.

### Agent Controller and Language Model

The controller coordinates the workflow. The Groq-hosted language model proposes actions based on the task and observed page information. Application code validates and constrains those actions.

### Browser Automation

Playwright interacts with the simulated invoice portal and AP form. The browser tool supports navigation, observation, clicking, filling fields, and retrieving page content.

### Policy and Approval

The policy layer checks whether proposed actions are permitted and identifies actions requiring approval. Submission is gated by human approval.

### Simulated Backend

FastAPI exposes the simulated business application and API endpoints. SQLite stores invoice and accounts-payable records.

### Independent Verifier

After submission, the verifier checks the database record against the expected invoice details. It checks record existence, vendor, amount, currency, due date, and pending status.

## 4. Execution Flow

1. The user submits a natural-language task.
2. The application identifies the invoice and required workflow.
3. The agent observes the available page information and proposes actions.
4. The application validates actions against its configured policy and available controls.
5. Playwright navigates the invoice portal and extracts the required details.
6. The system prepares the AP record and pauses for human approval.
7. After approval, the controlled submission flow creates the record.
8. The verifier independently checks the resulting database state.
9. The interface displays the verification outcome.

## 5. Design Decisions

- **Controlled execution:** Model-generated actions are validated before execution.
- **Human oversight:** The AP submission requires an approval checkpoint.
- **Independent verification:** Success is determined using the stored record rather than solely trusting the language model's response.
- **Bounded scope:** The initial implementation focuses on a specific invoice-to-AP workflow.
- **Explicit state:** Observations, execution steps, and verification results are tracked for debugging and review.

## 6. Current Limitations

The current implementation uses configured portal URLs, selectors, invoice patterns, policy rules, and verification fields. The post-approval submission flow is deterministic. Consequently, the system is not yet a general-purpose computer-use agent capable of reliably handling arbitrary applications and workflows.

Production deployment would require stronger authentication and authorization, audit logging, secure session handling, broader testing, and more robust recovery.
