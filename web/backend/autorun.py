from watchgod import run_process
import subprocess
import time


def run():
    time.sleep(3)
    p1 = subprocess.Popen(['python3', 'user-service/main.py'])
    p2 = subprocess.Popen(['python3', 'function-service/main.py'])
    p3 = subprocess.Popen(['python3', 'workflow-service/main.py'])
    p4 = subprocess.Popen(['python3', 'deploy-service/test_service.py'])
    p5 = subprocess.Popen(['python3', 'stats-service/main.py'])
    p1.wait()
    p2.wait()
    p3.wait()
    p4.wait()
    p5.wait()


run()
# run_process('./', run)
