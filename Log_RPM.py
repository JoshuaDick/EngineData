import nidaqmx
from nidaqmx.constants import AcquisitionType
import csv
from datetime import datetime
from time import perf_counter
import time

csv_filename = 'RPM_log.csv' #name of file to log data into
SCALE = 20.0 #Hz
THRESHOLD = 0.1 #RISING EDGE THRESHOLD IN VOLTS


with open(csv_filename,mode='w',newline='') as csvfile:
    fieldnames = ['Timestamp', 'RPM','Frequency (Hz)']
    writer = csv.DictWriter(csvfile,fieldnames=fieldnames)

    writer.writeheader()

    with nidaqmx.Task() as task:
        #Define channel for NI 9205 (pins 1 & 19)
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0",min_val=0,max_val=10)
        #100Khz sample rate
        task.timing.cfg_samp_clk_timing(100000,sample_mode=AcquisitionType.CONTINUOUS,samps_per_chan=1000)

        print("Logging RPM...")
        task.start()
        delay_start = time.time()
        DataPoints = []
        while True:
                #Read in an array of 1000 samples at 100kHz
                Vin = task.read(number_of_samples_per_channel = nidaqmx.constants.READ_ALL_AVAILABLE)
                if len(Vin) > 0:
                #Average the number of consecutive high signals in the array
                    consecutive_Values = []
                    current_count = 0
                    for i in range(len(Vin)):
                        if (Vin[i] >= THRESHOLD):
                             current_count += 1
                        else:
                             if current_count != 0:
                                consecutive_Values.append(current_count)
                             current_count = 0

                    if len(consecutive_Values)>0:
                         avgConsecutiveHighs = sum(consecutive_Values)/len(consecutive_Values)

                         highTime = avgConsecutiveHighs/100000
                        #Equation for rpm from duty cycle and measured high time
                         rpm = 0.499/(highTime)*60/SCALE
                         
                         #LIMIT TO 10HZ TO PREVENT INSANE STORAGE OVERFLOW
                         DataPoints.append(rpm)
                         if time.time() - delay_start > 0.1:
                            delay_start = time.time()
                            #log average RPM with timestamp
                            avgrpm = sum(DataPoints)/len(DataPoints)
                            DataPoints = []
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                            writer.writerow({'Timestamp': timestamp, 'RPM': avgrpm, 'Frequency (Hz)': SCALE*avgrpm/60})


