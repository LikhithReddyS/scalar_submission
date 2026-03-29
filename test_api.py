import requests
import json
import time

URL = "http://localhost:7860"
print("Resetting to EASY task...")
requests.post(f"{URL}/reset", params={"task_name": "easy"})

# Step 1: Assign to Billing
action1 = {
    "action": {
        "action_type": "assign_ticket",
        "ticket_id": "T001",
        "department": "Billing"
    }
}
res = requests.post(f"{URL}/step", json=action1)
print(f"Step 1: {res.json()}")

# Step 2: Submit
action2 = {
    "action": {
        "action_type": "submit",
        "reason": "done"
    }
}
res = requests.post(f"{URL}/step", json=action2)
print(f"Step 2: {res.json()}")

# Grader
res = requests.get(f"{URL}/grader")
print(f"EASY SCORE: {res.json()}")
