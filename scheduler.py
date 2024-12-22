import subprocess
import os
import schedule
import time

current_dir = os.path.dirname(os.path.abspath(__file__))

script_path = os.path.join(current_dir, "goodMorning.py")

def run_good_morning():
    subprocess.run(["python3", script_path])

schedule.every().day.at("06:30").do(run_good_morning)

print("Scheduler is running. The task will execute at 6:30 AM every day.")

while True:
    schedule.run_pending()
    time.sleep(1)
