# Architecture

TrustSentinel is a modular monolith: FastAPI routes call feature/risk/case services backed by SQLAlchemy and one relational database. PostgreSQL is configured for deployment; SQLite is the zero-configuration local/demo default. Model inference runs inside the API process using a pre-trained Isolation Forest artifact. Offline scripts generate the artifact; request handlers never train it.

Every score stores a transaction, triggered signals, versioned risk decision, applicable intervention, and audit event. HOLD and REVIEW recommendations create open analyst cases. Analyst outcomes update the case and append an audit event. Metrics are derived from stored decisions and outcomes.

The sandbox uses synthetic entities and stable demo transaction IDs. It does not execute payments, inspect private communications, or establish whether a customer was manipulated.
