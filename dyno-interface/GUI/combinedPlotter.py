import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import nidaqmx
import nidaqmx.constants
from nidaqmx.constants import AcquisitionType
from scipy.signal import stft
from scipy.signal.windows import hann
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
import serial
import serial.tools.list_ports
import threading



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

# Parameters for FFT (SAMPS_PER_CHANNEL is kinda useless atm)
fs = 250000
SAMPS_PER_CHANNEL = int(fs * 0.5)

# Parameter for recording
RECORDING_INTERVAL_SEC = 0.01 #10ms between each recorded value, 100Hz

# Parameters for serial comms
SERIAL_BAUD = 115200
SERIAL_RECONNECT_INTERVAL = 2.0

CANBED_VID = 0X2E8A
CANBED_PIDS = [0X000A, 0X0003, 0X0005]

"""
Continuously tries to find and connect to a CANBed RP2040 over USB-serial.
Call send_torque(value) from any thread to transmit a torque reading.
Read .connected and .port_name for UI status.
"""
class SerialManager:
    def __init__(self):
        self._conn: serial.Serial | None = None
        self._lock = threading.Lock()
        self.connected = False
        self.port_name = ""
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
 
    def _is_canbed(self, port) -> bool:
        # Return True if this port looks like a CANBed RP2040.
        desc = (port.description or "").lower()
        mfr  = (port.manufacturer or "").lower()
 
        # Match by VID/PID
        if port.vid == CANBED_VID and port.pid in CANBED_PIDS:
            return True
 
        # Friendly-name fallback
        keywords = ("canbed", "rp2040", "raspberry pi", "pico", "seeed")
        if any(k in desc or k in mfr for k in keywords):
            return True
 
        return False
 
    def _try_connect(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if self._is_canbed(port):
                try:
                    conn = serial.Serial(port.device, SERIAL_BAUD, timeout=1)
                    time.sleep(0.5)          # allow RP2040 USB CDC to settle
                    with self._lock:
                        self._conn = conn
                        self.connected = True
                        self.port_name = port.device
                    print(f"[Serial] Connected to CANBed RP2040 on {port.device}")
                    return True
                except Exception as e:
                    print(f"[Serial] Failed to open {port.device}: {e}")
        return False
 
    def _run(self):
        #Background loop: keep trying to connect; detect disconnections.
        while not self._stop_event.is_set():
            with self._lock:
                already_connected = self.connected
                conn = self._conn
 
            if not already_connected:
                self._try_connect()
            else:
                # Ping the port to detect disconnection
                if conn is None or not conn.is_open:
                    with self._lock:
                        self.connected = False
                        self._conn = None
                        self.port_name = ""
                    print("[Serial] Disconnected — will retry…")
 
            time.sleep(SERIAL_RECONNECT_INTERVAL)
 
    def send_torque(self, value: float):
        #Send a torque value as an ASCII line: 'T:<value>\\n'.
        with self._lock:
            conn = self._conn
            ok   = self.connected
 
        if not ok or conn is None:
            return
 
        try:
            line = f"{value}\n".encode()
            conn.write(line)
        except Exception as e:
            print(f"[Serial] Write error: {e}")
            with self._lock:
                self.connected = False
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None
                self.port_name = ""
 
    def stop(self):
        self._stop_event.set()
        with self._lock:
            if self._conn and self._conn.is_open:
                try:
                    self._conn.close()
                except Exception:
                    pass


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
    serial_mgr = SerialManager()

    plt.style.use('dark_background')

    fig, (ax_torque, ax_rpm, ax_hp) = plt.subplots(
        1, 3,
        num='Live Dashboard',
        figsize=(FIG_WIDTH, FIG_HEIGHT)
    )

    # Pre-create plot lines
    line_torque, = ax_torque.plot([], [], color='cyan')
    line_rpm, = ax_rpm.plot([], [], color='red')
    line_hp, = ax_hp.plot([], [], color='white')

    # Axis setup
    setup_axis(ax_torque, TORQUE_XMAX, TORQUE_YMAX)
    setup_axis(ax_rpm, RPM_XMAX, RPM_YMAX)
    setup_axis(ax_hp, HP_XMAX, HP_YMAX)

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

    arduino_dot = ax_hp.text(0.97, 0.96, "●", transform=ax_hp.transAxes, color='red', fontsize=8, ha='center')
    arduino_label = ax_hp.text(0.955, 0.96, "Arduino", transform=ax_hp.transAxes, color='white', fontsize=8, ha='right')

    # Shared state
    latest_rpm = [None]
    latest_torque = [None]

    last_time = [time.time()]
    fps = [0.0]

    # Logging file path
    default_output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data-logging'))
    output_path = [default_output_path]

    # Torque state
    x_torque, y_torque = [], []
    zero_voltage = [0.0]
    latest_avgVin = [0.0]
    slope = 5

    # RPM state
    x_rpm, y_rpm = [], []
    sample_rpm = [0]
    avgRPM_last = 0.0
    rpm_smoothed = [0.0]
    alpha = 0.5

    SCALE = 60.0

    # HP state
    x_hp, y_hp = [], []
    sample_hp = [0]
    hp_last = [0.0]


    # Recording state
    is_recording = [False]
    record_start_time = [None]
    recorded_data = []



    # DAQ Tasks
    with nidaqmx.Task() as torque_task, nidaqmx.Task() as rpm_task:

        torque_task.ai_channels.add_ai_voltage_chan(
            "cDAQ1Mod1/ai0", min_val=-0.125, max_val=0.125
        )

        torque_task.timing.cfg_samp_clk_timing(
            50.0,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=2
        )

        torque_task.ai_channels.ai_adc_timing_mode = \
            nidaqmx.constants.ADCTimingMode.HIGH_RESOLUTION

        torque_task.start()

        rpm_task.ai_channels.add_ai_voltage_chan(
            "cDAQ1Mod3/ai0", min_val=0, max_val=10
        )

        rpm_task.timing.cfg_samp_clk_timing(
            fs,
            sample_mode=AcquisitionType.CONTINUOUS
            #samps_per_chan=SAMPS_PER_CHANNEL
        )
        rpm_task.in_stream.input_buf_size = SAMPS_PER_CHANNEL * 10
        rpm_task.start()

        # Animation Loop

        def animate(i):
            nonlocal avgRPM_last
            current_time = time.time()
            dt = current_time - last_time[0]

            if dt > 0:
                fps[0] = 1/dt

            last_time[0] = current_time
            fps_text.set_text(f"FPS: {fps[0]:.1f}")


            #Arduino indicator
            if serial_mgr.connected:
                arduino_dot.set_color('lime')
                arduino_label.set_text(f"Arduino ({serial_mgr.port_name})")
            else:
                arduino_dot.set_color('red')
                arduino_label.set_text("Arduino")

            # TORQUE

            Vin = torque_task.read(
                number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE
            )

            if len(Vin) > 0:

                avgVin = (sum(Vin) / len(Vin)) * 1000
                latest_avgVin[0] = avgVin

                Force = (avgVin * 4.297 - 41.89) * (1 - 0.728)

                x_torque.append(i)
                y_torque.append(Force)

                if len(x_torque) >= MAX_POINTS_TORQUE:
                    x_torque.pop(0)
                    y_torque.pop(0)

                latest_torque[0] = Force

                title_torque.set_text(f"Torque (Ft-Lb): {round(Force,5)}")

                line_torque.set_data(range(len(y_torque)), y_torque)

                serial_mgr.send_torque(round(Force,1))

            # RPM
            Vin_rpm = rpm_task.read(
                number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE
            )


            if len(Vin_rpm) > 0:

                nparray = np.array(Vin_rpm)
                nparray = nparray - np.mean(nparray)

                f_bins, _, Zxx = stft(
                    nparray,
                    fs=fs,
                    window=hann(len(nparray)),
                    nperseg=len(nparray)
                )

                mag = np.abs(Zxx)

                strongest_freq_index = np.argmax(np.mean(mag, axis=1))
                strongest_frequency = f_bins[strongest_freq_index]

                avgRPM = strongest_frequency * 60 / SCALE

                if 20 * math.log10(mag.max()) < -30:
                    avgRPM = 0

                x_rpm.append(sample_rpm[0])
                y_rpm.append(avgRPM)

                if len(x_rpm) >= MAX_POINTS_RPM:
                    x_rpm.pop(0)
                    y_rpm.pop(0)

                sample_rpm[0] += 1

                
                rpm_smoothed[0] = alpha * avgRPM + (1-alpha) * rpm_smoothed[0]
                avgRPM_last = rpm_smoothed[0]
                latest_rpm[0] = avgRPM_last

            title_rpm.set_text(f"RPM: {round(avgRPM_last,2)}")

            line_rpm.set_data(range(len(y_rpm)), y_rpm)


            # HORSEPOWER
            rpm = latest_rpm[0]
            torque = latest_torque[0]

            if rpm is not None and torque is not None:

                hp = rpm * torque / 5252
                hp_last[0] = hp

                latest_rpm[0] = None
                latest_torque[0] = None

                x_hp.append(sample_hp[0])
                y_hp.append(hp)

                if len(x_hp) >= MAX_POINTS_HP:
                    x_hp.pop(0)
                    y_hp.pop(0)

                sample_hp[0] += 1

                title_hp.set_text(f"Power (HP): {round(hp,2)}")

                line_hp.set_data(range(len(y_hp)), y_hp)

            # RECORDING
            if (is_recording[0] and record_start_time[0] is not None):
                elapsed = round(current_time - record_start_time[0],3)
                if len(recorded_data) == 0 or elapsed - recorded_data[-1][0] >= RECORDING_INTERVAL_SEC: #prevent excessively large file size
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
                arduino_dot,
                arduino_label
            )

        anim = animation.FuncAnimation(
            fig,
            animate,
            interval=1,
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

            zero_voltage[0] = latest_avgVin[0]
            offset = slope * zero_voltage[0]

            print(f"Zero set to voltage: {zero_voltage[0]}")

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
                record_button.color = 'darkred'
                record_button.ax.set_facecolor('darkred')
                fig.canvas.draw_idle()
            else:
                is_recording[0] = False
                record_button.label.set_text('Record')
                record_button.ax.set_facecolor('black')
                fig.canvas.draw_idle()
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                os.makedirs(output_path[0], exist_ok=True)
                filename = os.path.join(output_path[0], f'{timestamp}.csv')
                with open(filename, 'w', newline='') as f:
                    f.write('"Time","RPM","Torque","Horsepower"\n')
                    for row in recorded_data:
                        f.write(f'{row[0]},{row[1]},{row[2]},{row[3]}\n')

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

    serial_mgr.stop()


warnings.filterwarnings("ignore")
ShowLiveDashboard()
os._exit(0)
