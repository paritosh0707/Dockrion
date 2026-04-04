# 1.1 What is Dockrion

[Home](../../README.md) > [Introduction](README.md)

## The Problem

You've built an AI agent — a LangGraph graph, a LangChain chain, or a plain Python function that calls an LLM. Now you need to:

- Wrap it in an HTTP API with health checks, authentication, and streaming
- Validate inputs and outputs at the API boundary
- Build it into a Docker image for deployment
- Add observability, safety guardrails, and secrets management

Doing this from scratch means writing boilerplate FastAPI code, Dockerfiles, auth middleware, and plumbing that has nothing to do with your agent's logic.

## What Dockrion Does

Dockrion is a deployment toolkit for AI agents. You describe your agent's configuration in a single YAML file (the **Dockfile**), and Dockrion handles everything else:

```
┌─────────────┐    validate    ┌───────────┐    generate     ┌──────────────┐
│  Dockfile   │ ─────────────► │  DockSpec  │ ──────────────► │  FastAPI App │
│  (YAML)     │                │  (Pydantic)│                 │  + Dockerfile│
└─────────────┘                └───────────┘                 └──────────────┘
       │                                                            │
       │  dockrion run                                  dockrion build
       ▼                                                            ▼
┌─────────────┐                                         ┌──────────────┐
│ Local server│                                         │ Docker image │
│ (uvicorn)   │                                         │ ready to push│
└─────────────┘                                         └──────────────┘
```

With one command (`dockrion run`) you get a local dev server. With another (`dockrion build`) you get a production Docker image. The generated API includes `/invoke`, `/health`, `/metrics`, Swagger UI, streaming endpoints, and authentication — all driven by your Dockfile.

## Who Is This For

- **AI/ML engineers** who build agents and want to deploy them without writing infra code
- **Platform teams** who want a standardized way to package and deploy agent services
- **Backend developers** who want a configuration-driven approach to agent APIs

## What Dockrion Is Not

- Dockrion is **not** an agent framework. It does not help you build the agent logic itself — use LangGraph, LangChain, or any Python framework for that.
- Dockrion is **not** an orchestration platform. It does not manage clusters, auto-scale, or route traffic. It produces Docker images you deploy with your existing infra.

---

**Next:** [1.2 Core Concepts →](core-concepts.md)
