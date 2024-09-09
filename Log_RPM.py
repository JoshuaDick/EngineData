import nidaqmx
from nidaqmx.constants import AcquisitionType
import csv
from datetime import datetime
from time import perf_counter

csv_filename = 'RPM_log.csv'
scale = 10.0
with open(csv_filename,mode='w',newline='') as csvfile:
    fieldnames = ['Timestamp', 'RPM','Voltage (mV)']
    writer = csv.DictWriter(csvfile,fieldnames=fieldnames)

    writer.writeheader()

    with nidaqmx.Task() as task:
        #Define channel for NI 9205 (pins 1 & 19)
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0",min_val=-1.0,max_val=1.0)
        #100Khz sample rate
        task.timing.cfg_samp_clk_timing(100000.0,sample_mode=AcquisitionType.CONTINUOUS)

        print("Logging RPM...")

        while True:
            try:
                t1_start = 0
                RisingEdge = False
                Vin = task.read()

            #once we see a high signal, we measure high time
                if (Vin > 0.1):
                    t1_start = perf_counter()
                    RisingEdge = True
                while Vin > 0.1:
                    Vin = task.read()

            #Log RPM based on high time, or log 0RPM
                if RisingEdge:
                    t1_end = perf_counter()

                #RPM calculation based on fixed 49.9% Duty Cycle from M130 with scale of 10.0Hz
                    rpm = (0.499/(t1_end-t1_start))*60/scale
                #log RPM with timestamp
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    writer.writerow({'Timestamp': timestamp, 'Force (LB)': rpm, 'Voltage (mV)': Vin*1000})
                else:
                #log RPM of 0 with timestamp
                    rpm = 0.0
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    writer.writerow({'Timestamp': timestamp, 'RPM': rpm, 'Voltage (mV)': Vin*1000})
            except nidaqmx.errors.DaqReadError:
                print("Buffer Overflow")


