"""OpenEnv baseline inference script.

Evaluator-facing requirements this script satisfies:
- File is named inference.py at repository root.
- Uses OpenAI client for model calls.
- Reads credentials/config from environment variables.
- Prints [START]/[STEP]/[END] structured output blocks to stdout.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List


ENV_API_URL = os.getenv("ENV_API_URL", "http://localhost:7860")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

MAX_STEPS = int(os.getenv("MAX_STEPS", "20"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
SLEEP_SECONDS = float(os.getenv("STEP_DELAY_SECONDS", "0.2"))


SYSTEM_PROMPT = """
You are solving a customer-support ticket environment.
Return exactly one JSON object with one action at each step.

Allowed action formats:
{"action_type":"search_kb","query":"..."}
{"action_type":"reply_ticket","ticket_id":"T...","response":"..."}
{"action_type":"assign_ticket","ticket_id":"T...","department":"Billing"}
{"action_type":"assign_ticket","ticket_id":"T...","department":"Technical Support"}
{"action_type":"assign_ticket","ticket_id":"T...","department":"Escalations"}
{"action_type":"close_ticket","ticket_id":"T..."}
{"action_type":"submit","reason":"..."}

Policy:
- Invoice or billing issues -> Billing.
- Crashes/bugs/system failures -> Technical Support.
- Legal/lawyer/severe complaints -> Escalations.
- For refund replies, include the exact phrase: 3-5 business days.
- For password reset replies, include the exact phrase: Forgot Password.
- After all tickets are handled, submit.
""".strip()


def log(msg: str) -> None:
    """Print debug/diagnostic messages to stderr so they don't interfere with
    the evaluator's stdout parsing."""
    print(msg, file=sys.stderr, flush=True)


def emit(msg: str) -> None:
    """Print structured output to stdout for the evaluator."""
    print(msg, flush=True)


def ensure_client():
    from openai import OpenAI
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN environment variable is required")
    return OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)


def safe_json_load(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def choose_fallback_action(state_data: Dict[str, Any]) -> Dict[str, Any]:
    tickets: List[Dict[str, Any]] = state_data.get("current_tickets", []) or []

    for t in tickets:
        if t.get("status") == "open" and "invoice" in t.get("issue_description", "").lower():
            return {
                "action_type": "assign_ticket",
                "ticket_id": t["ticket_id"],
                "department": "Billing",
            }

    for t in tickets:
        issue = t.get("issue_description", "").lower()
        if t.get("status") == "open" and "refund" in issue:
            if not any("3-5 business days" in r for r in t.get("replies", [])):
                return {
                    "action_type": "reply_ticket",
                    "ticket_id": t["ticket_id"],
                    "response": "Refunds are processed in 3-5 business days.",
                }
            return {"action_type": "close_ticket", "ticket_id": t["ticket_id"]}

    for t in tickets:
        issue = t.get("issue_description", "").lower()
        if t.get("status") != "open":
            continue
        if "crash" in issue or "bug" in issue or "upload" in issue:
            return {
                "action_type": "assign_ticket",
                "ticket_id": t["ticket_id"],
                "department": "Technical Support",
            }
        if "lawyer" in issue or "legal" in issue:
            return {
                "action_type": "assign_ticket",
                "ticket_id": t["ticket_id"],
                "department": "Escalations",
            }
        if "password" in issue:
            if not any("Forgot Password" in r for r in t.get("replies", [])):
                return {
                    "action_type": "reply_ticket",
                    "ticket_id": t["ticket_id"],
                    "response": "Please click Forgot Password on the login page.",
                }
            return {"action_type": "close_ticket", "ticket_id": t["ticket_id"]}

    return {"action_type": "submit", "reason": "All tickets handled"}


def get_action_from_model(
    client,
    current_task: str,
    state_data: Dict[str, Any],
    history: List[str],
) -> Dict[str, Any]:
    import requests as _req
    user_prompt = json.dumps(
        {
            "task": current_task,
            "state": state_data,
            "history": history[-10:],
            "instruction": "Return only one valid action JSON object.",
        },
        ensure_ascii=True,
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    return safe_json_load(raw)


def run_task(client, task_name: str) -> float:
    import requests

    # --- Structured output: [START] ---
    emit(f"[START] task={task_name}")

    log(f"--- Running task: {task_name} ---")
    reset_res = requests.post(f"{ENV_API_URL}/reset", params={"task_name": task_name}, timeout=30)
    reset_res.raise_for_status()

    done = False
    step_count = 0
    history: List[str] = []
    last_reward = 0.0

    while not done and step_count < MAX_STEPS:
        state_res = requests.get(f"{ENV_API_URL}/state", timeout=30)
        state_res.raise_for_status()
        state_data = state_res.json()

        try:
            action_payload = get_action_from_model(client, task_name, state_data, history)
        except Exception as exc:
            log(f"Model call failed, using fallback action: {exc}")
            action_payload = choose_fallback_action(state_data)

        api_action = {"action": action_payload}
        log(f"Step {step_count}: {json.dumps(api_action, ensure_ascii=True)}")

        step_res = requests.post(f"{ENV_API_URL}/step", json=api_action, timeout=30)
        if step_res.status_code >= 400:
            log(f"Step failed ({step_res.status_code}), using fallback action next turn.")
            history.append(f"step {step_count}: invalid action")
            # Emit [STEP] even on failure
            emit(f"[STEP] step={step_count} reward=0.0")
            step_count += 1
            time.sleep(SLEEP_SECONDS)
            continue

        step_data = step_res.json()
        done = bool(step_data.get("done", False))
        reward_val = (step_data.get("reward") or {}).get("value", 0.0)
        last_reward = reward_val
        history.append(f"step {step_count}: reward={reward_val}")

        # --- Structured output: [STEP] ---
        emit(f"[STEP] step={step_count} reward={reward_val}")

        step_count += 1
        time.sleep(SLEEP_SECONDS)

    # Get final score from grader
    grader_res = requests.get(f"{ENV_API_URL}/grader", timeout=30)
    score = 0.01
    if grader_res.status_code < 400:
        grader_data = grader_res.json()
        score = float(grader_data.get("score", 0.01))
    score = max(0.01, min(0.99, score))

    # --- Structured output: [END] ---
    emit(f"[END] task={task_name} score={score} steps={step_count}")

    log(f"Task {task_name} final score: {score:.2f}")
    return score


def main() -> None:
    import requests

    log("Starting baseline inference")
    log(f"Environment URL: {ENV_API_URL}")
    log(f"Model: {MODEL_NAME}")
    log(f"API base: {API_BASE_URL}")

    client = ensure_client()

    total_score = 0.0
    task_scores: Dict[str, float] = {}
    for task in ["easy", "medium", "hard"]:
        score = run_task(client, task)
        task_scores[task] = score
        total_score += score

    log("\n=== Baseline Summary ===")
    for task, score in task_scores.items():
        log(f"{task}: {score:.2f}")
    log(f"overall: {total_score:.2f}/3.00")


if __name__ == "__main__":
    main()
