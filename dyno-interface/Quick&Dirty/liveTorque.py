import matplotlib.pyplot as plt
import matplotlib.animation as animation
import nidaqmx.constants
import nidaqmx
from nidaqmx.constants import AcquisitionType
import warnings
import os
import platform
import ctypes as ct

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
    fig1,ax1 = plt.subplots(num='Live Torque ;)',figsize=(8,6))
    plt.title("Torque")
    move_figure(fig1,1000,100)
    dark_title_bar(fig1.canvas.manager.window)
    fig1.canvas.toolbar.pack_forget()
    x=[]
    y=[]
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0",min_val=-0.125,max_val=0.125)
        task.timing.cfg_samp_clk_timing(50.0,sample_mode=AcquisitionType.CONTINUOUS,samps_per_chan=2)
        task.ai_channels.ai_adc_timing_mode=nidaqmx.constants.ADCTimingMode.HIGH_RESOLUTION
        Voltage = 12.04

        Zero = 1.72
        slope = 1000/(float(Voltage)*2)
        offset = slope*Zero
        task.start()
        def animate(i):
            Vin = task.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)
            if (len(Vin) > 0):
                x.append(i)
                avgVin = sum(Vin)/len(Vin)
                avgVin = avgVin*1000
                Force = avgVin*slope-offset
                y.append(Force)

                if len(x) >= 50:
                    x.pop(0)
                    y.pop(0)

            ax1.clear()
            plt.xlabel('Sample #')
            plt.ylabel('Torque (Ft-LB)')
            ax1.plot(x,y)
            
            ax1.set_title("Torque")
            

        anim=animation.FuncAnimation(fig1,animate,interval=10)
        ax1.set_facecolor('black')
        plt.show()
        
warnings.filterwarnings("ignore")

ShowLiveTorque()
os._exit(0)