# Dockrion Documentation

Dockrion is a toolkit for deploying AI agents as production-ready APIs. Define your agent in a Dockfile, validate it, run it locally, and build a Docker image — all from the CLI.

---

## Table of Contents

### [1. Introduction](01-introduction/README.md)

- [1.1 What is Dockrion](01-introduction/what-is-dockrion.md)
- [1.2 Core Concepts](01-introduction/core-concepts.md)
- [1.3 Architecture Overview](01-introduction/architecture-overview.md)
- [1.4 Quickstart](01-introduction/quickstart.md)
- [1.5 Roadmap](01-introduction/roadmap.md)

### [2. The Dockfile](02-the-dockfile/README.md)

- [2.1 agent](02-the-dockfile/agent.md) — entrypoint vs handler, framework selection
- [2.2 io_schema](02-the-dockfile/io-schema.md) — input/output contracts, strict mode
- **2.3 auth** — authentication and access control
  - [Overview & Mode Comparison](02-the-dockfile/auth/README.md)
  - [API Key](02-the-dockfile/auth/api-key.md)
  - [JWT](02-the-dockfile/auth/jwt.md)
  - [OAuth2](02-the-dockfile/auth/oauth2.md) *(coming soon)*
  - [Roles & Rate Limits](02-the-dockfile/auth/roles-and-rate-limits.md)
- **2.4 policies** — safety and tool control
  - [Overview](02-the-dockfile/policies/README.md)
  - [Prompt Injection Blocking](02-the-dockfile/policies/prompt-injection.md)
  - [Output Controls](02-the-dockfile/policies/output-controls.md)
  - [Tool Gating](02-the-dockfile/policies/tool-gating.md)
- [2.5 secrets](02-the-dockfile/secrets.md) — declaring required and optional secrets
- **2.6 streaming** — real-time event streaming
  - [Overview & Expose Config](02-the-dockfile/streaming/README.md)
  - [SSE Streaming](02-the-dockfile/streaming/sse.md)
  - [Async Runs](02-the-dockfile/streaming/async-runs.md)
  - [Event Types](02-the-dockfile/streaming/event-types.md)
  - [Backends](02-the-dockfile/streaming/backends.md)
  - [StreamContext for Agent Authors](02-the-dockfile/streaming/stream-context.md)
- [2.7 observability](02-the-dockfile/observability.md) — metrics, tracing, logging
- [2.8 build config](02-the-dockfile/build-config.md) — Docker build includes, excludes, auto-detection
- [2.9 Environment Variable Substitution](02-the-dockfile/env-substitution.md)
- [2.10 metadata](02-the-dockfile/metadata.md)
- [2.11 Complete Annotated Example](02-the-dockfile/complete-example.md)

### [3. CLI Reference](03-cli-reference/README.md)

- [3.1 Core Commands](03-cli-reference/core-commands.md) — init, validate, run, build, test
- [3.2 Utility Commands](03-cli-reference/utility-commands.md) — inspect, add, doctor, logs, version
- [3.3 Exit Codes](03-cli-reference/exit-codes.md)

### [4. The Generated API](04-the-generated-api/README.md)

- [4.1 Endpoints Reference](04-the-generated-api/endpoints-reference.md)
- [4.2 How io_schema Shapes Swagger](04-the-generated-api/io-schema-and-swagger.md)
- [4.3 Auth from the Caller's Perspective](04-the-generated-api/auth-callers-perspective.md)
- [4.4 Streaming Consumption](04-the-generated-api/streaming-consumption.md)

### [5. Guides & Recipes](05-guides-and-recipes/README.md)

- [5.1 Installation & Extras](05-guides-and-recipes/installation.md)
- [5.2 Environment & Secrets Management](05-guides-and-recipes/environment-and-secrets.md)
- [5.3 Adding Auth](05-guides-and-recipes/adding-auth.md)
- [5.4 Adding Streaming](05-guides-and-recipes/adding-streaming.md)
- [5.5 Adding Policies](05-guides-and-recipes/adding-policies.md)
- [5.6 Docker Build & Deployment](05-guides-and-recipes/docker-build-and-deployment.md)
- [5.7 Cloud Deployment](05-guides-and-recipes/cloud-deployment.md)
- [5.8 Troubleshooting](05-guides-and-recipes/troubleshooting.md)
- [5.9 FAQ](05-guides-and-recipes/faq.md)
- [5.10 Walkthrough: Invoice Copilot](05-guides-and-recipes/invoice-copilot-walkthrough.md)

### [Appendix](appendix/README.md)

- [SDK Reference](appendix/sdk-reference.md)
- [Adapters Reference](appendix/adapters-reference.md)
- [Error Hierarchy](appendix/error-hierarchy.md)
