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

    # Shared state

    latest_rpm = [None]
    latest_torque = [None]

    last_time = [time.time()]
    fps = [0.0]

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

            return (
                line_torque,
                line_rpm,
                line_hp,
                title_torque,
                title_rpm,
                title_hp,
                fps_text
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

        plt.show()


warnings.filterwarnings("ignore")
ShowLiveDashboard()
os._exit(0)
