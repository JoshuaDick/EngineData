# Sooner Racing Team Dynamometer Data Collection

## Torque
Measured from the LC213-1K load cell. Voltage scales linearly based on force applied to the load cell. The slope of the output is 2mV/V(excitation). Stability of Vexcitation is key to success with this sensor.
## RPM
Measured from Tachometer output from the ECU (M130). The output is an open collector, which means it must be connected to a high voltage (through a resistor to be safe) in order to properly output the expected square wave. RPM is calculated based on the frequency of the output, which always has a duty cycle of 49.9%
