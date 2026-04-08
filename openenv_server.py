from fastapi import FastAPI, HTTPException
import subprocess
from environment import CustomerSupportEnv
from schema import CustomerAction
from tasks import TASKS
import os

app = FastAPI(title="OpenEnv - Customer Support Ticket Resolution")
env = CustomerSupportEnv()

@app.get("/")
def greet_json():
    return {"Hello": "World!"}

@app.post("/reset")
def reset(task_name: str = "easy"):
    if task_name not in TASKS:
        raise HTTPException(status_code=400, detail="Invalid task_name. Choose from: easy, medium, hard.")
    obs = env.reset(task_name)
    return obs.dict()

@app.post("/step")
def step(action: CustomerAction):
    try:
        obs, reward, done, info = env.step(action)
        return {
            "observation": obs.dict(),
            "reward": reward.dict(),
            "done": done,
            "info": info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
def state():
    return env.state().dict()

@app.get("/tasks")
def get_tasks():
    return {
        "tasks": [
            {"id": "easy", "description": TASKS["easy"]["description"]},
            {"id": "medium", "description": TASKS["medium"]["description"]},
            {"id": "hard", "description": TASKS["hard"]["description"]},
        ],
        "action_schema": CustomerAction.schema()
    }

@app.get("/grader")
def get_grader():
    if not env.done:
        return {"error": "Episode not finished. Call step with submit action to finish."}
    # Calculate score
    grader = TASKS[env.current_task_id]["grader"]
    final_score = grader([t.dict() for t in env.tickets])
    return {"score": final_score}

@app.get("/baseline")
def run_baseline():
    try:
        # Check if python is available
        import sys
        
        # Run baseline inference script
        env_vars = os.environ.copy()
        result = subprocess.run([sys.executable, "inference.py"], capture_output=True, text=True, env=env_vars)
        if result.returncode != 0:
            return {"error": "Baseline failed", "details": result.stderr, "stdout": result.stdout}
        return {"output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))