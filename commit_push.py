import subprocess
import sys

def run_cmd(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    result.check_returncode()

def main():
    try:
        run_cmd(['git', 'add', '-A'])
        run_cmd(['git', 'commit', '-m', 'Fix strict bounds evaluation edge cases in app.py and inference.py'])
        run_cmd(['git', 'push'])
        print("Successfully committed and pushed.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
