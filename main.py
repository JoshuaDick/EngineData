import subprocess
import tkinter as tk
import psutil
import platform
import ctypes as ct
from tkinter import PhotoImage
from tkinter import Label
import os
import sys

#Black bar on windows for aesthetics
def dark_title_bar(window):
    if 'Windows' in platform.platform():
        window.update()
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        value = 2
        value = ct.c_int(value)
        set_window_attribute(hwnd, 20, ct.byref(value), 4)

#Function to run the selected process chosen by the user
def run_process(process_number):
    new_window = tk.Toplevel(root)
    new_window.config(bg='black')
    new_window.resizable(False,False)
    new_window.attributes('-topmost',True)
    dark_title_bar(new_window)
    root.withdraw()
    processes = []

    new_window.protocol("WM_DELETE_WINDOW", lambda:doNothing())
    back_button = tk.Button(new_window, text="Back to Main", command=lambda:returnToMain(processes,new_window),bg='black',fg='white',activebackground='navy',activeforeground='white')
    back_button.pack(pady=5)
   
    if process_number == 1:
        new_window.title("Live RPM & Torque")
        label = tk.Label(new_window, text="Running Live RPM & Torque...", bg='black',fg='white')
        label.pack(pady=10)
        process = subprocess.Popen(['python',r'dyno-interface\\Quick&Dirty\\LivePlotter.py'])
        processes.append(process)
    else:
        new_window.title("Recording Interface")
        label = tk.Label(new_window, text="Running Recording Interface...",bg='black',fg='white')
        label.pack(pady=10)
        process = subprocess.Popen(["python",r'dyno-interface\\Quick&Dirty\\localBrowser.py'])
        processes.append(process)


#Crucial function in every codebase
def doNothing():
    pass

#Function to kill all subprocesses of a parent process
def kill_subprocesses(parent_pid):
    try:
        parent = psutil.Process(parent_pid)
        # Get all children of the parent process
        children = parent.children(recursive=True)
        for child in children:
            child.kill() 
    except psutil.NoSuchProcess:
        print(f"No process with PID {parent_pid} found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def returnToMain(processes,window):
    for process in processes:
        kill_subprocesses(process.pid)
        process.kill()
    window.destroy()
    root.deiconify()

def on_live_rpm():
    run_process(1)

def on_recording_interface():
    run_process(2)
    

#Animation function for background graphic
def update(ind):
    
    frame = frames[ind]
    ind += 1
    if ind == frameCnt:
        ind = 0
    label2.configure(image=frame)
    root.after(25, update, ind)

def onClose():
    kill_subprocesses(process.pid)
    process.kill()
    sys.exit(0)
    
    
#Initialize application
root = tk.Tk()

process = subprocess.Popen(["python",r'dyno-interface\\dyno-interface\\app.py'])
#Background Animation
frameCnt = 45
frame_directory = 'frames_cache'
frames = [PhotoImage(file=os.path.join(frame_directory, f"frame_{i}.gif")) for i in range(frameCnt)]
root.configure(bg='black')
root.protocol("WM_DELETE_WINDOW", onClose)  
label2 = Label(root,bg='black')

#Text Label
label2.config(text="Background")
label2.place(relx=0.5,rely=0.5,anchor=tk.CENTER)
root.title("Dyno Interface")
root.geometry("500x500")

label = tk.Label(root, text="Welcome to the Dyno Interface.",bg='black',fg='white',font=('Times',25))
label.pack(pady=(0,25))

#Button Labels
live_rpm_button = tk.Button(root, text="Live RPM & Torque", command=on_live_rpm, bg='gray9',fg='white',font='Times',activebackground='navy',activeforeground='white')
recording_button = tk.Button(root, text="Launch Recording Interface", command=on_recording_interface, bg='gray9',fg='white',font='Times',activebackground='navy',activeforeground='white')
live_rpm_button.pack(pady=5)
recording_button.pack(pady=20)

#Set attributes of root application
root.resizable(False,False)
dark_title_bar(root)
root.after(0, update, 0)
root.withdraw()
root.deiconify()
# Run the GUI event loop
root.mainloop()

