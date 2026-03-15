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


# Window helpers
def dark_title_bar(window):
    if 'Windows' in platform.platform():
        window.update()
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent   = ct.windll.user32.GetParent
        hwnd  = get_parent(window.winfo_id())
        value = ct.c_int(2)
        set_window_attribute(hwnd, 20, ct.byref(value), 4)


def move_figure(f, x, y):
    """Move figure's upper left corner to pixel (x, y)"""
    f.canvas.manager.window.wm_geometry("+%d+%d" % (x, y))


# Main dashboard
def ShowLiveDashboard():

    plt.style.use('dark_background')

    # Three subplots side-by-side; 15×4 gives each panel the same feel as
    # the original 5×4 individual windows.
    fig, (ax_torque, ax_rpm, ax_hp) = plt.subplots(
        1, 3,
        num='Live Dashboard',
        figsize=(15, 4)
    )
    fig.subplots_adjust(left=0.05, right=0.97, top=0.82, bottom=0.12, wspace=0.3)

    move_figure(fig, 100, 100)
    dark_title_bar(fig.canvas.manager.window)
    fig.canvas.toolbar.pack_forget()

    # Shared in-memory state 
    latest_rpm    = [None]   # written by RPM block, read & cleared by HP block
    latest_torque = [None]   # written by Torque block, read & cleared by HP block

    # Torque state  
    x_torque, y_torque = [], []
    zero_voltage  = [0.0]
    latest_avgVin = [0.0]
    slope         = 5

    # RPM state 
    x_rpm, y_rpm  = [], []
    sample_rpm    = [0]
    avgRPM_last   = [0.0]   # keeps last good value for the title

    SCALE    = 60.0
    fs       = 250000
    win_hann = hann(5000)
    nperseg  = 5000
    hop_size = 100
    nfft     = 2 ** 14
    noverlap = nperseg - hop_size

    # Horsepower state
    x_hp, y_hp = [], []
    sample_hp  = [0]
    hp_last    = [0.0]      # keeps last good value for the title

    # Open both DAQ tasks simultaneously
    with nidaqmx.Task() as torque_task, nidaqmx.Task() as rpm_task:

        # Torque task setup (continuous, high-resolution)
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

        # RPM task setup (finite, started/stopped each frame)
        rpm_task.ai_channels.add_ai_voltage_chan(
            "cDAQ1Mod3/ai0", min_val=0, max_val=10
        )
        rpm_task.timing.cfg_samp_clk_timing(
            fs,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=int(fs * 0.05)
        )

        # Single animate callback that runs all three panels sequentially
        def animate(i):
            # 1. TORQUE 
            Vin = torque_task.read(
                number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE
            )
            if len(Vin) > 0:
                x_torque.append(i)
                avgVin = (sum(Vin) / len(Vin)) * 1000
                latest_avgVin[0] = avgVin

                Force = (avgVin * 4.297 - 41.89) * (1 - 0.728)

                y_torque.append(Force)
                if len(x_torque) >= 200:
                    x_torque.pop(0)
                    y_torque.pop(0)

                # Share with HP panel via in-memory cell
                latest_torque[0] = Force

                ax_torque.clear()
                ax_torque.set_ylim(0, 200)
                ax_torque.set_facecolor('black')
                ax_torque.set_title(f"Torque (Ft-Lb) {round(Force, 5)}")
                ax_torque.plot(x_torque, y_torque)

            # 2. RPM 
            rpm_task.start()
            Vin_rpm = rpm_task.read(
                number_of_samples_per_channel=int(fs * 0.05)
            )
            rpm_task.stop()

            if len(Vin_rpm) > 0:
                nparray = np.array(Vin_rpm)
                nparray = nparray - np.mean(nparray)          # remove DC offset

                f_bins, _, Zxx = stft(
                    nparray,
                    fs=fs,
                    window=win_hann,
                    nperseg=nperseg,
                    noverlap=noverlap,
                    nfft=nfft
                )
                mag = np.abs(Zxx)

                strongest_freq_index = np.argmax(np.mean(mag, axis=1))
                strongest_frequency  = f_bins[strongest_freq_index]
                avgRPM = strongest_frequency * 60 / SCALE

                if 20 * math.log10(mag.max()) < -30:
                    avgRPM = 0

                x_rpm.append(sample_rpm[0])
                y_rpm.append(avgRPM)
                if len(x_rpm) >= 50:
                    x_rpm.pop(0)
                    y_rpm.pop(0)
                sample_rpm[0] += 1

                # Share with HP panel via in-memory cell
                latest_rpm[0] = avgRPM
                avgRPM_last[0] = avgRPM

            ax_rpm.clear()
            ax_rpm.set_ylim(0, 20000)
            ax_rpm.set_facecolor('black')
            ax_rpm.set_title(f"RPM {round(avgRPM_last[0], 2)}")
            ax_rpm.plot(x_rpm, y_rpm, color='red')
            ax_rpm.set_xlabel('Sample #')

            # 3. HORSEPOWER 
            rpm    = latest_rpm[0]
            torque = latest_torque[0]

            if rpm is not None and torque is not None:
                hp = rpm * torque / 5252
                hp_last[0] = hp

                # Consume both values (mirrors reset_data() in original)
                latest_rpm[0]    = None
                latest_torque[0] = None

                x_hp.append(sample_hp[0])
                y_hp.append(hp)
                if len(x_hp) >= 50:
                    x_hp.pop(0)
                    y_hp.pop(0)
                sample_hp[0] += 1

                ax_hp.clear()
                ax_hp.set_ylim(0, 120)
                ax_hp.set_facecolor('black')
                ax_hp.set_title(f"Horsepower {round(hp, 2)}")
                ax_hp.plot(x_hp, y_hp, color='white')
                ax_hp.set_xlabel('Sample #')

        # Interval matches the RPM original (50 ms); torque reads whatever
        # has accumulated since the last frame, just as it did originally.
        anim = animation.FuncAnimation(fig, animate, interval=50)

        # Zero button (positioned above the torque subplot in figure coords)
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
