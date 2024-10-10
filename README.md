# Sooner Racing Team Dynamometer Data Collection

## Torque
Measured from the LC213-1K load cell. Voltage scales linearly based on force applied to the load cell. The slope of the output is 2mV/V(excitation). Stability of Vexcitation is key to success with this sensor.
## RPM
Measured from Tachometer output from the ECU (M130). The output is an open collector, which means it must be connected to a high voltage (through a resistor to be safe) in order to properly output the expected square wave. Keep in mind this is a high voltage relative to Motec Signal Ground. RPM is calculated based on the frequency of the output, which always has a duty cycle of 49.9%

## Data Collection Devices
Torque is collected by the NI-9219. RPM is collected by the NI-9205. The details of these data acquisition devices can be found from the National Instruments website. To test their functionality, install the NI DAQmx drivers and the NI MAX software. 

## Setup
1. clone the repo and navigate to the main directory (EngineData)
2. type: python -m venv venv
3. if on windows, type: .\venv\Scripts\activate
4. If the previous command fails in an IDE, run this and try again: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
5. with the venv enabled, type: pip install -r requirements.txt
6. You are now set up and ready to run the main.py. Make sure to activate your virtual environment with venv\Scripts\activate when you launch your IDE or terminal.
7. To deactivate, simply type: deactivate

