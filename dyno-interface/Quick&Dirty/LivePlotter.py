import subprocess
import threading


def plotRPM():
    subprocess.run(['python',r'dyno-interface\\Quick&Dirty\\liveRPM.py'])
def plotTorque():
    subprocess.run(['python',r'dyno-interface\\Quick&Dirty\\liveTorque.py'])


if __name__ == "__main__":
    rpm = threading.Thread(target=plotRPM)
    torque = threading.Thread(target=plotTorque)
    rpm.start()
    torque.start()


    
    
