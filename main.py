#This will turn into the primary executable
import subprocess


if __name__ == "__main__":
    print("Welcome to the Dyno Interface.")
    print("Enter 1 for Live RPM & Torque")
    print("Enter 2 to launch recording interface")
    user_input = ''
    while ((user_input!=1) and (user_input !=2)):
        user_input=int(input("?"))
    
    if user_input==1:
        subprocess.run(['python',r'dyno-interface\Quick&Dirty\LivePlotter.py'])
    else:
        subprocess.run(["python",r'dyno-interface\dyno-interface\app.py'])
    