import subprocess
import tkinter as tk
import psutil
import webbrowser

def run_process(process_number):
    new_window = tk.Toplevel(root)
    root.withdraw()

        # Add a button to return to the main window
    new_window.protocol("WM_DELETE_WINDOW", lambda:doNothing)
    back_button = tk.Button(new_window, text="Back to Main", command=lambda:returnToMain(process,new_window))
    back_button.pack(pady=5)
    # Instead of running the subprocess directly, open a new window
    if process_number == 1:
        new_window.title("Live RPM & Torque")
        label = tk.Label(new_window, text="Running Live RPM & Torque...")
        label.pack(pady=10)
        process = subprocess.Popen(['python',r'dyno-interface\Quick&Dirty\LivePlotter.py'])  # Simulate running a process
    else:
        new_window.title("Recording Interface")
        label = tk.Label(new_window, text="Running Recording Interface...")
        label.pack(pady=10)
        process = subprocess.Popen(["python",r'dyno-interface\dyno-interface\app.py'])  # Simulate running a process
        webbrowser.open("http://127.0.0.1:8050/")


def doNothing():
    pass


def kill_subprocesses(parent_pid):
    try:
        parent = psutil.Process(parent_pid)
        # Get all children of the parent process
        children = parent.children(recursive=True)
        for child in children:
            #print(f"Killing subprocess: {child.pid} ({child.name()})")
            child.kill()  # or child.terminate() for a graceful exit
        #print(f"Killed all subprocesses of parent PID {parent_pid}")
    except psutil.NoSuchProcess:
        print(f"No process with PID {parent_pid} found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def returnToMain(process,window):
    kill_subprocesses(process.pid)
    process.kill()
    window.destroy()
    root.deiconify()

def on_live_rpm():
    run_process(1)

def on_recording_interface():
    run_process(2)
# Create the main window
root = tk.Tk()
root.title("Dyno Interface")
root.geometry("400x400")
# Create a label
label = tk.Label(root, text="Welcome to the Dyno Interface.")
label.pack(pady=10)
# Create buttons for selection
live_rpm_button = tk.Button(root, text="Live RPM & Torque", command=on_live_rpm)
recording_button = tk.Button(root, text="Launch Recording Interface", command=on_recording_interface)

live_rpm_button.pack(pady=5)
recording_button.pack(pady=5)

# Run the GUI event loop
root.mainloop()
