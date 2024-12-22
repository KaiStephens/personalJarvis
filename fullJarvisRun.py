import subprocess
import threading
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

scripts = [
    current_dir + "/jarvis.py",
    current_dir + "/scheduler.py",
    current_dir + "/jarvisUI.py"
]

def run_script(script):
    try:
        result = subprocess.run(["python", script], check=True, text=True, capture_output=True)
        print(f"Output from {script}:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error while running {script}: {e.stderr}")
    except FileNotFoundError:
        print(f"Script {script} not found.")

threads = []

for script in scripts:
    thread = threading.Thread(target=run_script, args=(script,))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

