"""
Authors: Joshua Dick, Casey Zandbergen III
Date: 10/7/2024
Description: This program creates a Dash app that reads
in data from a csv file and displays it in a plotly graph.
The UI allows the user to overlay various dyno runs along,
any changes made to the files in the data directory will automatically
update in the UI.
"""
import os
from dash import Dash, html, dcc, Input, Output, no_update, State
import nidaqmx.constants
import pandas as pd
import plotly.graph_objects as go
import threading
import nidaqmx
from nidaqmx.constants import AcquisitionType
import csv
from datetime import datetime, timedelta
import time
import numpy as np
from scipy.signal import ShortTimeFFT
from scipy.signal.windows import boxcar

#The Threading Event that stops logging data    
stop_event = threading.Event()


#Function to log torque data
def logTorque():
    global FinishedTorque
    FinishedTorque=False
    csv_filename = r'data-logging\mostRecentTorque.csv'

    with open(csv_filename,mode='w',newline='') as csvfile:
        fieldnames = ['Timestamp', 'Torque (Ft-LB)','Voltage (mV)']
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames)

        writer.writeheader()
        with nidaqmx.Task() as task:
    #Define channel to read in voltage
            task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0",min_val=-0.125,max_val=0.125)
    #read samples continuously
    
            task.timing.cfg_samp_clk_timing(50.0,sample_mode=AcquisitionType.CONTINUOUS,samps_per_chan=2)
            task.ai_channels.ai_adc_timing_mode=nidaqmx.constants.ADCTimingMode.HIGH_RESOLUTION
        
        #Measured voltage from the supply to the Load Cell
            Voltage = 12.04

            Zero = 1.2
            slope = 1000/(float(Voltage)*2)
            offset = slope*Zero

            task.start()
            print("Logging Torque...")
            while not stop_event.is_set():
                Vin = task.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)
                if (len(Vin) > 0):
                    avgVin = sum(Vin)/len(Vin)
                    avgVin = avgVin*1000
                    Force = avgVin*slope-offset
                #Force = Vin*slope-offset

                #Get formatted timestamp
                        
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    tstamp = datetime.strptime(timestamp,'%Y-%m-%d %H:%M:%S.%f')
                    tstamp = tstamp.replace(microsecond=round(tstamp.microsecond/10000)*1000)
                    tstamp = tstamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                    writer.writerow({'Timestamp': tstamp, 'Torque (Ft-LB)': Force, 'Voltage (mV)': avgVin})

            print("Torque Finished")
            FinishedTorque=True
            return

#Function to log RPM data via high time (DEPRECATED)
def logRPM():
    csv_filename = r'data-logging\mostRecentRPM.csv' #name of file to log data into
    SCALE = 20.0 #Hz
    THRESHOLD = 4.5 #RISING EDGE THRESHOLD IN VOLTS

    with open(csv_filename,mode='w',newline='') as csvfile:
        fieldnames = ['Timestamp', 'RPM','Frequency (Hz)']
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames)

        writer.writeheader()

        with nidaqmx.Task() as task:
        #Define channel for NI 9205 (pins 1 & 19)
            task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0",min_val=0,max_val=10)
        #100Khz sample rate
            task.timing.cfg_samp_clk_timing(100000,sample_mode=AcquisitionType.CONTINUOUS,samps_per_chan=1000)

            
            task.start()
            print("Logging RPM...")
            delay_start = time.time()
            DataPoints = []
            while not stop_event.is_set():
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
                            
                            #Divided because 100khz sample rate 
                            highTime = avgConsecutiveHighs/100000
                        #Equation for rpm from duty cycle and measured high time
                            rpm = 0.499/(highTime)*60/SCALE
                         
                         #LIMIT TO 100HZ TO PREVENT INSANE STORAGE OVERFLOW
                            DataPoints.append(rpm)
                            if time.time() - delay_start > 0.01:
                                delay_start = time.time()
                            #log average RPM with timestamp
                                avgrpm = sum(DataPoints)/len(DataPoints)
                                DataPoints = []
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                                writer.writerow({'Timestamp': timestamp, 'RPM': avgrpm, 'Frequency (Hz)': SCALE*avgrpm/60})
            print("RPM Finished")
            return
#Function to log RPM data via rising edges (DEPRECATED)
def logRPM2():
    csv_filename = r'data-logging\mostRecentRPM.csv' #name of file to log data into
    SCALE = 20.0 #Hz
    THRESHOLD = 3.0 #RISING EDGE THRESHOLD IN VOLTS

    with open(csv_filename,mode='w',newline='') as csvfile:
        fieldnames = ['Timestamp', 'RPM','Frequency (Hz)']
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames)

        writer.writeheader()

        with nidaqmx.Task() as task:
        #Define channel for NI 9205 (pins 1 & 19)
            task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0",min_val=0,max_val=10)
        #100Khz sample rate
            task.timing.cfg_samp_clk_timing(250000,sample_mode=AcquisitionType.FINITE,samps_per_chan=250000*5)

            

            print("Logging RPM...")
            
            while not stop_event.is_set():
                Vin = []
                task.start()
                #START TIMER
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                #Read in an array of 250k*5 samples at 250kHz until 5 seconds has passed
                Vin = task.read(number_of_samples_per_channel=250000*5,timeout=5.05)
                task.stop()

                if len(Vin) > 0:
                    #Split array of 250k*5 samples in 5 seconds into 250 arrays for every 1/50th of a second (This improves data collection speed)
                    nparray = np.array(Vin)
                    split_arrays = np.array_split(nparray,125)

                    for i, arr in enumerate(split_arrays):
                    #find the number of rising edge signals in the array
                        lowToHighs = (arr[:-1] <= THRESHOLD) & (arr[1:] > THRESHOLD)
                        rising_edges = np.sum(lowToHighs)

                    #number of samples/250khz = time that has passed in the array
                        if rising_edges>0:
                        #frequency = number of rising edges/time passed in the array
                            frequency = rising_edges/(len(arr)*0.000004)

                        #Equation for rpm from MoTeC
                            rpm = frequency*60/SCALE
                            #Timestamp manipulation to increment by 10ms for each data point
                            tstamp = datetime.strptime(timestamp,'%Y-%m-%d %H:%M:%S.%f')+timedelta(milliseconds=i*len(arr)*0.004)
                            tstamp = tstamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                            writer.writerow({'Timestamp': tstamp, 'RPM': rpm, 'Frequency (Hz)': SCALE*rpm/60})

            print("RPM Finished")
            return
#Function to log rpm based on the Short Time Fourier Tranform of the input signal 
def FourierRPM():
    global FinishedRPM
    FinishedRPM = False
    csv_filename = r'data-logging\mostRecentRPM.csv' #name of file to log data into
    SCALE = 60.0 #Hz

    with open(csv_filename,mode='w',newline='') as csvfile:
        fieldnames = ['Timestamp', 'RPM','Frequency (Hz)']
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames)

        writer.writeheader()
        all_data = []
        with nidaqmx.Task() as task:
        #Define channel for NI 9205 (pins 1 & 19)
            task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0",min_val=0,max_val=10)
        #250Khz sample rate
            fs = 250000 #Sample Rate
            task.timing.cfg_samp_clk_timing(fs,sample_mode=AcquisitionType.FINITE,samps_per_chan=int(fs*15))

            
            
            while not stop_event.is_set():
                Vin = []
                print("Logging RPM...")
                task.start()
                #Current Timestamp when data collection starts
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                #Read in an array of 250k*10 samples at 250kHz until 10 seconds has passed
                Vin = task.read(number_of_samples_per_channel=int(fs*15),timeout=15.1)
                task.stop()
                print("15 second interval recorded")
                if len(Vin) > 0:
                    #Compute Short Time Fourier Transform of signal array over 10 seconds
                    nparray = np.array(Vin)
                    #Subtract DC Component of Waveform:
                    nparray = nparray-np.mean(nparray)
                    window = boxcar(50000) #2^13 sample window function for efficiency 
                    #hop=2500 allows 100hz frequency data collection
                    SFT = ShortTimeFFT(win=window,hop=1000,fs=fs,scale_to='magnitude') #SciPy STFT 
                    Sx = SFT.stft(nparray)
                    #Extract only the frequency with the strongest magnitude at each time
                    strongest_indices = np.argmax(abs(Sx),axis=0)
                    strongest_frequencies = strongest_indices*SFT.delta_f #This comes from the SciPy documentation
                    
                    #Equation for RPM from MoTeC based on tachometer output
                    RPMS = strongest_frequencies*60/SCALE

                    #Iterate through rpms and write data to csv with corresponding timestamp & frequency
                    for i,rpm in enumerate(RPMS):
                        delta_t = i*SFT.delta_t

                        tstamp = datetime.strptime(timestamp,'%Y-%m-%d %H:%M:%S.%f')+timedelta(seconds=delta_t) #Change in time is stored in the delta_t
                        tstamp = tstamp.replace(microsecond=round(tstamp.microsecond/10000)*1000)
                        tstamp = tstamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                        writer.writerow({'Timestamp': tstamp, 'RPM': rpm, 'Frequency (Hz)': strongest_frequencies[i]})
            #for rows in all_data:
               # writer.writerow(rows)
            FinishedRPM=True
            print("RPM Finished")
            return
def save_CSV():
    global FinishedRPM
    global FinishedTorque
    #Wait until both torque and rpm logging is done to save csv
    while not (FinishedRPM and FinishedTorque):
        time.sleep(0.4)
        pass
    #Open both files and align timestamps
    df1 = pd.read_csv(r'data-logging\mostRecentRPM.csv',header=0,names=['Timestamp','RPM', 'Voltage (mV)'])
    df2 = pd.read_csv(r'data-logging\mostRecentTorque.csv',header=0,names=['Timestamp','Torque (ft-lbs)','Frequency (Hz)'])
    df1.pop('Voltage (mV)')
    df2.pop('Frequency (Hz)')

    merged_df = pd.merge(df1,df2,on='Timestamp')
#Calculate horsepower and remove timestamp from csv for graphing
    merged_df['Horsepower'] = merged_df['Torque (ft-lbs)']*merged_df['RPM']/5252
    merged_df.pop('Timestamp')
    first_row = pd.DataFrame([{'RPM': '0','Torque (ft-lbs)': '0','Horsepower': '0'}])
    merged_df = pd.concat([first_row,merged_df],ignore_index=True)
# Generate unique filename from current timestamp

    currentTime = str(datetime.now())
    filename = r"dyno-interface\dyno-interface\data" + "\\" +  currentTime.split(":")[0] + currentTime.split(":")[1] + currentTime.split(":")[2] + ".csv"
    merged_df.to_csv(filename,index=False)

    print("Created CSV: ", filename)



def plot_data(file: str) -> go.Figure:
    """
    Takes in a csv file and returns a plotly figure of the data.
    Parameters: file (str): path to csv file
    Returns: fig (go.Figure): plotly figure
    """

    # read in data
    dyno_df = pd.read_csv(file)

    # get rpm dataframe
    rpm_df = dyno_df["RPM"]
    # get torque dataframe
    torque_df = dyno_df["Torque (ft-lbs)"]
    # get horsepower dataframe
    hp_df = dyno_df["Horsepower"]
    # create figure
    fig = go.Figure()

    # plot torque curve
    fig.add_trace(
        go.Scatter(x=rpm_df, y=torque_df, mode="lines", name="Torque (ft-lbs)")
    )

    # plot horsepower curve
    fig.add_trace(go.Scatter(x=rpm_df, y=hp_df, mode="lines", name="HP"))

    return fig


def get_current_datetime() -> str:
    """
    Get the current date and time
    Returns: formatted_date (str): formatted date and time
    """
    now = datetime.now()
    formatted_date = now.strftime("%m/%d/%Y")
    formatted_time = now.strftime("%H:%M:%S")

    return f"{formatted_date} {formatted_time}"


def get_files_in_directory(path) -> list:
    """
    Get list of files within directory, filtered by .csv extension
    Parameters: path (str): path to directory
    Returns: csv_files (list): list of files with .csv extension
    """

    # get the list of files in the specified directory
    files_list = os.listdir(path)

    # filter only the files with ".csv" extension
    csv_files = [file for file in files_list if file.endswith(".csv")]

    # return the list of files with .csv extension
    return csv_files


# initialize the directory path where your files are located
directory_path = "dyno-interface\dyno-interface\data"

# get the list of files from the specified directory (dyno runs)
files = get_files_in_directory(directory_path)

# load data
dyno_graph = plot_data(directory_path + "/" + files[0])
dyno_graph.update_layout(
        # format x-axis
        xaxis_title="RPM",
        xaxis_dtick=1000,
        xaxis_tickformat=",.0f",
        xaxis_tickangle=45,
        xaxis_gridcolor="gray",
        xaxis_color="snow",
        # format y-axis
        yaxis_title="HP/Torque",
        yaxis_dtick=10,
        yaxis_color="snow",
        yaxis_gridcolor="gray",
        # format template
        template="plotly_dark",
        # format legend
        legend_borderwidth=1.5,
        legend_bordercolor="snow",
        # format plot and paper background
        plot_bgcolor="rgb(50, 50, 50)",
        paper_bgcolor="rgb(50, 50, 50)",
    )

# initialize Dash app
app = Dash(__name__)
FinishedRPM = False
FinishedTorque = False

# format app layout
app.layout = html.Div(
    [
        # header
        html.Div(
            [
                html.H1(
                    "Dyno Interface",
                    style={
                        "color": "snow",
                        "text-align": "center",
                        "margin-bottom": 0,
                        "font-family": "open sans",
                    },
                ),
            ]
        ),
        # date and time
        html.Div(
            [
                dcc.Interval(id="interval-component", interval=1000, n_intervals=0),
                html.H2(
                    id="live-datetime",
                    style={
                        "color": "snow",
                        "text-align": "center",
                        "font-family": "open sans",
                    },
                ),
            ]
        ),
        # dyno graph
        html.Div(
            dcc.Graph(
                id="dyno-graph",
                figure=dyno_graph,
                style={
                    "height": "60vh",
                    "margin-top": 0
                },
            )
        ),
        # files dropdown
        html.Div(
            [
                dcc.Dropdown(
                    files,
                    id="files-dropdown",
                    multi=True,
                    placeholder="Select a file",
                ),
                html.Div(id="dd-output-container"),
            ],
            style={
                "position": "absolute",
                "bottom": "12%",
                "left": "40%",
                "width": "20%",
                "font-family": "open sans",
            },
        ),
    ],
)


# callback to update the date and time
@app.callback(
    Output("live-datetime", "children"), [Input("interval-component", "n_intervals")]
)
def update_datetime(*_):
    """
    Get the current date and time and Display it in the app
    Returns: current_datetime (str): formatted date and time
    """
    current_datetime = get_current_datetime()
    return current_datetime


# callback to update the graph based on the selected files from the files-dropdown
@app.callback(Output("dyno-graph", "figure"), [Input("files-dropdown", "value")])
def update_graph(selected_files):
    """
    Update the graph based on the selected files from the files-dropdown
    Parameters: selected_files (list): list of selected files
    Returns: fig (go.Figure): plotly figure
    """

    # if no files are selected, return 
    if selected_files is None:
        return no_update

    # create a new figure
    fig = go.Figure()

    # for each selected file, generate the plot and add the data traces to the main figure
    for selected_file in selected_files:
        # construct the full path to the selected file
        file_path = os.path.join(directory_path, selected_file)

        # generate the plot for the selected file using the plot_data function
        file_fig = plot_data(file_path)

        # add the data traces of the current file to the main figure
        for trace in file_fig["data"]:
            # Add the file name as a suffix to the trace name
            trace_name = f"{trace['name']} - {selected_file}"
            trace["name"] = trace_name
            fig.add_trace(trace)

    # update the layout to retain the original formatting
    fig.update_layout(
        # format x-axis
        xaxis_title="RPM",
        xaxis_dtick=1000,
        xaxis_tickformat=",.0f",
        xaxis_tickangle=45,
        xaxis_gridcolor="gray",
        xaxis_color="snow",
        # format y-axis
        yaxis_title="HP/Torque",
        yaxis_dtick=10,
        yaxis_color="snow",
        yaxis_gridcolor="gray",
        # format template
        template="plotly_dark",
        # format legend
        legend_borderwidth=1.5,
        legend_bordercolor="snow",
        # format plot and paper background
        plot_bgcolor="rgb(50, 50, 50)",
        paper_bgcolor="rgb(50, 50, 50)",
    )

    # check the number of selected files
    num_files_selected = len(selected_files)

    # if only one file is selected, add annotations for max horsepower and max torque
    if num_files_selected == 1:
        # read in the selected file
        df = pd.read_csv(os.path.join(directory_path, selected_files[0]))
        # get the max horsepower
        max_hp = df["Horsepower"].max()
        # get the rpm value for the max horsepower
        max_hp_rpm = df.loc[df["Horsepower"].idxmax(), "RPM"]

        # get the max torque
        max_torque = df["Torque (ft-lbs)"].max()
        # get the rpm value for the max torque
        max_torque_rpm = df.loc[df["Torque (ft-lbs)"].idxmax(), "RPM"]

        # add annotations for max horsepower
        fig.add_annotation(
            x=max_hp_rpm,
            y=max_hp,
            text=f"Max HP: {round(max_hp, 1)}<br>RPM: " + "{:,}".format(max_hp_rpm),
            showarrow=True,
            arrowhead=2,
            bordercolor="snow",
            borderwidth=1.5,
            borderpad=4,
        )

        # add annotations for max torque
        fig.add_annotation(
            x=max_torque_rpm,
            y=max_torque,
            text=f"Max Torque: {round(max_torque, 1)} ft/lbs<br>RPM: "
            + "{:,}".format(max_torque_rpm),
            showarrow=True,
            arrowhead=2,
            bordercolor="snow",
            borderwidth=1.5,
            borderpad=4,
        )
    else:
        # if more than one file is selected, remove existing annotations
        fig.update_layout(annotations=[])

    # return the updated figure
    return fig



@app.callback(
    Output("files-dropdown", "options"), [Input("interval-component", "n_intervals")]
)
def update_dropdown_options(*_):
    """
    Update the files-dropdown when any change in the data directory
    occurs.
    """
    # check the current last modification time of the directory
    current_modification_time = os.path.getmtime(directory_path)

    # if the modification time is different from the last known one, update the options
    if current_modification_time != update_dropdown_options.last_modification_time:
        update_dropdown_options.last_modification_time = current_modification_time
        updated_files = get_files_in_directory(directory_path)
        dropdown_options = [{"label": file, "value": file} for file in updated_files]
        return dropdown_options

    # if the modification time is the same, return no_update to prevent unnecessary updates
    return no_update


# initialize the attribute to store the last modification time
update_dropdown_options.last_modification_time = os.path.getmtime(directory_path)


if __name__ == "__main__":
    app.run_server(debug=True)
