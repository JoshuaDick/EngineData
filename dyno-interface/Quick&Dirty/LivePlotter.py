import subprocess
import threading
import warnings

def plotRPM():
    subprocess.run(['python',r'dyno-interface\Quick&Dirty\liveRPM.py'])
def plotTorque():
    subprocess.run(['python',r'dyno-interface\Quick&Dirty\liveTorque.py'])


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    rpm = threading.Thread(target=plotRPM)
    torque = threading.Thread(target=plotTorque)
    rpm.start()
    torque.start()
    rpm.join()
    torque.join()

    
    
