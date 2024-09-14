#This will turn into the primary executable

import threading
import subprocess

def runTorque():
    subprocess.run(["python","data-logging\Log_Force.py"])

def runRPM():
    subprocess.run(["python","data-logging\Log_RPM.py"])


if __name__ == "__main__":
    thread1 = threading.Thread(target=runTorque)
    thread2 = threading.Thread(target=runRPM)
    
    thread1.start()
    print("Torque Running")
    thread2.start()
    print("RPM Running")

    thread1.join()
    thread2.join()
