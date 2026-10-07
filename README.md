# TrustSentinel

TrustSentinel is a synthetic-data prototype for identifying contextual indicators associated with potentially socially engineered payments. It provides an explainable backend risk assessment and recommended intervention; it does not process payments or determine customer intent.

The backend and ML implementation, setup instructions, API overview, synthetic data workflow, and prototype limitations are documented in [backend/README.md](backend/README.md). The backend is intended to run from `backend/`; Render is configured with that directory as its service root.

This project does not claim production fraud-detection accuracy. All generated scores, scenarios, and prevented-loss figures are synthetic prototype values.
