import matplotlib.pyplot as plt2
import matplotlib.animation as animation2
import numpy as np
import nidaqmx.constants
import nidaqmx
from nidaqmx.constants import AcquisitionType
from scipy.signal import ShortTimeFFT
from scipy.signal.windows import boxcar



def ShowLiveRPM():
    fig2,ax2 = plt2.subplots(num='Live RPM ;)')

    plt2.title("RPM")

    x=[]
    y=[]
    SCALE = 60.0
    window = boxcar(1250)
    fs = 250000 #Sample Rate
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
                    x.append(i)
                    y.append(avgRPM)
                    if len(x) >= 50:
                        x.pop(0)
                        y.pop(0)
                ax2.clear()
                ax2.plot(x,y)
                ax2.set_title("RPM")
                plt2.xlabel('Sample #')
                plt2.ylabel('RPM')
                    
        anim=animation2.FuncAnimation(fig2,animate2,interval=50)
        plt2.show()

ShowLiveRPM()