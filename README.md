# Sooner Racing Team Dynamometer Data Collection

## Getting started
1. Ensure you have the relevant NI-DAQ devices connected via USB
2. download the latest release and run the .exe

## Torque
Measured from the LC213-1K load cell. Voltage scales linearly based on force applied to the load cell. The slope of the output is 2mV/V(excitation). Stability of Vexcitation is key to success with this sensor.

## RPM
Measured from Tachometer output from the ECU (M130). RPM is calculated based on the frequency of the output (square wave), which always has a duty cycle of 49.9%

## File Storage
When data is collected, files are stored in the "data" folder as .csv files in the same location as the application. These can be accessed via the "Data Analysis" option in the main menu to view and compare diffferent recordings.

## Data Collection Devices
Torque is collected by the NI-9219. RPM is collected by the NI-9205. The details of these data acquisition devices can be found from the National Instruments website. To test their functionality, install the NI DAQmx drivers and the NI MAX software. 
This software assumes the signals are physically connecting to the topmost channel of both devices for voltage readings.


