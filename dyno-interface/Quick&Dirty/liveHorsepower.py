import matplotlib.pyplot as plt2
import matplotlib.animation as animation2
from flask import Flask, request, jsonify
import threading
import warnings
import os
import platform
import ctypes as ct
import matplotlib

# Flask app initialization
app = Flask(__name__)

# Global variables to store RPM and Torque values
latest_rpm = None
latest_torque = None

# Flask API routes
@app.route('/api/rpm', methods=['POST'])
def update_rpm():
    global latest_rpm
    data = request.json
    if "rpm" in data:
        latest_rpm = data["rpm"]
        return jsonify({"message": "RPM updated successfully"}), 200
    return jsonify({"error": "Missing 'rpm' in request"}), 400

@app.route('/api/torque', methods=['POST'])
def update_torque():
    global latest_torque
    data = request.json
    if "torque" in data:
        latest_torque = data["torque"]
        return jsonify({"message": "Torque updated successfully"}), 200
    return jsonify({"error": "Missing 'torque' in request"}), 400

# Helper functions
def reset_data():
    global latest_rpm
    global latest_torque
    latest_rpm = None
    latest_torque = None

def dark_title_bar(window):
    if 'Windows' in platform.platform():
        window.update()
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        value = 2
        value = ct.c_int(value)
        set_window_attribute(hwnd, 20, ct.byref(value), 4)

def move_figure(f, x, y):
    """Move figure's upper left corner to pixel (x, y)"""
    f.canvas.manager.window.wm_geometry("+%d+%d" % (x, y))

def getLatestRPM():
    return latest_rpm

def getLatestTorque():
    return latest_torque

def ShowLiveHP():
    global anim
    plt2.style.use('dark_background')
    fig2, ax2 = plt2.subplots(num='Live Horsepower ;)', figsize=(8, 6))
    plt2.title("Horsepower")
    
    move_figure(fig2, 200, 100)
    dark_title_bar(fig2.canvas.manager.window)
    fig2.canvas.toolbar.pack_forget()
    x = []
    y = []
    def animate2(i):
        global sample
        rpm = getLatestRPM()
        torque = getLatestTorque()
        if rpm is not None and torque is not None:
            hp = rpm * torque / 5252
            reset_data()

            # Append data for live plotting
            x.append(sample)
            y.append(hp)

            # Limit number of points for live update
            if len(x) >= 50:
                x.pop(0)
                y.pop(0)
            sample = sample + 1
            # Update the plot
            ax2.clear()
            ax2.plot(x, y, color='white')
            ax2.set_facecolor('black')
            ax2.set_title("Horsepower")
            plt2.xlabel('Sample #')
            plt2.ylabel('Horsepower')

    anim = animation2.FuncAnimation(fig2, animate2, interval=50)
    ax2.set_facecolor('lightgray')
    plt2.show()

# Run the Flask app in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    # Start Flask server in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    sample = 0
    # Run the live plot
    matplotlib.use('TkAgg')
    warnings.filterwarnings("ignore")
    ShowLiveHP()
    os._exit(0)
