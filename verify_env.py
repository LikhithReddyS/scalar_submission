import subprocess
import time
import sys
import os

print("Starting openenv_server...")
server_proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "openenv_server:app", "--port", "7860"])

time.sleep(5)
print("Running inference.py...")
env_vars = os.environ.copy()
env_vars["OPENAI_API_KEY"] = "dummy"

baseline_proc = subprocess.Popen([sys.executable, "inference.py"], env=env_vars, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = baseline_proc.communicate()

print("--- STDOUT ---")
print(stdout)
print("--- STDERR ---")
print(stderr)

server_proc.terminate()
print("Verification complete.")
