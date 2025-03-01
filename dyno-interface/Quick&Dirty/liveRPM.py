import matplotlib.pyplot as plt2
import matplotlib.animation as animation2
import numpy as np
import nidaqmx.constants
import nidaqmx
from nidaqmx.constants import AcquisitionType
from scipy.signal import stft
from scipy.signal.windows import hann
import warnings
import os
import math
import platform
import ctypes as ct
import matplotlib
import requests
API = 'http://127.0.0.1:5000/api/'

def send_rpm(rpm_value):
    url = API + 'rpm'
    data = {'rpm': rpm_value}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"RPM updated successfully: {rpm_value}")
        else:
            print(f"Failed to update RPM: {response.json()['error']}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending RPM data: {e}")

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

def ShowLiveRPM():
    global anim
    plt2.style.use('dark_background')
    fig2, ax2 = plt2.subplots(num='Live RPM ;)', figsize=(5, 4))
    plt2.title("RPM")
    
    move_figure(fig2, 100, 100)
    dark_title_bar(fig2.canvas.manager.window)
    fig2.canvas.toolbar.pack_forget()
    x = []
    y = []
    SCALE = 60.0
    fs = 250000  # Sampling frequency
    window = hann(5000)  # Hann window for better spectral resolution
    hop_size = 100  # Hop size for the short-time FFT
    nperseg = 5000  # Increased segment length for better frequency resolution
    nfft = 2 ** 14
    noverlap = nperseg - hop_size

    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0", min_val=0, max_val=10)
        task.timing.cfg_samp_clk_timing(fs, sample_mode=AcquisitionType.FINITE, samps_per_chan=int(fs * 0.05))

        def animate2(i):
            task.start()
            Vin = task.read(number_of_samples_per_channel=int(fs * 0.05))
            task.stop()

            if len(Vin) > 0:
                nparray = np.array(Vin)
                nparray = nparray - np.mean(nparray)  # Remove DC offset
                f, t, Zxx = stft(nparray, fs=fs, window=window, nperseg=nperseg, noverlap=noverlap, nfft=nfft)

                # Extract the magnitude spectrum
                mag = np.abs(Zxx)

                # Find the index of the peak frequency closest to the expected fundamental frequency
                strongest_freq_index = np.argmax(np.mean(mag, axis=1))  # Mean across time bins
                strongest_frequency = f[strongest_freq_index]  # Frequency corresponding to the peak

                # Compute RPM based on the strongest fundamental frequency
                RPMS = strongest_frequency * 60 / SCALE
                avgRPM = RPMS

                # Apply a threshold to remove noise based on the amplitude of the signal
                if (20 * math.log10(mag.max()) < -30):
                    avgRPM = 0

                # Append data for live plotting
                x.append(i)
                y.append(avgRPM)
                send_rpm(avgRPM)

                # Limit number of points for live update
                if len(x) >= 50:
                    x.pop(0)
                    y.pop(0)

            # Update the plot
            ax2.clear()
            ax2.plot(x, y, color='red')
            ax2.set_facecolor('black')
            ax2.set_title("RPM")
            plt2.xlabel('Sample #')

        anim = animation2.FuncAnimation(fig2, animate2, interval=50)
        ax2.set_facecolor('lightgray')

        plt2.show()
matplotlib.use('TkAgg')
warnings.filterwarnings("ignore")
ShowLiveRPM()
os._exit(0)