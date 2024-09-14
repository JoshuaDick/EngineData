import nidaqmx
from nidaqmx.constants import AcquisitionType
import csv
from datetime import datetime
import time

csv_filename = 'Torque_log.csv'




#THE CURRENT ERROR IS +-1LB ON THE SENSOR
with open(csv_filename,mode='w',newline='') as csvfile:
    fieldnames = ['Timestamp', 'Torque (Ft-LB)','Voltage (mV)']
    writer = csv.DictWriter(csvfile,fieldnames=fieldnames)

    writer.writeheader()
    with nidaqmx.Task() as task:
    #Define channel to read in voltage
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0",min_val=-0.1,max_val=0.1)
    #read samples continuously
    
        task.timing.cfg_samp_clk_timing(50,sample_mode=AcquisitionType.CONTINUOUS,samps_per_chan=2)
        task.ai_channels.ai_adc_timing_mode=nidaqmx.constants.ADCTimingMode.HIGH_SPEED
        
        #Measured voltage from the supply to the Load Cell
        Voltage = 12.04
        '''
        while rt != 'y':
            rt = input('ready to Tare? y/n')
        Zero = 0
        for i in range(1000):
            Zero += task.read()
        '''

        Zero = 0.3785
        slope = 1000/(float(Voltage)*2)
        offset = slope*Zero

        task.start()
        print("Logging Torque...")
        while True:
            Vin = task.read(number_of_samples_per_channel = nidaqmx.constants.READ_ALL_AVAILABLE)*1000
            if (len(Vin) > 0):
                avgVin = sum(Vin)/len(Vin)
                Force = avgVin*slope-offset

                #Get formatted timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

                writer.writerow({'Timestamp': timestamp, 'Torque (Ft-LB)': Force, 'Voltage (mV)': avgVin})




