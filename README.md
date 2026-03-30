---
title: Scalar Output
emoji: 😻
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🎧 OpenEnv: Customer Support Ticket Management

[![OpenEnv Spec Status](https://img.shields.io/badge/OpenEnv-Compliant-brightgreen)](https://github.com/meta-pytorch/OpenEnv)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces)

A complete, real-world **OpenEnv** environment simulating a customer support ticket management triage system. This environment is built to explicitly address the **OpenEnv Hackathon** requirements, taking AI agents out of toy game environments and challenging them with messy, knowledge-dependent workflows that humans perform every day.

---

## 🌎 Real-World Utility (30%)
Unlike standard grids or toy puzzles, **Customer Support Ticket Management** is a genuine domain where companies spend millions of hours annually. Agents must:
1. Parse unstructured user complaints.
2. Query an internal **Knowledge Base** dynamically.
3. Make categorical decisions (Assigning to "Billing", "Escalations", etc.).
4. Generate contextually accurate prose responses.
5. Prioritize queues and explicitly close/submit task queues upon condition fulfillment.

This environment has immediate value for the RL/agent community wanting to evaluate long-horizon reasoning combined with deterministic API tool usage.

## 🎯 Task & Grader Quality (25%)
This environment features **3 distinct tasks** structured with progressively challenging difficulty. Every task employs a programmatic deterministic grader scoring strictly natively from `0.0` to `1.0`.

- **Easy (`easy`)**: A single ticket requiring basic keyword routing. (Score `1.0` if successfully assigned to "Billing").
- **Medium (`medium`)**: A ticket requiring the agent to `search_kb` for the company refund policy, write a reply mentioning the specific "business days" clause, and then `close_ticket`. (Score `0.5` for policy mention + `0.5` for closing status).
- **Hard (`hard`)**: A complex queue of 3 concurrent tickets involving legal escalations, system crash routing, and multi-step password resets. Challenges frontier models in tracking multi-issue state across consecutive actions.

## 🏗️ Environment Design (20%)
The state management utilizes strict **Pydantic Models** enforcing type-safety across action spaces. The environment ensures deep-copied reset states and tracks intermediate actions dynamically through observation cycles.

**Observation Space (`CustomObservation`)**
- `feedback`: String output of the last action outcome (e.g. "Found 2 results in KB").
- `current_tickets`: Live dynamic array of Open Tickets in the immediate queue.
- `kb_results`: Knowledge base documents returned from successful search actions.

**Action Space (Strict JSON payload)**
The agent must pass `{"action": { ... }}` payloads wrapping one of the following exact types:
1. `{"action_type": "search_kb", "query": "..."}`
2. `{"action_type": "reply_ticket", "ticket_id": "T0XX", "response": "..."}`
3. `{"action_type": "assign_ticket", "ticket_id": "T0XX", "department": "Billing | Technical Support | Escalations"}`
4. `{"action_type": "close_ticket", "ticket_id": "T0XX"}`
5. `{"action_type": "submit", "reason": "..."}`

## 💻 Code Quality & Spec Compliance (15%)
Fully compliant with the unified OpenEnv `/step`, `/reset`, and `/state` API specifications.
- ✅ Uses `openenv-core` packaging.
- ✅ Provides the automated `openenv.yaml` schema manifest.
- ✅ Includes an automated testing OpenAI API baseline script (`inference.py`).
- ✅ Exposes the necessary Hugging Face `/baseline`, `/grader`, and `/tasks` programmatic endpoints.
- ✅ Features comprehensive exception handling within FastAPI endpoints.

---

## 🚀 Execution & Setup Instructions

### 1. Local Testing
Install the environment dependencies:
```bash
pip install -r requirements.txt
```
Run the FastAPI OpenEnv Server locally:
```bash
python -m uvicorn app:app --port 7860
```
*You can now visit `http://localhost:7860/docs` in your browser to manually test the visual API Swagger representation!*

### 2. Run the Automated Baseline Agent
We have included a reproducible inference script (`inference.py`) that utilizes OpenAI's `gpt-4o` acting as the standard evaluation agent navigating the environment step-by-step.
```bash
# Export your API key in the terminal
export OPENAI_API_KEY="sk-your-openai-api-key"

# OR in Windows PowerShell:
# $env:OPENAI_API_KEY="sk-your-openai-api-key"

# Run the agent against the live environment
python inference.py
```
*Note: Make sure the FastAPI server from step 1 is running before executing the baseline!*

### 3. Deploy to Hugging Face Spaces (Docker)
This repository is 100% compliant with standard Hugging Face Docker frameworks!
1. Create a new Space on [Hugging Face](https://huggingface.co/spaces) and select **Docker** as the space SDK.
2. Ensure you tag your Space with `openenv`.
3. Upload all the python and configuration files in this directory to the repository.
4. The included `Dockerfile` will automatically build the `python:3.10-slim` container, fetch `requirements.txt`, and execute Uvicorn continuously on port `7860`.
5. Your open environment will rapidly be live and evaluatable!
"# scalar_submission" 
