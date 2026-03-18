import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.widgets import Button
import warnings
import os
import platform
import ctypes as ct
import math
import time
import csv
from datetime import datetime
from tkinter import filedialog
import tkinter as tk

# Parameters for graphing

FIG_WIDTH  = 15
FIG_HEIGHT = 4

TORQUE_XMAX = 100
RPM_XMAX    = 100
HP_XMAX     = 100

TORQUE_YMAX = 200
RPM_YMAX    = 20000
HP_YMAX     = 120

MAX_POINTS_TORQUE = TORQUE_XMAX
MAX_POINTS_RPM    = RPM_XMAX
MAX_POINTS_HP     = HP_XMAX

# Parameter for recording
RECORDING_INTERVAL_SEC = 0.1  # 100ms between each recorded value, 10Hz

# Simulation Parameters
SIM_RPM_BASE       = 7000.0   # Base RPM around which simulation oscillates
SIM_RPM_AMPLITUDE  = 5000.0    # How much RPM varies (±)
SIM_RPM_FREQ       = 0.1      # Oscillation frequency in Hz

SIM_TORQUE_BASE      = 25.0   # Base torque (Ft-Lb)
SIM_TORQUE_AMPLITUDE = 10.0   # How much torque varies (±)
SIM_TORQUE_FREQ      = 0.07   # Oscillation frequency in Hz

SIM_NOISE_RPM    = 50.0  # Random noise amplitude for RPM
SIM_NOISE_TORQUE = 2.0   # Random noise amplitude for Torque


# Window helpers

def dark_title_bar(window):
    if 'Windows' in platform.platform():
        window.update()
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        value = ct.c_int(2)
        set_window_attribute(hwnd, 20, ct.byref(value), 4)


def move_figure(f, x, y):
    f.canvas.manager.window.wm_geometry("+%d+%d" % (x, y))


# Axis Setup Helper

def setup_axis(ax, xmax, ymax):
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_facecolor('black')
    ax.set_xlabel('Sample #')


# Main dashboard

def ShowLiveDashboard():

    plt.style.use('dark_background')

    fig, (ax_torque, ax_rpm, ax_hp) = plt.subplots(
        1, 3,
        num='Live Dashboard (Simulation)',
        figsize=(FIG_WIDTH, FIG_HEIGHT)
    )

    # Pre-create plot lines
    line_torque, = ax_torque.plot([], [], color='cyan')
    line_rpm,    = ax_rpm.plot([], [], color='red')
    line_hp,     = ax_hp.plot([], [], color='white')

    # Axis setup
    setup_axis(ax_torque, TORQUE_XMAX, TORQUE_YMAX)
    setup_axis(ax_rpm,    RPM_XMAX,    RPM_YMAX)
    setup_axis(ax_hp,     HP_XMAX,     HP_YMAX)

    fig.subplots_adjust(left=0.05, right=0.97, top=0.82, bottom=0.12, wspace=0.3)

    move_figure(fig, 100, 100)
    dark_title_bar(fig.canvas.manager.window)
    fig.canvas.toolbar.pack_forget()

    # Titles (axis-relative coords)

    title_torque = ax_torque.text(
        0.3, 0.92,
        "Torque: 0",
        transform=ax_torque.transAxes,
        color='cyan',
        fontsize=12,
        ha='center'
    )

    title_rpm = ax_rpm.text(
        0.5, 0.92,
        "RPM: 0",
        transform=ax_rpm.transAxes,
        color='red',
        fontsize=12,
        ha='center'
    )

    title_hp = ax_hp.text(
        0.5, 0.92,
        "HP: 0",
        transform=ax_hp.transAxes,
        color='white',
        fontsize=12,
        ha='center'
    )

    fps_text = ax_torque.text(
        0.8, 0.92,
        "FPS: 0",
        transform=ax_torque.transAxes,
        color='lime',
        fontsize=12,
        ha='center'
    )

    sim_label = ax_hp.text(
        0.98, 0.05,
        "[ SIMULATION ]",
        transform=ax_hp.transAxes,
        color='yellow',
        fontsize=9,
        ha='right',
        alpha=0.6
    )

    # Shared state
    latest_rpm    = [None]
    latest_torque = [None]

    last_time = [time.time()]
    fps = [0.0]

    # Logging file path
    default_output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data-logging'))
    output_path = [default_output_path]

    # Torque state
    x_torque, y_torque = [], []
    latest_avgVin = [0.0]

    # RPM state
    x_rpm, y_rpm = [], []
    sample_rpm  = [0]
    avgRPM_last = 0.0
    rpm_smoothed = [0.0]
    alpha = 0.5

    # HP state
    x_hp, y_hp = [], []
    sample_hp = [0]
    hp_last   = [0.0]

    # Recording state
    is_recording      = [False]
    record_start_time = [None]
    recorded_data     = []

    # Simulation start reference
    sim_start = time.time()

    # Animation Loop

    def animate(i):
        nonlocal avgRPM_last
        current_time = time.time()
        dt = current_time - last_time[0]

        if dt > 0:
            fps[0] = 1 / dt

        last_time[0] = current_time
        fps_text.set_text(f"FPS: {fps[0]:.1f}")

        t = current_time - sim_start  # seconds since start

        # TORQUE (simulated)

        simulated_torque = (
            SIM_TORQUE_BASE
            + SIM_TORQUE_AMPLITUDE * math.sin(2 * math.pi * SIM_TORQUE_FREQ * t)
            + np.random.uniform(-SIM_NOISE_TORQUE, SIM_NOISE_TORQUE)
        )

        Force = simulated_torque

        x_torque.append(i)
        y_torque.append(Force)

        if len(x_torque) >= MAX_POINTS_TORQUE:
            x_torque.pop(0)
            y_torque.pop(0)

        latest_torque[0] = Force
        title_torque.set_text(f"Torque (Ft-Lb): {round(Force, 5)}")
        line_torque.set_data(range(len(y_torque)), y_torque)

        # RPM (simulated)

        simulated_rpm = (
            SIM_RPM_BASE
            + SIM_RPM_AMPLITUDE * math.sin(2 * math.pi * SIM_RPM_FREQ * t)
            + np.random.uniform(-SIM_NOISE_RPM, SIM_NOISE_RPM)
        )
        simulated_rpm = max(0.0, simulated_rpm)

        avgRPM = simulated_rpm

        x_rpm.append(sample_rpm[0])
        y_rpm.append(avgRPM)

        if len(x_rpm) >= MAX_POINTS_RPM:
            x_rpm.pop(0)
            y_rpm.pop(0)

        sample_rpm[0] += 1

        rpm_smoothed[0] = alpha * avgRPM + (1 - alpha) * rpm_smoothed[0]
        avgRPM_last = rpm_smoothed[0]
        latest_rpm[0] = avgRPM_last

        title_rpm.set_text(f"RPM: {round(avgRPM_last, 2)}")
        line_rpm.set_data(range(len(y_rpm)), y_rpm)

        # HORSEPOWER

        rpm    = latest_rpm[0]
        torque = latest_torque[0]

        if rpm is not None and torque is not None:

            hp = rpm * torque / 5252
            hp_last[0] = hp

            latest_rpm[0]    = None
            latest_torque[0] = None

            x_hp.append(sample_hp[0])
            y_hp.append(hp)

            if len(x_hp) >= MAX_POINTS_HP:
                x_hp.pop(0)
                y_hp.pop(0)

            sample_hp[0] += 1

            title_hp.set_text(f"Power (HP): {round(hp, 2)}")
            line_hp.set_data(range(len(y_hp)), y_hp)

        # RECORDING
        if is_recording[0] and record_start_time[0] is not None:
            elapsed = round(current_time - record_start_time[0], 3)
            if len(recorded_data) == 0 or elapsed - recorded_data[-1][0] >= RECORDING_INTERVAL_SEC:
                torque_val = y_torque[-1] if y_torque else 0.0
                recorded_data.append([elapsed, rpm_smoothed[0], torque_val, hp_last[0]])

        return (
            line_torque,
            line_rpm,
            line_hp,
            title_torque,
            title_rpm,
            title_hp,
            fps_text,
            sim_label
        )

    anim = animation.FuncAnimation(
        fig,
        animate,
        interval=10,
        blit=True
    )

    # Zero Button (not being used atm)
    ax_button = fig.add_axes([0.05, 0.88, 0.07, 0.07])

    zero_button = Button(
        ax_button,
        'Zero Now',
        color='black',
        hovercolor='blue'
    )

    zero_button.label.set_color('white')

    for spine in ax_button.spines.values():
        spine.set_edgecolor('white')

    def zero_callback(event):
        print(f"Zero set (simulation — no-op)")

    zero_button.on_clicked(zero_callback)

    # Record Button
    ax_record = fig.add_axes([0.13, 0.88, 0.10, 0.07])
    record_button = Button(ax_record, 'Record', color='black', hovercolor='green')
    record_button.label.set_color('white')
    for spine in ax_record.spines.values():
        spine.set_edgecolor('white')

    def record_callback(event):
        if not is_recording[0]:
            is_recording[0] = True
            record_start_time[0] = time.time()
            recorded_data.clear()
            record_button.label.set_text('Stop Recording')
            record_button.ax.set_facecolor('darkred')
            fig.canvas.draw_idle()
        else:
            is_recording[0] = False
            record_button.label.set_text('Record')
            record_button.ax.set_facecolor('black')
            fig.canvas.draw_idle()
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = os.path.join(output_path[0], f'{timestamp}.csv')
            with open(filename, 'w', newline='') as f:
                f.write('"Time","RPM","Torque","Horsepower"\n')
                for row in recorded_data:
                    f.write(f'{row[0]},{row[1]},{row[2]},{row[3]}\n')
            print(f"Saved {len(recorded_data)} rows to {filename}")

    record_button.on_clicked(record_callback)
    # Set Path Button
    ax_path = fig.add_axes([0.24, 0.88, 0.10, 0.07])
    path_button = Button(ax_path, 'Set Log File Path', color='black', hovercolor='blue')
    path_button.label.set_color('white')
    for spine in ax_path.spines.values():
        spine.set_edgecolor('white')

    def path_callback(event):
        os.makedirs(output_path[0], exist_ok=True)
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        chosen = filedialog.askdirectory(
            title="Select output folder for logs",
            initialdir=output_path[0]
        )
        root.destroy()
        if chosen:
            output_path[0] = chosen
            print(f"Output path set to: {output_path[0]}")

    path_button.on_clicked(path_callback)
    plt.show()

    plt.show()


warnings.filterwarnings("ignore")
ShowLiveDashboard()
os._exit(0)