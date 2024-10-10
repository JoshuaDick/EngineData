import subprocess
import tkinter as tk


def run_process(process_number):
    new_window = tk.Toplevel(root)
    process = subprocess.Popen(['echo','Starting...'])
        # Add a button to return to the main window
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




def returnToMain(process,window):
    process.kill()
    window.destroy()
def on_live_rpm():
    run_process(1)

def on_recording_interface():
    run_process(2)

# Create the main window
root = tk.Tk()
root.title("Dyno Interface")

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
