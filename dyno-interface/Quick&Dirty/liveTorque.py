import matplotlib.pyplot as plt
import matplotlib.animation as animation
import nidaqmx.constants
import nidaqmx
from nidaqmx.constants import AcquisitionType
import warnings
import os
import platform
import ctypes as ct
import matplotlib
import requests
from matplotlib.widgets import Button

API = 'http://127.0.0.1:5000/api/'

def send_torque(torque_value):
    url = API + 'torque'
    data = {'torque': torque_value}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Torque updated successfully: {torque_value}")
        else:
            print(f"Failed to update Torque: {response.json()['error']}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Torque data: {e}")

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

def ShowLiveTorque():
    plt.style.use('dark_background')
    fig1,ax1 = plt.subplots(num='Live Torque ;))',figsize=(5,4))
    plt.title("Torque (Ft-LB)")
    move_figure(fig1,1100,100)
    dark_title_bar(fig1.canvas.manager.window)
    fig1.canvas.toolbar.pack_forget()
    x=[]
    y=[]
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0",min_val=-0.125,max_val=0.125)
        task.timing.cfg_samp_clk_timing(50.0,sample_mode=AcquisitionType.CONTINUOUS,samps_per_chan=2)
        task.ai_channels.ai_adc_timing_mode=nidaqmx.constants.ADCTimingMode.HIGH_RESOLUTION
        VOLTAGE = 14.02

        slope = 5

        zero_voltage = [0.0]        # stores voltage that represents zero torque
        offset = [0.0]              # slope * zero_voltage
        latest_avgVin = [0.0]       # most recent measured voltage
        task.start()
        def animate(i):
            Vin = task.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)
            if (len(Vin) > 0):
                x.append(i)
                avgVin = sum(Vin)/len(Vin)
                avgVin = avgVin*1000
                latest_avgVin[0] = avgVin   # store most recent voltage

                Force = (avgVin - zero_voltage[0]) * slope
                #Force = avgVin - Zero
                y.append(Force)

                if len(x) >= 200:
                    x.pop(0)
                    y.pop(0)
                send_torque(Force)

                ax1.clear()
                ax1.set_ylim(0, 200)
                #plt.xlabel('Sample #')
                ax1.set_title(f"Torque (Ft-Lb) {round(Force, 5)}")
                ax1.plot(x,y)
            
        
        anim=animation.FuncAnimation(fig1,animate,interval=10)
        ax1.set_facecolor('black')
        # Create Zero button
        ax_button = plt.axes([0.75, 0.9, 0.15, 0.06])
        ax_button.set_facecolor('black')
        zero_button = Button(ax_button, 'Zero Now')

        zero_button = Button(
        ax_button,
        'Zero Now',
        color='black',          # button background
        hovercolor='blue'    # darker gray on hover
        )
        zero_button.label.set_color('white')
        # Style border to white
        for spine in ax_button.spines.values():
            spine.set_edgecolor('white')

        def zero_callback(event):
            zero_voltage[0] = latest_avgVin[0]
            offset[0] = slope * zero_voltage[0]
            print(f"Zero set to voltage: {zero_voltage[0]}")

        zero_button.on_clicked(zero_callback)
        plt.show()

matplotlib.use('TkAgg')
warnings.filterwarnings("ignore")

ShowLiveTorque()
os._exit(0)

