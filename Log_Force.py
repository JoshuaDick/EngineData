import nidaqmx
from nidaqmx.constants import AcquisitionType
import csv
from datetime import datetime

csv_filename = 'Force_log.csv'




#THE CURRENT ERROR IS +-1LB ON THE SENSOR
with open(csv_filename,mode='w',newline='') as csvfile:
    fieldnames = ['Timestamp', 'Force (LB)','Voltage (mV)']
    writer = csv.DictWriter(csvfile,fieldnames=fieldnames)

    writer.writeheader()
    with nidaqmx.Task() as task:
    #Define channel to read in voltage
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0",min_val=-0.1,max_val=0.1)
    #read samples continuously
    
        task.timing.cfg_samp_clk_timing(100.0,sample_mode=AcquisitionType.CONTINUOUS)
        task.ai_channels.ai_adc_timing_mode=nidaqmx.constants.ADCTimingMode.HIGH_RESOLUTION
        
        Voltage = input("Measure Battery Voltage: ")
        rt = 'no'
        while rt != 'y':
            rt = input('ready to Tare? y/n')
        Zero = 0
        for i in range(1000):
            Zero += task.read()

        slope = 1000/(float(Voltage)*2)
        offset = slope*Zero

        print("Logging Torque...")
        while True:
            Vin = task.read()*1000
            Force = Vin*slope-offset
            #print(Vin, " mV")
            #print("Force = ", Force, " LB")

            #Get formatted timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

            writer.writerow({'Timestamp': timestamp, 'Force (LB)': Force, 'Voltage (mV)': Vin})




