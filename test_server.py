import requests
import time

url = "http://localhost:7860"

def run_test():
    print("Testing /reset (easy)...")
    try:
        res = requests.post(f"{url}/reset?task_name=easy")
        print("Reset:", res.json())
        
        print("\nTesting /state...")
        res = requests.get(f"{url}/state")
        state = res.json()
        print("State tickets:", len(state.get("current_tickets", [])))
        
        if len(state.get("current_tickets", [])) > 0:
            ticket_id = state["current_tickets"][0]["ticket_id"]
            
            print(f"\nTesting /step (AssignTicket to Billing for {ticket_id})...")
            action = {
                "action": {
                    "action_type": "assign_ticket",
                    "ticket_id": ticket_id,
                    "department": "Billing"
                }
            }
            res = requests.post(f"{url}/step", json=action)
            print("Step Output:", res.json())
            
            print("\nTesting /step (Submit)...")
            action_submit = {
                "action": {
                    "action_type": "submit",
                    "reason": "test finish"
                }
            }
            res = requests.post(f"{url}/step", json=action_submit)
            print("Submit Output:", res.json())
            
            print("\nTesting /grader...")
            res = requests.get(f"{url}/grader")
            print("Final Score:", res.json())
    except Exception as e:
        print("Error connecting to server:", e)

if __name__ == "__main__":
    # Wait for server to start before running tests
    print("Running integration tests against the OpenEnv server...")
    run_test()
