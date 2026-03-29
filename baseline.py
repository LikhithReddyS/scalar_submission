import requests
import json
import os
import time
from openai import OpenAI

API_URL = os.getenv("API_URL", "http://localhost:7860")

def get_action_from_llm(client, state_desc, current_task):
    system_prompt = f"""
You are receiving observation texts from a customer support environment. Your job is to resolve the open tickets.
The environment expects actions in JSON format.
The current task is: {current_task}

Valid action formats (you must return ONLY valid JSON matching exactly one of these forms):
{{"action_type": "search_kb", "query": "your search term"}}
{{"action_type": "reply_ticket", "ticket_id": "T001", "response": "your reply text"}}
{{"action_type": "assign_ticket", "ticket_id": "T001", "department": "Billing"}}  (Valid departments: "Billing", "Technical Support", "Escalations")
{{"action_type": "close_ticket", "ticket_id": "T001"}}
{{"action_type": "submit", "reason": "Completed task"}} (Call this action when all required tickets are fully handled according to the task)

Remember, your output must be purely JSON without markdown backticks.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Using gpt-4o as standard baseline
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state_desc}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("LLM Call Failed:", e)
        # return empty search as fallback
        return {"action_type": "search_kb", "query": "error fallback"}

def run_task(client, task_name):
    print(f"\n--- Running Task: {task_name} ---")
    requests.post(f"{API_URL}/reset", params={"task_name": task_name})
    
    done = False
    step_count = 0
    max_steps = 15
    while not done and step_count < max_steps:
        try:
            state_res = requests.get(f"{API_URL}/state")
            state_data = state_res.json()
            obs_desc = json.dumps(state_data, indent=2)
            
            action_payload = get_action_from_llm(client, obs_desc, task_name)
            
            # Format according to Pydantic Discriminator structure from Schema
            api_action = {"action": action_payload}
                
            print(f"[{step_count}] Action: {api_action}")
            step_res = requests.post(f"{API_URL}/step", json=api_action)
            step_data = step_res.json()
            
            if "done" in step_data:
                done = step_data["done"]
            else:
                print("Error in step:", step_data)
                break
        except Exception as e:
            print("Exception during step execution:", e)
            break
            
        step_count += 1
        time.sleep(1) # simple rate limiting
        
    # Get grader score
    grader_res = requests.get(f"{API_URL}/grader")
    score_data = grader_res.json()
    score = score_data.get("score", 0.0)
    print(f"Task {task_name} Final Score: {score}")
    return score

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
         print("Missing OPENAI_API_KEY, cannot run baseline.")
         # Mock or exit in CI environments
         exit(0)
         
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    total_score = 0
    for task in ["easy", "medium", "hard"]:
        score = run_task(client, task)
        total_score += score
    
    print(f"\nOverall Baseline Score: {total_score}/3.0")
