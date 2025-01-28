import matplotlib.pyplot as plt2
import matplotlib.animation as animation2
import numpy as np
import nidaqmx.constants
import nidaqmx
from nidaqmx.constants import AcquisitionType
from scipy.signal import ShortTimeFFT
from scipy.signal.windows import boxcar
import warnings
import os
import math


def move_figure(f, x, y):
    """Move figure's upper left corner to pixel (x, y)"""
    f.canvas.manager.window.wm_geometry("+%d+%d" % (x, y))

def ShowLiveRPM():
    global anim
    fig2,ax2 = plt2.subplots(num='Live RPM ;)',figsize=(8,6))
    plt2.title("RPM")
    plt2.color='red'
    move_figure(fig2,200,100)

    x=[]
    y=[]
    SCALE = 60.0
    window = boxcar(1250)
    fs = 250000
    SFT = ShortTimeFFT(win=window,hop=100,fs=fs,scale_to='magnitude') 
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0",min_val=0,max_val=10)
                
        task.timing.cfg_samp_clk_timing(fs,sample_mode=AcquisitionType.FINITE,samps_per_chan=int(fs*0.05))
        
        
        def animate2(i):
                task.start()
                Vin = task.read(number_of_samples_per_channel=int(fs*0.05))
                task.stop()
                if(len(Vin)>0):
                    nparray = np.array(Vin)
                    nparray = nparray - np.mean(nparray)
                    Sx = SFT.stft(nparray)

                    strongest_indices = np.argmax(abs(Sx),axis=0)
                    strongest_frequencies = strongest_indices*SFT.delta_f
                    RPMS = strongest_frequencies*60/SCALE
                    avgRPM = sum(RPMS)/len(RPMS)
                    #define dBm cutoff to prevent noise from affecting the signal
                    if (20*math.log10(abs(Sx).max()) < -30):
                         avgRPM = 0
                    x.append(i)
                    y.append(avgRPM)
                    if len(x) >= 50:
                        x.pop(0)
                        y.pop(0)
                ax2.clear()
                ax2.plot(x,y,color='red')
                ax2.set_title("RPM")
                plt2.xlabel('Sample #')
                plt2.ylabel('RPM')
                
                    
        anim=animation2.FuncAnimation(fig2,animate2,interval=50)
        ax2.set_facecolor('lightgray')
        
        plt2.show()

warnings.filterwarnings("ignore")
ShowLiveRPM()
os._exit(0)