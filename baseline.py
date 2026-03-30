import requests
import json
import os
import time
from openai import OpenAI

API_URL = os.getenv("API_URL", "http://localhost:7860")

def get_action_from_llm(client, state_desc, current_task):
    system_prompt = f"""
You are an elite customer support AI agent. Your job is to fully resolve ALL tickets exactly ONCE in the current queue and then ALWAYS call the `submit` action immediately!
The current environment task you are performing is: {current_task}

CRITICAL RULES FOR A PERFECT SCORE & AVOIDING INFINITE LOOPS:
1. KB Quoting: When you reply to a ticket, you MUST explicitly quote verbatim key phrases from the Knowledge Base (e.g., if the policy mentions "3-5 business days" or "Forgot Password", explicitly type those exact phrases in your "response").
2. Routing: Assign crashes/bugs to "Technical Support". Assign legal threats/lawyers to "Escalations". Assign invoice issues to "Billing".
3. Closing: Once a ticket's core issue is fully addressed (e.g. you sent a reply), your IMMEDIATELY following action MUST be exactly `{{"action_type": "close_ticket", "ticket_id": "<ACTUAL_TICKET_ID>"}}`.
4. AVOIDING LOOPS: Once you have assigned a ticket to a department, DO NOT assign it again. Even if it says "open" on the next turn, consider it perfectly handled!
5. FINISHING: The very second that every ticket in your observed queue has been EITHER assigned to a department OR closed, you MUST output exactly `{{"action_type": "submit", "reason": "All tickets handled"}}`.

Valid action formats (return ONLY ONE pure JSON object per turn, with NO markdown backticks):
{{"action_type": "search_kb", "query": "..."}}
{{"action_type": "reply_ticket", "ticket_id": "<ACTUAL_TICKET_ID>", "response": "..."}}
{{"action_type": "assign_ticket", "ticket_id": "<ACTUAL_TICKET_ID>", "department": "Billing"}} (or Technical Support, Escalations)
{{"action_type": "close_ticket", "ticket_id": "<ACTUAL_TICKET_ID>"}}
{{"action_type": "submit", "reason": "Completed Task"}}
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
        print("OpenAI Call Failed:", e)
        print("Falling back to Gemini API (New SDK)...")
        try:
            from google import genai
            from google.genai import types
            
            gemini_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAYFNNhg4U20Waz-qiqzqXe885R37bKIAU")
            gemini_client = genai.Client(api_key=gemini_key)
            
            prompt = f"{system_prompt}\n\nCurrent Observation:\n{state_desc}"
            
            res = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(res.text)
            
        except Exception as gemini_e:
            print("Gemini Call Failed:", gemini_e)
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
    openai_key = os.environ.get("OPENAI_API_KEY", "dummy-key-to-trigger-gemini-fallback")
    client = OpenAI(api_key=openai_key)
    
    total_score = 0
    for task in ["easy", "medium", "hard"]:
        score = run_task(client, task)
        total_score += score
    
    print(f"\nOverall Baseline Score: {total_score}/3.0")
