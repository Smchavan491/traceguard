# TraceGuard

**An evidence-first AI investigator for production incidents.**

TraceGuard is an AI incident investigator for software teams. Given an alert or incident description, it gathers evidence from logs, recent deployments, service dependencies, and runbooks, ranks likely root causes with cited evidence, and proposes a diagnostic or remediation step for human approval. It never claims a cause is proven without evidence, and it never executes a remediation without approval. All data is synthetic.

> **Status:** Under development. **Stage 1 is done.** See the [roadmap](#roadmap).

---

## Table of contents

1. [The problem](#the-problem)
2. [What makes TraceGuard different](#what-makes-traceguard-different)
3. [Example investigation](#example-investigation)
4. [How it works](#how-it-works)
5. [Tech stack](#tech-stack)
6. [Project structure](#project-structure)
7. [Getting started](#getting-started)
8. [Configuration](#configuration)
9. [Running tests](#running-tests)
10. [Roadmap](#roadmap)
11. [Evaluation plan](#evaluation-plan)
12. [Safety and security design](#safety-and-security-design)
13. [Troubleshooting](#troubleshooting)
14. [Known limitations](#known-limitations)

---

## The problem

When an application breaks, engineers must manually correlate many sources: error logs, metrics, recent deployments, service dependencies, and runbooks. This is slow and stressful, and a generic AI chatbot can make it worse by confidently suggesting a cause it has no evidence for.

## What makes TraceGuard different

- **Evidence-linked diagnoses.** Every claim cites a specific log line, deployment event, or runbook passage.
- **"Likely" vs "proven".** The system separates a plausible cause from one backed by direct evidence.
- **Knows when to stop.** If evidence is insufficient, it asks for more information or escalates instead of guessing.
- **Approval-gated actions.** It can propose a rollback or diagnostic step, but a human must approve before anything runs.
- **Measured, not assumed.** A built-in evaluation suite compares the full agent against simpler baselines.

## Example investigation

**Alert:** `checkout-api p95 latency rose from 200ms to 3s at 14:05`

1. The agent classifies this as a latency incident.
2. It searches logs for the time window and finds a spike in database connection timeouts.
3. It checks deployment history and finds `v2.4.1` of `checkout-api` shipped at 14:02.
4. It retrieves the runbook "Connection pool exhaustion".
5. It reports:
   - **Hypothesis 1 (likely):** the connection pool size was reduced in `v2.4.1`. Evidence: `deploy-0412`, `log-8831`, `runbook-chunk-17`.
   - **Hypothesis 2 (unlikely):** downstream payment service slowness. Evidence against: `log-8840`.
6. It proposes: *"Roll back checkout-api to v2.4.0."* Status: **awaiting human approval**.

*(This example is illustrative. Real results will be measured and reported once the system is built.)*

## How it works

```
Incident alert
      |
      v
Input validation and guardrails (injection checks, PII handling)
      |
      v
Investigation state machine (LangGraph)
  classify -> gather evidence -> assess evidence
                                   |-> enough: build diagnosis
                                   |-> not enough: retry retrieval (bounded)
                                   |-> still not enough: ask for info or escalate
      |
      v
Answer verification (grounding check, citation check, policy check)
      |
      v
Human review: approve / edit / reject / escalate
```

Evidence sources the agent can use (read-only tools):
- **Log search:** filter by service, time window, and severity.
- **Deployment history:** what changed, when, and by whom.
- **Dependency map:** which services call which.
- **Runbook retrieval (RAG):** semantic search over runbooks stored in pgvector.

LangSmith traces every step so failures can be inspected and compared across versions.

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| API | FastAPI, Uvicorn |
| LLM framework | LangChain |
| Agent workflow | LangGraph |
| Observability and evals | LangSmith, pytest |
| Database | PostgreSQL + pgvector |
| Validation | Pydantic, pydantic-settings |
| Containers | Docker, Docker Compose |
| Frontend (later) | React + Vite |

## Project structure

```
traceguard/
  app/              # FastAPI app: routes, config, db
  ingestion/        # runbook loading, chunking, embedding
  tools/            # log search, deploy history, dependency lookup
  agent/            # LangGraph workflow
  evals/            # incident dataset, evaluators, experiments
  data/
    runbooks/       # synthetic runbooks
    incidents/      # synthetic incidents with ground truth
    logs/           # synthetic logs
    deployments/    # synthetic deployment history
  tests/
  docker-compose.yml
  .env.example
  requirements.txt
  AGENTS.md         # instructions for coding agents
  README.md
```

## Getting started

### Prerequisites

| Tool | Version | Check with |
|---|---|---|
| Python | 3.11 or newer | `python --version` |
| Git | any recent | `git --version` |
| Docker Desktop | any recent, running | `docker --version` |

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd traceguard
```

### 2. Create a virtual environment

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\activate
```

Mac / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Windows: `copy .env.example .env`
Mac / Linux: `cp .env.example .env`

Open `.env` and set a local database password if needed. The example values are for local development only. The API reads these settings from the environment; `POSTGRES_HOST` defaults to `localhost`.

### 5. Start the database

```bash
docker compose up -d
```

This starts PostgreSQL with the pgvector extension. Make sure Docker Desktop is running first.

### 6. Start the API

```bash
uvicorn app.main:app --reload
```

### 7. Verify it works

The API attempts to enable PostgreSQL's `vector` extension when it starts. When the database is reachable, open http://localhost:8000/health. You should see:

```json
{"status": "ok", "db": "ok"}
```

FastAPI also provides interactive docs at http://localhost:8000/docs.

If PostgreSQL is unavailable, `/health` returns HTTP 503 with `{"status": "error", "db": "unreachable"}`.

## Configuration

All settings are loaded from environment variables (see `.env.example`). Never commit your real `.env` file.

| Variable | Purpose | Example |
|---|---|---|
| `POSTGRES_USER` | Database user | `traceguard` |
| `POSTGRES_PASSWORD` | Database password | choose a local password |
| `POSTGRES_DB` | Database name | `traceguard` |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |

Added in later stages:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` (or another provider key) | LLM and embeddings |
| `LANGSMITH_API_KEY` | Tracing and evaluations |
| `LANGSMITH_TRACING` | Enable or disable tracing |

Exact variable names are defined in `.env.example` and `app/config.py`.

## Running tests

With the virtual environment active:

```bash
pytest
```

Tests do not call real LLM APIs. Model calls are mocked.

## Roadmap

| Stage | Goal | Status |
|---|---|---|
| 1 | Repo skeleton, Postgres + pgvector, `/health` endpoint | Done |
| 2 | Synthetic incident data and ground-truth format | Planned |
| 3 | Runbook ingestion and baseline RAG with citations | Planned |
| 4 | Investigation tools: log search, deploy history, dependency lookup | Planned |
| 5 | LangGraph investigation workflow with bounded retries | Planned |
| 6 | Guardrails and human-approval gate | Planned |
| 7 | LangSmith evaluations against three baselines | Planned |
| 8 | Dashboard and deployment | Planned |

## Evaluation plan

Quality will be measured on a fixed dataset of synthetic incidents, including clear, ambiguous, missing-evidence, contradictory, and adversarial cases.

| Metric | What it tells us |
|---|---|
| Retrieval Recall@k | Did retrieval find the passages needed? |
| Root-cause accuracy (top-1, top-3) | Did the agent identify the true cause? |
| Groundedness | Are claims supported by cited evidence? |
| Citation accuracy | Do citations actually support their claims? |
| Correct abstention / escalation rate | Does it stop when evidence is insufficient? |
| Guardrail attack success rate | Do adversarial inputs bypass the controls? |
| Latency and cost | Is it practical to run? |

Three systems will be compared on the same test set:

- **Baseline A:** a plain LLM given only the incident symptom.
- **Baseline B:** simple RAG over runbooks.
- **Baseline C:** the full guarded LangGraph agent.

Results will be reported as measured, including cases where the agent fails.

## Safety and security design

- **Untrusted input.** Logs and retrieved documents are treated as data, never as instructions.
- **Least privilege.** The agent can only call allowlisted, read-only tools.
- **Human approval.** No remediation runs without explicit approval, and approvals are audit-logged.
- **Validated output.** All model outputs must pass Pydantic schema validation.
- **Bounded loops.** Retries are capped, with a defined escalation path.
- **No real data.** All logs, incidents, and documents are synthetic.
- **Secrets.** Kept in `.env`, which is excluded from Git.

LangSmith is used for tracing and evaluation. It is not a substitute for application-level security.

## Troubleshooting

| Problem | Fix |
|---|---|
| `docker` command not found, or cannot connect | Start Docker Desktop and wait until it shows as running. |
| Port 5432 already in use | Another Postgres is running. Change the host port in `docker-compose.yml` (for example to 5433) and update `POSTGRES_PORT` in `.env`. |
| `python` not found | Reinstall Python and tick "Add Python to PATH", or try `py` (Windows) or `python3` (Mac/Linux). |
| PowerShell blocks venv activation | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then retry. |
| `/health` shows `db: error` | Check that `docker compose up -d` succeeded and that `.env` values match `docker-compose.yml`. |

## Known limitations

- Uses synthetic data only. Results may not transfer to real production systems.
- Evaluation sets start small and are not statistically exhaustive.
- Not connected to real monitoring or deployment tools.
- Remediation is proposal-only; nothing is executed automatically.

---

## Learning goals

This project is built to learn and demonstrate: LangChain, LangGraph, LangSmith, RAG with vector search, LLM evaluation, guardrails, FastAPI, PostgreSQL + pgvector, and Docker.

## License

Choose a license before making the repository public (MIT is a common choice for portfolio projects).
