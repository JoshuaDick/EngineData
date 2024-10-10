import matplotlib.pyplot as plt
import matplotlib.animation as animation
import nidaqmx.constants
import nidaqmx
from nidaqmx.constants import AcquisitionType
import warnings
import psutil, os, time




me = psutil.Process(os.getpid())

def ShowLiveTorque():
    fig1,ax1 = plt.subplots(num='Live Torque ;)',figsize=(8,6))
    plt.title("Torque")


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
        
        plt.show()
        
warnings.filterwarnings("ignore")

ShowLiveTorque()
while 1:
    if me.parent() is not None:
        # still alive
        time.sleep(0.1)
        continue
    else:
        os._exit(0)
        break