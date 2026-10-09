# Evaluation — Autonomous AI Task Worker

## 1. Evaluation Objective

The objective is to evaluate whether the agent can execute the configured invoice-to-accounts-payable workflow, obtain human approval before submission, and verify the final stored record.

## 2. Test Environment

- Language: Python
- Language model: Groq API using `openai/gpt-oss-20b`
- Agent and model integration: LangChain
- Browser automation: Playwright
- Backend: FastAPI
- Database: SQLite
- User interface: Streamlit
- Test framework: pytest

## 3. End-to-End Demonstration

**Task:** Find invoice `INV-1041` and add it to AP.

The invoice used in the demonstration has the following expected details:

| Field          | Expected value  |
| -------------- | --------------- |
| Invoice number | INV-1041        |
| Vendor         | Acme Components |
| Amount         | 12500 INR       |
| Due date       | 2026-10-15      |
| Final status   | Pending         |

The workflow inspects the invoice, prepares the AP record, pauses for human approval, submits the record after approval, and checks the resulting database state.

## 4. Verification Results

The final demonstration passed all six configured verification checks.

| Check             | Expected result |
| ----------------- | --------------- |
| Record exists     | Pass            |
| Vendor matches    | Pass            |
| Amount matches    | Pass            |
| Currency matches  | Pass            |
| Due date matches  | Pass            |
| Status is pending | Pass            |

These checks validate the stored record for the demonstrated task. They do not establish that the agent will succeed on arbitrary invoices, applications, or workflows.

## 5. Automated Tests

The recorded test run completed with:

```text
pytest -q
17 passed
```

This result represents the test suite at the time of that run. Run the tests again before submission if the code has changed.

## 6. Reliability and Safety Considerations

The implementation includes configured action validation, an approval checkpoint for submission, execution-state tracking, and a verifier that checks the resulting database record.

The current evaluation does not establish robustness against every possible UI change, network failure, malicious page instruction, or unfamiliar workflow. Those cases require dedicated tests before broader reliability claims can be made.

## 7. Known Limitations

- The workflow is specialized for invoice-to-AP processing.
- Portal URLs, selectors, field mappings, and verification rules are configured for the simulated environment.
- The post-approval submission flow is deterministic rather than entirely model-planned.
- Evaluation coverage is limited to the existing automated tests and demonstrated scenarios.
- The project has not been validated as a production ERP integration.

## 8. Future Improvements

1. Add repeatable evaluations across multiple invoice scenarios.
2. Test UI changes, timeouts, interrupted sessions, and ambiguous outcomes.
3. Improve selector grounding and recovery from failed actions.
4. Expand task definitions to support additional business workflows.
5. Add execution traces and more detailed audit logs.
6. Strengthen authorization, isolation, and secret management for production use.
