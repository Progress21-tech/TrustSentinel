# MASTER IMPLEMENTATION PROMPT: CERVIQON

## ROLE AND OBJECTIVE

Act as the lead full-stack engineer, ML systems engineer, API architect, quality engineer, fintech security reviewer, and product designer responsible for evolving the existing Cerviqon repository into a dependable, integration-ready transaction-risk intelligence MVP.

Cerviqon is being developed for Nigerian financial institutions, including banks, payment providers, and fintechs. Its intended focus is explainable transaction-risk assessment, beneficiary-risk context, suspicious activity analysis, and support for fraud investigation workflows.

The repository already contains an existing prototype. Your responsibility is to audit it before changing it, preserve working functionality, implement the missing pieces based on evidence, thoroughly test the finished MVP, and ONLY THEN create a responsive public landing page.

Follow this exact order:
1. Audit the existing repository and user workflows.
2. Document the baseline findings.
3. Implement the required improvements using the existing architecture wherever practical.
4. Test and validate all product workflows.
5. Complete documentation and MVP acceptance checks.
6. Only after the MVP acceptance gate passes, build the public Cerviqon landing page.
7. Run final functional, visual, accessibility, and production-build checks.

Do not build the landing page during the audit or before the product passes its acceptance gate. Do not stop after generating a report; proceed through the implementation phases unless a genuine blocker requires a decision or credential that is unavailable.

## NON-NEGOTIABLE RULES

- Inspect the real repository before making assumptions about its stack, architecture, API routes, database, hosting, model artifacts, or framework.
- Preserve existing working features. Do not rewrite the application merely to fit a preferred architecture.
- Do not replace the existing model, overwrite model artifacts, delete data, or perform destructive database migrations without a justified and documented reason.
- Do not hardcode credentials, expose secrets in client code, or print sensitive environment variables.
- Do not use real bank credentials, access private bank systems, or connect to live payment infrastructure without explicit authorisation.
- Use synthetic data for local development and simulations. Real financial data requires appropriate authority, permissions, safeguards, and agreements.
- Never fabricate fraud-detection results, customers, bank partnerships, testimonials, transaction volumes, certifications, regulatory approval, or production-readiness claims.
- Do not treat a risk score as proof of fraud. A first-time beneficiary or incomplete history alone must not be treated as evidence of fraud.
- Do not claim that the system prevents, blocks, or reverses a payment unless the implemented and authorised workflow genuinely supports that action.
- Keep the rules engine, ML model, feature extraction, and evaluation results consistent. Do not implement a second scoring algorithm in the dashboard or integration adapter.
- Keep the customer-facing brand as CERVIQON. Update old TrustSentinel references carefully without breaking routes, environment variables, database compatibility, or deployment configurations.
- Keep the implementation modular, documented, secure, maintainable, and testable.
- When a feature cannot be completed, report the exact blocker and finish all independent work that can be completed safely.

## PHASE 0 — REPOSITORY INVENTORY AND BASELINE AUDIT

Do not modify application behaviour during the initial audit.

### A. Establish the actual project state

Inspect:
- Git status, current branch, existing uncommitted changes, and recent history.
- Repository structure, entry points, framework versions, package scripts, dependencies, and configuration.
- Frontend routes, backend routes, middleware, database models, migrations, and environment configuration.
- Existing tests, model artifacts, evaluation scripts, CI/build workflows, and deployment configuration.
- Existing documentation and previous technical decisions.

Preserve uncommitted user changes. Do not reset the repository or discard work.

### B. Trace the current transaction-scoring workflow end to end

Trace one complete transaction from the existing user interface through the backend and risk engine.

Document:
1. Which page or component collects transaction input.
2. Which route or API endpoint receives it.
3. How the request is authenticated and validated.
4. How identifiers, amounts, currency, channel, timestamps, and optional context are normalised.
5. How features are extracted.
6. How the rules engine and ML model are invoked.
7. How component scores are combined and how thresholds are applied.
8. How a final risk band and recommendation are produced.
9. Where the result and its supporting information are persisted.
10. How the frontend receives and displays the result.
11. What happens when inputs are missing, the model is unavailable, the database fails, or a request is duplicated.

Trace the actual code path and file locations. Do not assume the documentation accurately describes the implementation.

### C. Audit the ML and evaluation pipeline

Inspect the available:
- Training and inference code.
- Feature definitions and ordering.
- Preprocessing and missing-value handling.
- Model loading and versioning.
- Rules-to-ML combination policy.
- Decision thresholds.
- Train, validation, and test separation.
- Dataset generation, schema, and label definitions.
- Evaluation code and reported metrics.

Check whether features used during training match the features generated at inference.

Check for data leakage, inconsistent transformations, unexplained fallback scores, non-deterministic behaviour, and unrealistic cold-start assumptions.

Prior project notes describe synthetic transaction data, a separate 2,000-record holdout evaluation, and a hybrid rules/ML policy. Treat those details as historical context to verify against the current repository, not values to hardcode or advertise without evidence.

### D. Audit persistence and system reliability

Determine whether:
- Assessments are persisted correctly and retrieved correctly.
- Repeated requests can create inconsistent records.
- Every saved assessment can be tied to a model/policy version.
- The system handles malformed inputs and database errors cleanly.
- Health/readiness checks actually reflect the dependencies they claim to check.
- Logs contain potentially sensitive information.
- Existing API authentication behaves as expected.

### E. Audit security and tenant separation

Review authentication, authorisation, credential handling, input validation, logging, data retention, rate limiting where applicable, and cross-tenant isolation.

Determine whether an institution could access another institution's transaction data or assessment records.

Do not claim that security requirements are satisfied simply because the application uses HTTPS or an API key.

### F. Create the audit report

Write:

docs/audit/CERVIQON_CURRENT_STATE_AUDIT.md

Include:
- Architecture and dependency map.
- Current user workflows.
- API and data-flow diagram.
- Route and endpoint inventory.
- Current model and scoring behaviour.
- Findings classified as IMPLEMENTED, PARTIALLY IMPLEMENTED, BROKEN, MISSING, or NOT VERIFIED.
- Severity and business impact of each finding.
- Relevant file paths and code references.
- Tests executed and their actual results.
- Existing capabilities that must be preserved.
- A prioritised implementation plan with acceptance criteria for each change.

Do not make application changes during this initial baseline audit. Once the report and baseline test results are recorded, proceed to implementation using the findings. Do not wait for approval unless a genuine architectural, destructive-data, permission, or credential blocker requires it.

## PHASE 1 — STABILISE THE EXISTING PRODUCT

Before adding new capabilities, resolve the verified issues that prevent the existing scoring workflow from operating reliably.

### Requirements

- Fix broken request handling, validation, authentication, persistence, feature extraction, scoring, or response formatting where evidence shows an issue.
- Preserve the existing dashboard and its core workflows.
- Ensure the manual scoring form and any new external API use the same underlying scoring service.
- Keep the current model artifact until a replacement has been evaluated and approved.
- Correct inconsistent model and feature versions where necessary.
- Make missing context explicit instead of silently inventing default information.
- Establish consistent error handling, structured logs, request IDs, and model/policy-version tracking.
- Avoid introducing dependencies or architectural complexity without a clear need.

Add regression tests before or alongside fixes so that previously working behaviour remains protected.

Acceptance criteria:
- The existing scoring workflow completes successfully for valid synthetic transactions.
- Invalid requests receive appropriate errors.
- Assessment persistence and retrieval work.
- Model-unavailable and dependency-failure cases are handled explicitly.
- Existing product routes still function.
- The application builds successfully using its supported environment.

## PHASE 2 — ESTABLISH A STANDARD INTEGRATION API

The goal is to let a bank or fintech call Cerviqon from its own backend instead of requiring an operator to enter transaction details manually through the dashboard.

First inspect existing endpoints. Reuse or extend them if appropriate. Do not introduce a duplicate route solely to follow this example.

A possible endpoint is:

POST /v1/risk/assess

Define and document the actual request and response schemas.

### Request requirements

Support the fields necessary for the agreed use case, such as:
- Institution-scoped transaction identifier.
- Event type or transaction lifecycle stage.
- Timestamp and currency.
- Amount in one documented, consistently applied representation.
- Pseudonymous sender and beneficiary references where authorised.
- Channel and other context only where supported by the existing feature pipeline.

Do not require fields that the engine does not need. Clearly distinguish required, optional, unavailable, and unsupported fields.

Do not use real account numbers in examples. Use synthetic, clearly identifiable fixtures.

### Response requirements

Return a structured response containing, where supported:
- Transaction/request identifier.
- Risk score and documented risk band.
- Advisory recommendation.
- Reason codes based on signals actually used.
- Data completeness or cold-start status.
- Model and policy versions.
- A traceable assessment identifier.

The response must clearly distinguish a risk assessment from a confirmed fraud finding.

Do not claim that an external API can block or authorise payments unless a customer-approved payment decision workflow genuinely exists.

### API engineering requirements

- Validate the request contract.
- Keep the existing scoring engine as the shared source of scoring logic.
- Enforce authentication and institution-level authorisation.
- Enforce institution/tenant isolation.
- Handle repeated requests and retries consistently.
- Document timeout, unavailable-model, validation-error, and dependency-failure behaviour.
- Never expose server-side secrets to the frontend.
- Add request and assessment correlation IDs.
- Add audit records without unnecessarily storing sensitive payloads.
- Version the contract and document backward-compatibility expectations.
- Produce OpenAPI documentation or an equivalent machine-readable API specification.

Use the established project conventions and dependencies where suitable.

## PHASE 3 — ADD BENEFICIARY CONTEXT AND EXPLAINABLE RESULTS

Build only what the existing data and validated architecture can support.

### Beneficiary context

Where authorised transaction history is available, assess potentially useful context such as:
- Recent transaction frequency.
- Changes in observed beneficiary activity.
- Number of distinct counterparties.
- Relevant transaction-pattern anomalies.
- Potentially connected account activity within the available dataset.

Do not implement unsupported network-wide intelligence. The first version should operate only on data an authorised institution provides. Do not pool information across institutions without appropriate permissions, agreements, and controls.

A new beneficiary should not automatically be treated as suspicious. The model should distinguish missing information from observed risk signals.

### Explainability

Each risk assessment should identify the actual reason codes and supporting information that contributed to the result.

The UI must not show a reason merely because it sounds plausible. It must correspond to the real calculation or rule that influenced the result.

If available history is insufficient, explicitly display that limitation.

### Investigator feedback

If the existing product supports investigations, inspect and extend that workflow where appropriate so an authorised reviewer can record a defined outcome.

Do not assume an alert is confirmed fraud. Support clear distinctions such as unresolved, false positive, legitimate activity, and confirmed case where the partner's definitions support these labels.

Do not use investigation outcomes for model training automatically. Define a controlled evaluation and approval process first.

Acceptance criteria:
- Tests cover missing, limited, and available context.
- First-time beneficiaries are not automatically classified as fraudulent.
- Reason codes are grounded in real scoring logic.
- Assessment outputs remain reproducible and auditable.
- No cross-institution data sharing is introduced by default.

## PHASE 4 — BUILD AN INTEGRATION SIMULATOR

Create a minimal but realistic synthetic client that behaves like a bank or fintech backend.

The simulator should:
1. Submit a synthetic transaction to Cerviqon's actual API.
2. Authenticate as a development/test client.
3. Display the response returned by the real backend.
4. Show risk score, band, reason codes and data completeness.
5. Handle request validation, authentication failures, timeouts and service errors.
6. Support repeated requests without creating inconsistent assessments.
7. Allow testing of different synthetic scenarios.

Use the same scoring endpoint used by other approved clients. Do not use fabricated frontend responses or bypass the backend.

Keep the simulator clearly separate from the public product website and from any production banking integration.

Acceptance criterion: a separate test client can submit a synthetic transaction programmatically and receive the backend's real assessment.

## PHASE 5 — EVALUATION AND SECURITY VALIDATION

### Model evaluation

Using reproducible synthetic data:
- Verify dataset and label definitions.
- Keep training, validation, and final test sets appropriately separated.
- Compare applicable baseline rules, ML, and hybrid approaches.
- Measure precision, recall, false-positive rate, and other relevant metrics.
- Record threshold selection and its rationale.
- Evaluate cold-start cases and missing context.
- Save a reproducible evaluation report.

Verify every metric against the actual evaluation artifacts before documenting it.

Do not present synthetic metrics as evidence of real-world fraud prevention. The evaluation report must state the dataset's limitations.

### Integration testing

Test:
- Authentication and authorisation.
- Valid and invalid requests.
- Missing fields and unsupported event types.
- Repeated requests and retries.
- Model and database failures.
- Tenant isolation.
- Response consistency.
- API latency under a documented, repeatable synthetic test.
- Frontend integration with the common scoring service.

### Security and privacy

Add or verify appropriate controls for:
- Server-side credential handling.
- Institution-specific access control.
- Data minimisation.
- Secure transport and appropriate storage protections.
- Auditability and access logging.
- Retention rules.
- Input validation and rate limiting where suitable.
- Safe errors and redacted logs.
- Dependency and configuration hygiene.

Document anything that remains incomplete. Never claim production readiness if required controls remain unverified.

## PHASE 6 — DOCUMENTATION AND MVP ACCEPTANCE GATE

Create or update:
- README with setup, test, and build instructions.
- Architecture overview and data-flow diagram.
- API specification and integration guide.
- Synthetic test data and scenario documentation.
- Model evaluation report and limitations.
- Environment-variable example containing placeholders only.
- Deployment and rollback instructions.
- Known limitations and security-readiness checklist.
- MVP implementation summary.

Do not put secrets, credentials, personal data, or real bank information in the documentation.

### MVP acceptance gate

Do not start building the public landing page until all applicable criteria below have been tested:

1. The existing manual transaction-scoring workflow works.
2. The API supports validated synthetic requests and returns a documented response.
3. The dashboard and API call the same scoring engine.
4. Results and model/policy versions are traceable.
5. Tests cover key success, failure, and cold-start cases.
6. The integration simulator calls the actual backend.
7. The reproducible synthetic evaluation report is available.
8. Tenant isolation and core API security controls have been tested.
9. The frontend production build and backend tests succeed in the supported environment.
10. Setup, API, integration, evaluation, and known-limitation documentation is complete.

If a criterion fails, fix it or document the exact blocker. Do not represent an incomplete criterion as passed.

This gate defines MVP completion; it does not require completed integrations with five banks or an unapproved production banking deployment.

## PHASE 7 — BUILD THE RESPONSIVE CERVIQON PUBLIC LANDING PAGE

Start this phase only after the core MVP has passed its acceptance gate.

The landing page is a public, buyer-facing company website intended for banks, fintechs, payment providers, innovation teams, fraud operations leaders, and relevant technology partners.

It must not read like a developer update, internal project report, or pitch deck written directly to the founder.

### A. Preserve the product application

Inspect existing routing and deployment behaviour before adding the public website.

Make the public landing page available at the root path if this is compatible with the existing application and deployment. Preserve the current product dashboard behind an appropriate application route and preserve compatibility with existing routes where necessary.

Do not replace the dashboard with the marketing website. Do not break authentication, scoring, internal navigation, or API calls.

If a root-route change requires redirect or hosting configuration, implement and test it.

### B. Brand identity

Use the approved Cerviqon Eucalyptus brand system:
- Mist Green: #E9EFE7
- Soft Sage: #B8CBAE
- Dusty Clay: #D9B9A9
- Forest Graphite: #35453B

Use Space Grotesk for headings and Inter for body and interface text where the repository can support them appropriately.

The visual direction should be calm, thoughtful, premium, precise, and credible to financial institutions.

Do not reintroduce the discarded Midnight Ink or Ivory branding directions. Avoid generic dark cybersecurity aesthetics, oversized gradients, stock shield imagery, glowing circuits, fabricated data visualisations, or decorative animations without purpose.

The earlier logo concept was considered generic. Do not simply reproduce a generic letter C, shield, or circuit icon. Inspect the current brand assets first. Build the landing page so that the wordmark remains clear and professional; use only approved or refined assets. If the final logo is not available, use a typographic wordmark as a temporary brand treatment instead of presenting a generic logo as final.

### C. Content and value proposition

The site should communicate a clear value proposition around explainable transaction-risk assessment, beneficiary context, relevant transaction patterns, and support for existing investigation workflows.

Use a structure similar to the following, adapted to the capabilities genuinely implemented:

1. **Hero:** State the financial-institution problem and what Cerviqon is designed to help with. Use the brand line “See risk in context.” as a supporting statement if it fits the final copy. Include a functional primary call to action to discuss a design-partner evaluation.
2. **The problem:** Explain the practical challenges of suspicious transaction patterns, limited visibility into beneficiary behaviour, and investigation workload. Do not claim every institution experiences the same shortcomings.
3. **How Cerviqon works:** Explain the actual flow from transaction context to assessment, evidence, and a decision or investigation workflow controlled by the institution.
4. **Core capabilities:** Describe only what is implemented and verifiable. Distinguish operational features from planned capabilities.
5. **Why it can be useful:** Explain the intended value of explainable risk signals, available beneficiary context, and integration alongside existing systems. Do not claim measured superiority over competitors unless supported by comparative evidence.
6. **Integration approach:** Explain the API-driven approach and the possibility of controlled historical and shadow-mode evaluation, but do not imply that any named bank is already integrated.
7. **Trust and responsible use:** Explain data minimisation, authorised use of data, auditability, human review, and the institution's control of its decisions where these are supported by the actual implementation and operating model.
8. **Research-backed context:** Use a small number of credible, attributable facts only where helpful. Do not turn the landing page into a market-size report.
9. **Call to action:** Invite a bank or fintech to discuss an evaluation or design-partner engagement.
10. **Footer:** Include brand identity, navigation, a configurable contact method, and links to any actual privacy or legal policies that exist.

Do not add unsupported claims such as “first in Nigeria,” “zero fraud,” “guaranteed prevention,” “industry-leading accuracy,” or “proven to reduce losses.”

Do not display bank logos, fabricated testimonials, or customer names without explicit permission.

### D. Use research responsibly

Review relevant market research notes and sources in the repository before writing public claims. Verify facts and dates before use.

Potential sources to assess include:

- Nigerian electronic-payment fraud figures: https://ir.nilds.gov.ng/handle/123456789/3473
- Central Bank of Nigeria regulatory updates: https://www.cbn.gov.ng/AboutCBN/Reforms.html
- Nigeria fraud-detection market estimate from 6Wresearch: https://www.6wresearch.com/industry-report/nigeria-fraud-detection-and-prevention-market
- Pastel Sigma's public transaction-monitoring documentation: https://sigma-docs.pastel.africa/products/transaction-monitoring/introduction

The 6Wresearch market figure describes a broad fraud-detection-and-prevention category covering more than Cerviqon's initial use case. Do not label it Cerviqon's TAM or SAM.

If industry figures are shown on the page:
- Attribute them directly to the source.
- Include the measurement period and context.
- Never imply that industry fraud losses represent Cerviqon's revenue opportunity.
- Avoid presenting declining fraud losses as proof that the problem grows every year.
- Keep sources available through concise footnotes or a references section.

Competitor research may inform internal positioning, but the landing page should explain Cerviqon's own value rather than make unsubstantiated accusations or superiority claims about other vendors.

### E. Landing-page functionality

All controls must work:
- Navigation links go to real sections or existing pages.
- Primary and secondary calls to action have real destinations.
- Forms must validate input and genuinely submit through a supported backend or configured contact workflow.
- Never display a success message when nothing was submitted.
- Do not invent an email address, telephone number, office address, bank partnership, or social account.
- Use configurable contact details. If a required production contact setting is unavailable, document it as a launch blocker rather than fabricating it.

Keep the public marketing content independent from the transaction-scoring engine. The landing page must not call sensitive risk-assessment APIs merely to render its content.

### F. Responsive design and accessibility

The landing page must work on:
- Small mobile screens.
- Larger mobile screens.
- Tablets.
- Desktop monitors.
- Wide screens.

Requirements:
- No horizontal page overflow.
- Navigation works with touch and keyboard.
- Text remains readable without requiring zoom.
- Maintain accessible colour contrast.
- Use semantic headings and landmarks.
- Add useful link and button labels.
- Add descriptive alt text to meaningful images.
- Respect reduced-motion preferences.
- Avoid excessive motion, layout shifts, and unnecessarily large images.
- Include page title, description, relevant Open Graph metadata, and favicon.
- Test loading, routing, and navigation in the actual supported deployment environment.

Do not rebuild the existing dashboard's design system without need.

## PHASE 8 — FINAL VERIFICATION AND DELIVERY REPORT

After implementation, perform a complete verification run.

Report separately:
1. Audit findings and how they were addressed.
2. Implemented capabilities.
3. Automated tests and actual results.
4. Manual workflow test results.
5. ML evaluation results and synthetic-data limitations.
6. API contract and simulator status.
7. Security checks passed, failed, or not performed.
8. Landing-page routes and responsive testing results.
9. Production build and deployment status.
10. Known limitations and any remaining release blockers.
11. Relevant files changed and the reason for each significant change.
12. Exact commands for reproducing tests and the build.
13. Environment variables the operator must configure, without including secret values.

Never mark tests as successful if they were not run. Distinguish local verification from live deployment verification.

## FINAL DEFINITION OF DONE

Cerviqon is ready for controlled external MVP evaluation when:
- The existing scoring workflow remains functional.
- External test clients can use the documented API.
- Assessments have traceable model versions and evidence.
- Synthetic evaluation is reproducible and accurately described.
- Relevant security and tenant-isolation tests pass.
- The integration simulator uses the real backend.
- Technical documentation is complete.
- The public landing page is responsive, accessible, research-grounded, and consistent with the Eucalyptus identity.
- The current dashboard and application routes remain functional.

A successful build or polished landing page alone does not establish real-world fraud-detection effectiveness, institutional approval, or production readiness.

Begin with PHASE 0 now. Audit the repository first, record the baseline, and then proceed through the phases in order.