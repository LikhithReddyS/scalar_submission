import subprocess
import time
import sys
import os

print("Killing any existing uvicorn...")
subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)

time.sleep(1)

print("Starting server...")
server_proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--port", "7860"])

time.sleep(3)

print("Running baseline...")
env_vars = os.environ.copy()
env_vars["OPENAI_API_KEY"] = "dummy"

baseline_proc = subprocess.Popen([sys.executable, "baseline.py"], env=env_vars, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

stdout, stderr = baseline_proc.communicate()

print("--- STDOUT ---")
print(stdout)
print("--- STDERR ---")
print(stderr)

server_proc.terminate()
print("Done.")
